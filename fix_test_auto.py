import re

with open("tests/test_vocal_logic.py", "r") as f:
    content = f.read()

# Find test_auto_vocals
# Expectation: negative_prompt == "low quality, glitch, distorted"
# Currently: "female vocals, low quality, glitch, distorted" (due to bad replace)

block_start = "def test_auto_vocals(self):"
if block_start in content:
    parts = content.split(block_start)
    parts[1] = parts[1].replace('self.assertEqual(negative_prompt, "female vocals, low quality, glitch, distorted")',
                                'self.assertEqual(negative_prompt, "low quality, glitch, distorted")', 1)
    content = block_start.join(parts)

with open("tests/test_vocal_logic.py", "w") as f:
    f.write(content)
