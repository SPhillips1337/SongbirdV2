import unittest
import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import SongbirdWorkflow

class TestKeyscaleNormalization(unittest.TestCase):
    def setUp(self):
        self.flow = SongbirdWorkflow()

    def test_normalization(self):
        test_cases = {
            "C Major": "C major",
            "C major": "C major",
            "a minor": "A minor",
            "A MINOR": "A minor",
            "F# major": "F# major",
            "Gb minor": "Gb minor",
            "d#": "D# major", # Default to major
            "Eb": "Eb major",
            "   C   Major   ": "C major",
            "": "C major",
            None: "C major"
        }
        
        for input_val, expected in test_cases.items():
            with self.subTest(input_val=input_val):
                result = self.flow.normalize_keyscale(input_val)
                self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()
