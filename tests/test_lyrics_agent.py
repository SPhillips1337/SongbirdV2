import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies that might not be installed or need isolation
sys.modules['psycopg2'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()

# Now import the class under test
from agents.lyrics import LyricsAgent

class TestLyricsAgentNormalization(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Suppress logging during tests
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)

    def setUp(self):
        self.agent = LyricsAgent()

    def test_normalize_basic(self):
        """Test basic normalization with valid markers and lyrics."""
        raw_lyrics = """
        [Intro]
        Hello world

        [Verse 1]
        Singing a song
        """
        expected = "[Intro]\nHello world\n[Verse 1]\nSinging a song"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_strip_quotes(self):
        """Test stripping of surrounding quotes."""
        raw_lyrics = '"[Intro]\nHello"'
        expected = "[Intro]\nHello"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

        raw_lyrics_single = "'[Intro]\nHello'"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics_single), expected)

    def test_remove_musical_directions_parentheses(self):
        """Test removal of parenthetical musical directions."""
        raw_lyrics = """
        [Intro]
        (Guitar solo)
        (Epic drums)
        Singing
        (Piano interlude)
        """
        expected = "[Intro]\nSinging"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_preserve_background_vocals(self):
        """Test preservation of background vocals in parentheses."""
        raw_lyrics = """
        [Chorus]
        I love you (love you)
        (yeah yeah)
        """
        expected = "[Chorus]\nI love you (love you)\n(yeah yeah)"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_preserve_valid_markers(self):
        """Test preservation of valid ACE-Step markers."""
        raw_lyrics = """
        [Intro]
        [Verse]
        [Chorus]
        [Bridge]
        [Outro]
        [Instrumental Break]
        """
        expected = "[Intro]\n[Verse]\n[Chorus]\n[Bridge]\n[Outro]\n[Instrumental Break]"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_remove_invalid_bracketed_directions(self):
        """Test removal of bracketed directions that are not valid markers and contain musical keywords."""
        # [Heavy Distortion] contains 'distortion' (musical keyword) and no valid marker.
        raw_lyrics = """
        [Verse]
        [Heavy Distortion]
        Singing
        """
        expected = "[Verse]\nSinging"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_mixed_content(self):
        """Test a mix of all cases."""
        raw_lyrics = """
        "
        [Intro]
        (Guitar feedback)

        [Verse 1]
        The sky is blue (so blue)
        (Oh yeah)

        [Chorus]
        [Heavy Drums]
        Sing it loud
        "
        """
        # [Heavy Drums] -> 'drums' is not in valid markers, but 'drum' is in musical keywords.
        # So [Heavy Drums] should be removed.

        expected = "[Intro]\n[Verse 1]\nThe sky is blue (so blue)\n(Oh yeah)\n[Chorus]\nSing it loud"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_empty_and_whitespace(self):
        """Test empty and whitespace-only inputs."""
        self.assertEqual(self.agent.normalize_lyrics(""), "")
        self.assertEqual(self.agent.normalize_lyrics("   "), "")
        self.assertEqual(self.agent.normalize_lyrics("\n\n"), "")

if __name__ == '__main__':
    unittest.main()
