import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLyricsAgentNormalization(unittest.TestCase):

    def setUp(self):
        # Suppress logging during tests
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)

        # Patch sys.modules to mock missing dependencies
        self.modules_patcher = patch.dict(sys.modules, {
            'psycopg2': MagicMock(),
            'langgraph': MagicMock(),
            'dotenv': MagicMock(),
            'requests': MagicMock()
        })
        self.modules_patcher.start()

        # Remove modules from cache to force reload with mocks
        modules_to_reload = ['agents.lyrics', 'tools.rag', 'tools.perplexity']
        for mod in modules_to_reload:
            if mod in sys.modules:
                del sys.modules[mod]

        # Import the class under test
        from agents.lyrics import LyricsAgent
        self.agent = LyricsAgent()

    def tearDown(self):
        self.modules_patcher.stop()

        # Clean up mocked modules from cache
        modules_to_reload = ['agents.lyrics', 'tools.rag', 'tools.perplexity']
        for mod in modules_to_reload:
            if mod in sys.modules:
                del sys.modules[mod]

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

    def test_preserve_vocal_with_musical_keyword(self):
        """Test preservation of vocals even if they contain musical keywords."""
        # 'guitar' is a musical keyword, but 'vocals' is a vocal keyword.
        # Should be preserved.
        raw_lyrics = """
        [Chorus]
        (Background vocals: epic guitar)
        (Singing over the bass)
        """
        expected = "[Chorus]\n(Background vocals: epic guitar)\n(Singing over the bass)"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

if __name__ == '__main__':
    unittest.main()
