import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.comfy import ComfyClient

class TestComfyClient(unittest.TestCase):
    def setUp(self):
        self.client = ComfyClient(url="http://mock-url")

    @patch('requests.post')
    def test_submit_prompt_timeout(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"prompt_id": "123"}
        mock_post.return_value = mock_response

        self.client.submit_prompt("lyrics", "tags")

        # Verify timeout is present in kwargs
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "Timeout missing in requests.post")
        self.assertEqual(kwargs['timeout'], 30, "Timeout should be set to 30 seconds")

    @patch('requests.get')
    def test_get_history_timeout(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        self.client.get_history("123")

        # Verify timeout is present in kwargs
        args, kwargs = mock_get.call_args
        self.assertIn('timeout', kwargs, "Timeout missing in requests.get")
        self.assertEqual(kwargs['timeout'], 30, "Timeout should be set to 30 seconds")

    @patch('requests.get')
    def test_download_file_timeout(self, mock_get):
        mock_response = MagicMock()
        mock_response.content = b"data"
        mock_get.return_value = mock_response

        # Mock open to avoid writing files
        with patch('builtins.open', unittest.mock.mock_open()):
            self.client.download_file("test.mp3", "", "output")

        # Verify timeout is present in kwargs
        args, kwargs = mock_get.call_args
        self.assertIn('timeout', kwargs, "Timeout missing in requests.get")
        self.assertEqual(kwargs['timeout'], 30, "Timeout should be set to 30 seconds")

if __name__ == '__main__':
    unittest.main()
