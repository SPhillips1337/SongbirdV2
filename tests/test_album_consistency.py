import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Add parent directory to path to find app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import SongbirdWorkflow
from state import SongState

class TestAlbumConsistency(unittest.TestCase):
    def setUp(self):
        self.workflow = SongbirdWorkflow()
        # Mock internal agents
        self.workflow.artist_agent = MagicMock()
        self.workflow.music_agent = MagicMock()
        self.workflow.lyrics_agent = MagicMock()
        self.workflow.comfy = MagicMock()

        # Mock the compiled graph invocation
        self.workflow.app = MagicMock()

    def test_run_passes_seed(self):
        """Test that run() passes the seed to the initial state."""
        seed = 12345
        self.workflow.run("ROCK", "Test Direction", seed=seed)

        # Check if app.invoke was called with the seed in initial_state
        args, _ = self.workflow.app.invoke.call_args
        initial_state = args[0]
        self.assertEqual(initial_state["seed"], seed)

    def test_node_create_artist_respects_existing_state(self):
        """Test that node_create_artist does not regenerate if style/background exist."""
        state = {
            "genre": "ROCK",
            "user_direction": "Test",
            "artist_style": "Existing Style",
            "artist_background": "Existing Background",
            "artist_name": None
        }

        new_state = self.workflow.node_create_artist(state)

        # Should not call generation methods
        self.workflow.artist_agent.select_artist_style.assert_not_called()
        self.workflow.artist_agent.generate_persona.assert_not_called()

        self.assertEqual(new_state["artist_style"], "Existing Style")
        self.assertEqual(new_state["artist_background"], "Existing Background")

    def test_node_create_artist_generates_if_missing(self):
        """Test that node_create_artist generates if style/background are missing."""
        state = {
            "genre": "ROCK",
            "user_direction": "Test",
            "artist_style": None,
            "artist_background": None,
            "artist_name": None
        }

        self.workflow.artist_agent.select_artist_style.return_value = "Generated Style"
        self.workflow.artist_agent.generate_persona.return_value = "Generated Background"

        new_state = self.workflow.node_create_artist(state)

        self.workflow.artist_agent.select_artist_style.assert_called_once()
        self.workflow.artist_agent.generate_persona.assert_called_once()

        self.assertEqual(new_state["artist_style"], "Generated Style")
        self.assertEqual(new_state["artist_background"], "Generated Background")

    def test_node_generate_audio_uses_seed(self):
        """Test that node_generate_audio passes seed to ComfyClient."""
        state = {
            "genre": "ROCK",
            "musical_direction": {"tags": "Rock", "bpm": 120, "keyscale": "C major"},
            "cleaned_lyrics": "Test Lyrics",
            "artist_name": "Songbird",
            "seed": 98765
        }

        self.workflow.comfy.submit_prompt.return_value = {"prompt_id": "123"}
        self.workflow.comfy.wait_and_download_output.return_value = "song.mp3"

        self.workflow.node_generate_audio(state)

        self.workflow.comfy.submit_prompt.assert_called_once()
        _, kwargs = self.workflow.comfy.submit_prompt.call_args
        self.assertEqual(kwargs["seed"], 98765)

if __name__ == "__main__":
    unittest.main()
