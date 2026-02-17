import unittest
import os
import json
import shutil
import time
from unittest.mock import MagicMock, patch
from tools.cache import CacheManager
from tools.band import save_band_profile, load_band_profile
from tools.suggestions import scan_history
from config import GENRE_ARTISTS, ARTIST_STYLES
from agents.artist import ArtistAgent

class TestFeatures(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_output"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        if os.path.exists(".test_cache.json"):
            os.remove(".test_cache.json")

    def test_cache(self):
        cache = CacheManager(cache_file=".test_cache.json", ttl=1)
        cache.set("key", "value")
        self.assertEqual(cache.get("key"), "value")
        time.sleep(1.1)
        self.assertIsNone(cache.get("key"))

    def test_band_profile(self):
        state = {
            "artist_name": "Test Band",
            "seed": 12345,
            "genre": "ROCK",
            "artist_background": "A cool band.",
            "artist_style": "Test Style"
        }
        save_band_profile(state, self.test_dir)
        profile_path = os.path.join(self.test_dir, "band_profile.json")
        self.assertTrue(os.path.exists(profile_path))

        loaded = load_band_profile(profile_path)
        self.assertEqual(loaded["band_name"], "Test Band")
        self.assertEqual(loaded["master_seed"], 12345)

    def test_suggestions_scan(self):
        # Create fake metadata files
        with open(os.path.join(self.test_dir, "song_1_metadata.txt"), "w") as f:
            f.write("Genre: POP\nStyle (Reference): Artist A\n")
        with open(os.path.join(self.test_dir, "song_2_metadata.txt"), "w") as f:
            f.write("Genre: POP\nStyle (Reference): Artist B\n")
        with open(os.path.join(self.test_dir, "song_3_metadata.txt"), "w") as f:
            f.write("Genre: ROCK\nStyle (Reference): Artist A\n")

        history = scan_history(self.test_dir)
        self.assertEqual(history["total_songs"], 3)
        self.assertEqual(history["top_genres"][0], "POP")
        self.assertEqual(history["top_styles"][0], "Artist A")

    def test_genre_artists_config(self):
        self.assertIsInstance(GENRE_ARTISTS, dict)
        self.assertIn("POP", GENRE_ARTISTS)
        self.assertIsInstance(GENRE_ARTISTS["POP"], list)

    def test_artist_agent_selection(self):
        agent = ArtistAgent()

        # Case 1: Genre with list
        style = agent.select_artist_style("POP")
        # style should be in the list OR in ARTIST_STYLES
        valid_options = GENRE_ARTISTS.get("POP", [])
        if "POP" in ARTIST_STYLES:
            valid_options.append(ARTIST_STYLES["POP"])

        self.assertTrue(style in valid_options)

        # Case 2: Unknown genre
        style = agent.select_artist_style("UNKNOWN_GENRE")
        self.assertEqual(style, "Adele") # Default

if __name__ == '__main__':
    unittest.main()
