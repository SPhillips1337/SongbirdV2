import re

with open("app.py", "r") as f:
    content = f.read()

# Define the new method content
new_method = """    def node_generate_audio(self, state: SongState):
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

        if result and "prompt_id" in result:"""

# Regex to find the method block
# We match from `def node_generate_audio` up to `if result and "prompt_id" in result:`
# But `re` dotall greedy might be dangerous.
# Let's find start and a unique point inside the method that we want to keep or replace up to.
# The original code structure:
# def node_generate_audio(self, state: SongState):
#     ...
#     result = self.comfy.submit_prompt(...)
#     if result and "prompt_id" in result:
#         ...

# I'll replace everything from `def node_generate_audio` until `if result and "prompt_id" in result:` with my new code.
# The end marker `if result and "prompt_id" in result:` is inside the new code too, so I'll exclude it from the replacement string and include it in the regex match to be preserved, or just include it in the replacement.
# I included it in the replacement string above (at the end).

pattern = r'def node_generate_audio\(self, state: SongState\):.*?if result and "prompt_id" in result:'
# Use dotall
match = re.search(pattern, content, re.DOTALL)
if match:
    print("Found method block.")
    content = content.replace(match.group(0), new_method)
else:
    print("Method block not found!")
    exit(1)

with open("app.py", "w") as f:
    f.write(content)
