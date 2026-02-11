import unittest
import os
import shutil
import tempfile
import sys

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import scan_recent_songs

class TestScanRecentSongs(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def create_dummy_file(self, filename, content=""):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath

    def test_scan_recent_songs_sorting(self):
        # Create dummy files with different numbers
        # Format: Songbird_song_{number}__metadata.txt
        filenames = [
            "Songbird_song_00001__metadata.txt",
            "Songbird_song_00003__metadata.txt",
            "Songbird_song_00002__metadata.txt",
            "Songbird_song_00010__metadata.txt",
        ]

        # Create files with minimal content needed for parsing
        content_template = """Artist: Test Artist {i}
Background: Background {i}
--- Musical Direction ---
Direction {i}
--- Lyrics ---
Lyrics {i}
--- Research Notes ---
"""
        for f in filenames:
            num = int(f.split('_')[2])
            self.create_dummy_file(f, content_template.format(i=num))

        # Scan for recent songs (n=4 to get all)
        summaries = scan_recent_songs(self.test_dir, n=4)

        # Check order
        self.assertEqual(len(summaries), 4)
        self.assertEqual(summaries[0]['number'], 1)
        self.assertEqual(summaries[1]['number'], 2)
        self.assertEqual(summaries[2]['number'], 3)
        self.assertEqual(summaries[3]['number'], 10)

    def test_scan_recent_songs_limit(self):
        # Create 5 files
        for i in range(1, 6):
            self.create_dummy_file(f"Songbird_song_{i:05d}__metadata.txt", f"Artist: Artist {i}\nBackground: BG {i}")

        # Request only last 2
        summaries = scan_recent_songs(self.test_dir, n=2)

        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0]['number'], 4)
        self.assertEqual(summaries[1]['number'], 5)

if __name__ == '__main__':
    unittest.main()
