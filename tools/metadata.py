import os
import glob
import re
import logging
import heapq

def scan_recent_songs(output_dir, n=3):
    """
    Scans the output directory for recent song metadata files.
    Returns summaries of the last n songs by song number.
    Uses heapq.nlargest for O(N log K) complexity instead of O(N log N).
    """
    files = glob.glob(os.path.join(output_dir, "*_metadata.txt"))

    # Extract song number from filename
    # Assuming filename format: Songbird_song_{number}__metadata.txt
    def extract_number(filename):
        # Match "song_" followed by digits and another underscore
        # Actual format is usually: Songbird_song_00040__metadata.txt
        match = re.search(r"song_(\d+)_", filename)
        if match:
            return int(match.group(1))
        return 0

    # Use heapq.nlargest for better performance: O(N log K) vs O(N log N)
    # Note: nlargest returns in descending order, so we reverse to get ascending
    recent_files = list(reversed(heapq.nlargest(n, files, key=extract_number))) if n > 0 else []

    summaries = []
    for filepath in recent_files:
        try:
            with open(filepath, "r") as f:
                content = f.read()

            summary = {}
            # simple parsing
            artist_match = re.search(r"Artist: (.*)", content)
            background_match = re.search(r"Background: (.*)", content)

            # Extract lyrics section (first few lines)
            lyrics_section = ""
            if "--- Lyrics ---" in content:
                parts = content.split("--- Lyrics ---")
                if len(parts) > 1:
                    lyrics_raw = parts[1].split("--- Research Notes ---")[0].strip()
                    # Take first 10 lines
                    lyrics_lines = lyrics_raw.split("\n")[:10]
                    lyrics_section = "\n".join(lyrics_lines)

            # Extract musical direction
            music_section = ""
            if "--- Musical Direction ---" in content:
                parts = content.split("--- Musical Direction ---")
                if len(parts) > 1:
                    music_section = parts[1].split("--- Lyrics ---")[0].strip()

            summary["number"] = extract_number(filepath)
            summary["artist"] = artist_match.group(1) if artist_match else "Unknown"
            summary["background"] = background_match.group(1) if background_match else "Unknown"
            summary["lyrics_snippet"] = lyrics_section
            summary["musical_direction"] = music_section

            summaries.append(summary)
        except Exception as e:
            logging.error(f"Error reading metadata file {filepath}: {e}")

    return summaries
