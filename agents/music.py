import os
import requests
import json
from config import MUSIC_PROMPTS


class MusicAgent:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LYRIC_MODEL", "qwen3:14b")

    def generate_direction(self, genre, user_direction):
        system_prompt = MUSIC_PROMPTS.get(genre.upper(), MUSIC_PROMPTS["POP"])
        
        user_prompt = (
            f"User Direction: {user_direction}\n"
            f"Genre: {genre}\n\n"
            "Task: Create a musical direction for this song.\n"
            "Output Format: Strict JSON object with no markdown formatting.\n"
            "Required Fields:\n"
            "- 'tags': A string of evocative, descriptive tags suitable for music generation (e.g., 'ethereal vocals, thumping bass, neon atmosphere').\n"
            "- 'bpm': An integer representing the tempo.\n"
            "- 'keyscale': A string representing the key (e.g., 'C major', 'F# minor')."
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
            try:
                direction = json.loads(response_text)
                # Ensure all fields exist, provide defaults if missing
                return {
                    "tags": direction.get("tags", "upbeat, emotional, popular music"),
                    "bpm": int(direction.get("bpm", 120)),
                    "keyscale": direction.get("keyscale", "C major")
                }
            except (json.JSONDecodeError, ValueError) as e:
                print(f"JSON Parse Error. Response: {response_text}. Error: {e}")
                raise ValueError("Invalid JSON output")

        except Exception as e:
            print(f"Error generating musical direction: {e}")
            return {
                "tags": "upbeat, emotional, popular music",
                "bpm": 120,
                "keyscale": "C major"
            }
