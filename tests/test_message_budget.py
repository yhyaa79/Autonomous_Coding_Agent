from django.test import SimpleTestCase

from agent.message_budget import (
    prepare_messages_for_chat_completion,
    truncate_tool_arguments_json,
    trim_history_message_content,
)


class MessageBudgetTests(SimpleTestCase):
    def test_truncate_patch_arguments(self):
        raw = '{"path":"a.html","old_string":"' + ("x" * 5000) + '","new_string":"y"}'
        out = truncate_tool_arguments_json(raw, max_field=200)
        parsed = __import__("json").loads(out)
        self.assertLessEqual(len(parsed["old_string"]), 250)
        self.assertIn("truncated", parsed["old_string"])

    def test_trim_tool_summary_in_history(self):
        body = "reply " * 100
        summary = "line\n" * 800
        text = body + "\n\n[خلاصهٔ ابزارهای این نوبت]\n" + summary
        trimmed = trim_history_message_content(text)
        self.assertLess(len(trimmed), len(text))
        self.assertIn("[خلاصهٔ ابزارهای این نوبت]", trimmed)

    def test_prepare_drops_middle_when_over_cap(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "system", "content": "scope"},
            {"role": "user", "content": "u1 " * 5000},
            {"role": "assistant", "content": "a1 " * 5000},
            {"role": "user", "content": "u2"},
        ]
        out = prepare_messages_for_chat_completion(
            msgs, "gpt-4o-mini", aggressive=True
        )
        self.assertGreaterEqual(len(out), 3)
        self.assertEqual(out[-1]["content"], "u2")
