import unittest
from unittest.mock import MagicMock, patch
import sys
import os

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

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import SongbirdWorkflow

class TestVocalLogic(unittest.TestCase):

    def setUp(self):
        # Patch dependencies that might be called in __init__
        self.patcher_comfy = patch('tools.comfy.ComfyClient')
        self.patcher_artist = patch('app.ArtistAgent')
        self.patcher_music = patch('app.MusicAgent')
        self.patcher_lyrics = patch('app.LyricsAgent')

        self.MockComfy = self.patcher_comfy.start()
        self.MockArtist = self.patcher_artist.start()
        self.MockMusic = self.patcher_music.start()
        self.MockLyrics = self.patcher_lyrics.start()

        self.workflow = SongbirdWorkflow()
        # Replace the comfy instance with a MagicMock we control
        self.workflow.comfy = MagicMock()
        self.workflow.comfy.submit_prompt.return_value = {"prompt_id": "test_id"}
        self.workflow.comfy.wait_and_download_output.return_value = "output/song.mp3"

    def tearDown(self):
        self.patcher_comfy.stop()
        self.patcher_artist.stop()
        self.patcher_music.stop()
        self.patcher_lyrics.stop()

    def test_female_vocals_default_strength(self):
        state = {
            "musical_direction": {"tags": "pop, upbeat"},
            "genre": "POP",
            "vocals": "female",
            "vocal_strength": 1.2,
            "artist_name": "TestArtist",
            "track_number": 1,
            "song_title": "TestSong",
            "cleaned_lyrics": "La la la"
        }

        self.workflow.node_generate_audio(state)

        args, kwargs = self.workflow.comfy.submit_prompt.call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')
        cfg = kwargs.get('cfg')

        self.assertIn("(female vocals:1.2)", tags)
        self.assertEqual(negative_prompt, "male vocals")
        # Base CFG is 1.5, should be reduced by 15% -> 1.5 * 0.85 = 1.275
        self.assertAlmostEqual(cfg, 1.275, places=3)

    def test_male_vocals_custom_strength(self):
        state = {
            "musical_direction": "rock, heavy",
            "genre": "ROCK",
            "vocals": "male",
            "vocal_strength": 1.5,
            "artist_name": "TestArtist",
            "cleaned_lyrics": "Yeah yeah"
        }

        self.workflow.node_generate_audio(state)

        args, kwargs = self.workflow.comfy.submit_prompt.call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')
        cfg = kwargs.get('cfg')

        self.assertIn("(male vocals:1.5)", tags)
        self.assertEqual(negative_prompt, "female vocals")
        self.assertAlmostEqual(cfg, 1.275, places=3)

    def test_instrumental(self):
        state = {
            "musical_direction": "lo-fi beats",
            "genre": "LO-FI",
            "vocals": "instrumental",
            "vocal_strength": 1.2,
            "artist_name": "TestArtist",
            "cleaned_lyrics": ""
        }

        self.workflow.node_generate_audio(state)

        args, kwargs = self.workflow.comfy.submit_prompt.call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')
        cfg = kwargs.get('cfg')

        self.assertIn("(instrumental:1.2)", tags)
        self.assertEqual(negative_prompt, "vocals, voice, singing, lyrics, speech")
        self.assertAlmostEqual(cfg, 1.275, places=3)

    def test_auto_vocals(self):
        state = {
            "musical_direction": "jazz",
            "genre": "JAZZ",
            "vocals": "auto",
            "vocal_strength": 1.2,
            "artist_name": "TestArtist",
            "cleaned_lyrics": "Scat singing"
        }

        self.workflow.node_generate_audio(state)

        args, kwargs = self.workflow.comfy.submit_prompt.call_args
        tags = kwargs.get('tags')
        negative_prompt = kwargs.get('negative_prompt')
        cfg = kwargs.get('cfg')

        # Should NOT have vocal injection
        self.assertNotIn("(female vocals:", tags)
        self.assertNotIn("(male vocals:", tags)
        self.assertEqual(negative_prompt, "")
        # CFG should be default (1.5)
        self.assertEqual(cfg, 1.5)

if __name__ == '__main__':
    unittest.main()
