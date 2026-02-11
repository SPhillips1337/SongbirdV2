import unittest
from tools.utils import sanitize_input

class TestInputSanitization(unittest.TestCase):
    def test_sanitize_input_limit(self):
        # Create a string longer than 1000 characters
        long_input = "a" * 1050
        sanitized = sanitize_input(long_input)
        self.assertEqual(len(sanitized), 1000)
        
    def test_sanitize_input_control_chars(self):
        input_text = "Hello\nWorld\tTest"
        sanitized = sanitize_input(input_text)
        self.assertEqual(sanitized, "Hello World Test")

    def test_sanitize_input_empty(self):
        self.assertEqual(sanitize_input(""), "")
        self.assertEqual(sanitize_input(None), "")

if __name__ == "__main__":
    unittest.main()
