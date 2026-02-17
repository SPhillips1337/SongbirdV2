import json
import os
import logging
import uuid
import shutil
import datetime
from tools.utils import sanitize_filename

def ensure_band_directory(output_root):
    """
    Ensures that the Output/Bands/ directory exists.
    """
    band_dir = os.path.join(output_root, "Bands")
    os.makedirs(band_dir, exist_ok=True)
    return band_dir

def get_band_path(output_root, band_name):
    """
    Returns the file path for a band profile.
    """
    safe_name = sanitize_filename(band_name)
    return os.path.join(output_root, "Bands", f"{safe_name}.json")

def load_band(output_root, band_name):
    """
    Loads a band profile if it exists.
    """
    path = get_band_path(output_root, band_name)
    if not os.path.exists(path):
        logging.info(f"Band profile not found at: {path}")
        return None

    try:
        with open(path, "r") as f:
            profile = json.load(f)
        logging.info(f"Loaded band profile from {path}")
        return profile
    except Exception as e:
        logging.error(f"Failed to load band profile: {e}")
        return None

def create_band_profile(output_root, name, genre, sub_genre, master_seed, biography, visual_style):
    """
    Creates and saves a new band profile with the standard schema.
    """
    ensure_band_directory(output_root)
    path = get_band_path(output_root, name)

    profile = {
        "name": name,
        "id": str(uuid.uuid4()),
        "genre": genre,
        "sub_genre": sub_genre,
        "master_seed": master_seed,
        "biography": biography,
        "visual_style": visual_style,
        "discography": [],
        "creation_date": datetime.date.today().isoformat()
    }

    try:
        with open(path, "w") as f:
            json.dump(profile, f, indent=4)
        logging.info(f"Created new band profile: {path}")
        return profile
    except Exception as e:
        logging.error(f"Failed to create band profile: {e}")
        return None

def update_discography(output_root, band_name, album_title):
    """
    Appends a new album to the band's discography.
    """
    path = get_band_path(output_root, band_name)
    if not os.path.exists(path):
        logging.warning(f"Cannot update discography: Band profile {band_name} not found.")
        return

    try:
        with open(path, "r") as f:
            profile = json.load(f)

        # Avoid duplicates
        if album_title not in profile.get("discography", []):
            profile.setdefault("discography", []).append(album_title)

            with open(path, "w") as f:
                json.dump(profile, f, indent=4)
            logging.info(f"Updated discography for {band_name} with '{album_title}'")
    except Exception as e:
        logging.error(f"Failed to update discography: {e}")

def copy_band_profile_to_album(output_root, band_name, album_dir):
    """
    Copies the band profile to the album directory as a snapshot.
    """
    source_path = get_band_path(output_root, band_name)
    if not os.path.exists(source_path):
        logging.warning(f"Cannot copy band profile: Source {source_path} not found.")
        return

    dest_path = os.path.join(album_dir, "artist_profile_snapshot.json")
    try:
        shutil.copy2(source_path, dest_path)
        logging.info(f"Copied band profile snapshot to {dest_path}")
    except Exception as e:
        logging.error(f"Failed to copy band profile snapshot: {e}")

# Legacy functions for compatibility (if needed during transition, though mostly replaced)
def save_band_profile(state, output_dir):
    # This was the old per-album save. We are moving to centralized.
    # We might keep this or deprecate it. For now, I'll leave it as a stub or redirect if needed.
    pass

def load_band_profile(path):
    # Legacy loading from path
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load band profile from path {path}: {e}")
        return None
