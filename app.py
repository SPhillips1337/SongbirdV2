import os
import json
import argparse
import logging
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

from state import SongState
from agents.artist import ArtistAgent
from agents.music import MusicAgent
from agents.lyrics import LyricsAgent
from tools.comfy import ComfyClient

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

    def node_create_artist(self, state: SongState):
        state["artist_style"] = self.artist_agent.select_artist_style(state["genre"])
        state["artist_background"] = self.artist_agent.generate_persona(state["genre"])
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
            keyscale = music_dir.get("keyscale", "C major")
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

def main():
    parser = argparse.ArgumentParser(description="Songbird: AI Song Generation Agent")
    parser.add_argument("--genre", type=str, default="POP", help="Song genre (default: POP)")
    parser.add_argument("--direction", type=str, default="A catchy upbeat pop song in the style of Black Pink about freedom with powerful female vocals and a live drummer.", help="Musical direction for the song")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", type=str, default="output", help="Output directory (default: output)")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    flow = SongbirdWorkflow(output_dir=args.output)

    # Use the parsed arguments
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
