import re

# Fix test_vocal_logic.py
with open("tests/test_vocal_logic.py", "r") as f:
    content = f.read()

# We need to change the assertion inside test_male_vocals_custom_strength
# It currently expects "low quality, glitch, distorted"
# It should expect "female vocals, low quality, glitch, distorted"
# We can find the block and replace.
block_start = "def test_male_vocals_custom_strength(self):"
if block_start in content:
    # Find the assertion in this block
    # It's likely the first assertion after the def
    # "self.assertEqual(negative_prompt, \"low quality, glitch, distorted\")"
    # But wait, test_auto_vocals also uses this string.
    # So a global replace is bad.

    parts = content.split(block_start)
    # parts[0] is before
    # parts[1] is the function body and rest of file

    # In parts[1], replace the FIRST occurrence of the assertion string.
    parts[1] = parts[1].replace('self.assertEqual(negative_prompt, "low quality, glitch, distorted")',
                                'self.assertEqual(negative_prompt, "female vocals, low quality, glitch, distorted")', 1)

    content = block_start.join(parts)

with open("tests/test_vocal_logic.py", "w") as f:
    f.write(content)

# Fix test_vocals.py
with open("tests/test_vocals.py", "r") as f:
    content = f.read()

block_start = "def test_vocals_male(self):"
if block_start in content:
    parts = content.split(block_start)
    parts[1] = parts[1].replace('self.assertEqual(negative_prompt, "low quality, glitch, distorted")',
                                'self.assertEqual(negative_prompt, "female vocals, low quality, glitch, distorted")', 1)
    content = block_start.join(parts)

with open("tests/test_vocals.py", "w") as f:
    f.write(content)
