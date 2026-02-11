import unittest
from unittest.mock import MagicMock
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock requests before importing agents.artist
sys.modules['requests'] = MagicMock()

# Now import the module under test
from agents.artist import ArtistAgent
from config import DEFAULT_ARTIST_STYLE, ARTIST_STYLES

class TestArtistAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ArtistAgent()

    def test_select_artist_style_known_genre(self):
        # Test a known genre from ARTIST_STYLES
        # "POP" -> "Taylor Swift" (based on config.py)
        # Note: We rely on the actual config.py here.
        style = self.agent.select_artist_style("POP")
        self.assertEqual(style, "Taylor Swift")

        # Test case insensitivity
        style_lower = self.agent.select_artist_style("pop")
        self.assertEqual(style_lower, "Taylor Swift")

    def test_select_artist_style_unknown_genre(self):
        # Test an unknown genre
        style = self.agent.select_artist_style("UNKNOWN_GENRE_XYZ")
        self.assertEqual(style, DEFAULT_ARTIST_STYLE)

    def test_select_artist_style_default_exists(self):
        # Verify DEFAULT_ARTIST_STYLE is not empty or None
        self.assertIsNotNone(DEFAULT_ARTIST_STYLE)
        self.assertIsInstance(DEFAULT_ARTIST_STYLE, str)
        self.assertTrue(len(DEFAULT_ARTIST_STYLE) > 0)

if __name__ == '__main__':
    unittest.main()
