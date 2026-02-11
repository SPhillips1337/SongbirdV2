import os
import json
import argparse
import logging
import requests
import glob
import re
import config
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

from config import OLLAMA_BASE_URL, ALBUM_MODEL
from state import SongState
from agents.artist import ArtistAgent
from agents.music import MusicAgent
from agents.lyrics import LyricsAgent
from tools.comfy import ComfyClient

SONG_FILENAME_PATTERN = re.compile(r"song_(\d+)_")

class SongbirdWorkflow:
    def __init__(self, output_dir="output"):
        self.artist_agent = ArtistAgent()
        self.music_agent = MusicAgent()
        self.lyrics_agent = LyricsAgent()
        self.comfy = ComfyClient(output_dir=output_dir)
        
        # Build the graph
        workflow = StateGraph(SongState)
        
        # Define nodes
        workflow.add_node("create_artist", self.node_create_artist)
        workflow.add_node("create_music_direction", self.node_create_music)
        # Combined lyrics generation node
        workflow.add_node("write_lyrics", self.lyrics_agent.write_lyrics_node)
        workflow.add_node("generate_audio", self.node_generate_audio)
        
        # Define edges
        workflow.set_entry_point("create_artist")
        workflow.add_edge("create_artist", "create_music_direction")
        workflow.add_edge("create_music_direction", "write_lyrics")
        workflow.add_edge("write_lyrics", "generate_audio")
        workflow.add_edge("generate_audio", END)
        
        self.app = workflow.compile()
        
    def normalize_keyscale(self, keyscale_str):
        """Normalizes keyscale string for ComfyUI validation.
        Expected format: '{Note} {major/minor}' (e.g., 'C major', 'F# minor')
        """
        if not keyscale_str or not isinstance(keyscale_str, str):
            return "C major"
            
        parts = keyscale_str.strip().split()
        if not parts:
            return "C major"
            
        # Note normalization (capitalize first letter, handle # and b)
        note = parts[0]
        if len(note) > 1:
            note = note[0].upper() + note[1:].lower()
        else:
            note = note.upper()
            
        # Scale normalization (major or minor)
        scale = "major" # Default
        if len(parts) > 1:
            scale_part = parts[1].lower()
            if "minor" in scale_part or "m" == scale_part:
                scale = "minor"
            else:
                scale = "major"
                
        return f"{note} {scale}"

    def node_create_artist(self, state: SongState):
        state["artist_style"] = self.artist_agent.select_artist_style(state["genre"], state["user_direction"])
        state["artist_background"] = self.artist_agent.generate_persona(state["genre"], state["user_direction"])
        state["artist_name"] = "Songbird" # Placeholder for name extraction
        return state

    def node_create_music(self, state: SongState):
        state["musical_direction"] = self.music_agent.generate_direction(
            state["genre"], state["user_direction"]
        )
        return state

    def node_generate_audio(self, state: SongState):
        music_dir = state["musical_direction"]
        # Handle dict or fallback string
        if isinstance(music_dir, dict):
            tags = music_dir.get("tags", "")
            bpm = music_dir.get("bpm", 120)
            keyscale = self.normalize_keyscale(music_dir.get("keyscale", "C major"))
        else:
            tags = str(music_dir)
            bpm = 120
            keyscale = "C major"

        result = self.comfy.submit_prompt(
            state["cleaned_lyrics"], 
            tags=tags,
            bpm=bpm,
            keyscale=keyscale,
            filename_prefix=f"{state['artist_name']}_song"
        )

        if result and "prompt_id" in result:
            prompt_id = result["prompt_id"]
            logging.info(f"Audio generation started. Prompt ID: {prompt_id}")
            audio_path = self.comfy.wait_and_download_output(prompt_id)
            state["audio_path"] = audio_path
        else:
            state["audio_path"] = "error"

        return state

    def run(self, genre, user_direction):
        initial_state = {
            "genre": genre,
            "user_direction": user_direction,
            "artist_name": None,
            "artist_background": None,
            "artist_style": None,
            "musical_direction": None,
            "lyrics": None,
            "cleaned_lyrics": None,
            "audio_path": None,
            "research_notes": None,
            "history": []
        }
        final_state = self.app.invoke(initial_state)
        self.save_metadata(final_state)
        return final_state

    def save_metadata(self, state: SongState):
        """Saves song details to a text file in the output directory."""
        if not state.get("audio_path") or state["audio_path"] == "error":
            logging.info("Skipping metadata save: No audio generated.")
            return

        # Derive metadata path from audio path (e.g., song.mp3 -> song_metadata.txt)
        base_path = os.path.splitext(state["audio_path"])[0]
        meta_path = f"{base_path}_metadata.txt"

        content = [
            f"Artist: {state['artist_name']}",
            f"Background: {state['artist_background']}",
            f"Genre: {state['genre']}",
            f"Style (Reference): {state['artist_style']}",
            "\n--- Musical Direction ---",
            json.dumps(state['musical_direction'], indent=2) if isinstance(state['musical_direction'], dict) else str(state['musical_direction']),
            "\n--- Lyrics ---",
            state.get('cleaned_lyrics', state.get('lyrics', 'No lyrics generated.')),
            "\n--- Research Notes ---",
            state.get('research_notes', 'No research notes.')
        ]

        try:
            with open(meta_path, "w") as f:
                f.write("\n".join(content))
            logging.info(f"Saved song metadata to {meta_path}")
        except Exception as e:
            logging.error(f"Error saving metadata: {e}")

def scan_recent_songs(output_dir, n=3):
    """
    Scans the output directory for recent song metadata files.
    Sorts by the song number in the filename and returns summaries of the last n songs.
    """
    files = glob.glob(os.path.join(output_dir, "*_metadata.txt"))

    # Sort files by the numeric part in the filename
    # Assuming filename format: Songbird_song_{number}__metadata.txt
    def extract_number(filename):
        # Match "song_" followed by digits and another underscore
        # Actual format is usually: Songbird_song_00040__metadata.txt
        match = SONG_FILENAME_PATTERN.search(filename)
        if match:
            return int(match.group(1))
        return 0

    sorted_files = sorted(files, key=extract_number)
    recent_files = sorted_files[-n:] if n > 0 else []

    summaries = []
    for filepath in recent_files:
        try:
            with open(filepath, "r") as f:
                content = f.read()

            summary = {}
            # simple parsing
            artist_match = re.search(r"Artist: (.*)", content)
            background_match = re.search(r"Background: (.*)", content)

            # Extract lyrics section (first few lines)
            lyrics_section = ""
            if "--- Lyrics ---" in content:
                parts = content.split("--- Lyrics ---")
                if len(parts) > 1:
                    lyrics_raw = parts[1].split("--- Research Notes ---")[0].strip()
                    # Take first 10 lines
                    lyrics_lines = lyrics_raw.split("\n")[:10]
                    lyrics_section = "\n".join(lyrics_lines)

            # Extract musical direction
            music_section = ""
            if "--- Musical Direction ---" in content:
                parts = content.split("--- Musical Direction ---")
                if len(parts) > 1:
                    music_section = parts[1].split("--- Lyrics ---")[0].strip()

            summary["number"] = extract_number(filepath)
            summary["artist"] = artist_match.group(1) if artist_match else "Unknown"
            summary["background"] = background_match.group(1) if background_match else "Unknown"
            summary["lyrics_snippet"] = lyrics_section
            summary["musical_direction"] = music_section

            summaries.append(summary)
        except Exception as e:
            logging.error(f"Error reading metadata file {filepath}: {e}")

    return summaries

def generate_next_direction(theme, base_direction, previous_songs_summaries, current_song_index, total_songs):
    """
    Generates the direction for the next song using Ollama.
    """
    system_prompt = (
        "You are an expert rock album concept writer. Given an album theme and summaries of previous songs, "
        "suggest the NEXT direction prompt (a short string, 50-100 words) that logically continues the narrative arc "
        "while keeping musical cohesion. Make it feel like the next chapter in a story. "
        "Always include references to progression (e.g., 'continue the wolf saga', 'now the pack unites', 'climactic hunt', 'dawn reflection/finale')."
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
        return result.get("response", "").strip()
    except Exception as e:
        logging.error(f"Error calling Ollama: {e}")
        # Graceful fallback if Ollama fails or times out
        return f"{base_direction} {theme}. Continue the story (Song {current_song_index}/{total_songs})."

def main():
    parser = argparse.ArgumentParser(description="Songbird: AI Song Generation Agent")
    parser.add_argument("--genre", type=str, default="POP", help="Song genre (default: POP)")
    parser.add_argument("--direction", type=str, default="A catchy upbeat pop song in the style of Black Pink about freedom with powerful female vocals and a live drummer.", help="Musical direction for the song")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", type=str, default="output", help="Output directory (default: output)")

    # Album mode arguments
    parser.add_argument("--album", action="store_true", help="Enable album mode")
    parser.add_argument("--theme", type=str, help="Album theme (required if --album is used)")
    parser.add_argument("--num-songs", type=int, default=6, help="Number of songs for the album (default: 6)")
    parser.add_argument("--base-direction", type=str, default="", help="Shared constraints for every song")

    args = parser.parse_args()

    if args.album and not args.theme:
        parser.error("--theme is required when --album is used.")

    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    flow = SongbirdWorkflow(output_dir=args.output)

    if args.album:
        print(f"Starting Album Generation Mode: '{args.theme}'")
        print(f"Total songs: {args.num_songs}")

        for i in range(1, args.num_songs + 1):
            print(f"\n--- Generating Song {i}/{args.num_songs} ---")

            if i == 1:
                # First song direction
                current_direction = f"{args.base_direction} Start the album saga: {args.theme}. Begin with the awakening/escape/origin story."
            else:
                # Subsequent songs: get context from previous songs
                print("Retrieving context from previous songs...")
                recent_summaries = scan_recent_songs(args.output, n=3)
                current_direction = generate_next_direction(
                    args.theme,
                    args.base_direction,
                    recent_summaries,
                    i,
                    args.num_songs
                )

            logging.info(f"Song {i} Direction: {current_direction}")
            print(f"Direction: {current_direction}")

            # Run workflow for this song
            final_state = flow.run(args.genre, current_direction)

            if final_state.get('audio_path') and final_state['audio_path'] != "error":
                print(f"Song {i} complete: {final_state['audio_path']}")
            else:
                print(f"Song {i} failed to generate audio.")

        print("\nAlbum Generation Complete!")

    else:
        # Standard single song mode
        final_state = flow.run(args.genre, args.direction)

        print("Workflow Complete!")
        if final_state.get('cleaned_lyrics'):
            print(f"Lyrics Preview: {final_state['cleaned_lyrics'][:100]}...")

        if final_state.get('audio_path'):
            print(f"Audio Path: {final_state['audio_path']}")
        else:
            print("Audio Path: None")

if __name__ == "__main__":
    main()
