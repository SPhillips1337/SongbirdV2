import os
import requests
import logging
from tools.rag import RAGTool
from tools.perplexity import PerplexityClient

# Keywords that indicate instrumental/musical directions (not sung vocals)
MUSICAL_KEYWORDS = [
    'guitar', 'drum', 'bass', 'riff', 'solo', 'synth', 'piano', 'keys',
    'reverb', 'distortion', 'atmospheric', 'shredding', 'face-melting',
    'crushing', 'pounding', 'grunty', 'snare', 'kick', 'cymbal',
    'trumpet', 'sax', 'strings', 'orchestra', 'instrumental', 'beat',
    'melody', 'chord', 'note', 'tempo', 'rhythm', 'percussion',
    'fade', 'echo', 'delay', 'chorus effect', 'flanger', 'phaser'
]

# Valid ACE-Step structural markers (case-insensitive)
VALID_MARKERS = [
    'intro', 'verse', 'chorus', 'bridge', 'outro', 'drop',
    'build-up', 'breakdown', 'pre-chorus', 'hook', 'instrumental break',
    'interlude', 'refrain', 'coda', 'solo'
]


class LyricsAgent:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("LYRIC_MODEL", "qwen3:14b")
        self.rag = RAGTool()
        self.perplexity = PerplexityClient()

    def write_lyrics_node(self, state):
        """Node: Research and Generate ACE-formatted lyrics."""
        
        # 1. Research (Combined)
        query = f"Songwriting themes for {state['genre']} music in the style of {state['artist_style']}"
        try:
            search_results = self.perplexity.search(query)
        except Exception as e:
            logging.error(f"Perplexity search failed: {e}")
            search_results = "No search results."

        try:
            rag_results = self.rag.query_lightrag(f"Lyrics by {state['artist_style']}")
        except Exception as e:
            logging.error(f"RAG query failed: {e}")
            rag_results = "No RAG results."

        research_notes = f"Perplexity: {search_results}\n\nLightRAG: {rag_results}"
        state["research_notes"] = research_notes

        # 2. Write
        prompt = f"""Role: Expert AI Songwriter
Goal: Produce unique, high-quality, raw, and 'street' lyrics for a {state['genre']} track.
Artist: {state['artist_name']}
Background: {state['artist_background']}
Style: {state['artist_style']}
Musical Direction: {state.get('musical_direction', {})}
User Direction (High Priority): {state.get('user_direction', 'No specific direction.')}
Research Notes: {research_notes}

Output Requirements:
- PRIMARY GOAL: Strictly follow the User Direction (High Priority) regarding vocal types, themes, and specific avoidances.
- STRUCTURE: You MUST use ACE-Step markers like [Intro], [Verse], [Chorus], [Bridge], [Outro], [Instrumental Break].
- BACKGROUND VOCALS: Use (parentheses) ONLY for sung background vocals or ad-libs (e.g., "(oh yeah)", "(I can't stop)").
- INSTRUMENTAL DIRECTIONS: DO NOT include any instrumental or musical stage directions in parentheses (e.g., NO "(Guitar solo)", NO "(Epic drums)", NO "(Crushing riffs)"). Use [Instrumental Break] markers instead for non-vocal sections.
- CONTENT: Make the lyrics raw, emotional, and authentic to the genre. Avoid cheesy rhymes.
- FORMAT: STRICTLY lyrics only. No conversational text, no explanations.

Begin creative workflow immediately."""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=90
            )
            response.raise_for_status()
            lyrics = response.json().get("response", "").strip()
            state["lyrics"] = lyrics

            # Apply cleaning immediately
            state["cleaned_lyrics"] = self.normalize_lyrics(lyrics)

        except Exception as e:
            logging.error(f"Error generating lyrics: {e}")
            state["lyrics"] = "[Intro]\nError generating lyrics."
            state["cleaned_lyrics"] = "[Intro]\nError generating lyrics."

        return state

    def strip_musical_directions(self, lyrics):
        """
        Removes lines that are purely parenthetical instrumental/musical directions.
        
        Preserves:
        - Background vocals like "(oh yeah)", "(I can't stop)", "(singing along)"
        - ACE-Step markers like [Intro], [Verse], [Chorus]
        - Regular lyric lines
        
        Removes:
        - Instrumental directions like "(Guitar riff: crushing, driving)"
        - Musical stage directions like "(Epic drums, crushing riffs)"
        - Square bracket instrumental markers like "[Guitar distortion kicks in]"
        - Empty parentheses "()"
        """
        
        lines = lyrics.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check if the entire line is a parenthetical expression
            if stripped.startswith('(') and stripped.endswith(')'):
                # Extract content inside parentheses
                content = stripped[1:-1].strip()
                
                # Remove empty parentheses
                if not content:
                    continue

                # Explicitly preserve background vocals even if they contain keywords
                # Common variations: (Background vocals: ...), (Vocals: ...)
                if content.lower().startswith("background vocals") or content.lower().startswith("vocals"):
                    filtered_lines.append(line)
                    continue
                
                # Check if it contains any musical keywords
                is_musical_direction = any(keyword in content.lower() for keyword in MUSICAL_KEYWORDS)
                
                if is_musical_direction:
                    # Skip this line - it's an instrumental direction
                    continue
            
            # Check if the entire line is a square bracket expression
            elif stripped.startswith('[') and stripped.endswith(']'):
                # Extract content inside brackets
                content = stripped[1:-1].strip().lower()
                
                # Check if it's a valid structural marker
                is_valid_marker = any(marker in content for marker in VALID_MARKERS)
                
                # If it's not a valid marker, check if it contains musical keywords
                if not is_valid_marker:
                    is_musical_direction = any(keyword in content for keyword in MUSICAL_KEYWORDS)
                    if is_musical_direction:
                        # Skip this line - it's an instrumental direction
                        continue
            
            # Keep all other lines (including background vocals)
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def normalize_lyrics(self, lyrics):
        """
        Cleans and normalizes lyrics while preserving ACE-Step markers and background vocals.

        Steps:
        1. Strips leading/trailing whitespace and surrounding quotes from the whole text.
        2. Filters out parenthetical instrumental/musical directions.
        3. Splits by lines and strips each line individually.
        4. Removes empty lines.
        5. Preserves genuine background vocals in parentheses.
        """
        # Strip whitespace first
        lyrics = lyrics.strip()

        # Strip surrounding quotes if the LLM output was wrapped in them
        if (lyrics.startswith('"') and lyrics.endswith('"')) or (lyrics.startswith("'") and lyrics.endswith("'")):
            lyrics = lyrics[1:-1].strip()

        # Filter out musical directions
        lyrics = self.strip_musical_directions(lyrics)

        lines = lyrics.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned = line.strip()
            # Remove empty lines
            if cleaned:
                cleaned_lines.append(cleaned)
        return '\n'.join(cleaned_lines)
