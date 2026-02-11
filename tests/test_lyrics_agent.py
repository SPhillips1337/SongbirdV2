import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.lyrics import LyricsAgent
from config import OLLAMA_BASE_URL, LYRIC_MODEL

class TestLyricsAgent(unittest.TestCase):
    def test_init(self):
        agent = LyricsAgent()
        self.assertEqual(agent.base_url, OLLAMA_BASE_URL)
        self.assertEqual(agent.model, LYRIC_MODEL)

    @patch('requests.post')
    def test_write_lyrics_node(self, mock_post):
        # Mock responses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "[Intro]\nTest lyrics"}
        mock_post.return_value = mock_response

        agent = LyricsAgent()

        # Mock internal tools
        agent.perplexity.search = MagicMock(return_value="Search results")
        agent.rag.query_lightrag = MagicMock(return_value="RAG results")

        state = {
            "genre": "POP",
            "artist_name": "Test Artist",
            "artist_background": "Background",
            "artist_style": "Style",
            "user_direction": "Make it pop",
        }

        new_state = agent.write_lyrics_node(state)

        self.assertEqual(new_state["lyrics"], "[Intro]\nTest lyrics")

        # Verify that requests.post was called with the correct URL and model
        mock_post.assert_called_with(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": LYRIC_MODEL, "prompt": unittest.mock.ANY, "stream": False},
            timeout=90
        )

if __name__ == '__main__':
    unittest.main()
