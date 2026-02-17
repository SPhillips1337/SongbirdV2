import unittest
import os
import json
import shutil
import uuid
import datetime
from unittest.mock import MagicMock, patch
from tools.band import (
    create_band_profile,
    load_band,
    update_discography,
    copy_band_profile_to_album,
    ensure_band_directory
)

class TestBandManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_band_output"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        os.makedirs(self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_ensure_band_directory(self):
        band_dir = ensure_band_directory(self.test_dir)
        self.assertTrue(os.path.exists(band_dir))
        self.assertTrue(band_dir.endswith("Bands"))

    def test_create_band_profile(self):
        name = "The Test Band"
        genre = "ROCK"
        sub_genre = "Alternative"
        seed = 123456
        bio = "A great test band."
        style = "Grungy"

        profile = create_band_profile(self.test_dir, name, genre, sub_genre, seed, bio, style)

        self.assertIsNotNone(profile)
        self.assertEqual(profile["name"], name)
        self.assertEqual(profile["master_seed"], seed)
        self.assertEqual(profile["genre"], genre)
        self.assertTrue("id" in profile)
        self.assertTrue("creation_date" in profile)
        self.assertEqual(profile["discography"], [])

        # Check file existence
        expected_path = os.path.join(self.test_dir, "Bands", "The_Test_Band.json")
        self.assertTrue(os.path.exists(expected_path))

    def test_load_band_profile(self):
        name = "Load Me"
        create_band_profile(self.test_dir, name, "POP", "", 123, "Bio", "Style")

        loaded = load_band(self.test_dir, name)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["name"], name)
        self.assertEqual(loaded["master_seed"], 123)

        # Test non-existent
        self.assertIsNone(load_band(self.test_dir, "NonExistent"))

    def test_update_discography(self):
        name = "Discography Band"
        create_band_profile(self.test_dir, name, "JAZZ", "", 111, "Bio", "Style")

        update_discography(self.test_dir, name, "Album One")
        loaded = load_band(self.test_dir, name)
        self.assertIn("Album One", loaded["discography"])

        # Test duplicate avoidance
        update_discography(self.test_dir, name, "Album One")
        loaded = load_band(self.test_dir, name)
        self.assertEqual(len(loaded["discography"]), 1)

        update_discography(self.test_dir, name, "Album Two")
        loaded = load_band(self.test_dir, name)
        self.assertEqual(len(loaded["discography"]), 2)

    def test_copy_profile_to_album(self):
        name = "Copy Band"
        create_band_profile(self.test_dir, name, "METAL", "", 666, "Bio", "Style")

        album_dir = os.path.join(self.test_dir, "My_Album")
        os.makedirs(album_dir)

        copy_band_profile_to_album(self.test_dir, name, album_dir)

        expected_snapshot = os.path.join(album_dir, "artist_profile_snapshot.json")
        self.assertTrue(os.path.exists(expected_snapshot))

        with open(expected_snapshot, "r") as f:
            snapshot = json.load(f)
        self.assertEqual(snapshot["name"], name)

if __name__ == '__main__':
    unittest.main()
