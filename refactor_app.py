import re

with open("app.py", "r") as f:
    content = f.read()

# 1. Update imports
if "from config import" not in content:
    content = content.replace("import config", "import config\nfrom config import DEFAULT_NEGATIVE_PROMPT_SUFFIX")
else:
    # Check if already imported or append
    pass
    # For simplicity, assuming 'import config' exists.
    # Actually, config is imported as `import config`.
    # I can just use `config.DEFAULT_NEGATIVE_PROMPT_SUFFIX` if I import `config`.
    # But `from config import ...` is cleaner if I want to use the name directly.
    # Let's just use `config.DEFAULT_NEGATIVE_PROMPT_SUFFIX`.

# 2. Refactor node_generate_audio
new_node_method = """    def node_generate_audio(self, state: SongState):
        music_dir = state["musical_direction"]
        # Handle dict or fallback string
        if isinstance(music_dir, dict):
            tags = music_dir.get("tags", "")
            bpm = music_dir.get("bpm", 120)
            # We defer key resolution to the dedicated logic block below
            generated_key = normalize_keyscale(music_dir.get("keyscale", "C major"))
        else:
            tags = str(music_dir)
            bpm = 120
            generated_key = "C major"

        # Vocal Prompt Injection Logic
        vocals = state.get("vocals", "auto")
        vocal_strength = state.get("vocal_strength", 1.2)

        # Negative Prompt Logic
        suffix = config.DEFAULT_NEGATIVE_PROMPT_SUFFIX
        negative_prompt = ""

        if vocals == "female":
            tags = f"(female vocals:{vocal_strength}), female singer, {tags}"
            negative_prompt = "male vocals" + suffix
        elif vocals == "male":
            tags = f"(male vocals:{vocal_strength}), male singer, {tags}"
            negative_prompt = "female vocals" + suffix
        elif vocals == "instrumental":
            tags = f"(instrumental:{vocal_strength}), no vocals, {tags}"
            negative_prompt = "vocals, voice, singing, lyrics, speech" + suffix
        else:
            # Auto, Duet, Choir, etc.
            if vocals in ["duet", "choir"]:
                 tags = f"({vocals} vocals:{vocal_strength}), {tags}"
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
        # Priority: User Input > Genre Default > Generated/Fallback
        user_key = state.get("key")
        genre_default_key = params.get("default_key")

        if user_key:
            keyscale = normalize_keyscale(user_key)
            logging.info(f"Using User Key: {keyscale}")
        elif genre_default_key:
            keyscale = normalize_keyscale(genre_default_key)
            logging.info(f"Using Genre Default Key: {keyscale}")
        else:
            keyscale = generated_key
            logging.info(f"Using Generated/Fallback Key: {keyscale}")

        # Adjust CFG for vocal control
        # Calculate final CFG explicitly instead of mutating params
        final_cfg = params["cfg"]
        if vocals != "auto":
            final_cfg = final_cfg * 0.85
            logging.info(f"Vocal control active: Lowering CFG to {final_cfg:.2f}")

        # Hard cap CFG at 3.0
        if final_cfg > 3.0:
            final_cfg = 3.0
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
            cfg=final_cfg,
            sampler_name=params["sampler_name"],
            scheduler=params["scheduler"],
            negative_prompt=negative_prompt
        )

        if result and "prompt_id" in result:"""

# Regex to find the method block
pattern = r'def node_generate_audio\(self, state: SongState\):.*?if result and "prompt_id" in result:'
match = re.search(pattern, content, re.DOTALL)
if match:
    content = content.replace(match.group(0), new_node_method)
else:
    print("Method block not found for replacement")
    exit(1)

# 3. Add docstring to run method
run_def = "def run(self, genre, user_direction, seed=None, artist_style=None, artist_background=None, song_title=None, album_name=None, track_number=None, vocals=\"auto\", vocal_strength=1.2, key=None):"
run_docstring = """        \"\"\"
        Executes the Songbird workflow.

        Args:
            genre (str): Musical genre.
            user_direction (str): User's description/direction.
            seed (int, optional): Random seed.
            artist_style (str, optional): Pre-defined artist style.
            artist_background (str, optional): Pre-defined artist background.
            song_title (str, optional): Title of the song.
            album_name (str, optional): Name of the album.
            track_number (int, optional): Track number in album.
            vocals (str, optional): Vocal mode (female, male, instrumental, duet, choir, auto).
            vocal_strength (float, optional): Strength of vocal steering prompts.
            key (str, optional): Musical key (e.g., 'C Minor') to override defaults.

        Returns:
            dict: Final state of the workflow.
        \"\"\""""

if run_def in content:
    # Check if docstring exists? No, checking previous `cat` showed none.
    content = content.replace(run_def, run_def + "\n" + run_docstring)

with open("app.py", "w") as f:
    f.write(content)
