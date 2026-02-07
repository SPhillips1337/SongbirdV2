import os
import requests
import logging
from config import ARTIST_STYLES


class ArtistAgent:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("ARTIST_MODEL", "qwen3:14b")

    def generate_persona(self, genre):
        prompt = f"""Generate a detailed character profile for a {genre} song protagonist. The persona should be a woman in their early 20s to 30s.

The profile must include:
A classic, {genre} star two-part name like .

Please generate a backgrounds story and persona that would fit the {genre} for their life that we can reference when making music for them.

The final output should be a single, descriptive paragraph summarizing this character's background, ready to be used as the basis for a song.

Important: Do not include any additional text, explanations, or conversational phrases. Your final response must contain only the generated artist background persona."""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            logging.error(f"Error generating artist persona: {e}")
            return f"A mysterious singer in the {genre} scene."

    def select_artist_style(self, genre):
        return ARTIST_STYLES.get(genre.upper(), "Adele")
