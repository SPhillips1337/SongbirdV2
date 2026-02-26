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
    'vocal', 'vocals', 'voice', 'voices', 'singer', 'singing', 'choir',
    'applause', 'cheer', 'crowd', 'noise', 'sound', 'effect', 'fx',
    'sample', 'scratch', 'scratching', 'turntable', 'dj', 'mix', 'remix',
    'producer', 'production', 'track', 'song', 'music', 'record', 'recording',
    'studio', 'mic', 'microphone', 'headphones', 'speaker', 'speakers',
    'volume', 'level', 'gain', 'EQ', 'equalizer', 'compressor', 'limiter',
    'reverb', 'delay', 'echo', 'distortion', 'overdrive', 'fuzz', 'wah',
    'flanger', 'phaser', 'chorus', 'tremolo', 'vibrato', 'pitch', 'shift',
    'tempo', 'bpm', 'rhythm', 'beat', 'groove', 'swing', 'shuffle',
    'syncopation', 'measure', 'bar', 'staff', 'score', 'note', 'chord',
    'scale', 'key', 'major', 'minor', 'sharp', 'flat', 'natural',
    'octave', 'interval', 'tone', 'semitone', 'tuning', 'standard',
    'drop-d', 'open', 'alternate', 'capo', 'slide', 'bend', 'hammer-on',
    'pull-off', 'tapping', 'sweep', 'picking', 'fingerstyle', 'strumming',
    'pattern', 'arpeggio', 'palm', 'mute', 'harmonic', 'pinch', 'natural',
    'artificial', 'whammy', 'bar', 'arm', 'pedal', 'board', 'amp',
    'amplifier', 'cabinet', 'stack', 'combo', 'tube', 'solid', 'state',
    'digital', 'modeling', 'simulation', 'plugin', 'vst', 'au', 'aax',
    'rtas', 'daw', 'workstation', 'sequencer', 'sampler', 'synthesizer',
    'keyboard', 'controller', 'midi', 'interface', 'audio', 'signal',
    'chain', 'routing', 'bus', 'send', 'return', 'insert', 'master',
    'fader', 'knob', 'button', 'switch', 'potentiometer', 'encoder',
    'display', 'screen', 'monitor', 'meter', 'analyzer', 'spectrum',
    'frequency', 'amplitude', 'phase', 'polarity', 'stereo', 'mono',
    'surround', 'spatial', '3d', 'binaural', 'ambisonic', 'hrtf',
    'convolution', 'impulse', 'response', 'filter', 'cut', 'boost',
    'shelf', 'bell', 'notch', 'band', 'pass', 'stop', 'low', 'high',
    'mid', 'presence', 'air', 'body', 'warmth', 'brightness', 'clarity',
    'definition', 'punch', 'attack', 'decay', 'sustain', 'release',
    'transient', 'envelope', 'gate', 'expander', 'ducker', 'sidechain',
    'lookahead', 'knee', 'ratio', 'threshold', 'ceiling', 'makeup',
    'output', 'input', 'source', 'destination', 'channel', 'strip',
    'console', 'mixer', 'desk', 'board', 'surface', 'control', 'remote',
    'automation', 'recall', 'scene', 'snapshot', 'preset', 'bank',
    'program', 'change', 'message', 'event', 'trigger', 'clock', 'sync',
    'transport', 'play', 'stop', 'record', 'pause', 'rewind', 'fast',
    'forward', 'loop', 'cycle', 'punch', 'in', 'out', 'marker', 'locator',
    'region', 'clip', 'segment', 'slice', 'sample', 'editor', 'piano',
    'roll', 'score', 'notation', 'tablature', 'lyrics', 'text', 'font',
    'color', 'theme', 'skin', 'layout', 'workspace', 'window', 'pane',
    'panel', 'tab', 'menu', 'toolbar', 'status', 'bar', 'scroll', 'zoom',
    'navigate', 'select', 'edit', 'copy', 'cut', 'paste', 'delete',
    'undo', 'redo', 'save', 'load', 'import', 'export', 'render',
    'bounce', 'mixdown', 'mastering', 'distribution', 'release', 'album',
    'single', 'ep', 'lp', 'cd', 'vinyl', 'cassette', 'digital', 'streaming',
    'platform', 'service', 'spotify', 'apple', 'music', 'youtube',
    'soundcloud', 'bandcamp', 'tidal', 'deezer', 'amazon', 'pandora',
    'radio', 'broadcast', 'podcast', 'playlist', 'library', 'catalog',
    'database', 'metadata', 'tag', 'id3', 'isrc', 'upc', 'ean', 'barcode',
    'copyright', 'royalty', 'publishing', 'licensing', 'sync', 'performance',
    'rights', 'organization', 'pro', 'ascap', 'bmi', 'sesac', 'gema',
    'prs', 'mcps', 'sacem', 'siae', 'sgae', 'jasrac', 'komca', 'cash',
    'cow', 'money', 'business', 'industry', 'label', 'manager', 'agent',
    'promoter', 'publicist', 'marketing', 'social', 'media', 'fan',
    'base', 'audience', 'concert', 'tour', 'festival', 'gig', 'venue',
    'stage', 'light', 'sound', 'engineer', 'technician', 'roadie',
    'crew', 'backstage', 'rider', 'contract', 'negotiation', 'deal',
    'advance', 'recoupment', 'profit', 'loss', 'budget', 'finance',
    'tax', 'legal', 'lawyer', 'attorney', 'court', 'litigation',
    'dispute', 'settlement', 'judgment', 'verdict', 'appeal', 'precedent',
    'statute', 'regulation', 'policy', 'guideline', 'standard', 'practice',
    'ethics', 'morality', 'integrity', 'reputation', 'image', 'brand',
    'identity', 'logo', 'design', 'art', 'artwork', 'cover', 'sleeve',
    'booklet', 'insert', 'poster', 'flyer', 'banner', 'merchandise',
    't-shirt', 'hoodie', 'hat', 'cap', 'sticker', 'patch', 'pin',
    'button', 'badge', 'magnet', 'keychain', 'poster', 'flag', 'banner',
    'backdrop', 'scrim', 'riser', 'platform', 'staging', 'truss',
    'rigging', 'lighting', 'fixture', 'spot', 'wash', 'beam', 'laser',
    'strobe', 'fog', 'haze', 'smoke', 'pyro', 'fire', 'confetti',
    'streamer', 'balloon', 'bubble', 'snow', 'foam', 'cryo', 'jet',
    'co2', 'cannon', 'launcher', 'dispenser', 'machine', 'device',
    'equipment', 'gear', 'hardware', 'software', 'firmware', 'driver',
    'update', 'upgrade', 'patch', 'fix', 'bug', 'glitch', 'error',
    'crash', 'freeze', 'hang', 'lag', 'latency', 'delay', 'buffer',
    'underrun', 'overflow', 'clipping', 'distortion', 'noise', 'hum',
    'hiss', 'buzz', 'crackle', 'pop', 'click', 'dropout', 'artifact',
    'aliasing', 'quantization', 'jitter', 'drift', 'skew', 'offset',
    'drift', 'wandering', 'instability', 'fluctuation', 'variation',
    'deviation', 'error', 'mistake', 'failure', 'breakdown', 'malfunction',
    'defect', 'flaw', 'fault', 'imperfection', 'limitation', 'constraint',
    'restriction', 'boundary', 'limit', 'threshold', 'ceiling', 'floor',
    'range', 'scope', 'extent', 'magnitude', 'amplitude', 'level',
    'volume', 'loudness', 'intensity', 'power', 'energy', 'force',
    'pressure', 'impact', 'effect', 'influence', 'consequence', 'result',
    'outcome', 'output', 'product', 'creation', 'work', 'piece',
    'composition', 'arrangement', 'orchestration', 'instrumentation',
    'voicing', 'part', 'line', 'melody', 'harmony', 'rhythm', 'beat',
    'groove', 'feel', 'vibe', 'mood', 'atmosphere', 'ambience', 'texture',
    'timbre', 'color', 'tone', 'sound', 'sonic', 'audio', 'acoustic',
    'electric', 'electronic', 'digital', 'analog', 'hybrid', 'fusion',
    'mixture', 'blend', 'combination', 'synthesis', 'integration',
    'unification', 'convergence', 'divergence', 'contrast', 'juxtaposition',
    'conflict', 'tension', 'release', 'resolution', 'cadence', 'phrase',
    'sentence', 'period', 'section', 'movement', 'chapter', 'verse',
    'chorus', 'bridge', 'intro', 'outro', 'coda', 'refrain', 'hook',
    'riff', 'lick', 'fill', 'solo', 'improvisation', 'jam', 'session',
    'performance', 'recital', 'concert', 'show', 'gig', 'set', 'list',
    'repertoire', 'catalog', 'discography', 'filmography', 'bibliography',
    'biography', 'history', 'background', 'context', 'perspective',
    'viewpoint', 'standpoint', 'angle', 'approach', 'method', 'technique',
    'style', 'genre', 'category', 'classification', 'type', 'kind',
    'sort', 'form', 'format', 'structure', 'organization', 'arrangement',
    'order', 'sequence', 'progression', 'development', 'evolution',
    'growth', 'maturity', 'refinement', 'polishing', 'finishing',
    'completion', 'finalization', 'conclusion', 'ending', 'closure',
    'wrap-up', 'summary', 'review', 'analysis', 'critique', 'evaluation',
    'assessment', 'judgment', 'opinion', 'feedback', 'comment', 'remark',
    'observation', 'note', 'memo', 'reminder', 'alert', 'warning',
    'notice', 'announcement', 'declaration', 'statement', 'proclamation',
    'manifesto', 'creed', 'doctrine', 'dogma', 'tenet', 'principle',
    'rule', 'law', 'regulation', 'statute', 'ordinance', 'decree',
    'mandate', 'order', 'command', 'instruction', 'direction', 'guidance',
    'advice', 'counsel', 'suggestion', 'recommendation', 'proposal',
    'offer', 'bid', 'tender', 'quote', 'estimate', 'valuation',
    'appraisal', 'audit', 'inspection', 'examination', 'investigation',
    'inquiry', 'probe', 'survey', 'study', 'research', 'exploration',
    'discovery', 'invention', 'innovation', 'creation', 'development',
    'design', 'plan', 'scheme', 'strategy', 'tactic', 'maneuver',
    'operation', 'mission', 'project', 'program', 'campaign', 'initiative',
    'enterprise', 'venture', 'undertaking', 'endeavor', 'effort',
    'attempt', 'try', 'trial', 'test', 'experiment', 'pilot', 'prototype',
    'model', 'sample', 'specimen', 'example', 'instance', 'case',
    'illustration', 'demonstration', 'exhibition', 'display', 'showcase',
    'presentation', 'lecture', 'talk', 'speech', 'address', 'sermon',
    'homily', 'discourse', 'discussion', 'debate', 'argument', 'controversy',
    'dispute', 'conflict', 'struggle', 'battle', 'war', 'fight',
    'combat', 'clash', 'confrontation', 'encounter', 'meeting',
    'gathering', 'assembly', 'convention', 'conference', 'symposium',
    'seminar', 'workshop', 'clinic', 'masterclass', 'lesson', 'tutorial',
    'guide', 'manual', 'handbook', 'reference', 'dictionary',
    'encyclopedia', 'thesaurus', 'almanac', 'atlas', 'map', 'chart',
    'graph', 'diagram', 'table', 'list', 'index', 'register', 'log',
    'record', 'file', 'document', 'paper', 'report', 'article', 'essay',
    'thesis', 'dissertation', 'book', 'novel', 'story', 'tale',
    'narrative', 'account', 'chronicle', 'history', 'biography', 'memoir',
    'diary', 'journal', 'blog', 'post', 'comment', 'tweet', 'status',
    'update', 'message', 'email', 'letter', 'note', 'card', 'invitation',
    'ticket', 'pass', 'badge', 'id', 'credential', 'license', 'permit',
    'certificate', 'diploma', 'degree', 'award', 'prize', 'trophy',
    'medal', 'ribbon', 'plaque', 'shield', 'cup', 'bowl', 'plate',
    'dish', 'saucer', 'mug', 'glass', 'bottle', 'can', 'jar', 'box',
    'carton', 'packet', 'bag', 'sack', 'pouch', 'case', 'crate', 'bin',
    'basket', 'bucket', 'barrel', 'drum', 'tank', 'vat', 'cistern',
    'reservoir', 'pool', 'pond', 'lake', 'sea', 'ocean', 'river',
    'stream', 'creek', 'brook', 'spring', 'well', 'fountain', 'geyser',
    'waterfall', 'cascade', 'rapids', 'current', 'tide', 'wave', 'swell',
    'surf', 'foam', 'spray', 'mist', 'fog', 'cloud', 'rain', 'snow',
    'hail', 'sleet', 'ice', 'frost', 'dew', 'wind', 'breeze', 'gale',
    'storm', 'hurricane', 'typhoon', 'cyclone', 'tornado', 'twister',
    'whirlwind', 'vortex', 'eddy', 'spiral', 'circle', 'ring', 'loop',
    'coil', 'curl', 'curve', 'arc', 'bend', 'turn', 'twist', 'spin',
    'rotation', 'revolution', 'orbit', 'trajectory', 'path', 'course',
    'route', 'way', 'road', 'street', 'avenue', 'boulevard', 'lane',
    'drive', 'court', 'place', 'square', 'plaza', 'park', 'garden',
    'yard', 'lawn', 'field', 'meadow', 'pasture', 'grass', 'turf',
    'ground', 'earth', 'soil', 'dirt', 'mud', 'sand', 'gravel', 'stone',
    'rock', 'boulder', 'pebble', 'dust', 'powder', 'ash', 'soot',
    'smoke', 'fume', 'vapor', 'gas', 'liquid', 'fluid', 'solid',
    'plasma', 'matter', 'energy', 'power', 'force', 'strength', 'might',
    'vigor', 'vitality', 'life', 'spirit', 'soul', 'heart', 'mind',
    'brain', 'intellect', 'intelligence', 'wisdom', 'knowledge',
    'understanding', 'comprehension', 'insight', 'intuition', 'instinct',
    'feeling', 'emotion', 'sentiment', 'passion', 'desire', 'wish',
    'hope', 'dream', 'fantasy', 'imagination', 'creativity', 'invention',
    'innovation', 'discovery', 'exploration', 'adventure', 'journey',
    'voyage', 'travel', 'trip', 'tour', 'expedition', 'quest', 'search',
    'hunt', 'chase', 'pursuit', 'race', 'competition', 'contest',
    'match', 'game', 'sport', 'play', 'fun', 'entertainment', 'amusement',
    'leisure', 'recreation', 'hobby', 'interest', 'pastime', 'activity',
    'action', 'movement', 'motion', 'gestures', 'expression', 'communication',
    'language', 'speech', 'voice', 'sound', 'noise', 'silence', 'quiet',
    'peace', 'calm', 'tranquility', 'serenity', 'happiness', 'joy',
    'bliss', 'ecstasy', 'delight', 'pleasure', 'satisfaction',
    'contentment', 'fulfillment', 'success', 'achievement',
    'accomplishment', 'victory', 'triumph', 'glory', 'fame', 'honor',
    'respect', 'admiration', 'love', 'affection', 'friendship',
    'camaraderie', 'brotherhood', 'sisterhood', 'unity', 'solidarity',
    'cooperation', 'collaboration', 'partnership', 'alliance',
    'coalition', 'union', 'association', 'organization', 'society',
    'community', 'group', 'team', 'squad', 'crew', 'band', 'gang',
    'mob', 'crowd', 'audience', 'public', 'people', 'humans',
    'humanity', 'mankind', 'world', 'earth', 'planet', 'universe',
    'cosmos', 'space', 'time', 'eternity', 'infinity', 'forever',
    'always', 'never', 'nothing', 'everything', 'something', 'anything',
    'snare', 'snares', 'kick', 'kicks',
    'cymbal', 'cymbals', 'trumpet', 'trumpets', 'sax', 'saxes', 'strings',
    'orchestra', 'orchestras', 'instrumental', 'instrumentals', 'beat', 'beats',
    'melody', 'melodies', 'chord', 'chords', 'note', 'notes', 'tempo', 'tempos',
    'rhythm', 'rhythms', 'percussion', 'fade', 'fades', 'echo', 'echoes',
    'delay', 'delays', 'chorus effect', 'flanger', 'phaser'
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
- OUTRO: You MUST end the song with an [Outro] section containing 2-4 lines of simple, fading text (e.g., "Fading out...", "Echoes...") to allow the audio to resolve naturally.
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
