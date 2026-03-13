import requests
import logging
import json
from config import OLLAMA_BASE_URL, ALBUM_MODEL
from tools.utils import strip_thinking

class NarrativeAgent:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = ALBUM_MODEL

    def generate_album_narrative(self, genre, theme, album_title, band_bio=None, num_songs=6):
        """
        Generates a master narrative arc for the entire album.
        """
        system_prompt = (
            "You are an expert concept album writer and narrative designer. Your goal is to create a cohesive "
            "and compelling story arc for a music album based on the provided theme and genre."
        )

        user_prompt = f"""
        ALBUM TITLE: {album_title}
        GENRE: {genre}
        THEME: {theme}
        BAND/ARTIST BIO: {band_bio if band_bio else "N/A"}
        NUMBER OF SONGS: {num_songs}

        Please generate a master narrative arc for this album. 
        Your output must be a structured plan that describes the overall story and provides a brief summary/direction 
        for each of the {num_songs} tracks.

        The narrative should have a clear beginning, middle (development/conflict), and end (resolution/finale).
        Avoid clichés unless they are specifically requested.

        Format:
        Overall Narrative: [A paragraph describing the album's concept and story arc]
        Track 1: [Direction/Theme for track 1]
        Track i: [Direction/Theme for track i]
        ...
        Track {num_songs}: [Direction/Theme for track {num_songs}]

        Important: Do not include any additional text or explanations. 
        Focus purely on the narrative content.
        """

        payload = {
            "model": self.model,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "options": {
                "temperature": 0.8,
                "top_p": 0.9
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            text = response.json().get("response", "").strip()
            return strip_thinking(text)
        except Exception as e:
            logging.error(f"Error generating album narrative: {e}")
            return f"A cohesive {genre} album following the theme of {theme}."
