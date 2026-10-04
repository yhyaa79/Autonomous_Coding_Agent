from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from projects.debug_hub import execute_scan, get_or_create_profile, hub_public_dict
from projects.debug_scanner import run_page_debug_scan
from projects.models import Project


class DebugScannerTests(TestCase):
    def test_normalize_requires_url(self):
        result = run_page_debug_scan("", ["ui"])
        self.assertFalse(result["ok"])
        self.assertTrue(result["error"])

    @patch("projects.debug_scanner._fetch_page")
    def test_ui_finding_no_viewport(self, mock_fetch):
        html = b"<html><head><title>Test</title></head><body><h1>x</h1></body></html>"
        mock_fetch.return_value = (html, {"content-type": "text/html"}, 120.0, 200)
        result = run_page_debug_scan("https://example.com", ["ui"])
        self.assertTrue(result["ok"])
        titles = [f["title"] for f in result["findings"]]
        self.assertTrue(any("viewport" in t for t in titles))


class DebugHubApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="dbg", password="dbg")
        self.project = Project.objects.create(
            name="p",
            root_path="/tmp",
            owner=self.user,
        )

    def test_hub_public_has_categories(self):
        data = hub_public_dict(self.project)
        self.assertGreaterEqual(len(data["categories"]), 6)
        profile = get_or_create_profile(self.project)
        self.assertIsNotNone(profile)

    @patch("projects.debug_hub.run_page_debug_scan")
    def test_execute_scan_persists(self, mock_run):
        mock_run.return_value = {
            "ok": True,
            "url": "https://example.com",
            "categories": ["ui"],
            "findings": [],
            "metrics": {"status_code": 200},
            "summary": {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "error": "",
        }
        scan = execute_scan(self.project, "https://example.com", ["ui"])
        self.assertEqual(scan.status, "completed")

    def test_api_get_authenticated(self):
        client = Client()
        client.force_login(self.user)
        r = client.get(f"/api/projects/{self.project.id}/debug-hub/")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("debug_hub", body)
        self.assertIn("categories", body["debug_hub"])
