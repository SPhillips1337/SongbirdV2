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
        # Ensure cache is empty or mocked
        with patch('tools.cache.CacheManager') as MockCache:
             MockCache.return_value.get.return_value = None
             self.client = PerplexityClient()
             self.client.cache = MagicMock()
             self.client.cache.get.return_value = None

    def tearDown(self):
        if "PERPLEXITY_API_KEY" in os.environ:
             del os.environ["PERPLEXITY_API_KEY"]
        if "PERPLEXICA_URL" in os.environ:
             del os.environ["PERPLEXICA_URL"]

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

        # Verify that requests.post was called with timeout=60 (updated from 240)
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['timeout'], 60, "Timeout should be 60 seconds")

    @patch('requests.post')
    def test_perplexica_search(self, mock_post):
        # Setup mock for Perplexica
        os.environ["PERPLEXICA_URL"] = "http://localhost:3000"
        # Unset API key to force local usage
        if "PERPLEXITY_API_KEY" in os.environ:
            del os.environ["PERPLEXITY_API_KEY"]

        # Mock cache for this instance too
        with patch('tools.cache.CacheManager'):
             client = PerplexityClient()
             client.cache = MagicMock()
             client.cache.get.return_value = None
        
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": "Perplexica result"}
        mock_post.return_value = mock_response

        # Call search
        result = client.search("test query")
        
        # Verify URL and format
        self.assertIsNotNone(client.local_url)
        self.assertIn("/api/search", client.local_url)
        self.assertEqual(result, "Perplexica result")
        
        # specific request format
        args, kwargs = mock_post.call_args
        self.assertIn("focusMode", kwargs['json'])
