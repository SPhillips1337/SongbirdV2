import re
import logging
import os

def sanitize_input(text, max_length=1000):
    """
    Sanitizes user input to prevent prompt injection attacks.
    Removes potentially dangerous characters and limits length.
    """
    if not text:
        return ""
    
    # Remove control characters and limit length
    sanitized = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # Limit length to prevent excessively long inputs
    if len(sanitized) > max_length:
        logging.warning(f"Input truncated from {len(sanitized)} to {max_length} characters")
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def sanitize_filename(name):
    """
    Sanitizes a string to be safe for use as a filename or directory name.
    """
    if not name:
        return "untitled"

    # Remove invalid characters for filenames
    # Explicitly remove path separators to prevent directory traversal
    s = name.replace(os.sep, '').replace(os.altsep or '', '')

    # Remove filesystem reserved characters
    s = re.sub(r'[<>:"/\\|?*]', '', s)
    s = s.strip().replace(' ', '_')

    # Keep only alphanumeric, underscore, hyphen, dot
    s = re.sub(r'[^\w\.-]', '', s)

    # Remove leading/trailing dots to prevent hiding files or directory traversal
    s = s.strip('.')

    # Limit length
    s = s[:100]

    if not s:
        return "untitled"

    return s

def normalize_keyscale(keyscale_str):
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
