import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import argparse

# Robust Mocking: Mock missing dependencies before app imports
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app
from config import ALBUM_MODEL

class TestAlbumMode(unittest.TestCase):

    @patch('app.SongbirdWorkflow')
    @patch('app.scan_recent_songs')
    @patch('requests.post')
    def test_album_mode_loop(self, mock_post, mock_scan, MockWorkflow):
        # Setup mocks
        mock_flow_instance = MockWorkflow.return_value
        mock_flow_instance.run.return_value = {
            "audio_path": "output/test_song.mp3",
            "cleaned_lyrics": "Test lyrics",
            "musical_direction": "Test direction"
        }

        # Mock scan_recent_songs to return dummy data
        mock_scan.return_value = [
            {
                "number": 1,
                "artist": "Test Artist",
                "background": "Test Background",
                "lyrics_snippet": "Test Lyrics Snippet",
                "musical_direction": "Test Musical Direction"
            }
        ]

        # Mock Ollama response for generate_next_direction
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Next song direction"}
        mock_post.return_value = mock_response

        # Mock sys.argv to simulate CLI arguments
        test_args = [
            "app.py",
            "--album",
            "--theme", "Test Album Theme",
            "--num-songs", "2",
            "--base-direction", "Rock music"
        ]

        with patch.object(sys, 'argv', test_args):
            app.main()

        # Verify calls
        # Expected calls to flow.run: 2 times
        self.assertEqual(mock_flow_instance.run.call_count, 2)

        # First call should have the initial direction
        call_args_list = mock_flow_instance.run.call_args_list
        first_call_args = call_args_list[0]
        # args are (genre, user_direction)
        # genre default is POP
        self.assertEqual(first_call_args[0][0], "POP")
        self.assertIn("Test Album Theme", first_call_args[0][1])
        self.assertIn("Rock music", first_call_args[0][1])

        # Second call should use the generated direction
        second_call_args = call_args_list[1]
        self.assertEqual(second_call_args[0][0], "POP")
        self.assertEqual(second_call_args[0][1], "Next song direction")

        # Verify scan_recent_songs was called once (for the second song)
        self.assertEqual(mock_scan.call_count, 1)

        # Verify requests.post (Ollama) was called once (for the second song)
        self.assertEqual(mock_post.call_count, 1)
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs['json']['model'], ALBUM_MODEL)
        self.assertIn("Test Album Theme", kwargs['json']['prompt'])

if __name__ == '__main__':
    unittest.main()
