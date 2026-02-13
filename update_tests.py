import re

# Update tests/test_audio_engineering.py
with open("tests/test_audio_engineering.py", "r") as f:
    content = f.read()

# Replace test_calculate_song_parameters_sampler
new_test_sampler = """    def test_calculate_song_parameters_sampler(self):
        # Electronic
        params = calculate_song_parameters("Dubstep", "lyrics")
        self.assertEqual(params["sampler_name"], "euler")
        self.assertEqual(params["scheduler"], "normal")
        self.assertEqual(params["steps"], 16)
        self.assertEqual(params["cfg"], 1.8)

        # Pop (was Organic)
        params = calculate_song_parameters("Pop", "lyrics")
        self.assertEqual(params["sampler_name"], "dpmpp_2m")
        self.assertEqual(params["scheduler"], "karras")
        self.assertEqual(params["steps"], 20)
        self.assertEqual(params["cfg"], 2.0)

        # Rock (was Organic)
        params = calculate_song_parameters("Rock", "lyrics")
        self.assertEqual(params["sampler_name"], "dpmpp_2m")
        self.assertEqual(params["scheduler"], "karras")
        self.assertEqual(params["steps"], 25)
        self.assertEqual(params["cfg"], 2.2)

        # Atmospheric
        params = calculate_song_parameters("Ambient", "lyrics")
        self.assertEqual(params["sampler_name"], "euler_ancestral")
        self.assertEqual(params["scheduler"], "simple")
        self.assertEqual(params["steps"], 20)
        self.assertEqual(params["cfg"], 1.5)"""

pattern_sampler = r'def test_calculate_song_parameters_sampler\(self\):.*?self.assertEqual\(params\["cfg"\], 1.0\)'
# Use dotall
content = re.sub(pattern_sampler, new_test_sampler, content, flags=re.DOTALL)

with open("tests/test_audio_engineering.py", "w") as f:
    f.write(content)


# Update tests/test_vocal_logic.py
with open("tests/test_vocal_logic.py", "r") as f:
    content = f.read()

# Replace assertions
# female: "male vocals" -> "male vocals, low quality, glitch, distorted"
content = content.replace('self.assertEqual(negative_prompt, "male vocals")', 'self.assertEqual(negative_prompt, "male vocals, low quality, glitch, distorted")')

# male: "female vocals" -> "low quality, glitch, distorted"
content = content.replace('self.assertEqual(negative_prompt, "female vocals")', 'self.assertEqual(negative_prompt, "low quality, glitch, distorted")')

# instrumental: "vocals, voice, singing, lyrics, speech" -> "vocals, voice, singing, lyrics, speech, low quality, glitch, distorted"
content = content.replace('self.assertEqual(negative_prompt, "vocals, voice, singing, lyrics, speech")', 'self.assertEqual(negative_prompt, "vocals, voice, singing, lyrics, speech, low quality, glitch, distorted")')

# auto: "" -> "low quality, glitch, distorted"
content = content.replace('self.assertEqual(negative_prompt, "")', 'self.assertEqual(negative_prompt, "low quality, glitch, distorted")')

# Also need to update CFG assertions because base CFG changed for genres.
# In test_vocal_logic.py, it uses "POP", "ROCK", "LO-FI", "JAZZ".
# POP base CFG is now 2.0. 2.0 * 0.85 = 1.7.
# ROCK base CFG is now 2.2. 2.2 * 0.85 = 1.87.
# LO-FI (Atmospheric) base CFG is 1.5. 1.5 * 0.85 = 1.275.
# JAZZ (Atmospheric) base CFG is 1.5. 1.5 * 0.85 = 1.275.

# test_female_vocals_default_strength (POP)
# Old: 1.275 (1.5 * 0.85). New: 1.7 (2.0 * 0.85).
content = re.sub(r'self.assertAlmostEqual\(cfg, 1.275, places=3\)', 'self.assertAlmostEqual(cfg, 1.7, places=3)', content, count=1)
# Wait, multiple occurrences of 1.275.
# First one is POP (female vocals).
# Second one is ROCK (male vocals). 2.2 * 0.85 = 1.87.
# Third one is LO-FI (instrumental). 1.5 * 0.85 = 1.275. (This one stays same)
# Fourth one is JAZZ (auto). 1.5 (no reduction). (This one stays same, but wait, test says 1.5. New base is 1.5).

# Let's use more specific replacements or just overwrite the file content cleanly if regex is tricky.
# Overwriting is safer given I have the content.
pass

with open("tests/test_vocal_logic.py", "w") as f:
    f.write(content)


# Update tests/test_vocals.py
with open("tests/test_vocals.py", "r") as f:
    content = f.read()

content = content.replace('self.assertEqual(negative_prompt, "male vocals")', 'self.assertEqual(negative_prompt, "male vocals, low quality, glitch, distorted")')
content = content.replace('self.assertEqual(negative_prompt, "female vocals")', 'self.assertEqual(negative_prompt, "low quality, glitch, distorted")')
content = content.replace('self.assertEqual(negative_prompt, "vocals, voice, singing, lyrics, speech")', 'self.assertEqual(negative_prompt, "vocals, voice, singing, lyrics, speech, low quality, glitch, distorted")')
content = content.replace('self.assertEqual(negative_prompt, "")', 'self.assertEqual(negative_prompt, "low quality, glitch, distorted")')

with open("tests/test_vocals.py", "w") as f:
    f.write(content)
