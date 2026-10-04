from django.test import SimpleTestCase

from agent.code_changes import (
    _highlight_lines,
    diff_file_maps,
    file_maps_differ,
)


class CodeChangesTests(SimpleTestCase):
    def test_detects_modified_file(self):
        before = {"a.py": b"x = 1\n"}
        after = {"a.py": b"x = 2\n"}
        self.assertTrue(file_maps_differ(before, after))
        files = diff_file_maps(before, after)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["status"], "modified")
        self.assertGreater(files[0]["insertions"] + files[0]["deletions"], 0)

    def test_detects_added_removed(self):
        before = {"old.py": b"print(1)\n"}
        after = {"new.py": b"print(2)\n"}
        files = diff_file_maps(before, after)
        statuses = {f["path"]: f["status"] for f in files}
        self.assertEqual(statuses["old.py"], "removed")
        self.assertEqual(statuses["new.py"], "added")

    def test_ignores_agent_store_paths(self):
        before = {"main.py": b"a\n", ".aca/backups/x/payload/main.py": b"b\n"}
        after = {"main.py": b"a\n", ".aca/runtime/foo.py": b"c\n"}
        self.assertFalse(file_maps_differ(before, after))
        self.assertEqual(diff_file_maps(before, after), [])

    def test_highlight_truncates_with_context(self):
        before = (
            "head\n"
            + "unchanged\n" * 20
            + "old_a\n"
            + "middle\n" * 20
            + "old_b\n"
            + "tail\n" * 20
        )
        after = (
            "head\n"
            + "unchanged\n" * 20
            + "new_a\n"
            + "middle\n" * 20
            + "new_b\n"
            + "tail\n" * 20
        )
        h = _highlight_lines(before, after)
        self.assertLess(len(h["before_lines"]), len(before.splitlines()))
        self.assertIn("old_a", h["before_lines"])
        self.assertIn("old_b", h["before_lines"])
        self.assertIn("new_a", h["after_lines"])
        gap = next(l for l in h["before_lines"] if l.startswith("▼"))
        self.assertIn("برای خوانایی نمایش داده نشده", gap)
        self.assertTrue(any(m == "-" for m in h["before_marks"]))
        self.assertTrue(any(m == "+" for m in h["after_marks"]))
