import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock dependencies before importing app
# Check if they are already mocked (e.g. by run_tests_patched.py)
if 'requests' not in sys.modules or not isinstance(sys.modules['requests'], MagicMock):
    sys.modules['requests'] = MagicMock()
    sys.modules['langgraph'] = MagicMock()
    sys.modules['langgraph.graph'] = MagicMock()
    sys.modules['dotenv'] = MagicMock()
    sys.modules['psycopg2'] = MagicMock()
    sys.modules['tools.rag'] = MagicMock()

    # Mock config
    config_mock = MagicMock()
    config_mock.OLLAMA_BASE_URL = "http://localhost:11434"
    config_mock.ALBUM_MODEL = "llama3"
    config_mock.MUSIC_PROMPTS = {"POP": "pop prompt", "ROCK": "rock prompt", "LO-FI": "lo-fi prompt", "JAZZ": "jazz prompt"}
    sys.modules['config'] = config_mock

import app
from state import SongState
from tools.comfy import ComfyClient

class TestVocalsCLI(unittest.TestCase):
    def setUp(self):
        # We need to re-patch app dependencies if they were mocked during import but we want fresh mocks
        # However, app has already imported them.
        # But we want to test SongbirdWorkflow which instantiates classes.

        # Patch app classes to avoid real instantiation
        self.patcher_artist = patch('app.ArtistAgent')
        self.patcher_music = patch('app.MusicAgent')
        self.patcher_lyrics = patch('app.LyricsAgent')
        self.patcher_comfy = patch('app.ComfyClient') # This patches ComfyClient in app.py

        # We also need to patch calculate_song_parameters
        self.patcher_calc = patch('app.calculate_song_parameters')

        self.mock_artist_agent = self.patcher_artist.start()
        self.mock_music_agent = self.patcher_music.start()
        self.mock_lyrics_agent = self.patcher_lyrics.start()
        self.mock_comfy_client_class = self.patcher_comfy.start()
        self.mock_calculate_song_parameters = self.patcher_calc.start()

        # Setup mocks
        self.mock_calculate_song_parameters.return_value = {
            "duration": 120,
            "steps": 8,
            "cfg": 1,
            "sampler_name": "euler",
            "scheduler": "simple"
        }

        # Initialize workflow
        # Note: SongbirdWorkflow.__init__ uses ComfyClient(). Since we patched it, self.workflow.comfy will be a mock.
        self.workflow = app.SongbirdWorkflow()

        # But we need access to the instance created
        self.mock_comfy_instance = self.mock_comfy_client_class.return_value
        # Ensure submit_prompt is a mock
        self.mock_comfy_instance.submit_prompt = MagicMock()

        # We also need to mock workflow.app.invoke if we call run, but we are calling node_generate_audio directly.
        self.workflow.app = MagicMock()

    def tearDown(self):
        patch.stopall()

    def test_vocals_female(self):
        state = {
            "genre": "POP",
            "user_direction": "test direction",
            "artist_name": "Test Artist",
            "musical_direction": {"tags": "pop song", "bpm": 120, "keyscale": "C major"},
            "lyrics": "lyrics",
            "cleaned_lyrics": "lyrics",
            "vocals": "female"
        }

        self.workflow.node_generate_audio(state)

        call_args = self.mock_comfy_instance.submit_prompt.call_args
        self.assertIsNotNone(call_args, "submit_prompt was not called")

        args, kwargs = call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')

        self.assertIn("(female vocals:1.2), female singer,", tags)
        self.assertEqual(negative_prompt, "male vocals")

    def test_vocals_male(self):
        state = {
            "genre": "ROCK",
            "user_direction": "test direction",
            "artist_name": "Test Artist",
            "musical_direction": {"tags": "rock song", "bpm": 120, "keyscale": "C major"},
            "lyrics": "lyrics",
            "cleaned_lyrics": "lyrics",
            "vocals": "male"
        }

        self.workflow.node_generate_audio(state)

        call_args = self.mock_comfy_instance.submit_prompt.call_args
        self.assertIsNotNone(call_args)
        args, kwargs = call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')

        self.assertIn("(male vocals:1.2), male singer,", tags)
        self.assertEqual(negative_prompt, "female vocals")

    def test_vocals_instrumental(self):
        state = {
            "genre": "JAZZ",
            "user_direction": "test direction",
            "artist_name": "Test Artist",
            "musical_direction": {"tags": "jazz song", "bpm": 120, "keyscale": "C major"},
            "lyrics": "lyrics",
            "cleaned_lyrics": "lyrics",
            "vocals": "instrumental"
        }

        self.workflow.node_generate_audio(state)

        call_args = self.mock_comfy_instance.submit_prompt.call_args
        self.assertIsNotNone(call_args)
        args, kwargs = call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')

        self.assertIn("(instrumental:1.2), no vocals,", tags)
        self.assertEqual(negative_prompt, "vocals, voice, singing, lyrics, speech")

    def test_vocals_duet(self):
        state = {
            "genre": "POP",
            "user_direction": "test direction",
            "artist_name": "Test Artist",
            "musical_direction": {"tags": "pop song", "bpm": 120, "keyscale": "C major"},
            "lyrics": "lyrics",
            "cleaned_lyrics": "lyrics",
            "vocals": "duet"
        }

        self.workflow.node_generate_audio(state)

        call_args = self.mock_comfy_instance.submit_prompt.call_args
        self.assertIsNotNone(call_args)
        args, kwargs = call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')

        self.assertIn("(duet vocals:1.2),", tags)
        # Assuming empty string for duet/choir unless specified otherwise
        # In implementation:
        # elif vocals == "duet":
        #    tags = f"(duet vocals:{vocal_strength}), {tags}"
        # Negative prompt is initialized to ""
        self.assertEqual(negative_prompt, "low quality, glitch, distorted")

    def test_vocals_auto(self):
        state = {
            "genre": "POP",
            "user_direction": "test direction",
            "artist_name": "Test Artist",
            "musical_direction": {"tags": "pop song", "bpm": 120, "keyscale": "C major"},
            "lyrics": "lyrics",
            "cleaned_lyrics": "lyrics",
            "vocals": "auto"
        }

        self.workflow.node_generate_audio(state)

        call_args = self.mock_comfy_instance.submit_prompt.call_args
        self.assertIsNotNone(call_args)
        args, kwargs = call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')

        self.assertEqual(tags, "pop song") # Unchanged
        self.assertEqual(negative_prompt, "low quality, glitch, distorted")

if __name__ == '__main__':
    unittest.main()
