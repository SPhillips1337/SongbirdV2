import re
import logging

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
