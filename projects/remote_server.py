"""اتصال SSH پروژه — ذخیرهٔ رمزنگاری‌شده و بارگذاری برای اجرای ایجنت روی سرور."""

from __future__ import annotations

import base64
import hashlib
import posixpath
import re
import socket
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from .models import Project, ProjectServerConnection

_FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/=]+$")


def _fernet_key() -> bytes:
    material = (settings.SECRET_KEY + ":aca-project-ssh-v1").encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plain: str) -> str:
    from cryptography.fernet import Fernet

    token = (plain or "").strip()
    if not token:
        raise ValueError("مقدار خالی است")
    return Fernet(_fernet_key()).encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_secret(cipher: str) -> str:
    from cryptography.fernet import Fernet

    if not cipher:
        return ""
    return Fernet(_fernet_key()).decrypt(cipher.encode("ascii")).decode("utf-8")


@dataclass(frozen=True)
class RemoteServerConfig:
    host: str
    port: int
    username: str
    auth_method: str
    secret: str
    passphrase: str
    remote_root_path: str
    strict_host_key: bool
    host_key_fingerprint: str
    allow_server_wide_paths: bool = False


def connection_row(project: Project) -> ProjectServerConnection | None:
    try:
        return project.server_connection
    except Exception:
        return None


def project_remote_config(project: Project) -> RemoteServerConfig | None:
    row = connection_row(project)
    if not row or not row.is_enabled:
        return None
    host = (row.host or "").strip()
    username = (row.username or "").strip()
    root = (row.remote_root_path or "").strip()
    if not host or not username or not root:
        return None
    if not row.secret_encrypted:
        return None
    try:
        secret = decrypt_secret(row.secret_encrypted)
    except Exception:
        return None
    passphrase = ""
    if row.key_passphrase_encrypted:
        try:
            passphrase = decrypt_secret(row.key_passphrase_encrypted)
        except Exception:
            passphrase = ""
    return RemoteServerConfig(
        host=host,
        port=int(row.port or 22),
        username=username,
        auth_method=row.auth_method or ProjectServerConnection.AUTH_PASSWORD,
        secret=secret,
        passphrase=passphrase,
        remote_root_path=posixpath.normpath(root),
        strict_host_key=bool(row.strict_host_key),
        host_key_fingerprint=(row.host_key_fingerprint or "").strip(),
        allow_server_wide_paths=bool(row.allow_server_wide_paths),
    )


def project_uses_remote(project: Project) -> bool:
    return project_remote_config(project) is not None


def remote_root_path_from_request(
    body: dict,
    row: ProjectServerConnection | None,
) -> str:
    """مسیر SSH روی سرور؛ اگر در body ارسال شده باشد به root_path لوکال پروژه برنمی‌گردد."""
    if "remote_root_path" in body:
        return (body.get("remote_root_path") or "").strip()
    if row:
        return (row.remote_root_path or "").strip()
    return ""


def public_status(project: Project) -> dict:
    local_root = (project.root_path or "").strip()
    row = connection_row(project)
    if not row:
        return {
            "configured": False,
            "enabled": False,
            "host": "",
            "port": 22,
            "username": "",
            "auth_method": "password",
            "remote_root_path": "",
            "local_root_path": local_root,
            "strict_host_key": True,
            "host_key_fingerprint": "",
            "has_secret": False,
            "allow_server_wide_paths": False,
        }
    return {
        "configured": bool(row.secret_encrypted and row.host and row.username),
        "enabled": bool(row.is_enabled),
        "host": row.host or "",
        "port": int(row.port or 22),
        "username": row.username or "",
        "auth_method": row.auth_method or "password",
        "remote_root_path": (row.remote_root_path or "").strip(),
        "local_root_path": local_root,
        "strict_host_key": bool(row.strict_host_key),
        "host_key_fingerprint": (row.host_key_fingerprint or "").strip(),
        "has_secret": bool(row.secret_encrypted),
        "allow_server_wide_paths": bool(row.allow_server_wide_paths),
    }


def validate_remote_root_path(path: str) -> str:
    p = posixpath.normpath((path or "").strip())
    if not p.startswith("/"):
        raise ValueError("مسیر پروژه روی سرور باید مطلق باشد (با / شروع شود)")
    if p in ("/", "."):
        raise ValueError("مسیر پروژه روی سرور نامعتبر است")
    if ".." in p.split("/"):
        raise ValueError("مسیر پروژه روی سرور نامعتبر است")
    return p


def validate_fingerprint(fp: str) -> str:
    fp = (fp or "").strip()
    if not fp:
        return ""
    if not _FINGERPRINT_RE.fullmatch(fp):
        raise ValueError("فرمت fingerprint باید SHA256:… باشد")
    return fp


def test_ssh_connection(config: RemoteServerConfig) -> dict:
    from agent.remote_ssh import RemoteSSHSession

    session = RemoteSSHSession(config)
    try:
        session.connect()
        fingerprint = session.server_fingerprint()
        cwd_ok, cwd_msg = session.verify_remote_root()
        return {
            "ok": True,
            "fingerprint": fingerprint,
            "remote_root": config.remote_root_path,
            "remote_root_check": cwd_msg if cwd_ok else cwd_msg,
            "remote_root_ok": cwd_ok,
        }
    finally:
        session.close()


def resolve_remote_relative(
    remote_root: str,
    relative_path: str,
    *,
    allow_server_wide: bool = False,
) -> str:
    """مسیر مطلق روی سرور؛ پیش‌فرض فقط داخل remote_root."""
    raw = (relative_path or ".").strip().replace("\\", "/")
    if allow_server_wide and raw.startswith("/"):
        combined = posixpath.normpath(raw)
        if ".." in combined.split("/"):
            raise ValueError(f"Path outside workspace: {relative_path}")
        return combined
    root = posixpath.normpath(remote_root.rstrip("/") or "/")
    rel = raw.lstrip("/")
    if rel in ("", "."):
        return root
    combined = posixpath.normpath(posixpath.join(root, rel))
    if combined != root and not combined.startswith(root + "/"):
        raise ValueError(f"Path outside workspace: {relative_path}")
    return combined
