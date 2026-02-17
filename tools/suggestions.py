import os
import glob
import re
import logging
import json
import requests
from collections import Counter
from config import OLLAMA_BASE_URL, ALBUM_MODEL

def scan_history(output_dir):
    """
    Scans all metadata files in the output directory to analyze user history.
    Returns a summary of frequent genres, themes, and styles.
    """
    # Recursive search for metadata files
    files = glob.glob(os.path.join(output_dir, "**", "*_metadata.txt"), recursive=True)

    genres = []
    styles = []

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            genre_match = re.search(r"Genre: (.*)", content)
            if genre_match:
                g = genre_match.group(1).strip()
                if g and g != "Unknown":
                    genres.append(g)

            style_match = re.search(r"Style \(Reference\): (.*)", content)
            if style_match:
                s = style_match.group(1).strip()
                if s and s != "N/A":
                    styles.append(s)

        except Exception as e:
            logging.warning(f"Error reading {filepath}: {e}")

    genre_counts = Counter(genres).most_common(5)
    style_counts = Counter(styles).most_common(5)

    return {
        "top_genres": [g[0] for g in genre_counts],
        "top_styles": [s[0] for s in style_counts],
        "total_songs": len(files)
    }

def generate_suggestion(history):
    """
    Generates a new song suggestion based on user history.
    """
    if not history or history["total_songs"] == 0:
        return None

    prompt = f"""Based on the user's history, suggest a creative new song idea.

    User History:
    - Top Genres: {', '.join(history['top_genres'])}
    - Top Artist Styles: {', '.join(history['top_styles'])}

    Task:
    1. Analyze the patterns in the history.
    2. Propose a new song idea that fits the user's taste but offers a fresh twist.
    3. Output the result in a strict JSON format with keys: 'genre', 'direction', 'rationale'.

    Output JSON only.
    """

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": ALBUM_MODEL,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            },
            timeout=60
        )
        response.raise_for_status()
        result = json.loads(response.json().get("response", "{}"))
        return result
    except Exception as e:
        logging.error(f"Error generating suggestion: {e}")
        return None
