import requests
import json
import logging
import re
from config import OLLAMA_BASE_URL, LYRIC_MODEL
from tools.utils import strip_thinking
from tools.rag import RAGTool
from tools.perplexity import PerplexityClient
from tools.audio_engineering import calculate_lyric_budget, DURATION_CATEGORIES

# Keywords that indicate musical/instrumental directions (should be removed)
MUSICAL_KEYWORDS = [
    'guitar', 'solo', 'riff', 'drums', 'drum', 'bass', 'synth', 'piano',
    'intro', 'outro', 'bridge', 'chorus', 'verse', 'break', 'drop',
    'build', 'build-up', 'instrumental', 'hook', 'refrain', 'interlude',
    'coda', 'pre-chorus', 'post-chorus', 'ad-lib', 'harmony', 'background',
    'applause', 'cheer', 'crowd', 'noise', 'sound', 'effect', 'fx',
    'distorted', 'heavy', 'gritty', 'clean', 'acoustic', 'electric',
    'keys', 'strings', 'horns', 'brass', 'percussion', 'tempo', 'bpm',
    'rhythm', 'beat', 'groove', 'swing', 'shuffle', 'syncopation',
    'fade', 'fades', 'echo', 'echoes', 'delay', 'delays'
]

# Keywords that indicate vocal-related lines (should be preserved)
VOCAL_KEYWORDS = [
    'vocal', 'vocals', 'singing', 'ad-lib', 'ad-libs', 'harmony', 'harmonies',
    'background', 'verse', 'verses', 'chorus', 'choruses', 'hook', 'hooks',
    'bridge', 'bridges', 'outro', 'outros', 'intro', 'intros', 'ooh', 'aah',
    'yeah', 'voice', 'voices', 'sung', 'choir', 'choirs', 'backing',
    'na', 'la', 'da', 'whoa', 'oh'
]

# Valid ACE-Step structural markers (case-insensitive)
VALID_MARKERS = [
    'intro', 'verse', 'chorus', 'bridge', 'outro', 'drop',
    'build-up', 'breakdown', 'pre-chorus', 'hook', 'instrumental break',
    'interlude', 'refrain', 'coda', 'solo'
]

# Compile regex patterns for performance
MUSICAL_KEYWORDS_REGEX = re.compile(
    r'\b(?:' + '|'.join(map(re.escape, MUSICAL_KEYWORDS)) + r')\b',
    re.IGNORECASE
)

VALID_MARKERS_REGEX = re.compile(
    r'\b(?:' + '|'.join(map(re.escape, VALID_MARKERS)) + r')\b',
    re.IGNORECASE
)

VOCAL_KEYWORDS_REGEX = re.compile(
    r'\b(?:' + '|'.join(map(re.escape, VOCAL_KEYWORDS)) + r')\b',
    re.IGNORECASE
)

class LyricsAgent:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = LYRIC_MODEL
        self.rag = RAGTool()
        self.perplexity = PerplexityClient()

    def write_lyrics_node(self, state):
        """Node: Research and Generate ACE-formatted lyrics."""
        
        # 1. Research (Combined)
        trending_data = state.get("trending_data", "")
        if trending_data:
            query = f"Using this trend: {trending_data}, find songwriting themes for {state['genre']} in the style of {state['artist_style']}"
        else:
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

        # 2. Determine Time Budget
        # Use target duration from state if available, otherwise 240s
        target_duration = state.get("target_duration", 240)
        budget = calculate_lyric_budget(state["genre"], target_duration)
        state["lyric_budget"] = budget

        # 3. Write
        poetic_mode = state.get("poetic_mode", False)

        if poetic_mode:
             role_description = f"""Role: Avant-Garde Poet & Lyricist
Goal: Produce lyrics that elevate {state['genre']} into high art.
INSTRUCTIONS (POETIC MODE):
- Do not just rhyme. Focus on specific, concrete imagery over abstract feelings.
- Use constraints (e.g., 'avoid the word *love*', 'focus on a specific object').
- Create tension between the structure and the meaning.
- Be surprising, subversive, and intellectually stimulating.
- Avoid clichés and standard pop tropes.
"""
        else:
             role_description = f"""Role: Expert AI Songwriter
Goal: Produce unique, high-quality, raw, and 'street' lyrics for a {state['genre']} track.
"""

        prompt = f"""{role_description}
Artist: {state['artist_name']}
Background: {state['artist_background']}
Style: {state['artist_style']}
Song Title: {state.get('song_title', 'Untitled')}
Musical Direction: {state.get('musical_direction', {})}
User Direction (High Priority): {state.get('user_direction', 'No specific direction.')}
Research Notes: {research_notes}

TIME BUDGET (CRITICAL):
- Target Duration: {budget['duration']} seconds
- BPM: {budget['bpm']}
- Seconds per Bar: {budget['seconds_per_bar']:.2f}
- Total Bar Budget: ~{budget['total_bars']} bars
- STRICTLY FOLLOW THIS STRUCTURE:
{budget['structure_template']}

Output Requirements:
- PRIMARY GOAL: Strictly follow the User Direction (High Priority) regarding vocal types, themes, and specific avoidances.
- STRUCTURE: You MUST use ACE-Step markers like [Intro], [Verse], [Chorus], [Bridge], [Outro], [Instrumental Break].
- OUTRO: You MUST end the song with an [Outro] section. Do NOT use the words "fading out" or "fade". Instead, use 2-4 lines of simple, repetitive vocalizations (e.g., "mm...", "yeah...", "ooh..."), a repetitive refrain from the chorus, or sparse emotional ad-libs to allow the audio to resolve naturally.
- BACKGROUND VOCALS: Use (parentheses) ONLY for sung background vocals or ad-libs (e.g., "(oh yeah)", "(I can't stop)").
- INSTRUMENTAL DIRECTIONS: DO NOT include any instrumental or musical stage directions in parentheses (e.g., NO "(Guitar solo)", NO "(Epic drums)", NO "(Crushing riffs)"). Use [Instrumental Break] markers instead for non-vocal sections.
- CONTENT: Make the lyrics raw, emotional, and authentic to the genre. Avoid cheesy rhymes.
- FORMAT: STRICTLY lyrics only. No conversational text, no explanations.

Audio Engineering / Punctuation Rules (CRITICAL):
- Enforce "Breathable" Syntax:
    - Every single line MUST end with a punctuation mark ('.' or ',' or '?' or '!').
    - Use commas (',') mid-line to create short rhythmic pauses (micro-breaths).
    - Use periods ('.') at the end of phrases to force a full breath/reset.
    - Use ellipses ('...') to create tension or trailing vocals.
    - Use hyphens ('-') to indicate stuttering or stretched words (e.g., "S-stop").
- Structural Formatting:
    - Ensure the output always uses clear section headers in brackets: [Verse 1], [Chorus], [Bridge].
    - Insert a blank line between every section.
- Implementation:
    - Write lyrics with strict punctuation. Treat punctuation as musical notation for breathing. Never write a line without ending punctuation.

CRITICAL CONSTRAINTS:
- DO NOT include ANY meta-commentary, notes, or explanations about your creative process.
- DO NOT write lines like "Note:", "Explanation:", "I tried to...", or any self-referential text.
- OUTPUT ONLY the lyrics themselves with ACE-Step markers.
- If you find yourself wanting to explain something, DON'T. Just write better lyrics instead.

Begin creative workflow immediately."""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,  # Creative but controlled
                        "min_p": 0.05,       # Filter out low-probability garbage while keeping creativity
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
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
                lower_content = content.lower()
                if lower_content.startswith("background vocals") or lower_content.startswith("vocals"):
                    filtered_lines.append(line)
                    continue
                
                # Check if it's explicitly vocal-related
                is_vocal = VOCAL_KEYWORDS_REGEX.search(content)
                
                # Check if it contains any musical keywords
                is_musical_direction = MUSICAL_KEYWORDS_REGEX.search(content)
                
                if is_musical_direction and not is_vocal:
                    # Skip this line - it's an instrumental direction
                    continue
            
            # Check if the entire line is a square bracket expression
            elif stripped.startswith('[') and stripped.endswith(']'):
                # Extract content inside brackets
                content = stripped[1:-1].strip()
                
                # Check if it's a valid structural marker
                is_valid_marker = VALID_MARKERS_REGEX.search(content)
                
                # If it's not a valid marker, check if it contains musical keywords
                if not is_valid_marker:
                    is_vocal = VOCAL_KEYWORDS_REGEX.search(content)
                    is_musical_direction = MUSICAL_KEYWORDS_REGEX.search(content)
                    if is_musical_direction and not is_vocal:
                        # Skip this line - it's an instrumental direction
                        continue
            
            # Keep all other lines (including background vocals)
            filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def strip_meta_commentary(self, lyrics):
        """
        Removes LLM meta-commentary and explanations that sometimes appear in lyrics.
        
        Removes lines starting with:
        - "Note:"
        - "Explanation:"
        - "I tried to..."
        - "I've tried to..."
        - "The lyrics..."
        - Other self-referential commentary
        """
        lines = lyrics.split('\n')
        filtered_lines = []
        skip_rest = False
        
        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()
            
            # Check for meta-commentary markers
            meta_markers = [
                'note:', 'explanation:', 'i tried to', "i've tried to",
                'the lyrics', 'this song', 'these lyrics', 'i focused on',
                'i aimed to', 'i wanted to', 'i incorporated', 'i used',
                'i avoided', 'i created', 'i wrote', 'i included'
            ]
            
            # If we find meta-commentary, skip this line and all following lines
            if any(lower.startswith(marker) for marker in meta_markers):
                skip_rest = True
                continue
            
            if not skip_rest:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def strip_standalone_musical_instructions(self, lyrics):
        """
        Removes standalone lines that are musical instructions without parentheses/brackets.
        
        Examples to remove:
        - "Anguished vocals, crushing guitars"
        - "Anthemic, soaring vocals"
        - "Heavy, distorted guitars"
        - "Fading vocals, fading riffs"
        
        These are lines that contain ONLY musical keywords and no actual lyrical content.
        """
        lines = lyrics.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines and section markers
            if not stripped or (stripped.startswith('[') and stripped.endswith(']')):
                filtered_lines.append(line)
                continue
            
            # Check if this line is ONLY musical instructions
            # Remove all musical keywords and see if anything meaningful remains
            test_line = stripped.lower()
            
            # Remove common punctuation and conjunctions
            test_line = re.sub(r'[,;:]', ' ', test_line)
            test_line = re.sub(r'\b(and|with|the|a|an)\b', ' ', test_line)
            
            # Split into words
            words = test_line.split()
            
            # Check if ALL words are musical keywords
            if words:
                musical_word_count = sum(1 for word in words if MUSICAL_KEYWORDS_REGEX.search(word))
                total_words = len(words)
                
                # If 80% or more of the words are musical keywords, it's likely a musical instruction
                if total_words > 0 and (musical_word_count / total_words) >= 0.8:
                    logging.info(f"Filtering standalone musical instruction: {stripped}")
                    continue
            
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

        # Strip surrounding quotes if they exist
        if (lyrics.startswith('"') and lyrics.endswith('"')) or (lyrics.startswith("'") and lyrics.endswith("'")):
            lyrics = lyrics[1:-1].strip()
        
        # Strip thinking blocks first
        lyrics = strip_thinking(lyrics)

        # Filter out musical directions
        lyrics = self.strip_musical_directions(lyrics)
        
        # Filter out meta-commentary
        lyrics = self.strip_meta_commentary(lyrics)
        
        # Filter out standalone musical instructions
        lyrics = self.strip_standalone_musical_instructions(lyrics)

        lines = lyrics.split('\n')
        cleaned_lines = []
        last_line_was_empty = True  # Start true to avoid leading blank lines

        for line in lines:
            cleaned = line.strip()

            if cleaned:
                cleaned_lines.append(cleaned)
                last_line_was_empty = False
            elif not last_line_was_empty:
                # Add a blank line if the previous line wasn't empty
                cleaned_lines.append("")
                last_line_was_empty = True

        # Remove trailing blank lines
        if cleaned_lines and cleaned_lines[-1] == "":
            cleaned_lines.pop()

        return '\n'.join(cleaned_lines)
