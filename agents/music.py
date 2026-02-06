import os
import requests


class MusicAgent:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LYRIC_MODEL", "qwen3:14b")

    def generate_direction(self, genre, user_direction):
        # Switch logic based on genre as seen in n8n
        prompts = {
            "RAP": "You are an expert RAP music producer. Generate a detailed musical direction for a hard-hitting RAP track...",
            "POP": "You are an expert POP music producer. Generate a detailed musical direction for a catchy POP track...",
            "JAZZ": "You are an expert JAZZ music producer. Generate a detailed musical direction for a smooth JAZZ track..."
        }
        
        system_prompt = prompts.get(genre.upper(), prompts["POP"])
        user_prompt = f"User Direction: {user_direction}\nGenre: {genre}\n\nReturn a JSON-like object with 'tags' (a descriptive styling paragraph), 'bpm' (numeric), and 'keyscale' (e.g. 'C major')."

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model, 
                    "prompt": f"{system_prompt}\n\n{user_prompt}", 
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Error generating musical direction: {e}")
            return "upbeat, 120 BPM, emotional"
