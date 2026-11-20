import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient


class APIWorkflowTest(unittest.TestCase):
    def test_approval_required_and_live_disabled(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {'SOCIAL_FACTORY_OUTPUT': td, 'ENABLE_LIVE_PUBLISH':'false', 'OPENAI_BASE_URL':'', 'RENDER_ENGINE':'demo'}):
                import importlib
                import app as app_module
                importlib.reload(app_module)
                client = TestClient(app_module.app)
                r = client.get('/health'); self.assertEqual(r.status_code, 200)
                r = client.post('/api/jobs', json={'topic':'Three ways to learn French', 'platforms':['youtube','tiktok']})
                self.assertEqual(r.status_code, 200, r.text)
                jid = r.json()['id']
                self.assertTrue(client.get(f'/api/jobs/{jid}/video').content)
                self.assertEqual(client.post(f'/api/jobs/{jid}/publish', json={'confirm':'PUBLISH'}).status_code, 409)
                self.assertEqual(client.post(f'/api/jobs/{jid}/approve').status_code, 200)
                self.assertEqual(client.post(f'/api/jobs/{jid}/publish', json={'confirm':'PUBLISH'}).status_code, 403)
                self.assertEqual(client.get('/api/jobs').status_code, 200)
