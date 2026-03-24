import unittest
from tools.audio_engineering import calculate_song_parameters, DURATION_CATEGORIES, AUDIO_SETTINGS

class TestAudioEngineering(unittest.TestCase):
    def test_duration_categories(self):
        # 1. Test DURATION_CATEGORIES structure
        self.assertIn("SHORT", DURATION_CATEGORIES)
        self.assertIn("MEDIUM", DURATION_CATEGORIES)
        self.assertEqual(DURATION_CATEGORIES["SHORT"]["min"], 120)
        self.assertEqual(DURATION_CATEGORIES["MEDIUM"]["max"], 240)

    def test_calculate_song_parameters_defaults(self):
        # 2. Test default parameters (Pop)
        params = calculate_song_parameters("Pop", "lyrics")
        self.assertEqual(params["steps"], 16)
        self.assertEqual(params["cfg"], 1.4)
        self.assertEqual(params["sampler_name"], "dpmpp_2m")
        self.assertEqual(params["scheduler"], "sgm_uniform")

    def test_calculate_song_parameters_genres(self):
        # 3. Test genre-specific parameters
        # Dubstep (Electronic)
        params = calculate_song_parameters("Dubstep", "lyrics")
        self.assertEqual(params["steps"], 12)
        self.assertEqual(params["cfg"], 1.0)
        self.assertEqual(params["sampler_name"], "euler")

        # Rock
        params = calculate_song_parameters("Rock", "lyrics")
        self.assertEqual(params["steps"], 16)
        self.assertEqual(params["cfg"], 1.3)
        self.assertEqual(params["sampler_name"], "dpmpp_2m")

    def test_calculate_song_parameters_sampler(self):
        # Electronic
        params = calculate_song_parameters("Dubstep", "lyrics")
        self.assertEqual(params["sampler_name"], "euler")
        self.assertEqual(params["scheduler"], "sgm_uniform")
        self.assertEqual(params["steps"], 12)
        self.assertEqual(params["cfg"], 1.0)

        # Pop
        params = calculate_song_parameters("Pop", "lyrics")
        self.assertEqual(params["sampler_name"], "dpmpp_2m")
        self.assertEqual(params["scheduler"], "sgm_uniform")
        self.assertEqual(params["steps"], 16)
        self.assertEqual(params["cfg"], 1.4)

    def test_get_bpm(self):
        from tools.audio_engineering import get_bpm
        self.assertEqual(get_bpm("Pop"), 120)
        self.assertEqual(get_bpm("Dubstep"), 140)
        self.assertEqual(get_bpm("HIP HOP"), 90)
        self.assertEqual(get_bpm("Unknown Genre"), 120)

if __name__ == "__main__":
    unittest.main()
