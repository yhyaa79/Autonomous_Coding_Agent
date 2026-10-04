import tempfile
from pathlib import Path

from django.test import TestCase

from agent.options import AgentOptions
from agent.project_tools.loader import load_project_tool_entries
from agent.project_tools.service import create_project_tool
from agent.tool_create_budget import reset_tool_create_budget
from projects.models import Conversation, Project, SharedTool, SharedToolVersion
from projects.shared_tools import (
    attach_by_public_ref,
    create_new_version,
    delete_shared_tool,
    latest_version,
    parse_public_ref,
    register_shared_tool,
)


class SharedToolDeleteTests(TestCase):
    def test_delete_removes_tool(self):
        version = register_shared_tool(
            tool_id="to_delete",
            display_name="x",
            description="d",
            parameters={"type": "object", "properties": {}, "required": []},
            source_body='return tool_result(True, "1")',
        )
        self.assertTrue(delete_shared_tool(version.public_id))
        self.assertFalse(SharedTool.objects.filter(tool_id="to_delete").exists())


class SharedToolVersionTests(TestCase):
    def test_register_creates_new_version(self):
        v1 = register_shared_tool(
            tool_id="ver_tool",
            display_name="V",
            description="one",
            parameters={"type": "object", "properties": {}, "required": []},
            source_body='return tool_result(True, "1")',
        )
        v2 = register_shared_tool(
            tool_id="ver_tool",
            display_name="V",
            description="two",
            parameters={"type": "object", "properties": {}, "required": []},
            source_body='return tool_result(True, "2")',
            new_version=True,
        )
        self.assertEqual(v1.version_number, 1)
        self.assertEqual(v2.version_number, 2)
        self.assertEqual(SharedToolVersion.objects.filter(shared_tool__tool_id="ver_tool").count(), 2)
        self.assertEqual(latest_version(v1.shared_tool).description, "two")


class SharedToolParseTests(TestCase):
    def test_parse_uuid_and_link(self):
        uid = "a1b2c3d4-e5f6-4789-a012-3456789abcde"
        self.assertEqual(parse_public_ref(uid), uid)
        self.assertEqual(
            parse_public_ref(f"https://example.com/tool/{uid}/?conversation_id=3&project_id=1"),
            uid,
        )
        self.assertEqual(parse_public_ref(f"aca-tool:{uid}"), uid)


class SharedToolConversationFilterTests(TestCase):
    def setUp(self):
        reset_tool_create_budget()
        self.tmp_path = Path(tempfile.mkdtemp())
        self.project = Project.objects.create(name="P", root_path=str(self.tmp_path))
        self.conv_a = Conversation.objects.create(project=self.project, title="A")
        self.conv_b = Conversation.objects.create(project=self.project, title="B")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp_path, ignore_errors=True)

    def test_tool_visible_only_in_attached_conversation(self):
        opts_a = AgentOptions(
            workspace_root=str(self.tmp_path),
            project_id=self.project.id,
            conversation_id=self.conv_a.id,
            allow_write=True,
        )
        body = 'return tool_result(True, "ok")'
        out = create_project_tool(
            "conv_tool",
            "توضیح",
            {"type": "object", "properties": {}, "required": []},
            body,
            opts_a,
            test_arguments={},
        )
        self.assertTrue(out.startswith("OK:"))
        self.assertEqual(SharedTool.objects.filter(tool_id="conv_tool").count(), 1)

        entries_a = load_project_tool_entries(
            self.project.id, self.tmp_path, self.conv_a.id
        )
        self.assertEqual(len(entries_a), 1)

        entries_b = load_project_tool_entries(
            self.project.id, self.tmp_path, self.conv_b.id
        )
        self.assertEqual(len(entries_b), 0)

        shared = SharedTool.objects.get(tool_id="conv_tool")
        version = latest_version(shared)
        self.assertIsNotNone(version)
        attach_by_public_ref(self.conv_b, version.public_id)
        entries_b2 = load_project_tool_entries(
            self.project.id, self.tmp_path, self.conv_b.id
        )
        self.assertEqual(len(entries_b2), 1)

    def test_prompt_resource_versioning(self):
        family = SharedTool.objects.create(tool_id="guide", display_name="راهنما")
        create_new_version(
            family,
            description="v1",
            parameters={},
            source_body="",
            content_blocks=[{"type": "text", "text": "hello"}],
            content_kind="prompt",
        )
        v2 = create_new_version(
            family,
            description="v2",
            parameters={},
            source_body="",
            content_blocks=[{"type": "text", "text": "world"}],
            content_kind="prompt",
        )
        self.assertEqual(v2.version_number, 2)
