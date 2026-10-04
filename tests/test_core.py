from pathlib import Path

from django.test import SimpleTestCase, TestCase

from agent.history import (
    enrich_assistant_content,
    estimate_history_tokens,
    summarize_tool_steps,
    trim_chat_history,
)
from agent.model_catalog import model_context_window
from agent.options import AgentOptions
from agent.registry import ensure_agents_loaded, get_agent
from agent.scope import format_search_match, merge_scope_paths, path_in_scope, paths_from_scope_note
from agent.security import project_path_allowed, shell_command_allowed
from agent.store import AGENT_STORE_DIR, is_private_relative, path_is_private
from agent.tool_registry import all_tool_ids
from agent.workspace import WorkspaceError, resolve_in_workspace


class WorkspaceTests(SimpleTestCase):
    def test_resolve_blocks_traversal(self):
        root = Path("/tmp/aca-test-root").resolve()
        root.mkdir(parents=True, exist_ok=True)
        try:
            with self.assertRaises(WorkspaceError):
                resolve_in_workspace(root, "../etc/passwd")
        finally:
            root.rmdir()

    def test_scope(self):
        self.assertTrue(path_in_scope("src/foo.py", ["src"]))
        self.assertFalse(path_in_scope("lib/x.py", ["src"]))

    def test_paths_from_scope_note(self):
        note = "src/app.py\nاین یک جمله است\nagent/loop.py"
        self.assertEqual(paths_from_scope_note(note), ["src/app.py", "agent/loop.py"])

    def test_merge_scope_paths(self):
        self.assertEqual(merge_scope_paths(["src"], ["lib"]), ["src", "lib"])

    def test_search_match_masks_outside_focus(self):
        inside = format_search_match("src/a.py", 10, "secret line", ["src"])
        self.assertIn("secret line", inside)
        outside = format_search_match("lib/b.py", 3, "secret line", ["src"])
        self.assertIn("lib/b.py:3:", outside)
        self.assertNotIn("secret line", outside)


class SecurityTests(SimpleTestCase):
    def test_shell_block(self):
        self.assertIsNotNone(shell_command_allowed("rm -rf /"))

    def test_allowlist_empty_allows(self):
        self.assertTrue(project_path_allowed("/any/path"))

    def test_shell_blocks_agent_store(self):
        self.assertIsNotNone(shell_command_allowed(f"cat {AGENT_STORE_DIR}/backups/x/manifest.json"))

    def test_private_store_paths(self):
        self.assertTrue(is_private_relative(f"{AGENT_STORE_DIR}/backups/token"))
        self.assertTrue(is_private_relative(".agent/debug/attempts.jsonl"))
        self.assertFalse(is_private_relative("src/main.py"))
        root = Path("/tmp/aca-private-root").resolve()
        root.mkdir(parents=True, exist_ok=True)
        try:
            self.assertTrue(path_is_private(root, f"{AGENT_STORE_DIR}/runtime/custom_tools/x.py"))
        finally:
            root.rmdir()


class ScopePriorityTests(SimpleTestCase):
    def test_user_scope_over_inferred(self):
        opts = AgentOptions(
            scope_paths=["src"],
            inferred_scope_paths=["lib"],
        )
        self.assertTrue(opts.has_user_scope())
        self.assertEqual(opts.effective_scope(), ["src"])

    def test_inferred_when_no_user(self):
        opts = AgentOptions(scope_paths=[], inferred_scope_paths=["agent"])
        self.assertFalse(opts.has_user_scope())
        self.assertEqual(opts.effective_scope(), ["agent"])
        self.assertEqual(opts.enforced_scope(), [])

    def test_enforced_only_with_user_scope(self):
        opts = AgentOptions(scope_paths=["src"], inferred_scope_paths=["lib"])
        self.assertEqual(opts.enforced_scope(), ["src"])


class HistoryTests(SimpleTestCase):
    def test_tool_summary(self):
        steps = [{"tool": "read_file", "args": {"path": "a.py"}, "result": "OK: line 1"}]
        s = summarize_tool_steps(steps)
        self.assertIn("read_file", s)
        out = enrich_assistant_content("done", steps)
        self.assertIn("خلاصه", out)

    def test_trim(self):
        hist = [{"role": "user", "content": "a"}] * 10
        t = trim_chat_history(hist, 2)
        self.assertEqual(len(t), 4)

    def test_estimate_history_tokens(self):
        hist = [
            {"role": "user", "content": "abcd"},
            {"role": "assistant", "content": "efgh"},
        ]
        self.assertEqual(estimate_history_tokens(hist), 2)

    def test_model_context_window(self):
        self.assertGreater(model_context_window("gpt-4o-mini"), 1000)


class AgentRegistryTests(TestCase):
    def test_all_agent_tools_registered(self):
        ensure_agents_loaded()
        known = set(all_tool_ids())
        for aid in ("coding", "seo", "social", "maintenance", "marketing", "autonomous"):
            spec = get_agent(aid)
            missing = [t for t in spec.tool_definition_ids if t not in known]
            self.assertEqual(missing, [], msg=f"{aid} missing tools: {missing}")
