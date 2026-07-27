import json
import logging
import os
from config import MUSIC_PROMPTS, ALBUM_MODEL
from tools.utils import strip_thinking
from tools.llm import generate_text


class MusicAgent:
    def __init__(self):
        self.model = os.getenv("MUSIC_MODEL", ALBUM_MODEL)

    def generate_direction(self, genre, user_direction, trending_data=None):
        system_prompt = MUSIC_PROMPTS.get(genre.upper(), MUSIC_PROMPTS.get("POP", "Default POP Prompt"))
        
        trending_context = f"TRENDING DATA (Incorporate if relevant): {trending_data}\n\n" if trending_data else ""

        user_prompt = (
            f"PRIMARY INSTRUCTION (USER DIRECTION): {user_direction}\n\n"
            f"GENRE CONTEXT: {genre}\n\n"
            f"{trending_context}"
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
            response_text = generate_text(
                self.model,
                f"{system_prompt}\n\n{user_prompt}",
                timeout=60,
                temperature=0.7,
                json_mode=True,
            )
            
            # Strip thinking blocks before parsing JSON
            response_text = strip_thinking(response_text)
            if response_text.startswith("```"):
                response_text = response_text.strip("`").removeprefix("json").strip()

            # Parse JSON
            direction = json.loads(response_text)
            # Ensure all fields exist, provide defaults if missing
            return {
                "tags": direction.get("tags", "upbeat, emotional, popular music"),
                "bpm": int(direction.get("bpm", 120)),
                "keyscale": direction.get("keyscale", "C major")
            }
        except Exception as e:
            # Catch both parsing errors and request errors here
            logging.error(f"Error generating or parsing musical direction: {e}")
            if 'response_text' in locals():
                logging.error(f"Raw Response: {response_text}")

            return {
                "tags": "upbeat, emotional, popular music",
                "bpm": 120,
                "keyscale": "C major"
            }
