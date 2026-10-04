import json
import threading
import time

from django.test import SimpleTestCase

from agent.user_input_gate import (
    assistant_text_promised_user_form,
    create_user_input_request,
    execute_ask_user,
    iter_ask_user,
    redact_ask_user_step,
    resolve_user_input,
    wait_user_input,
)


class UserInputGateTests(SimpleTestCase):
    def test_invalid_fields_returns_error(self):
        events, result = execute_ask_user({"title": "x", "fields": []})
        self.assertEqual(events, [])
        self.assertTrue(result.startswith("ERROR:"))

    def test_wait_user_input_resolves(self):
        rid = create_user_input_request(
            "t",
            "m",
            [{"id": "a", "label": "A", "type": "text", "required": True}],
        )

        def _resolve():
            time.sleep(0.05)
            resolve_user_input(rid, {"cancelled": False, "values": {"a": "v"}})

        threading.Thread(target=_resolve, daemon=True).start()
        resp = wait_user_input(rid, timeout=2.0)
        self.assertIsNotNone(resp)
        self.assertEqual(resp["values"]["a"], "v")

    def test_iter_ask_user_yields_request_before_wait(self):
        holder: list[dict] = []

        def worker():
            gen = iter_ask_user({"title": "T", "fields": [{"id": "x", "label": "X"}]})
            try:
                while True:
                    holder.append(next(gen))
            except StopIteration:
                pass

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        time.sleep(0.05)
        self.assertEqual(len(holder), 1)
        self.assertEqual(holder[0]["type"], "user_input_request")
        from agent.user_input_gate import _pending

        rid = holder[0]["request_id"]
        self.assertIn(rid, _pending)
        resolve_user_input(rid, {"cancelled": False, "values": {"x": "1"}})
        t.join(timeout=3)

    def test_execute_ask_user_end_to_end(self):
        holder: list[tuple] = []

        def worker():
            holder.append(
                execute_ask_user({"title": "T", "fields": [{"id": "x", "label": "X"}]})
            )

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        time.sleep(0.05)
        from agent.user_input_gate import _pending

        self.assertEqual(len(_pending), 1)
        rid = next(iter(_pending.keys()))
        resolve_user_input(rid, {"cancelled": False, "values": {"x": "1"}, "notes": "n"})
        t.join(timeout=3)
        self.assertTrue(holder)
        events, result = holder[0]
        self.assertEqual(events[0]["type"], "user_input_request")
        self.assertIn('"x": "1"', result)

    def test_assistant_text_promised_user_form(self):
        text = (
            "برای اتصال به سرور به IP، نام کاربری و گذرواژه نیاز دارم. "
            "لطفاً این اطلاعات را در فرم زیر وارد کنید."
        )
        self.assertTrue(assistant_text_promised_user_form(text))

    def test_wait_user_input_cancelled_by_run(self):
        from agent.run_control import request_cancel, start_run

        run_id = start_run(99)
        rid = create_user_input_request(
            "t",
            "m",
            [{"id": "a", "label": "A", "type": "text", "required": True}],
            run_id=run_id,
        )

        def _cancel():
            time.sleep(0.05)
            request_cancel(99, run_id)

        threading.Thread(target=_cancel, daemon=True).start()
        resp = wait_user_input(rid, timeout=5.0, run_id=run_id)
        self.assertIsNotNone(resp)
        self.assertTrue(resp.get("cancelled"))

    def test_redact_ask_user_step_masks_password(self):
        step = {
            "tool": "ask_user",
            "args": {
                "fields": [{"id": "pass", "type": "password", "label": "P"}],
            },
            "result": 'OK: {"values": {"pass": "secret"}, "notes": "x"}',
        }
        out = redact_ask_user_step(step)
        data = json.loads(out["result"].split(":", 1)[1].strip())
        self.assertEqual(data["values"]["pass"], "••••••••")
