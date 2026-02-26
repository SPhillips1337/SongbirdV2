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

        # Mock opening the template file
        with patch('builtins.open', unittest.mock.mock_open(read_data='{"3": {"inputs": {}}}')):
            self.client.submit_prompt("lyrics", "tags")

        # Verify timeout is present in kwargs
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "Timeout missing in requests.post")
        self.assertEqual(kwargs['timeout'], 120, "Timeout should be set to 120 seconds")

    @patch('requests.get')
    def test_get_history_timeout(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        self.client.get_history("123")

        # Verify timeout is present in kwargs
        args, kwargs = mock_get.call_args
        self.assertIn('timeout', kwargs, "Timeout missing in requests.get")
        self.assertEqual(kwargs['timeout'], 120, "Timeout should be set to 120 seconds")

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
        self.assertEqual(kwargs['timeout'], 120, "Timeout should be set to 120 seconds")

    @patch('tools.comfy.ComfyClient.get_history')
    @patch('tools.comfy.ComfyClient.download_file')
    def test_wait_and_download_output_robust(self, mock_download, mock_get_history):
        # Scenario: Node 104 is missing, but Node 200 has audio files
        prompt_id = "abc"
        mock_get_history.return_value = {
            prompt_id: {
                "outputs": {
                    "200": {
                        "audio": [{"filename": "robust_output.mp3", "subfolder": "", "type": "output"}]
                    }
                }
            }
        }
        mock_download.return_value = "output/robust_output.mp3"

        result = self.client.wait_and_download_output(prompt_id)

        self.assertEqual(result, "output/robust_output.mp3")
        mock_download.assert_called_once_with("robust_output.mp3", "", "output")

if __name__ == '__main__':
    unittest.main()
