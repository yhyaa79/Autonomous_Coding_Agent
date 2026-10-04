from django.test import TestCase

from projects.conversation_feed import build_conversation_timeline, make_topic_summary
from projects.models import ChatMessage, Conversation, ConversationFeedItem, Project


class ConversationFeedTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name="p", root_path="/tmp/aca-test-p")

    def test_topic_summary_truncates(self):
        s = make_topic_summary("یک دو سه چهار پنج شش هفت", max_words=4)
        self.assertIn("…", s)
        self.assertLessEqual(len(s.split()), 5)

    def test_timeline_interleaves_phase_and_credits(self):
        conv = Conversation.objects.create(project=self.project, title="t")
        ChatMessage.objects.create(conversation=conv, role=ChatMessage.ROLE_USER, content="hi")
        ConversationFeedItem.objects.create(
            conversation=conv,
            turn_index=0,
            sub_order=0,
            kind=ConversationFeedItem.KIND_PHASE,
            payload={"type": "phase", "label": "شروع", "phase": "start"},
        )
        ChatMessage.objects.create(
            conversation=conv, role=ChatMessage.ROLE_ASSISTANT, content="hello"
        )
        ConversationFeedItem.objects.create(
            conversation=conv,
            turn_index=0,
            sub_order=1,
            kind=ConversationFeedItem.KIND_CREDITS,
            payload={"total_credits": "0.5"},
        )
        timeline = build_conversation_timeline(conv)
        kinds = [t["type"] for t in timeline]
        self.assertEqual(
            kinds,
            ["message", "phase_log", "message", "credits"],
        )
