"""ردیابی شکست ابزار، بازیابی خودکار، و در نهایت ارجاع خطا به کاربر."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from django.conf import settings
from openai import OpenAI

from agent.options import AgentOptions
from agent.phase_context import emit_phase_event
from agent.phases import phase_event

FailureAction = Literal["none", "hint", "recover", "escalate"]


@dataclass
class DebugTracker:
    """ردیابی خطا در یک اجرای agent."""

    project_id: int | None
    workspace: Path
    threshold: int = 3
    hint_threshold: int = 2
    _signatures: list[str] = field(default_factory=list)
    _total_errors: int = 0
    recovery_count: int = 0
    max_recoveries: int = 2
    _hint_sent: set[str] = field(default_factory=set)
    escalated: bool = False
    escalation_count: int = 0

    def __post_init__(self) -> None:
        self.threshold = int(
            getattr(settings, "AGENT_DEBUG_RETRY_THRESHOLD", self.threshold)
        )
        self.max_recoveries = int(
            getattr(settings, "AGENT_DEBUG_MAX_RECOVERIES", self.max_recoveries)
        )
        self.hint_threshold = int(
            getattr(settings, "AGENT_DEBUG_HINT_THRESHOLD", self.hint_threshold)
        )

    def _signature(self, tool: str, result: str) -> str:
        return f"{tool}|{(result or '')[:160]}"

    def handle_failure(
        self,
        tool: str,
        result: str,
        args: dict[str, Any] | None,
    ) -> FailureAction:
        """تعیین اقدام بعد از ERROR ابزار: hint → recover (AI) → escalate به کاربر."""
        if not (result or "").startswith("ERROR:"):
            return "none"
        self._total_errors += 1
        sig = self._signature(tool, result)
        self._signatures.append(sig)
        self._append_log(tool, result, args)
        counts = Counter(self._signatures)
        sig_count = counts[sig]
        at_threshold = sig_count >= self.threshold or (
            self._total_errors >= self.threshold * 2
            and self._total_errors % self.threshold == 0
        )
        if at_threshold:
            if self.can_recover():
                return "recover"
            if not self.escalated:
                return "escalate"
            return "none"
        if (
            sig_count >= self.hint_threshold
            and sig not in self._hint_sent
            and sig_count < self.threshold
        ):
            self._hint_sent.add(sig)
            return "hint"
        return "none"

    def build_error_hint(self, recent_failures: list[dict[str, Any]]) -> str:
        lines = [
            "[ACA Debug — خطای تکراری]",
            "همان خطا دوباره رخ داد. قبل از فراخوانی مجدد همان ابزار با همان ورودی:",
            "۱) علت را از متن ERROR استخراج کن.",
            "۲) رویکرد را عوض کن (مسیر دیگر، ابزار دیگر، یا اصلاح کد/ابزار سفارشی).",
            "۳) در صورت ابزار پروژه: list_project_tools و create_project_tool با replace_existing.",
            "",
            "خطاهای اخیر (خلاصه):",
        ]
        for step in recent_failures[-5:]:
            tool = step.get("tool", "?")
            res = str(step.get("result", ""))[:240]
            lines.append(f"- {tool}: {res}")
        return "\n".join(lines)

    def _append_log(
        self,
        tool: str,
        result: str,
        args: dict[str, Any] | None,
    ) -> None:
        if not self.project_id:
            return
        from agent.project_data import append_debug_attempt

        append_debug_attempt(
            self.project_id,
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "tool": tool,
                "result": (result or "")[:500],
                "args": args or {},
            },
        )

    def can_recover(self) -> bool:
        return self.recovery_count < self.max_recoveries

    def run_recovery_analysis(
        self,
        client: OpenAI,
        user_message: str,
        recent_failures: list[dict[str, Any]],
        options: AgentOptions,
    ) -> str:
        self.recovery_count += 1
        emit_phase_event(
            phase_event(
                "debug_analyze",
                f"تلاش {self.recovery_count}/{self.max_recoveries}",
            )
        )
        model = options.model or settings.GAPGPT_MODEL
        failures_text = json.dumps(recent_failures[-8:], ensure_ascii=False, indent=2)
        prompt = f"""چند بار ابزارها برای این درخواست خطا دادند. به‌عنوان دیباگر ACA تحلیل کن:

درخواست کاربر:
{user_message}

خطاهای اخیر:
{failures_text}

خروجی فارسی و عملی:
1. علت محتمل
2. راه‌حل جایگزین (ابزار دیگر، تغییر رویکرد)
3. گام بعدی مشخص برای agent

قوانین create_project_tool:
- tool_id جدید با پسوند _v2/_v3 نسازید؛ همان tool_id با replace_existing:true و source_body اصلاح‌شده.
- source_body بدون def run تودرتو؛ فقط return tool_result(...) در سطح run.
- برای خواندن فایل: from agent.tool_impl import read_file (نه open).
- بعد از خطا: list_project_tools و سپس create_project_tool با همان tool_id و replace_existing:true، یا test_project_tool.
- فایل‌های داخلی ایجنت را با read_file یا apply_patch باز نکن."""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are ACA debug assistant for one project."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.25,
            )
            text = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            text = (
                "تحلیل خودکار خطا ناموفق بود.\n"
                f"({type(exc).__name__}: {exc})\n\n"
                "۱) متن ERROR را بخوان و علت را اصلاح کن.\n"
                "۲) ابزار یا مسیر دیگر امتحان کن.\n"
                "۳) در صورت ابزار پروژه: list_project_tools و create_project_tool با replace_existing."
            )
        emit_phase_event(phase_event("debug_strategy", "اعمال راه‌حل جایگزین"))
        from agent.project_data import save_debug_recovery

        save_debug_recovery(self.project_id, text + "\n")
        return text

    def run_user_escalation(
        self,
        client: OpenAI,
        user_message: str,
        recent_failures: list[dict[str, Any]],
        options: AgentOptions,
    ) -> str:
        """پس از اتمام بازیابی خودکار، گزارش فارسی برای کاربر."""
        self.escalated = True
        self.escalation_count += 1
        emit_phase_event(
            phase_event(
                "debug_escalate",
                "ارجاع خطا به کاربر — بازیابی خودکار تمام شد",
            )
        )
        model = options.model or settings.GAPGPT_MODEL
        failures_text = json.dumps(recent_failures[-12:], ensure_ascii=False, indent=2)
        prompt = f"""ایجنت ACA پس از چند بار خطای ابزار و {self.recovery_count} بار تحلیل/بازیابی خودکار
هنوز نتوانست مشکل را حل کند. برای کاربر نهایی یک پیام فارسی بنویس (نه برای ایجنت).

درخواست کاربر:
{user_message}

خطاهای ثبت‌شده:
{failures_text}

پیام باید شامل این بخش‌ها باشد:
1. عنوان کوتاه که ایجنت به خطای غیرقابل رفع خودکار برخورد
2. خلاصهٔ plain-language از خطا (چه ابزاری، چه پیامی ERROR)
3. علت محتمل به زبان ساده
4. پیشنهاد عملی برای کاربر (چه چیزی را دستی بررسی/اصلاح کند)
5. جملهٔ صریح: از این نقطه به بعد ادامهٔ کار بر عهدهٔ کاربر است و ایجنت بدون راهنمایی جدید
   یا تغییر شرایط (مثلاً اجازهٔ write/shell، اصلاح فایل، یا دستور جدید) ادامه نمی‌دهد.

متن ERROR خام را در بلوک جداگانهٔ «جزئیات فنی» بگذار. لحن محترمانه و روشن."""
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You write clear Persian status messages for developers.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            text = (response.choices[0].message.content or "").strip()
        except Exception as exc:
            last = recent_failures[-1] if recent_failures else {}
            text = (
                "ایجنت پس از چند تلاش خودکار برای رفع خطا موفق نشد.\n\n"
                f"آخرین خطا ({last.get('tool', 'ابزار')}): "
                f"{str(last.get('result', ''))[:400]}\n\n"
                f"({type(exc).__name__}: {exc})\n\n"
                "از این نقطه به بعد ادامهٔ کار بر عهدهٔ شماست؛ "
                "شرایط را اصلاح کنید یا درخواست جدید با جزئیات بیشتر بفرستید."
            )
        from agent.project_data import save_debug_escalation

        save_debug_escalation(self.project_id, text + "\n")
        return text
