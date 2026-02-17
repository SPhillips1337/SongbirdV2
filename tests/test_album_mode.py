import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import argparse

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestAlbumMode(unittest.TestCase):

    def setUp(self):
        self.patcher = patch.dict('sys.modules', {
            'langgraph': MagicMock(),
            'langgraph.graph': MagicMock(),
            'psycopg2': MagicMock(),
            'dotenv': MagicMock(),
            'tools.rag': MagicMock(),
            # Do NOT mock requests here if we want to patch it specifically later?
            # Or mock it here and patch it later?
            # Safer to mock it here if app.py imports it at top level.
            'requests': MagicMock()
        })
        self.patcher.start()

        # We must import app AFTER patching modules
        if 'app' in sys.modules:
            del sys.modules['app']
        import app
        self.app_module = app

        from config import ALBUM_MODEL
        self.ALBUM_MODEL = ALBUM_MODEL

    def tearDown(self):
        self.patcher.stop()

    def test_album_mode_loop(self):
        # We need to patch symbols in the imported app module
        with patch('app.SongbirdWorkflow') as MockWorkflow, \
             patch('app.scan_recent_songs') as mock_scan, \
             patch('requests.post') as mock_post:

            # Setup mocks
            mock_flow_instance = MockWorkflow.return_value
            mock_flow_instance.run.return_value = {
                "audio_path": "output/test_song.mp3",
                "cleaned_lyrics": "Test lyrics",
                "musical_direction": "Test direction"
            }

            # Mock scan_recent_songs
            mock_scan.return_value = [
                {
                    "number": 1,
                    "artist": "Test Artist",
                    "background": "Test Background",
                    "lyrics_snippet": "Test Lyrics Snippet",
                    "musical_direction": "Test Musical Direction"
                }
            ]

            # Mock Ollama response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "Next song direction"}
            mock_post.return_value = mock_response

            # Mock sys.argv
            test_args = [
                "app.py",
                "--album",
                "--theme", "Test Album Theme",
                "--num-songs", "2",
                "--base-direction", "Rock music"
            ]

            with patch.object(sys, 'argv', test_args):
                self.app_module.main()

            # Verify calls
            self.assertEqual(mock_flow_instance.run.call_count, 2)

            # First call
            call_args_list = mock_flow_instance.run.call_args_list
            first_call_args = call_args_list[0]
            # args: (genre, user_direction, ...)
            self.assertEqual(first_call_args[0][0], "POP")
            self.assertIn("Test Album Theme", first_call_args[0][1])

            # Second call
            second_call_args = call_args_list[1]
            self.assertEqual(second_call_args[0][0], "POP")
            self.assertEqual(second_call_args[0][1], "Next song direction")

if __name__ == '__main__':
    unittest.main()
