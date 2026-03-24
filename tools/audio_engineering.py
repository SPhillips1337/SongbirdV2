import random
from typing import TypedDict, Dict, List, Any

# Genre BPM Logic
GENRE_BPM = {
    "DUBSTEP": 140,
    "DRUM AND BASS": 174,
    "HOUSE": 128,
    "TECHNO": 130,
    "HIP HOP": 90,
    "POP": 120,
    "AMBIENT": 80
}

# Genre Duration Logic
# Note: Order matters for partial matches. More specific genres (e.g. "PROG ROCK") should be checked before broader ones (e.g. "ROCK").
DURATION_CATEGORIES = {
    "LONG": {"min": 240, "max": 320, "genres": ["PROG ROCK", "TRANCE", "CLASSICAL", "AMBIENT", "DOOM METAL", "JAZZ", "CYBERPUNK", "ELECTRONIC", "CINEMATIC"]},
    "SHORT": {"min": 120, "max": 180, "genres": ["PUNK", "GRINDCORE", "JINGLE", "LO-FI", "PHONK"]},
    "MEDIUM": {"min": 180, "max": 240, "genres": ["POP", "ROCK", "COUNTRY", "RAP", "DUBSTEP", "R&B", "FUNK", "SOUL", "LATIN", "METAL"]}
}
# Adaptive Inference Settings
# Note: ACE Step 1.5 Turbo Sweet Spot: Steps 12-16, CFG 1.2-1.5.
# Exceeding CFG 2.0 often causes "phase burn" artifacts.
AUDIO_SETTINGS = {
    "ELECTRONIC": {
        "sampler": "euler",         # Keep Euler for punchy transients (Drums/Bass)
        "scheduler": "sgm_uniform", # Correct for Turbo
        "steps": 12,                # Bumped from 8->12 for better sub-bass definition
        "cfg": 1.0,                 # Keep Sampler CFG low for stability
        "cfg_scale": 3.0,           # Bump Text Guidance slightly so it follows genre tags
        "default_key": "F Minor",   # Optimal for sub-bass
        "genres": ["DUBSTEP", "TECHNO", "TRANCE", "HOUSE", "DRUM AND BASS", "ELECTRONIC", "CYBERPUNK", "PHONK", "JINGLE"]
    },
    "POP": {
        "sampler": "dpmpp_2m",      # Best for coherent vocals (less robotic)
        "scheduler": "sgm_uniform",
        "steps": 16,                # Vocals need more steps to resolve clearly
        "cfg": 1.4,                 # The "Organic" sweet spot you remembered
        "cfg_scale": 3.5,           # Stronger text guidance to force lyrical adherence
        "default_key": "G Minor",   # Modern pop clarity
        "genres": ["POP", "K-POP", "R&B", "DISCO", "SYNTHWAVE", "FUNK", "SOUL", "LATIN"]
    },
    "ROCK": {
        "sampler": "dpmpp_2m",      # Stable for guitars
        "scheduler": "sgm_uniform",
        "steps": 16,                # Needed for texture detail
        "cfg": 1.3,                 # Slightly lower than Pop to allow "fuzz/distortion"
        "cfg_scale": 3.0,
        "default_key": "E Minor",   # Guitar key
        "genres": ["ROCK", "METAL", "PUNK", "GRINDCORE", "INDIE", "PROG ROCK", "DOOM METAL", "COUNTRY", "ACOUSTIC"]
    },
    "RAP": {
        "sampler": "dpmpp_2m",  # High vocal clarity
        "scheduler": "sgm_uniform",
        "steps": 8,
        "cfg": 1,
        "cfg_scale": 2,
        "default_key": "C# Minor",  # Strong sub-bass resonance for Rap/Trap
        "genres": ["RAP", "HIP HOP", "TRAP", "DRILL", "GRIME", "BOOM BAP"]
    },    
    "ATMOSPHERIC": {
        "sampler": "euler",         # Euler is smoother for pads than dpmpp
        "scheduler": "sgm_uniform",
        "steps": 12,
        "cfg": 1.0,                 # Keep loose for dreamy/drifting feel
        "cfg_scale": 2.5,           # Low guidance prevents "trying too hard"
        "default_key": "C Minor",   # Deep/Moody
        "genres": ["AMBIENT", "CINEMATIC", "LO-FI", "JAZZ", "CLASSICAL"]
    }
}

class SongParameters(TypedDict):
    duration: int
    steps: int
    cfg: float
    sampler_name: str
    scheduler: str
    default_key: str

class LyricBudget(TypedDict):
    bpm: int
    seconds_per_bar: float
    total_bars: int
    structure_template: str
    duration: int

def get_bpm(genre: str) -> int:
    """Retrieves the BPM for a given genre, defaulting to 120."""
    genre_upper = genre.upper().strip()
    # Check exact match first
    if genre_upper in GENRE_BPM:
        return GENRE_BPM[genre_upper]

    # Check partial match
    for key, val in GENRE_BPM.items():
        if key in genre_upper:
            return val

    return 120

def calculate_lyric_budget(genre: str, duration: int = 240) -> LyricBudget:
    """
    Calculates the time budget and structure for lyrics based on genre and duration.
    """
    bpm = get_bpm(genre)
    seconds_per_bar = (60 / bpm) * 4
    total_bars = int(duration / seconds_per_bar)

    # Structure Templates
    genre_upper = genre.upper().strip()

    if "DUBSTEP" in genre_upper:
        # Dubstep specific template (approx 80 bars for 2.5 mins of content in 3.5 min song)
        structure = (
            "Dubstep Structure Template:\n"
            "- [Intro]: 8 bars\n"
            "- [Build-Up]: 8 bars\n"
            "- [Drop 1]: 16 bars (High energy, minimal lyrics)\n"
            "- [Breakdown/Verse]: 16 bars\n"
            "- [Build-Up 2]: 8 bars\n"
            "- [Drop 2]: 16 bars\n"
            "- [Outro]: 8 bars (Instrumental Resolution / Vocal Echoes)"
        )
    else:
        # Generic Template scaled to bars
        # ~10% Intro, ~40% Verses, ~30% Choruses, ~10% Bridge, ~10% Outro
        intro_bars = max(4, int(total_bars * 0.1))
        outro_bars = max(4, int(total_bars * 0.1))
        remaining = total_bars - intro_bars - outro_bars
        verse_bars = int(remaining * 0.4)
        chorus_bars = int(remaining * 0.4)
        bridge_bars = remaining - verse_bars - chorus_bars

        structure = (
            f"Generic Structure Template (Total {total_bars} bars):\n"
            f"- [Intro]: {intro_bars} bars\n"
            f"- [Verse 1]: {max(1, verse_bars // 2)} bars\n"
            f"- [Chorus]: {max(1, chorus_bars // 2)} bars\n"
            f"- [Verse 2]: {max(1, verse_bars // 2)} bars\n"
            f"- [Chorus]: {max(1, chorus_bars // 2)} bars\n"
            f"- [Bridge]: {bridge_bars} bars\n"
            f"- [Outro]: {outro_bars} bars"
        )

    return {
        "bpm": bpm,
        "seconds_per_bar": seconds_per_bar,
        "total_bars": total_bars,
        "structure_template": structure,
        "duration": duration
    }

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
    # Default fallback: euler / sgm_uniform, steps: 50
    sampler = "euler"
    scheduler = "simple"
    steps = 8
    cfg = 1
    cfg_scale = 2.0
    default_key = "C Major"

    found_audio_settings = False
    for cat_name, settings in AUDIO_SETTINGS.items():
        for g in settings["genres"]:
            if g in genre_upper:
                sampler = settings.get("sampler", sampler)
                scheduler = settings.get("scheduler", scheduler)
                steps = settings.get("steps", steps)
                cfg = settings.get("cfg", cfg)
                cfg_scale = settings.get("cfg_scale", cfg_scale)
                default_key = settings.get("default_key", default_key)
                found_audio_settings = True
                break
        if found_audio_settings:
            break

    return {
        "duration": duration,
        "steps": steps,
        "cfg": cfg,
        "cfg_scale": cfg_scale,
        "sampler_name": sampler,
        "scheduler": scheduler,
        "default_key": default_key
    }
