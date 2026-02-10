import unittest
from unittest.mock import MagicMock
import sys
import os

# Mock dependencies
sys.modules['requests'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
# sys.modules['langgraph'] is not needed for LyricsAgent unit test

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from agents.lyrics import LyricsAgent
except ImportError:
    # Fallback if imports fail
    sys.modules['tools.rag'] = MagicMock()
    sys.modules['tools.perplexity'] = MagicMock()
    from agents.lyrics import LyricsAgent

class TestLyricsAgent(unittest.TestCase):
    def setUp(self):
        self.agent = LyricsAgent()

    def test_strip_musical_directions(self):
        # Test case 1: Basic musical direction removal
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
        # Test case 2: Preserves background vocals
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

    def test_strip_musical_directions_complex(self):
        # Test case 3: Mixed content
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
        # Test case 4: Bracket musical directions
        # Note: [Drum solo] is preserved because 'solo' is a valid marker.
        # We test with [Heavy drums] which should be removed.
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
