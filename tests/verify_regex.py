import re

def extract_number(filename):
    # Match "song_" followed by digits and another underscore
    match = re.search(r"song_(\d+)_", filename)
    if match:
        return int(match.group(1))
    return 0

test_files = [
    "Songbird_song_00040__metadata.txt",
    "Songbird_song_00041__metadata.txt",
    "Songbird_song_00042__.mp3",
    "other_file.txt"
]

for f in test_files:
    num = extract_number(f)
    print(f"File: {f} -> Number: {num}")

assert extract_number("Songbird_song_00040__metadata.txt") == 40
assert extract_number("Songbird_song_001__.mp3") == 1
assert extract_number("invalid") == 0

print("Regex Verification Passed!")
