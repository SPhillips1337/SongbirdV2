import requests
import logging
from config import ARTIST_STYLES, OLLAMA_BASE_URL, ARTIST_MODEL, DEFAULT_ARTIST_STYLE


class ArtistAgent:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = ARTIST_MODEL

    def generate_persona(self, genre, user_direction=None):
        prompt = f"""Generate a detailed character profile for a {genre} song protagonist. The persona should be a woman in their early 20s to 30s.

        GENRE: {genre}
        USER DIRECTION: {user_direction if user_direction else "No specific direction provided."}

        The profile must include:
        A classic, {genre} star two-part name like .

        Please generate a background story and persona that would fit the {genre} and strictly incorporate any specific character traits or vibes mentioned in the USER DIRECTION.

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

    def select_artist_style(self, genre, user_direction=None):
        # We could use an LLM here for more dynamic style selection based on direction,
        # but for now, we'll stick to the mapping or a default.
        return ARTIST_STYLES.get(genre.upper(), DEFAULT_ARTIST_STYLE)
