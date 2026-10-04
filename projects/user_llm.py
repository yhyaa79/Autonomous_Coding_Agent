"""کلید API شخصی کاربر (BYOK) — ذخیرهٔ رمزنگاری‌شده و مسیر مدل امن."""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

from agent.model_catalog import BYOK_MODEL_ID


def _fernet_key() -> bytes:
    material = (settings.SECRET_KEY + ":aca-user-llm-v1").encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_api_key(plain: str) -> str:
    from cryptography.fernet import Fernet

    token = (plain or "").strip()
    if not token:
        raise ValueError("کلید API خالی است")
    return Fernet(_fernet_key()).encrypt(token.encode("utf-8")).decode("ascii")


def decrypt_api_key(cipher: str) -> str:
    from cryptography.fernet import Fernet

    if not cipher:
        return ""
    return Fernet(_fernet_key()).decrypt(cipher.encode("ascii")).decode("utf-8")


@dataclass(frozen=True)
class UserLlmRuntime:
    api_key: str
    base_url: str
    remote_model: str


def user_llm_settings_row(user):
    from .models import UserLlmSettings

    if not user or not getattr(user, "is_authenticated", False):
        return None
    try:
        return user.llm_settings
    except UserLlmSettings.DoesNotExist:
        return None


def user_llm_configured(user) -> bool:
    row = user_llm_settings_row(user)
    return bool(row and row.is_enabled and row.api_key_encrypted and row.remote_model)


def user_llm_public_status(user) -> dict:
    row = user_llm_settings_row(user)
    if not row or not row.is_enabled or not row.api_key_encrypted:
        return {
            "configured": False,
            "has_key": False,
            "base_url": "",
            "remote_model": "",
            "byok_model_id": BYOK_MODEL_ID,
        }
    return {
        "configured": True,
        "has_key": True,
        "base_url": row.base_url or "",
        "remote_model": row.remote_model or "",
        "byok_model_id": BYOK_MODEL_ID,
        "label": row.display_label(),
    }


def load_user_llm_runtime(user) -> UserLlmRuntime | None:
    row = user_llm_settings_row(user)
    if not row or not row.is_enabled or not row.api_key_encrypted or not row.remote_model:
        return None
    try:
        key = decrypt_api_key(row.api_key_encrypted)
    except Exception:
        return None
    if not key:
        return None
    base = (row.base_url or "").strip() or getattr(settings, "GAPGPT_BASE_URL", "")
    return UserLlmRuntime(api_key=key, base_url=base, remote_model=row.remote_model.strip())


def conversation_uses_byok(conv) -> bool:
    from agent.model_catalog import is_byok_model_id

    return is_byok_model_id(conv.llm_model or "")


def apply_byok_to_agent_options(opts, user) -> None:
    """فقط سمت سرور — هرگز از بدنهٔ درخواست کلید نمی‌گیریم."""
    from agent.model_catalog import resolve_model_id

    mid = resolve_model_id(opts.model)
    opts.billing_exempt = False
    opts.llm_api_key = None
    opts.llm_base_url = None

    if mid != BYOK_MODEL_ID:
        return
    if not user:
        raise ValueError("استفاده از API شخصی نیاز به ورود دارد")
    runtime = load_user_llm_runtime(user)
    if not runtime:
        raise ValueError("کلید API شخصی در تنظیمات ذخیره نشده یا غیرفعال است")
    opts.billing_exempt = True
    opts.llm_api_key = runtime.api_key
    opts.llm_base_url = runtime.base_url
    opts.model = runtime.remote_model


def validate_remote_api_key(api_key: str, base_url: str, remote_model: str) -> None:
    """یک درخواست سبک برای اطمینان از اعتبار کلید قبل از ذخیره."""
    from openai import AuthenticationError, OpenAI

    client = OpenAI(
        api_key=api_key.strip(),
        base_url=(base_url or "").strip() or getattr(settings, "GAPGPT_BASE_URL", ""),
    )
    try:
        client.chat.completions.create(
            model=remote_model.strip(),
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
    except AuthenticationError:
        raise ValueError("کلید API نامعتبر است")
    except Exception as exc:
        msg = str(exc).strip() or type(exc).__name__
        raise ValueError(f"اتصال به API برقرار نشد: {msg}")
