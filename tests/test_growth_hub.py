from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from projects.growth_hub import apply_hub_patch, get_or_create_hub, hub_public_dict
from projects.models import Project


class GrowthHubTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="gh", password="gh")
        self.project = Project.objects.create(
            name="p",
            root_path="/tmp",
            owner=self.user,
        )

    def test_get_or_create_hub_has_tasks(self):
        hub = get_or_create_hub(self.project)
        data = hub_public_dict(hub)
        self.assertGreaterEqual(len(data["maintenance_tasks"]), 4)
        self.assertGreaterEqual(len(data["marketing_tasks"]), 4)
        self.assertIn("telegram", data["channels"])

    def test_apply_toggle_task(self):
        hub = get_or_create_hub(self.project)
        ok, _ = apply_hub_patch(
            hub,
            {"toggle_task": {"list": "maintenance", "task_id": "m_health", "done": True}},
        )
        self.assertTrue(ok)
        hub.refresh_from_db()
        row = next(t for t in hub.maintenance_tasks if t["id"] == "m_health")
        self.assertTrue(row["done"])

    def test_api_get_authenticated(self):
        client = Client()
        client.force_login(self.user)
        r = client.get(f"/api/projects/{self.project.id}/growth-hub/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("growth_hub", body)
        self.assertIn("maintenance_tasks", body["growth_hub"])
