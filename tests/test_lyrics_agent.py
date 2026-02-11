import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add root directory to sys.path to allow imports from agents
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLyricsAgent(unittest.TestCase):

    def setUp(self):
        # Move mocking to setUp with patch.dict to avoid test pollution
        self.patcher = patch.dict('sys.modules', {'requests': MagicMock(), 'psycopg2': MagicMock()})
        self.patcher.start()
        
        # Patch dependencies of LyricsAgent during instantiation
        self.rag_patcher = patch('agents.lyrics.RAGTool')
        self.perplexity_patcher = patch('agents.lyrics.PerplexityClient')
        self.mock_rag = self.rag_patcher.start()
        self.mock_perplexity = self.perplexity_patcher.start()
        
        # Import inside setUp so the mocks are active
        from agents.lyrics import LyricsAgent
        self.agent = LyricsAgent()

    def tearDown(self):
        self.perplexity_patcher.stop()
        self.rag_patcher.stop()
        self.patcher.stop()

    def test_strip_musical_directions_preserves_lyrics(self):
        lyrics = "[Verse 1]\nI'm walking down the street\n(Walking down the street)\nYeah I feel the heat"
        expected = "[Verse 1]\nI'm walking down the street\n(Walking down the street)\nYeah I feel the heat"

        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_removes_instrumental_parentheses(self):
        lyrics = "[Intro]\n(Guitar solo starts)\n(Drums kick in)\nLet's go!\n(Epic synth pad)"
        expected = "[Intro]\nLet's go!"

        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_removes_square_bracket_directions(self):
        lyrics = "[Verse]\nSinging a song\n[Guitar Riff]\nJust singing along\n[Drum Fill]"
        expected = "[Verse]\nSinging a song\nJust singing along"
        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_preserves_valid_markers(self):
        lyrics = "[Intro]\n[Verse 1]\n[Chorus]\n[Bridge]\n[Outro]\n[Instrumental Break]"
        expected = "[Intro]\n[Verse 1]\n[Chorus]\n[Bridge]\n[Outro]\n[Instrumental Break]"
        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_removes_empty_parentheses(self):
        lyrics = "Line 1\n()\nLine 2\n(   )\nLine 3"
        expected = "Line 1\nLine 2\nLine 3"
        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_handles_case_insensitivity(self):
        lyrics = "(GUITAR SOLO)\n(drums)\n[VERSE]\n(Background Vocals)"
        expected = "[VERSE]\n(Background Vocals)"
        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_mixed_content(self):
        lyrics = "[Intro]\n(Soft piano melody)\nYeah\n(ooh ooh)\n[Guitar Distortion]\nEnd of song"
        expected = "[Intro]\nYeah\n(ooh ooh)\nEnd of song"
        result = self.agent.strip_musical_directions(lyrics)
        self.assertEqual(result, expected)

    def test_strip_musical_directions_preserves_vocals_with_musical_keywords(self):
        # From PR #7 fix: verify preservation of "(Background vocals: epic guitar)"
        lyrics = """
        (Background vocals: oh yeah)
        Singing loud
        (I can't stop)
        (Background vocals: epic guitar)
        """
        expected = """
        (Background vocals: oh yeah)
        Singing loud
        (I can't stop)
        (Background vocals: epic guitar)
        """
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), expected.strip())

    def test_normalize_lyrics(self):
        # normalize_lyrics strips quotes, removes musical directions, strips lines, removes empty lines
        lyrics = """
        "
        [Verse]
        (Guitar)
        Line 1
          Line 2

        (Vocals)
        "
        """
        # normalize_lyrics handles the cleanup nicely
        expected = "[Verse]\nLine 1\nLine 2\n(Vocals)"
        result = self.agent.normalize_lyrics(lyrics)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
