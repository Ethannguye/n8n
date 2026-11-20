import os
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from provider import make_script, ProviderError, publish_upload_post
from renderer import render_demo


class DemoTests(unittest.TestCase):
    def test_no_key_uses_template(self):
        with patch.dict(os.environ, {'OPENAI_BASE_URL':'', 'OPENAI_API_KEY':'', 'OPENAI_MODEL':''}):
            s = make_script('Studying French', 'English')
        self.assertIn('Studying French', s)
        self.assertIn('Demo template', s)

    def test_demo_mp4_has_content(self):
        with tempfile.TemporaryDirectory() as td:
            p = render_demo('French language tips', 'Tip one. Tip two. Tip three.', Path(td) / 'clip.mp4')
            self.assertTrue(p.is_file())
            self.assertGreater(p.stat().st_size, 5000)
            self.assertIn(b'ftyp', p.read_bytes()[:20])

    def test_live_publisher_requires_api_credentials(self):
        with patch.dict(os.environ, {'UPLOAD_POST_API_KEY': '', 'UPLOAD_POST_USER': ''}):
            with tempfile.TemporaryDirectory() as td:
                video = Path(td) / 'test.mp4'
                video.write_bytes(b'mp4')
                with self.assertRaises(ProviderError):
                    publish_upload_post(video=video, platforms=['youtube'], title='Test', description='Demo', job_id='test-1')


if __name__ == '__main__':
    unittest.main()
