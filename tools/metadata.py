import os
import glob
import re
import logging
import heapq
import json

def scan_recent_songs(output_dir, n=3):
    """
    Scans the output directory for recent song metadata files.
    Returns summaries of the last n songs by song number.
    Uses heapq.nlargest for O(N log K) complexity instead of O(N log N).
    """
    files = glob.glob(os.path.join(output_dir, "*_metadata.txt"))

    # Extract song number from filename
    # Legacy format: Songbird_song_{number}__metadata.txt
    # New format: {number}_{title}_metadata.txt
    def extract_number(filename):
        base = os.path.basename(filename)

        # Try new format: Starts with digits followed by underscore
        # e.g., "01_Song_Title_metadata.txt" -> 1
        match_new = re.match(r"^(\d+)_", base)
        if match_new:
            return int(match_new.group(1))

        # Try legacy format: Contains "song_{digits}_"
        # e.g., "Songbird_song_00040__metadata.txt" -> 40
        match_old = re.search(r"song_(\d+)_", base)
        if match_old:
            return int(match_old.group(1))

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

def save_metadata(state):
    """Saves song details to a text file in the output directory."""
    if not state.get("audio_path") or state["audio_path"] == "error":
        logging.info("Skipping metadata save: No audio generated.")
        return

    # Derive metadata path from audio path (e.g., song.mp3 -> song_metadata.txt)
    base_path = os.path.splitext(state["audio_path"])[0]
    meta_path = f"{base_path}_metadata.txt"

    content = [
        f"Artist: {state.get('artist_name', 'Unknown')}",
        f"Album: {state.get('album_name', 'N/A')}",
        f"Song Title: {state.get('song_title', 'N/A')}",
        f"Background: {state.get('artist_background', 'N/A')}",
        f"Genre: {state.get('genre', 'Unknown')}",
        f"Style (Reference): {state.get('artist_style', 'N/A')}",
        "\n--- Musical Direction ---",
        json.dumps(state['musical_direction'], indent=2) if isinstance(state.get('musical_direction'), dict) else str(state.get('musical_direction', 'N/A')),
        "\n--- Lyrics ---",
        state.get('cleaned_lyrics', state.get('lyrics', 'No lyrics generated.')),
        "\n--- Research Notes ---",
        state.get('research_notes', 'No research notes.')
    ]

    try:
        with open(meta_path, "w") as f:
            f.write("\n".join(content))
        logging.info(f"Saved song metadata to {meta_path}")
    except Exception as e:
        logging.error(f"Error saving metadata: {e}")
