import os
import json
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ARTIST_MODEL = os.getenv("ARTIST_MODEL", "llama3")
LYRIC_MODEL = os.getenv("LYRIC_MODEL", "llama3")
ALBUM_MODEL = os.getenv("ALBUM_MODEL", "llama3")

def load_json_config(filename, default=None):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "config_data", filename)
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading config {filename}: {e}")
        return default or {}

# Musical direction prompts by genre
MUSIC_PROMPTS = load_json_config("music_prompts.json")

# Artist styles by genre
ARTIST_STYLES = load_json_config("artist_styles.json")

# Default artist style when genre is not found in ARTIST_STYLES
DEFAULT_ARTIST_STYLE = "Adele"


# Default negative prompt suffix for high-fidelity audio
DEFAULT_NEGATIVE_PROMPT_SUFFIX = ", low quality, glitch, distorted"