"""کاتالوگ مدل‌ها — قیمت به ازای ۱ میلیون توکن (واحد: اعتبار ACA).

۱ اعتبار ≈ ۰٫۰۰۱ USD (قابل تنظیم با ACA_CREDIT_USD_RATE در settings).
"""

from decimal import Decimal
from typing import Any

from django.conf import settings

BYOK_MODEL_ID = "__aca_user_api__"


def _d(value: str | float) -> Decimal:
    return Decimal(str(value))


# قیمت‌ها بر اساس نرخ‌های رایج OpenAI/GapGPT (USD per 1M tokens) × 1000 → اعتبار
MODEL_CATALOG: list[dict[str, Any]] = [
    {
        "id": "gpt-4o-mini",
        "label": "GPT-4o mini",
        "input_per_million": _d("150"),
        "output_per_million": _d("600"),
        "context_window_tokens": 128_000,
    },
    {
        "id": "gpt-4o",
        "label": "GPT-4o",
        "input_per_million": _d("2500"),
        "output_per_million": _d("10000"),
        "context_window_tokens": 128_000,
    },
    {
        "id": "gpt-4.1-mini",
        "label": "GPT-4.1 mini",
        "input_per_million": _d("400"),
        "output_per_million": _d("1600"),
        "context_window_tokens": 1_047_576,
    },
    {
        "id": "gpt-4.1",
        "label": "GPT-4.1",
        "input_per_million": _d("2000"),
        "output_per_million": _d("8000"),
        "context_window_tokens": 1_047_576,
    },
    {
        "id": "o3-mini",
        "label": "o3-mini",
        "input_per_million": _d("1100"),
        "output_per_million": _d("4400"),
        "context_window_tokens": 200_000,
    },
    {
        "id": "o1-mini",
        "label": "o1-mini",
        "input_per_million": _d("1100"),
        "output_per_million": _d("4400"),
        "context_window_tokens": 128_000,
    },
    {
        "id": "deepseek-chat",
        "label": "DeepSeek Chat",
        "input_per_million": _d("140"),
        "output_per_million": _d("280"),
        "context_window_tokens": 64_000,
    },
    {
        "id": "gemini-2.0-flash",
        "label": "Gemini 2.0 Flash",
        "input_per_million": _d("100"),
        "output_per_million": _d("400"),
        "context_window_tokens": 1_048_576,
    },
]

_CATALOG_BY_ID: dict[str, dict[str, Any]] = {m["id"]: m for m in MODEL_CATALOG}


def default_model_id() -> str:
    return getattr(settings, "GAPGPT_MODEL", "gpt-4o-mini") or "gpt-4o-mini"


def catalog_model_ids() -> set[str]:
    return set(_CATALOG_BY_ID.keys())


def get_model_entry(model_id: str | None) -> dict[str, Any] | None:
    mid = (model_id or "").strip()
    if not mid:
        return None
    if mid in _CATALOG_BY_ID:
        return _CATALOG_BY_ID[mid]
    return None


def model_context_window(model_id: str | None) -> int:
    mid = resolve_model_id(model_id)
    if is_byok_model_id(mid):
        return int(getattr(settings, "AGENT_BYOK_CONTEXT_WINDOW_TOKENS", 128_000))
    entry = get_model_entry(mid)
    if entry and entry.get("context_window_tokens"):
        return int(entry["context_window_tokens"])
    return 128_000


def resolve_model_id(model_id: str | None) -> str:
    mid = (model_id or "").strip() or default_model_id()
    if mid == BYOK_MODEL_ID:
        return mid
    if mid in _CATALOG_BY_ID:
        return mid
    return default_model_id()


def is_byok_model_id(model_id: str | None) -> bool:
    return (model_id or "").strip() == BYOK_MODEL_ID


def models_for_api() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for m in MODEL_CATALOG:
        inp = m["input_per_million"]
        out_p = m["output_per_million"]
        out.append(
            {
                "id": m["id"],
                "label": m["label"],
                "input_per_million_credits": str(inp),
                "output_per_million_credits": str(out_p),
                "input_per_1k_credits": str((inp / _d("1000")).quantize(_d("0.000001"))),
                "output_per_1k_credits": str((out_p / _d("1000")).quantize(_d("0.000001"))),
                "context_window_tokens": int(m.get("context_window_tokens") or 128_000),
            }
        )
    return out


def credits_for_tokens(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> tuple[Decimal, Decimal, Decimal]:
    """برمی‌گرداند: (هزینه ورودی، هزینه خروجی، جمع)."""
    entry = get_model_entry(model_id)
    if not entry:
        entry = get_model_entry(default_model_id()) or MODEL_CATALOG[0]
    pin = max(int(prompt_tokens or 0), 0)
    pout = max(int(completion_tokens or 0), 0)
    million = _d("1000000")
    in_cost = (Decimal(pin) / million) * entry["input_per_million"]
    out_cost = (Decimal(pout) / million) * entry["output_per_million"]
    total = in_cost + out_cost
    quant = Decimal("0.000001")
    return (
        in_cost.quantize(quant),
        out_cost.quantize(quant),
        total.quantize(quant),
    )
