import unittest
from unittest.mock import MagicMock
import sys
import os

# Robustly mock dependencies BEFORE any imports from agents
sys.modules['requests'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['tools.rag'] = MagicMock()
sys.modules['tools.perplexity'] = MagicMock()

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.lyrics import LyricsAgent


class TestLyricsCleaning(unittest.TestCase):
    def setUp(self):
        self.agent = LyricsAgent()

    def test_strip_musical_directions_removes_instrumental_lines(self):
        """Test that instrumental directions are removed"""
        lyrics = """[Intro]
(Guitar riff: crushing, driving)
(Snare drum hit)
[Verse 1]
I wake up in the night
(Epic drums, crushing riffs)
[Chorus]
Breaking all the rules"""

        result = self.agent.strip_musical_directions(lyrics)
        
        # Should remove instrumental directions
        self.assertNotIn("(Guitar riff: crushing, driving)", result)
        self.assertNotIn("(Snare drum hit)", result)
        self.assertNotIn("(Epic drums, crushing riffs)", result)
        
        # Should preserve structure and lyrics
        self.assertIn("[Intro]", result)
        self.assertIn("[Verse 1]", result)
        self.assertIn("I wake up in the night", result)
        self.assertIn("[Chorus]", result)
        self.assertIn("Breaking all the rules", result)

    def test_strip_musical_directions_preserves_background_vocals(self):
        """Test that genuine background vocals are preserved"""
        lyrics = """[Verse]
I'm singing my heart out (oh yeah)
Can't stop this feeling (I can't stop)
We're dancing together (singing along)
(yeah yeah yeah)"""

        result = self.agent.strip_musical_directions(lyrics)
        
        # Should preserve background vocals
        self.assertIn("(oh yeah)", result)
        self.assertIn("(I can't stop)", result)
        self.assertIn("(singing along)", result)
        self.assertIn("(yeah yeah yeah)", result)

    def test_strip_musical_directions_mixed_content(self):
        """Test with mixed instrumental directions and background vocals"""
        lyrics = """[Intro]
(Atmospheric guitars, reverb-drenched)
[Verse 1]
Walking down the street (oh yeah)
(Shredding lead guitar)
Feeling so alive (can't stop now)
[Bridge]
(Grunty guitars, pounding bass)
Like a thunderclap (boom boom)
(Face-melting solos)"""

        result = self.agent.strip_musical_directions(lyrics)
        
        # Should remove instrumental directions
        self.assertNotIn("(Atmospheric guitars, reverb-drenched)", result)
        self.assertNotIn("(Shredding lead guitar)", result)
        self.assertNotIn("(Grunty guitars, pounding bass)", result)
        self.assertNotIn("(Face-melting solos)", result)
        
        # Should preserve background vocals
        self.assertIn("(oh yeah)", result)
        self.assertIn("(can't stop now)", result)
        self.assertIn("(boom boom)", result)
        
        # Should preserve structure and lyrics
        self.assertIn("Walking down the street", result)
        self.assertIn("Feeling so alive", result)
        self.assertIn("Like a thunderclap", result)

    def test_normalize_lyrics_end_to_end(self):
        """Test the full normalize_lyrics pipeline with real-world example"""
        lyrics = """[Intro]
(Guitar riff: crushing, driving)
(Snare drum hit)
[Verse 1]
I wake up in the night, fire burning deep inside
A rebel's heart beats strong and free, no chains to abide
[Guitar distortion kicks in]
[Chorus]
I'm breaking all the rules, gonna light up the night (oh yeah)
Got my guitar slung low, gonna take flight
[Bridge]
(Grunty guitars, pounding bass)
Like a stormy thunderclap, I'll shatter every mold
[Drop]
(Epic drums, crushing riffs)
Fists pumping, hearts beating as one"""

        result = self.agent.normalize_lyrics(lyrics)
        
        # Should remove instrumental directions
        self.assertNotIn("(Guitar riff: crushing, driving)", result)
        self.assertNotIn("(Snare drum hit)", result)
        self.assertNotIn("(Grunty guitars, pounding bass)", result)
        self.assertNotIn("(Epic drums, crushing riffs)", result)
        self.assertNotIn("[Guitar distortion kicks in]", result)
        
        # Should preserve background vocals
        self.assertIn("(oh yeah)", result)
        
        # Should preserve structure markers
        self.assertIn("[Intro]", result)
        self.assertIn("[Verse 1]", result)
        self.assertIn("[Chorus]", result)
        self.assertIn("[Bridge]", result)
        self.assertIn("[Drop]", result)
        
        # Should preserve lyrics
        self.assertIn("I wake up in the night", result)
        self.assertIn("I'm breaking all the rules", result)
        self.assertIn("Like a stormy thunderclap", result)

    def test_edge_cases(self):
        """Test edge cases like empty parentheses, partial matches"""
        lyrics = """[Verse]
This is a normal line
()
This line mentions guitar but not in parentheses
(This is just words)
(piano solo here)
Normal line with (background vocal)"""

        result = self.agent.strip_musical_directions(lyrics)
        
        # Should remove empty parentheses and piano solo
        self.assertNotIn("()", result)
        self.assertNotIn("(piano solo here)", result)
        
        # Should preserve lines that mention instruments but aren't parenthetical
        self.assertIn("This line mentions guitar but not in parentheses", result)
        
        # Should preserve non-musical parenthetical content
        self.assertIn("(This is just words)", result)
        self.assertIn("(background vocal)", result)

    def test_normalize_lyrics_strips_quotes(self):
        """Test that surrounding quotes are stripped"""
        lyrics = '"[Intro]\\nLyrics here"'
        result = self.agent.normalize_lyrics(lyrics)
        
        self.assertNotIn('"', result)
        self.assertIn("[Intro]", result)
        self.assertIn("Lyrics here", result)

    def test_normalize_lyrics_removes_empty_lines(self):
        """Test that empty lines are removed"""
        lyrics = """[Intro]

Lyrics here

More lyrics"""
        
        result = self.agent.normalize_lyrics(lyrics)
        lines = result.split('\n')
        
        # Should not have empty lines
        for line in lines:
            self.assertTrue(line.strip())


if __name__ == "__main__":
    unittest.main()
