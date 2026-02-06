import os
import requests
import re
from tools.rag import RAGTool
from tools.perplexity import PerplexityClient


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
            print(f"Perplexity search failed: {e}")
            search_results = "No search results."

        try:
            rag_results = self.rag.query_lightrag(f"Lyrics by {state['artist_style']}")
        except Exception as e:
            print(f"RAG query failed: {e}")
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
Research Notes: {research_notes}

Output Requirements:
- STRUCTURE: You MUST use markers like [Intro], [Verse], [Chorus], [Bridge], [Outro].
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
            state["cleaned_lyrics"] = self.clean_lyrics(lyrics)

        except Exception as e:
            print(f"Error generating lyrics: {e}")
            state["lyrics"] = "[Intro]\nError generating lyrics."
            state["cleaned_lyrics"] = "[Intro]\nError generating lyrics."

        return state

    def clean_lyrics(self, lyrics):
        """Logic from n8n CleanUpLyrics node."""
        lines = lyrics.split('\n')
        instruction_regex = r'\s*\(.*?\)'
        cleaned_lines = []
        for line in lines:
            cleaned = re.sub(instruction_regex, '', line).strip()
            if cleaned:
                cleaned_lines.append(cleaned)
        return '\n'.join(cleaned_lines)
