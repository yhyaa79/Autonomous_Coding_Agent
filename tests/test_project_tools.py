import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from agent.options import AgentOptions
from agent.project_tools.service import create_project_tool, list_project_tools
from agent.tool_create_budget import reset_tool_create_budget
from agent.project_tools.validator import (
    ToolValidationError,
    normalize_source_body,
    validate_instagram_publish_body,
    validate_run_body,
    validate_tool_id,
)


class ProjectToolValidatorTests(SimpleTestCase):
    def test_tool_id(self):
        self.assertEqual(validate_tool_id("my_tool"), "my_tool")
        with self.assertRaises(ToolValidationError):
            validate_tool_id("Bad-ID")

    def test_run_body_blocks_os(self):
        with self.assertRaises(ToolValidationError):
            validate_run_body("import os\nreturn tool_result(True, 'x')")

    def test_run_body_rejects_nested_run(self):
        body = (
            "def run(arguments, options):\n"
            "    def run(arguments, options):\n"
            "        return tool_result(True, 'x')\n"
            "    return tool_result(True, 'y')\n"
        )
        with self.assertRaises(ToolValidationError):
            validate_run_body(body)

    def test_run_body_requires_top_level_return(self):
        with self.assertRaises(ToolValidationError):
            validate_run_body("x = 1")

    def test_run_body_allows_braces_in_user_code(self):
        body = (
            "for i in range(3):\n"
            "    msg = f'Number: {i}'\n"
            "return tool_result(True, msg)"
        )
        validate_run_body(body)

    def test_normalize_peels_def_run_wrapper(self):
        wrapped = (
            "def run(arguments, options):\n"
            "    for i in range(2):\n"
            "        x = f'n{i}'\n"
            "    return tool_result(True, 'ok')\n"
        )
        inner = normalize_source_body(wrapped)
        self.assertNotIn("def run", inner)
        validate_run_body(inner)

    def test_run_body_allows_return_in_try_except(self):
        body = (
            "client = None\n"
            "try:\n"
            "    x = 1\n"
            "    return tool_result(True, 'ok')\n"
            "except Exception as e:\n"
            "    return tool_result(False, str(e))\n"
            "finally:\n"
            "    pass\n"
        )
        validate_run_body(body)

    def test_normalize_keeps_import_before_def_run(self):
        wrapped = (
            "import paramiko\n"
            "\n"
            "def run():\n"
            "    return tool_result(True, 'ok')\n"
        )
        inner = normalize_source_body(wrapped)
        self.assertIn("import paramiko", inner)
        self.assertNotIn("def run", inner)
        validate_run_body(inner)

    def test_run_body_rejects_parameters_get(self):
        with self.assertRaises(ToolValidationError) as ctx:
            validate_run_body(
                "username = parameters.get('username')\n"
                "return tool_result(True, username)"
            )
        self.assertIn("arguments", str(ctx.exception))

    def test_instagram_stub_rejected(self):
        stub = (
            "username = arguments.get('username')\n"
            "return tool_result(True, 'استوری با موفقیت ارسال شد')"
        )
        with self.assertRaises(ToolValidationError) as ctx:
            validate_instagram_publish_body(
                stub,
                "instagram_post_tool",
                "ابزار ارسال استوری به اینستاگرام",
                {
                    "type": "object",
                    "properties": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "story_text": {"type": "string"},
                    },
                },
            )
        self.assertIn("post_instagram_text_story", str(ctx.exception))

    def test_instagram_real_helper_allowed(self):
        body = (
            "from agent.tool_impl import post_instagram_text_story\n"
            "return post_instagram_text_story(\n"
            "    arguments.get('username'),\n"
            "    arguments.get('password'),\n"
            "    arguments.get('story_text'),\n"
            "    options,\n"
            ")"
        )
        validate_instagram_publish_body(
            body,
            "instagram_post_tool",
            "استوری اینستاگرام",
            {"type": "object", "properties": {"story_text": {"type": "string"}}},
        )

    def test_run_body_rejects_read_workspace_text_with_dict(self):
        with self.assertRaises(ToolValidationError) as ctx:
            validate_run_body(
                "from agent.tool_impl import read_workspace_text\n"
                "t = read_workspace_text('x.json', {})\n"
                "return tool_result(True, t)"
            )
        self.assertIn("options", str(ctx.exception))


class ProjectToolCreateTests(SimpleTestCase):
    def setUp(self):
        reset_tool_create_budget()

    def test_create_and_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            opts = AgentOptions(
                workspace_root=tmp,
                project_id=42,
                allow_write=True,
            )
            body = 'return tool_result(True, "hello")'
            out = create_project_tool(
                "demo_tool",
                "تست",
                {"type": "object", "properties": {}, "required": []},
                body,
                opts,
                test_arguments={},
            )
            self.assertTrue(out.startswith("OK:"))
            listed = list_project_tools(opts)
            self.assertIn("demo_tool", listed)

    def test_wrapped_def_run_is_normalized_and_writes(self):
        reset_tool_create_budget()
        with tempfile.TemporaryDirectory() as tmp:
            opts = AgentOptions(
                workspace_root=tmp,
                project_id=42,
                allow_write=True,
            )
            wrapped = (
                "def run(arguments, options):\n"
                "    return tool_result(True, 'ok')\n"
            )
            out = create_project_tool(
                "wrapped_tool",
                "x",
                {"type": "object", "properties": {}, "required": []},
                wrapped,
                opts,
            )
            self.assertTrue(out.startswith("OK:"))
            mod = Path(tmp) / ".aca/runtime/custom_tools/tools/wrapped_tool.py"
            self.assertTrue(mod.is_file())

    def test_bad_body_does_not_write_file(self):
        reset_tool_create_budget()
        with tempfile.TemporaryDirectory() as tmp:
            opts = AgentOptions(
                workspace_root=tmp,
                project_id=42,
                allow_write=True,
            )
            bad = "import os\nreturn tool_result(True, 'bad')"
            out = create_project_tool(
                "bad_tool",
                "x",
                {"type": "object", "properties": {}, "required": []},
                bad,
                opts,
            )
            self.assertTrue(out.startswith("ERROR:"))
            mod = Path(tmp) / ".aca/runtime/custom_tools/tools/bad_tool.py"
            self.assertFalse(mod.is_file())

    def test_count_file_lines_pattern(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "log_time.py"
            sample.write_text("a\nb\nc\n", encoding="utf-8")
            opts = AgentOptions(
                workspace_root=tmp,
                project_id=7,
                allow_write=True,
            )
            body = (
                'path = (arguments.get("path") or "").strip()\n'
                "if not path:\n"
                '    return tool_result(False, "path")\n'
                "from agent.tool_impl import read_workspace_text\n"
                "text = read_workspace_text(path, options)\n"
                'if text.startswith("ERROR:"):\n'
                "    return text\n"
                'return tool_result(True, str(len(text.splitlines())))'
            )
            out = create_project_tool(
                "count_file_lines",
                "شمارش خطوط",
                {
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                    "required": ["path"],
                },
                body,
                opts,
                test_arguments={"path": "log_time.py"},
            )
            self.assertTrue(out.startswith("OK:"))
