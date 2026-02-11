import requests
import json
import logging
from config import MUSIC_PROMPTS, OLLAMA_BASE_URL, LYRIC_MODEL


class MusicAgent:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = LYRIC_MODEL

    def generate_direction(self, genre, user_direction):
        system_prompt = MUSIC_PROMPTS.get(genre.upper(), MUSIC_PROMPTS.get("POP", "Default POP Prompt"))
        
        user_prompt = (
            f"PRIMARY INSTRUCTION (USER DIRECTION): {user_direction}\n\n"
            f"GENRE CONTEXT: {genre}\n\n"
            "Task: Create a musical direction for this song.\n"
            "INSTRUCTIONS:\n"
            "1. STRICTLY ADHERE to all stylistic details, vocals, and instruments mentioned in the PRIMARY INSTRUCTION.\n"
            "2. Use the GENRE CONTEXT for atmospheric inspiration but do not let it override specific user requests.\n"
            "3. Output Format: Strict JSON object with no markdown formatting.\n"
            "Required Fields:\n"
            "- 'tags': A string of evocative, descriptive, and structural tags suitable for music generation.\n"
            "  - IMPORTANT: You MUST include structural tags such as [Intro], [Verse], [Chorus], [Bridge], [Outro], [Solo], [Build-up], [Drop], etc. as per ACE-Step/Aisonify standards.\n"
            "  - Example tags: 'ethereal vocals, thumping bass, neon atmosphere, [Intro - synth], [Chorus - anthemic], [Build-up]'\n"
            "- 'bpm': An integer representing the tempo.\n"
            "- 'keyscale': A string representing the key (e.g., 'C major', 'F# minor'). Use lowercase for 'major' and 'minor'."
        )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model, 
                    "prompt": f"{system_prompt}\n\n{user_prompt}", 
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            response.raise_for_status()
            response_text = response.json().get("response", "").strip()

            # Parse JSON
            direction = json.loads(response_text)
            # Ensure all fields exist, provide defaults if missing
            return {
                "tags": direction.get("tags", "upbeat, emotional, popular music"),
                "bpm": int(direction.get("bpm", 120)),
                "keyscale": direction.get("keyscale", "C major")
            }
        except (json.JSONDecodeError, ValueError, requests.RequestException) as e:
            # Catch both parsing errors and request errors here
            logging.error(f"Error generating or parsing musical direction: {e}")
            if 'response_text' in locals():
                logging.error(f"Raw Response: {response_text}")

            return {
                "tags": "upbeat, emotional, popular music",
                "bpm": 120,
                "keyscale": "C major"
            }
