import requests
import logging
from config import OLLAMA_BASE_URL, ALBUM_MODEL
from tools.utils import strip_thinking

def generate_next_direction(theme, base_direction, previous_songs_summaries, current_song_index, total_songs, album_narrative=None):
    """
    Generates the direction for the next song using Ollama.
    """
    narrative_context = f"\nALBUM NARRATIVE ARC:\n{album_narrative}\n" if album_narrative else ""
    
    system_prompt = (
        "You are an expert rock album concept writer. Given an album theme, the overall narrative arc, "
        "and summaries of previous songs, suggest the NEXT direction prompt (a short string, 50-100 words) "
        "that logically continues the narrative while keeping musical cohesion. "
        "Make it feel like the next chapter in the story."
    )

    prev_songs_text = "".join(
        f"Song {summary.get('number', i+1)}: "
        f"Background: {summary.get('background', 'N/A')} | "
        f"Key lyrics: {summary.get('lyrics_snippet', 'N/A')[:200]}... | "
        f"Vibe: {summary.get('musical_direction', 'N/A')}\n"
        for i, summary in enumerate(previous_songs_summaries)
    )

    user_prompt = (
        f"Album theme: {theme}\n"
        f"Shared constraints: {base_direction}\n"
        f"{narrative_context}"
        f"Previous songs summary:\n{prev_songs_text}\n"
        f"Now generate the direction prompt for song {current_song_index} of {total_songs}:"
    )

    payload = {
        "model": ALBUM_MODEL,
        "prompt": f"{system_prompt}\n\n{user_prompt}",
        "stream": False
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120 # Prevent indefinite hangs
        )
        # Check status before trying to parse JSON
        if response.status_code != 200:
            logging.error(f"Ollama returned non-200 status: {response.status_code}")
            return f"{base_direction} {theme}. Continue the story (Song {current_song_index}/{total_songs})."

        result = response.json()
        text = result.get("response", "").strip()
        return strip_thinking(text)
    except Exception as e:
        logging.error(f"Error calling Ollama: {e}")
        # Graceful fallback if Ollama fails or times out
        return f"{base_direction} {theme}. Continue the story (Song {current_song_index}/{total_songs})."

def generate_album_title(genre, theme, direction):
    """
    Generates a creative album title using Ollama.
    """
    prompt = (
        f"Generate a creative, short (3-5 words) album title for a {genre} album.\n"
        f"Theme: {theme}\n"
        f"Style/Direction: {direction}\n"
        "Output ONLY the album title, nothing else. Do not use quotes."
    )

    payload = {
        "model": ALBUM_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            title = response.json().get("response", "").strip()
            title = strip_thinking(title)
            # Remove quotes if present
            if (title.startswith('"') and title.endswith('"')) or (title.startswith("'") and title.endswith("'")):
                title = title[1:-1]
            return title if title else theme
        else:
            logging.error(f"Ollama returned non-200 status for album title: {response.status_code}")
    except Exception as e:
        logging.error(f"Error generating album title: {e}")

    return theme

def generate_song_title(album_name, track_number, genre, theme, direction, album_narrative=None):
    """
    Generates a creative song title using Ollama.
    """
    narrative_context = f"Album Narrative: {album_narrative}\n" if album_narrative else ""
    prompt = (
        f"Generate a creative song title for track #{track_number} of the album '{album_name}'.\n"
        f"Genre: {genre}\n"
        f"Album Theme: {theme}\n"
        f"{narrative_context}"
        f"Song Direction: {direction}\n"
        "The title should be cohesive with the album concept.\n"
        "Output ONLY the song title, nothing else. Do not use quotes."
    )

    payload = {
        "model": ALBUM_MODEL,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=30
        )
        if response.status_code == 200:
            title = response.json().get("response", "").strip()
            title = strip_thinking(title)
            # Remove quotes if present
            if (title.startswith('"') and title.endswith('"')) or (title.startswith("'") and title.endswith("'")):
                title = title[1:-1]
            return title if title else f"Song {track_number}"
        else:
            logging.error(f"Ollama returned non-200 status for song title: {response.status_code}")
    except Exception as e:
        logging.error(f"Error generating song title: {e}")

    return f"Song {track_number}"
