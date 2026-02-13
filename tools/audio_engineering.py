import random
from typing import TypedDict, Dict, List, Any

# Genre Duration Logic
# Note: Order matters for partial matches. More specific genres (e.g. "PROG ROCK") should be checked before broader ones (e.g. "ROCK").
DURATION_CATEGORIES = {
    "LONG": {"min": 240, "max": 320, "genres": ["PROG ROCK", "TRANCE", "CLASSICAL", "AMBIENT", "DOOM METAL", "JAZZ", "CYBERPUNK", "ELECTRONIC", "CINEMATIC"]},
    "SHORT": {"min": 120, "max": 180, "genres": ["PUNK", "GRINDCORE", "JINGLE", "LO-FI", "PHONK"]},
    "MEDIUM": {"min": 180, "max": 240, "genres": ["POP", "ROCK", "COUNTRY", "RAP", "DUBSTEP", "R&B", "FUNK", "SOUL", "LATIN", "METAL"]}
}

# Adaptive Inference Settings
# Note: ACE Step 1.5 Turbo performs best with 'simple' or 'karras' rather than 'normal'.
AUDIO_SETTINGS = {
    "ELECTRONIC": {
        "sampler": "euler",
        "scheduler": "simple",
        "steps": 16,
        "cfg": 1.0,
        "genres": ["DUBSTEP", "TECHNO", "ELECTRONIC", "CYBERPUNK", "PHONK", "JINGLE", "LO-FI"]
    },
    "ORGANIC": {
        "sampler": "dpmpp_2m",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 1.2,
        "genres": ["ROCK", "JAZZ", "ACOUSTIC", "COUNTRY", "R&B", "SOUL", "FUNK", "LATIN", "METAL", "POP", "PUNK", "GRINDCORE", "PROG ROCK", "DOOM METAL", "CLASSICAL"]
    },
    "ATMOSPHERIC": {
        "sampler": "euler_ancestral",
        "scheduler": "simple",
        "steps": 20,
        "cfg": 1.0,
        "genres": ["AMBIENT", "CINEMATIC", "TRANCE"]
    }
}

class SongParameters(TypedDict):
    duration: int
    steps: int
    cfg: float
    sampler_name: str
    scheduler: str

def calculate_song_parameters(genre: str, lyrics: str) -> SongParameters:
    """
    Dynamically determines song parameters based on genre and lyrics for ACE Step 1.5.

    Args:
        genre: The musical genre.
        lyrics: The song lyrics (used for duration estimation).

    Returns:
        SongParameters: Dictionary containing duration, steps, cfg, sampler_name, and scheduler.
    """
    genre_upper = genre.upper().strip()

    # --- 1. Determine Duration ---
    # Default to Medium range if unsure
    target_range = DURATION_CATEGORIES["MEDIUM"]

    # Check for specific genre match in DURATION_CATEGORIES
    found_duration_cat = False
    for cat_name, settings in DURATION_CATEGORIES.items():
        # Check exact match or if genre contains any keyword
        for g in settings["genres"]:
            if g in genre_upper:
                target_range = settings
                found_duration_cat = True
                break
        if found_duration_cat:
            break

    # Base duration from range
    base_duration = random.randint(target_range["min"], target_range["max"])

    # Adjust based on Lyrical Density
    word_count = len(lyrics.split()) if lyrics else 0
    # Estimate WPM: Rap ~150, others ~100
    wpm = 150 if "RAP" in genre_upper else 100
    estimated_duration = int((word_count / wpm) * 60) if word_count > 0 else 0

    # Combine: If lyrics are long, extend duration, but respect soft cap.
    # We take the larger of base or estimated, to ensure lyrics fit,
    # but not too long if lyrics are short (keep musical intro/outro).
    duration = max(base_duration, estimated_duration)

    # Soft Cap at 280s (4m 40s)
    if duration > 280:
        duration = 280

    # --- 2. Adaptive Inference Settings ---
    # Default fallback: euler / simple, steps: 16
    sampler = "euler"
    scheduler = "simple"
    steps = 16
    cfg = 1.0

    found_audio_settings = False
    for cat_name, settings in AUDIO_SETTINGS.items():
        for g in settings["genres"]:
            if g in genre_upper:
                sampler = settings.get("sampler", sampler)
                scheduler = settings.get("scheduler", scheduler)
                steps = settings.get("steps", steps)
                cfg = settings.get("cfg", cfg)
                found_audio_settings = True
                break
        if found_audio_settings:
            break

    return {
        "duration": duration,
        "steps": steps,
        "cfg": cfg,
        "sampler_name": sampler,
        "scheduler": scheduler
    }
