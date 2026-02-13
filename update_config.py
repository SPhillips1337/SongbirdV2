import json

with open("config.py", "r") as f:
    content = f.read()

# Append DEFAULT_NEGATIVE_PROMPT_SUFFIX
if "DEFAULT_NEGATIVE_PROMPT_SUFFIX" not in content:
    content += '\n\n# Default negative prompt suffix for high-fidelity audio\nDEFAULT_NEGATIVE_PROMPT_SUFFIX = ", low quality, glitch, distorted"'

with open("config.py", "w") as f:
    f.write(content)
