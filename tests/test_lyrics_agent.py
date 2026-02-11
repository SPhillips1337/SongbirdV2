
import unittest
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.lyrics import LyricsAgent

class TestLyricsAgent(unittest.TestCase):
    def setUp(self):
        self.agent = LyricsAgent()

    def test_strip_musical_directions(self):
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
        # Note: [Guitar Solo] would be preserved because 'solo' is a valid marker.
        # But [Guitar Distortion Kicks In] should be removed because 'distortion' is a musical keyword
        # and it contains no valid marker.

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
        # Case insensitive
        lyrics = "(GUITAR SOLO)"
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), "")

        # Mixed content
        lyrics = "Start (guitar) End"
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), "Start (guitar) End")
        # Because it only removes if the ENTIRE line is parenthetical.

        # Valid marker with musical keyword
        lyrics = "[Instrumental Break]"
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), "[Instrumental Break]")

        # Invalid marker with musical keyword
        lyrics = "[Guitar Distortion Kicks In]"
        # "guitar", "distortion" in MUSICAL_KEYWORDS.
        # No valid marker.
        # Should be removed.
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), "")

        # Valid marker inside bracket that also has musical keyword
        lyrics = "[Guitar Solo]"
        # 'solo' is valid marker. So it is preserved.
        self.assertEqual(self.agent.strip_musical_directions(lyrics).strip(), "[Guitar Solo]")

if __name__ == '__main__':
    unittest.main()
