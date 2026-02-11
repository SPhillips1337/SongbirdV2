import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import textwrap

# Add root directory to sys.path to allow imports from agents
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestLyricsAgent(unittest.TestCase):

    def setUp(self):
        # Move mocking to setUp with patch.dict to avoid test pollution
        # Robust Mocking: Mock all external dependencies before any imports
        self.patcher = patch.dict('sys.modules', {
            'requests': MagicMock(),
            'psycopg2': MagicMock(),
            'langgraph': MagicMock(),
            'langgraph.graph': MagicMock(),
            'dotenv': MagicMock(),
            'tools.rag': MagicMock(),
            'tools.perplexity': MagicMock()
        })
        self.patcher.start()
        
        # Patch dependencies of LyricsAgent during instantiation
        self.rag_patcher = patch('agents.lyrics.RAGTool')
        self.perplexity_patcher = patch('agents.lyrics.PerplexityClient')
        self.mock_rag = self.rag_patcher.start()
        self.mock_perplexity = self.perplexity_patcher.start()
        
        # Import inside setUp during active patch session to guarantee correct mock application
        from agents.lyrics import LyricsAgent
        self.agent = LyricsAgent()

    def tearDown(self):
        self.perplexity_patcher.stop()
        self.rag_patcher.stop()
        self.patcher.stop()

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
        raw_lyrics = """
        [Verse]
        [Heavy Distortion]
        Singing
        """
        expected = "[Verse]\nSinging"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_preserve_vocals_with_musical_keywords(self):
        """Verify preservation of vocals even if they contain musical keywords like 'guitar'."""
        raw_lyrics = """
        (Background vocals: oh yeah)
        (Background vocals: epic guitar)
        """
        expected = "(Background vocals: oh yeah)\n(Background vocals: epic guitar)"
        self.assertEqual(self.agent.normalize_lyrics(raw_lyrics), expected)

    def test_empty_and_whitespace(self):
        """Test empty and whitespace-only inputs."""
        self.assertEqual(self.agent.normalize_lyrics(""), "")
        self.assertEqual(self.agent.normalize_lyrics("   "), "")
        self.assertEqual(self.agent.normalize_lyrics("\n\n"), "")

    def test_strip_musical_directions_comprehensive(self):
        """Comprehensive verification from PR #20."""
        lyrics = """
[Intro]
(Guitar riff starts playing)
Yeah, let's go!
(Drums kick in)
[Verse 1]
Walking down the street
(Bass line heavy)
Thinking about the beat
(Synth pad swells)
[Chorus]
This is the song (oh yeah)
We sing along (all night long)
(Guitar solo)
[Bridge]
Break it down
(Drum fill)
[Outro]
Fade out
(Echo effect)
[Instrumental Break]
[Guitar Distortion Kicks In]
(oh baby)
"""
        expected_lyrics = """
[Intro]
Yeah, let's go!
[Verse 1]
Walking down the street
Thinking about the beat
[Chorus]
This is the song (oh yeah)
We sing along (all night long)
[Bridge]
Break it down
[Outro]
Fade out
[Instrumental Break]
(oh baby)
"""
        processed = self.agent.strip_musical_directions(lyrics).strip()
        processed_lines = [l.strip() for l in processed.split('\n') if l.strip()]
        expected_lines = [l.strip() for l in expected_lyrics.split('\n') if l.strip()]
        self.assertEqual(processed_lines, expected_lines)

    def test_strip_musical_directions_edge_cases(self):
        """Edge cases from PR #20."""
        # Case insensitive
        self.assertEqual(self.agent.strip_musical_directions("(GUITAR SOLO)").strip(), "")
        # Mixed content
        self.assertEqual(self.agent.strip_musical_directions("Start (guitar) End").strip(), "Start (guitar) End")
        # Valid marker with musical keyword
        self.assertEqual(self.agent.strip_musical_directions("[Instrumental Break]").strip(), "[Instrumental Break]")

if __name__ == '__main__':
    unittest.main()
