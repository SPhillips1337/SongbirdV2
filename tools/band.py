import json
import os
import logging

def save_band_profile(state, output_dir):
    """
    Saves the band profile to the output directory.
    """
    if not state.get("artist_name"):
        logging.warning("No artist name to save in band profile.")
        return

    profile = {
        "band_name": state.get("artist_name"),
        "master_seed": state.get("seed"),
        "genre": state.get("genre"),
        "biography": state.get("artist_background"),
        "visual_style_prompt": state.get("artist_style")
    }

    try:
        path = os.path.join(output_dir, "band_profile.json")
        with open(path, "w") as f:
            json.dump(profile, f, indent=4)
        logging.info(f"Saved band profile to {path}")
    except Exception as e:
        logging.error(f"Failed to save band profile: {e}")

def load_band_profile(path):
    """
    Loads a band profile from the given path.
    """
    if not os.path.exists(path):
        logging.error(f"Band profile not found at: {path}")
        return None

    try:
        with open(path, "r") as f:
            profile = json.load(f)
        logging.info(f"Loaded band profile from {path}")
        return profile
    except Exception as e:
        logging.error(f"Failed to load band profile: {e}")
        return None
