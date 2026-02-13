import unittest
from tools.audio_engineering import calculate_song_parameters, DURATION_CATEGORIES, AUDIO_SETTINGS

class TestAudioEngineering(unittest.TestCase):
    def test_calculate_song_parameters_short(self):
        # Test Short Genre (Punk)
        # Using a genre known to be in SHORT
        params = calculate_song_parameters("PUNK", "some lyrics")

        # Verify min/max from constants to avoid hardcoding test values if constants change
        short_min = DURATION_CATEGORIES["SHORT"]["min"]
        short_max = DURATION_CATEGORIES["SHORT"]["max"]

        self.assertGreaterEqual(params["duration"], short_min)
        # It might be higher if lyrics are super long, but "some lyrics" is short.
        self.assertLessEqual(params["duration"], short_max)

    def test_calculate_song_parameters_long(self):
        # Test Long Genre (Prog Rock)
        params = calculate_song_parameters("PROG ROCK", "some lyrics")

        # Soft cap at 280s
        self.assertLessEqual(params["duration"], 280)

        # Check base duration logic (without cap)
        # If we didn't have the cap, it would be up to 320.
        # But with "some lyrics", it's purely random(240, 320).
        # So we assert it is >= min.
        long_min = DURATION_CATEGORIES["LONG"]["min"]
        self.assertGreaterEqual(params["duration"], long_min)

    def test_calculate_song_parameters_sampler(self):
        # Electronic
        params = calculate_song_parameters("Dubstep", "lyrics")
        self.assertEqual(params["sampler_name"], "euler")
        self.assertEqual(params["scheduler"], "simple")
        self.assertEqual(params["steps"], 16)
        self.assertEqual(params["cfg"], 1.0)

        # Organic
        params = calculate_song_parameters("Rock", "lyrics")
        self.assertEqual(params["sampler_name"], "dpmpp_2m")
        self.assertEqual(params["scheduler"], "karras")
        self.assertEqual(params["steps"], 20)
        self.assertEqual(params["cfg"], 1.2)

        # Atmospheric
        params = calculate_song_parameters("Ambient", "lyrics")
        self.assertEqual(params["sampler_name"], "euler_ancestral")
        self.assertEqual(params["scheduler"], "simple")
        self.assertEqual(params["steps"], 20)
        self.assertEqual(params["cfg"], 1.0)

    def test_word_count_estimation(self):
        # Test large word count affecting duration
        # Rap: 150 wpm.
        # 450 words -> 3 mins (180s).
        # Rap is Medium (180-240).
        # So random(180, 240) vs 180.
        # Duration will be max(base, 180).

        # Let's try something that exceeds the base max.
        # Short genre (Punk): 120-180.
        # 100 wpm default.
        # 400 words -> 4 mins (240s).
        # Result should be 240s (capped at 280).

        lyrics = "word " * 400
        params = calculate_song_parameters("Punk", lyrics)
        self.assertEqual(params["duration"], 240)

    def test_soft_cap(self):
        # Test exceeding soft cap
        # 1000 words -> 10 mins.
        # Should be capped at 280.
        lyrics = "word " * 1000
        params = calculate_song_parameters("Pop", lyrics)
        self.assertEqual(params["duration"], 280)

if __name__ == "__main__":
    unittest.main()
