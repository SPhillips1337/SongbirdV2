import unittest
from unittest.mock import MagicMock
import sys
import os

# Robust Mocking: Mock all external dependencies before any imports
sys.modules['requests'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['tools.rag'] = MagicMock()
sys.modules['tools.perplexity'] = MagicMock()

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.lyrics import LyricsAgent

class TestLyricsAgent(unittest.TestCase):
    def setUp(self):
        self.agent = LyricsAgent()

    def test_strip_musical_directions_basic(self):
        """Test basic removal of simple musical directions."""
        lyrics = """
        [Intro]
        (Guitar riff)
        Hello world
        """
        expected = """
        [Intro]
        Hello world
        """
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), expected.strip())

    def test_strip_musical_directions_preserves_vocals(self):
        """Test that background vocals are preserved."""
        lyrics = """
        (Background vocals: oh yeah)
        Singing loud
        (I can't stop)
        """
        expected = """
        (Background vocals: oh yeah)
        Singing loud
        (I can't stop)
        """
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), expected.strip())

    def test_strip_musical_directions_preserves_vocals_with_keywords(self):
        """Test that background vocals are preserved even if they contain musical keywords."""
        lyrics = """
        (Background vocals: heavy breathing over guitar)
        (Vocals: screaming like a synth)
        (Guitar solo)
        """
        expected = """
        (Background vocals: heavy breathing over guitar)
        (Vocals: screaming like a synth)
        """
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), expected.strip())

    def test_strip_musical_directions_complex(self):
        """Test mixed content with various markers and directions."""
        lyrics = """
        [Intro]
        (Guitar riff: crushing, driving)
        Yeah, listen up
        (Background vocals: oh yeah)

        [Verse 1]
        Walking down the street
        (Epic drums kick in)
        Feeling the heat

        [Chorus]
        This is the anthem
        (Synth solo)
        We are the phantom
        """
        expected = """
        [Intro]
        Yeah, listen up
        (Background vocals: oh yeah)

        [Verse 1]
        Walking down the street
        Feeling the heat

        [Chorus]
        This is the anthem
        We are the phantom
        """
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), expected.strip())

    def test_strip_bracket_musical_directions(self):
        """Test removal of bracketed musical directions that aren't valid structural markers."""
        lyrics = """
        [Guitar distortion kicks in]
        [Verse 1]
        Lyrics here
        [Heavy drums]
        More lyrics
        """
        expected = """
        [Verse 1]
        Lyrics here
        More lyrics
        """
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), expected.strip())

if __name__ == '__main__':
    unittest.main()
