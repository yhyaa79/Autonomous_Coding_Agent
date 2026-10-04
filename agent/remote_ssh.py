"""کلاینت SSH/SFTP برای workspace راه‌دور."""

from __future__ import annotations

import base64
import hashlib
import shlex
import socket
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from projects.remote_server import RemoteServerConfig


class RemoteSSHError(Exception):
    pass


def _paramiko():
    try:
        import paramiko
    except ImportError:
        raise RemoteSSHError(
            "پکیج paramiko نصب نیست — در محیط مجازی: pip install -r requirements.txt"
        ) from None
    return paramiko


def _fingerprint_sha256(key: Any) -> str:
    digest = hashlib.sha256(key.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


def _normalize_fingerprint(fp: str) -> str:
    """مقایسهٔ پایدار fingerprint (بدون تفاوت padding)."""
    fp = (fp or "").strip()
    if not fp.upper().startswith("SHA256:"):
        return fp
    body = fp[7:].rstrip("=")
    return "SHA256:" + body


class RemoteSSHSession:
    def __init__(self, config: RemoteServerConfig) -> None:
        self._config = config
        self._client: Any = None
        self._sftp: Any = None

    @property
    def config(self) -> RemoteServerConfig:
        return self._config

    def connect(self) -> None:
        if self._client is not None:
            return
        paramiko = _paramiko()
        client = paramiko.SSHClient()
        # تأیید host key در اپ با fingerprint ذخیره‌شده است، نه ~/.ssh/known_hosts
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        kwargs: dict = {
            "hostname": self._config.host,
            "port": self._config.port,
            "username": self._config.username,
            "timeout": 30,
            "banner_timeout": 30,
            "auth_timeout": 30,
            "allow_agent": False,
            "look_for_keys": False,
        }
        if self._config.auth_method == "private_key":
            key_text = self._config.secret
            passphrase = self._config.passphrase or None
            try:
                pkey = paramiko.RSAKey.from_private_key(
                    file_obj=__import__("io").StringIO(key_text), password=passphrase
                )
            except paramiko.SSHException:
                try:
                    pkey = paramiko.Ed25519Key.from_private_key(
                        file_obj=__import__("io").StringIO(key_text), password=passphrase
                    )
                except paramiko.SSHException:
                    pkey = paramiko.ECDSAKey.from_private_key(
                        file_obj=__import__("io").StringIO(key_text), password=passphrase
                    )
            kwargs["pkey"] = pkey
        else:
            kwargs["password"] = self._config.secret

        try:
            client.connect(**kwargs)
        except (paramiko.SSHException, socket.error, OSError) as exc:
            raise RemoteSSHError(str(exc)) from exc

        transport = client.get_transport()
        if transport is None:
            client.close()
            raise RemoteSSHError("اتصال SSH برقرار نشد")
        key = transport.get_remote_server_key()
        fp = _fingerprint_sha256(key)
        if self._config.strict_host_key:
            expected = (self._config.host_key_fingerprint or "").strip()
            if expected and _normalize_fingerprint(expected) != _normalize_fingerprint(fp):
                client.close()
                raise RemoteSSHError("fingerprint سرور با مقدار ذخیره‌شده مطابقت ندارد")
        self._client = client

    def server_fingerprint(self) -> str:
        self.connect()
        transport = self._client.get_transport() if self._client else None
        if transport is None:
            raise RemoteSSHError("اتصال SSH نیست")
        return _fingerprint_sha256(transport.get_remote_server_key())

    def sftp(self) -> Any:
        self.connect()
        if self._sftp is None:
            self._sftp = self._client.open_sftp()
        return self._sftp

    def close(self) -> None:
        if self._sftp is not None:
            try:
                self._sftp.close()
            except OSError:
                pass
            self._sftp = None
        if self._client is not None:
            try:
                self._client.close()
            except OSError:
                pass
            self._client = None

    def verify_remote_root(self) -> tuple[bool, str]:
        root = self._config.remote_root_path
        try:
            st = self.sftp().stat(root)
        except OSError as exc:
            return (
                False,
                f"مسیر روی سرور در دسترس نیست: {exc}. "
                f"مسیر باید روی VPS لینوکس باشد (مثلاً /root/...)، نه مسیر مک مثل /Users/...",
            )
        import stat as stat_mod

        if not stat_mod.S_ISDIR(st.st_mode):
            return False, "remote_root پوشه نیست"
        return True, "پوشهٔ پروژه روی سرور تأیید شد"

    def exec_command(
        self,
        command: str,
        cwd_abs: str,
        timeout: int,
    ) -> tuple[int, str, str]:
        paramiko = _paramiko()
        self.connect()
        if self._client is None:
            raise RemoteSSHError("اتصال SSH نیست")
        inner = f"cd {shlex.quote(cwd_abs)} && {command}"
        wrapped = f"bash -lc {shlex.quote(inner)}"
        try:
            _stdin, stdout, stderr = self._client.exec_command(wrapped, timeout=timeout)
        except paramiko.SSHException as exc:
            raise RemoteSSHError(str(exc)) from exc
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        code = stdout.channel.recv_exit_status()
        return code, out, err

    def abs_path(self, rel: str) -> str:
        from projects.remote_server import resolve_remote_relative

        cfg = self._config
        raw = (rel or ".").strip().replace("\\", "/")
        if cfg.allow_server_wide_paths and raw.startswith("/"):
            return resolve_remote_relative(
                cfg.remote_root_path,
                raw,
                allow_server_wide=True,
            )
        return resolve_remote_relative(cfg.remote_root_path, rel)
