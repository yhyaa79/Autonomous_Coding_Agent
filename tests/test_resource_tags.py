from django.test import TestCase

from projects.resource_tags import normalize_resource_tags, resource_agent_guide_snippet
from projects.shared_tools import create_knowledge_resource


class ResourceTagTests(TestCase):
    def test_normalize_tags_dedupes_and_filters(self):
        self.assertEqual(
            normalize_resource_tags(["connection", "time", "connection", "invalid"]),
            ["connection", "time"],
        )

    def test_create_resource_stores_tags(self):
        version = create_knowledge_resource(
            tool_id="ssh_conn_test",
            display_name="SSH",
            description="اتصال تست",
            content_kind="prompt",
            tags=["connection", "ops"],
        )
        family = version.shared_tool
        family.refresh_from_db()
        self.assertEqual(family.tags, ["connection", "ops"])

    def test_agent_guide_mentions_tags(self):
        guide = resource_agent_guide_snippet()
        self.assertIn("time", guide)
        self.assertIn("connection", guide)


class ConversationToolsUiTests(TestCase):
    def test_attached_tool_appears_only_in_that_conversation(self):
        from agent.project_tools.service import create_project_tool
        from agent.options import AgentOptions
        from agent.tool_create_budget import reset_tool_create_budget
        from projects.models import Conversation, Project
        from projects.shared_tools import list_tools_for_conversation_ui
        import tempfile
        from pathlib import Path
        import shutil

        reset_tool_create_budget()
        tmp = Path(tempfile.mkdtemp())
        try:
            project = Project.objects.create(name="P", root_path=str(tmp))
            conv_a = Conversation.objects.create(project=project, title="A")
            conv_b = Conversation.objects.create(project=project, title="B")
            opts = AgentOptions(
                project_id=project.id,
                conversation_id=conv_a.id,
                workspace_root=str(tmp),
                allow_write=True,
            )
            create_project_tool(
                "ui_list_tool",
                "for ui",
                {"type": "object", "properties": {}, "required": []},
                'return tool_result(True, "ok")',
                opts,
            )
            tools_a = list_tools_for_conversation_ui(conv_a)
            ids_a = {t["tool_id"] for t in tools_a}
            self.assertIn("ui_list_tool", ids_a)
            tools_b = list_tools_for_conversation_ui(conv_b)
            self.assertEqual(tools_b, [])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
