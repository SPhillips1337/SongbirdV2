import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import re
import shutil
import tempfile

# Mock ALL potentially missing dependencies before any imports
mock_modules = [
    'langgraph',
    'langgraph.graph',
    'psycopg2',
    'requests',
    'agents.artist',
    'agents.music',
    'agents.lyrics',
    'tools.comfy',
    'tools.rag'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import scan_recent_songs

class TestScanRecentSongs(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
        self.content_template = """Artist: Test Artist {i}
Background: Background {i}
--- Musical Direction ---
Direction {i}
--- Lyrics ---
Lyrics {i}
--- Research Notes ---
Notes {i}
"""

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

        for f in filenames:
            match = re.search(r"song_(\d+)_", f)
            num = int(match.group(1)) if match else 0
            self.create_dummy_file(f, self.content_template.format(i=num))

        # Scan for recent songs (n=4 to get all)
        summaries = scan_recent_songs(self.test_dir, n=4)

        # Check order
        self.assertEqual(len(summaries), 4)
        self.assertEqual(summaries[0]['number'], 1)
        self.assertEqual(summaries[1]['number'], 2)
        self.assertEqual(summaries[2]['number'], 3)
        self.assertEqual(summaries[3]['number'], 10)

    def test_scan_recent_songs_limit(self):
        # Create 5 files with complete metadata
        for i in range(1, 6):
            self.create_dummy_file(f"Songbird_song_{i:05d}__metadata.txt", self.content_template.format(i=i))

        # Request only last 2
        summaries = scan_recent_songs(self.test_dir, n=2)

        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0]['number'], 4)
        self.assertEqual(summaries[1]['number'], 5)
        self.assertEqual(summaries[0]['artist'], "Test Artist 4")

if __name__ == '__main__':
    unittest.main()
