import os
import time
import argparse
import logging
import re
import config
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from state import SongState
from agents.artist import ArtistAgent
from agents.music import MusicAgent
from agents.lyrics import LyricsAgent
from tools.comfy import ComfyClient
from tools.metadata import scan_recent_songs, save_metadata
from tools.utils import sanitize_input, sanitize_filename, normalize_keyscale
from tools.audio_engineering import calculate_song_parameters
from agents.director import generate_next_direction, generate_album_title, generate_song_title

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
        
    def set_output_dir(self, output_dir):
        """Updates the output directory for the workflow."""
        self.comfy.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def node_create_artist(self, state: SongState):
        # Check if artist style/background are already provided (e.g. in Album Mode)
        if not state.get("artist_style"):
            state["artist_style"] = self.artist_agent.select_artist_style(state["genre"], state["user_direction"])

        if not state.get("artist_background"):
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
            # Default fallback, will be overridden by key logic below
            keyscale = normalize_keyscale(music_dir.get("keyscale", "C major"))
        else:
            tags = str(music_dir)
            bpm = 120
            keyscale = "C major"

        # Vocal Prompt Injection Logic
        vocals = state.get("vocals", "auto")
        vocal_strength = state.get("vocal_strength", 1.2)

        # New Negative Prompt Logic - High Fidelity / Minimal
        # Rule: ("male vocals" if female else "") + ", low quality, glitch, distorted"
        suffix = ", low quality, glitch, distorted"
        negative_prompt = ""

        if vocals == "female":
            tags = f"(female vocals:{vocal_strength}), female singer, {tags}"
            negative_prompt = "male vocals" + suffix
        elif vocals == "male":
            tags = f"(male vocals:{vocal_strength}), male singer, {tags}"
            # Minimal negative prompt as requested
            negative_prompt = suffix.lstrip(", ")
        elif vocals == "instrumental":
            tags = f"(instrumental:{vocal_strength}), no vocals, {tags}"
            # For instrumental, we must negate vocals to ensure compliance
            negative_prompt = "vocals, voice, singing, lyrics, speech" + suffix
        elif vocals == "duet":
            tags = f"(duet vocals:{vocal_strength}), {tags}"
            negative_prompt = suffix.lstrip(", ")
        elif vocals == "choir":
            tags = f"(choir vocals:{vocal_strength}), {tags}"
            negative_prompt = suffix.lstrip(", ")
        else:
            # Auto or others
            negative_prompt = suffix.lstrip(", ")

        # Use seed if provided (for consistent audio generation)
        seed = state.get("seed")

        filename_prefix = f"{state['artist_name']}_song"
        # Use song title and track number for clean filename
        if state.get("track_number") and state.get("song_title"):
            safe_title = sanitize_filename(state["song_title"])
            filename_prefix = f"{state['track_number']:02d}_{safe_title}"

        # Dynamic Audio Engineering
        params = calculate_song_parameters(state["genre"], state.get("cleaned_lyrics", ""))

        # Resolve Key
        # Priority: User Input > Genre Default > Fallback (MusicAgent/C Major)
        user_key = state.get("key")
        genre_default_key = params.get("default_key")

        if user_key:
            keyscale = normalize_keyscale(user_key)
            logging.info(f"Using User Key: {keyscale}")
        elif genre_default_key:
            keyscale = normalize_keyscale(genre_default_key)
            logging.info(f"Using Genre Default Key: {keyscale}")
        else:
            # Keep existing keyscale from MusicAgent or fallback
            logging.info(f"Using Generated/Fallback Key: {keyscale}")

        # Adjust CFG for vocal control (lower CFG to compensate for high prompt weights)
        if vocals != "auto":
            params["cfg"] = params["cfg"] * 0.85
            logging.info(f"Vocal control active: Lowering CFG to {params['cfg']:.2f}")

        # Hard cap CFG at 3.0 to prevent metallic artifacts
        if params["cfg"] > 3.0:
            params["cfg"] = 3.0
            logging.info(f"CFG Hard-capped at 3.0")

        logging.info(f"Optimizing for [{state['genre']}]: Duration {params['duration']}s, Sampler {params['sampler_name']}, Scheduler {params['scheduler']}, Key {keyscale}")

        result = self.comfy.submit_prompt(
            state["cleaned_lyrics"], 
            tags=tags,
            bpm=bpm,
            keyscale=keyscale,
            filename_prefix=filename_prefix,
            seed=seed,
            duration=params["duration"],
            steps=params["steps"],
            cfg=params["cfg"],
            sampler_name=params["sampler_name"],
            scheduler=params["scheduler"],
            negative_prompt=negative_prompt
        )

        if result and "prompt_id" in result:
            prompt_id = result["prompt_id"]
            logging.info(f"Audio generation started. Prompt ID: {prompt_id}")
            audio_path = self.comfy.wait_and_download_output(prompt_id)

            # Rename file to remove ComfyUI suffix if needed
            if audio_path and state.get("track_number") and state.get("song_title"):
                dir_name = os.path.dirname(audio_path)
                ext = os.path.splitext(audio_path)[1]
                safe_title = sanitize_filename(state["song_title"])
                new_filename = f"{state['track_number']:02d}_{safe_title}{ext}"
                new_path = os.path.join(dir_name, new_filename)

                try:
                    if audio_path != new_path:
                        if not os.path.exists(audio_path):
                            logging.error(f"Source file does not exist for rename: {audio_path}")
                        elif os.path.exists(new_path):
                            logging.warning(f"Target file already exists, skipping rename: {new_path}")
                        else:
                            os.rename(audio_path, new_path)
                            logging.info(f"Renamed {audio_path} to {new_path}")
                            audio_path = new_path
                except OSError as e:
                    logging.error(f"Failed to rename file: {e}")

            state["audio_path"] = audio_path
        else:
            state["audio_path"] = "error"

        return state

    def run(self, genre, user_direction, seed=None, artist_style=None, artist_background=None, song_title=None, album_name=None, track_number=None, vocals="auto", vocal_strength=1.2, key=None):
        initial_state = {
            "genre": genre,
            "user_direction": user_direction,
            "artist_name": None,
            "artist_background": artist_background,
            "artist_style": artist_style,
            "seed": seed,
            "musical_direction": None,
            "lyrics": None,
            "cleaned_lyrics": None,
            "audio_path": None,
            "research_notes": None,
            "history": [],
            "song_title": song_title,
            "album_name": album_name,
            "track_number": track_number,
            "vocals": vocals,
            "vocal_strength": vocal_strength,
            "key": key
        }
        final_state = self.app.invoke(initial_state)
        save_metadata(final_state)
        return final_state


def main():
    parser = argparse.ArgumentParser(description="Songbird: AI Song Generation Agent")
    parser.add_argument("--genre", type=str, default="POP", help="Song genre (default: POP)")
    parser.add_argument("--direction", type=str, default="A catchy upbeat pop song in the style of Black Pink about freedom with powerful female vocals and a live drummer.", help="Musical direction for the song")
    parser.add_argument("--vocals", type=str, default="auto", choices=['female', 'male', 'instrumental', 'duet', 'choir', 'auto'], help="Strict vocal control")
    parser.add_argument("--vocal-strength", type=float, default=1.2, help="Strength of vocal steering (default: 1.2)")
    parser.add_argument("--key", type=str, help="Musical key (e.g. \'C Minor\')")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output", type=str, default="output", help="Output directory (default: output)")

    # Album mode arguments
    parser.add_argument("--album", action="store_true", help="Enable album mode")
    parser.add_argument("--theme", type=str, help="Album theme (required if --album is used)")
    parser.add_argument("--album-name", type=str, help="Album name (optional, auto-generated if not provided)")
    parser.add_argument("--num-songs", type=int, default=6, help="Number of songs for the album (default: 6)")
    parser.add_argument("--base-direction", type=str, default="", help="Shared constraints for every song")

    args = parser.parse_args()

    if args.album and not args.theme:
        parser.error("--theme is required when --album is used.")

    # Validate genre against known genres
    valid_genres = list(config.MUSIC_PROMPTS.keys())
    if args.genre.upper() not in valid_genres:
        logging.warning(f"Unknown genre '{args.genre}'. Valid genres: {', '.join(valid_genres)}")
        logging.warning(f"Falling back to default genre: POP")
        args.genre = "POP"

    # Sanitize user inputs to prevent prompt injection
    if args.album and args.theme:
        args.theme = sanitize_input(args.theme)
    if args.base_direction:
        args.base_direction = sanitize_input(args.base_direction)
    args.direction = sanitize_input(args.direction)

    # Configure logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    flow = SongbirdWorkflow(output_dir=args.output)

    if args.album:
        # Determine album name
        album_name = args.album_name
        if not album_name:
            print("Auto-generating album title...")
            album_name = generate_album_title(args.genre, args.theme, args.base_direction)

        print(f"Starting Album Generation Mode: '{album_name}' (Theme: '{args.theme}')")
        print(f"Total songs: {args.num_songs}")

        # Create album output directory
        safe_album_name = sanitize_filename(album_name)
        album_output_dir = os.path.join(args.output, safe_album_name)
        logging.info(f"Album output directory: {album_output_dir}")
        flow.set_output_dir(album_output_dir)

        # Master Seed Logic for Consistent Audio
        master_seed = int(time.time() * 1000)
        persistent_artist_style = None
        persistent_artist_background = None

        logging.info(f"Album Master Seed: {master_seed}")

        for i in range(1, args.num_songs + 1):
            print(f"\n--- Generating Song {i}/{args.num_songs} ---")

            # Generate song title
            song_title = generate_song_title(album_name, i, args.genre, args.theme, args.base_direction)
            print(f"Title: {song_title}")

            if i == 1:
                # First song direction
                current_direction = f"{args.base_direction} Start the album saga: {args.theme}. Begin with the awakening/escape/origin story."
            else:
                # Subsequent songs: get context from previous songs
                print("Retrieving context from previous songs...")
                recent_summaries = scan_recent_songs(album_output_dir, n=3)
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
            final_state = flow.run(
                args.genre,
                current_direction,
                seed=master_seed,
                artist_style=persistent_artist_style,
                artist_background=persistent_artist_background,
                song_title=song_title,
                album_name=album_name,
                track_number=i,
                vocals=args.vocals,
                vocal_strength=args.vocal_strength,
                key=args.key
            )

            # Capture artist info from the first song if not already captured, but only if successful
            if persistent_artist_style is None and final_state.get('audio_path') and final_state['audio_path'] != "error":
                persistent_artist_style = final_state.get("artist_style")
                persistent_artist_background = final_state.get("artist_background")
                logging.info(f"Captured Persistent Artist Style: {persistent_artist_style}")

            if final_state.get('audio_path') and final_state['audio_path'] != "error":
                print(f"Song {i} complete: {final_state['audio_path']}")
            else:
                print(f"Song {i} failed to generate audio.")

        print("\nAlbum Generation Complete!")

    else:
        # Standard single song mode
        final_state = flow.run(args.genre, args.direction, vocals=args.vocals, vocal_strength=args.vocal_strength, key=args.key)

        print("Workflow Complete!")
        if final_state.get('cleaned_lyrics'):
            print(f"Lyrics Preview: {final_state['cleaned_lyrics'][:100]}...")

        if final_state.get('audio_path'):
            print(f"Audio Path: {final_state['audio_path']}")
        else:
            print("Audio Path: None")

if __name__ == "__main__":
    main()
