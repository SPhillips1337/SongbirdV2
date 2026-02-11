import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.perplexity import PerplexityClient

class TestPerplexityClient(unittest.TestCase):
    def setUp(self):
        self.api_key = "test_api_key"
        os.environ["PERPLEXITY_API_KEY"] = self.api_key
        self.client = PerplexityClient()

    def tearDown(self):
        del os.environ["PERPLEXITY_API_KEY"]

    @patch('requests.post')
    def test_search_timeout(self, mock_post):
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test content"}}]
        }
        mock_post.return_value = mock_response

        # Call the method
        self.client.search("test query")

        # Verify that requests.post was called with timeout
        args, kwargs = mock_post.call_args
        self.assertIn('timeout', kwargs, "requests.post should be called with a timeout parameter")
