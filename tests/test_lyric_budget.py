import unittest
from tools.audio_engineering import calculate_lyric_budget, GENRE_BPM

class TestLyricBudget(unittest.TestCase):
    def test_get_bpm(self):
        # Verify BPM lookups
        budget_dubstep = calculate_lyric_budget("DUBSTEP")
        self.assertEqual(budget_dubstep["bpm"], 140)

        budget_pop = calculate_lyric_budget("POP")
        self.assertEqual(budget_pop["bpm"], 120)

        # Verify default fallback
        budget_unknown = calculate_lyric_budget("UNKNOWN_GENRE")
        self.assertEqual(budget_unknown["bpm"], 120)

    def test_calculate_seconds_per_bar(self):
        # Dubstep: 140 BPM. (60/140)*4 = 1.714...
        budget = calculate_lyric_budget("DUBSTEP")
        expected = (60 / 140) * 4
        self.assertAlmostEqual(budget["seconds_per_bar"], expected, places=4)

    def test_calculate_total_bars(self):
        # 240 seconds at 140 BPM
        # Bars = 240 / ((60/140)*4) = 240 / 1.714 = 140 beats per minute -> 35 bars per minute -> 4 mins * 35 = 140 bars
        budget = calculate_lyric_budget("DUBSTEP", duration=240)
        self.assertEqual(budget["total_bars"], 140)

        # 120 seconds at 120 BPM
        # Bars = 120 / ((60/120)*4) = 120 / 2 = 60 bars
        budget = calculate_lyric_budget("POP", duration=120)
        self.assertEqual(budget["total_bars"], 60)

    def test_dubstep_structure_template(self):
        # Verify Dubstep gets the specific template requested
        budget = calculate_lyric_budget("DUBSTEP")
        self.assertIn("Dubstep Structure Template", budget["structure_template"])
        self.assertIn("[Drop 1]: 16 bars", budget["structure_template"])
        self.assertIn("[Outro]: 8 bars", budget["structure_template"])

    def test_generic_structure_template(self):
        # Verify generic template for non-Dubstep
        budget = calculate_lyric_budget("POP")
        self.assertIn("Generic Structure Template", budget["structure_template"])
        self.assertIn("[Intro]", budget["structure_template"])
        self.assertIn("[Outro]", budget["structure_template"])

if __name__ == "__main__":
    unittest.main()
