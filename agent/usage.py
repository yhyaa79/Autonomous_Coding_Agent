"""جمع‌آوری مصرف توکن از پاسخ API و برآورد در صورت نبود usage."""

from dataclasses import dataclass, field
from typing import Any

from .model_catalog import credits_for_tokens, resolve_model_id


def _estimate_tokens(text: str) -> int:
    """برآورد محافظه‌کار: ~۴ کاراکتر به ازای ۱ توکن."""
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)


def _messages_char_count(messages: list[dict[str, Any]]) -> int:
    total = 0
    for m in messages:
        c = m.get("content")
        if isinstance(c, str):
            total += len(c)
        elif c is not None:
            total += len(str(c))
        tool_calls = m.get("tool_calls")
        if tool_calls:
            total += len(str(tool_calls))
    return total


@dataclass
class UsageSlice:
    model: str
    prompt_tokens: int
    completion_tokens: int
    estimated: bool = False

    def credits(self) -> tuple[str, str, str]:
        _in, _out, total = credits_for_tokens(
            self.model, self.prompt_tokens, self.completion_tokens
        )
        return str(_in), str(_out), str(total)


@dataclass
class UsageTracker:
    slices: list[UsageSlice] = field(default_factory=list)

    def add_completion(
        self,
        model: str,
        response: Any,
        *,
        messages_for_estimate: list[dict[str, Any]] | None = None,
        completion_text: str = "",
    ) -> None:
        mid = resolve_model_id(model)
        usage = getattr(response, "usage", None)
        if usage is not None:
            prompt = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion = int(getattr(usage, "completion_tokens", 0) or 0)
            if prompt or completion:
                self.slices.append(
                    UsageSlice(
                        model=mid,
                        prompt_tokens=prompt,
                        completion_tokens=completion,
                        estimated=False,
                    )
                )
                return
        prompt_est = _estimate_tokens(
            str(messages_for_estimate) if messages_for_estimate else ""
        )
        if messages_for_estimate:
            prompt_est = max(
                prompt_est,
                _estimate_tokens("".join(str(m.get("content", "")) for m in messages_for_estimate)),
            )
        completion_est = _estimate_tokens(completion_text)
        self.slices.append(
            UsageSlice(
                model=mid,
                prompt_tokens=prompt_est,
                completion_tokens=completion_est,
                estimated=True,
            )
        )

    @property
    def prompt_tokens(self) -> int:
        return sum(s.prompt_tokens for s in self.slices)

    @property
    def completion_tokens(self) -> int:
        return sum(s.completion_tokens for s in self.slices)

    def total_credits(self) -> str:
        from decimal import Decimal

        total = Decimal("0")
        for s in self.slices:
            *_, t = credits_for_tokens(s.model, s.prompt_tokens, s.completion_tokens)
            total += t
        return str(total.quantize(Decimal("0.000001")))

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_credits": self.total_credits(),
            "slices": [
                {
                    "model": s.model,
                    "prompt_tokens": s.prompt_tokens,
                    "completion_tokens": s.completion_tokens,
                    "estimated": s.estimated,
                    "input_credits": s.credits()[0],
                    "output_credits": s.credits()[1],
                    "total_credits": s.credits()[2],
                }
                for s in self.slices
            ],
        }
