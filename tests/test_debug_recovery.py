from django.test import SimpleTestCase, override_settings

from agent.debug_recovery import DebugTracker


@override_settings(
    AGENT_DEBUG_RETRY_THRESHOLD=3,
    AGENT_DEBUG_HINT_THRESHOLD=2,
    AGENT_DEBUG_MAX_RECOVERIES=2,
)
class DebugTrackerFlowTests(SimpleTestCase):
    def _tracker(self) -> DebugTracker:
        return DebugTracker(project_id=None, workspace=__import__("pathlib").Path("."))

    def test_none_on_first_error(self):
        t = self._tracker()
        self.assertEqual(t.handle_failure("read_file", "ERROR: missing", {}), "none")

    def test_hint_on_second_same_error(self):
        t = self._tracker()
        err = "ERROR: same"
        t.handle_failure("read_file", err, {})
        self.assertEqual(t.handle_failure("read_file", err, {}), "hint")
        self.assertEqual(t.handle_failure("read_file", err, {}), "recover")

    def test_recover_at_threshold(self):
        t = self._tracker()
        err = "ERROR: stuck"
        for _ in range(3):
            action = t.handle_failure("run_shell", err, {})
        self.assertEqual(action, "recover")
        self.assertTrue(t.can_recover())

    def test_escalate_after_max_recoveries(self):
        t = self._tracker()
        err = "ERROR: stuck"
        t.recovery_count = t.max_recoveries
        for _ in range(3):
            action = t.handle_failure("run_shell", err, {})
        self.assertEqual(action, "escalate")

    def test_build_error_hint_contains_tool(self):
        t = self._tracker()
        text = t.build_error_hint(
            [{"tool": "write_file", "result": "ERROR: denied"}]
        )
        self.assertIn("write_file", text)
        self.assertIn("ERROR: denied", text)
