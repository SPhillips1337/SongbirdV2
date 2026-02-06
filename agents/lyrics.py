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

    def research_node(self, state):
        """Node: Research themes and artist style."""
        query = f"Songwriting themes for {state['genre']} music in the style of {state['artist_style']}"
        
        # 1. Search Perplexity
        search_results = self.perplexity.search(query)
        
        # 2. Query LightRAG
        rag_results = self.rag.query_lightrag(f"Lyrics by {state['artist_style']}")
        
        state["research_notes"] = f"Perplexity: {search_results}\n\nLightRAG: {rag_results}"
        return state

    def writer_node(self, state):
        """Node: Generate ACE-formatted lyrics."""
        prompt = f"""Role: Expert AI Songwriter
Goal: Produce unique, high-quality lyrics for a {state['genre']} track.
Artist: {state['artist_name']}
Background: {state['artist_background']}
Style: {state['artist_style']}
Musical Direction: {state['musical_direction']}
Research Notes: {state['research_notes']}

Output Requirements:
- Start with tags like [intro], [verse], [chorus], [outro].
- FORMAT FOR ACE TEXT-TO-AUDIO (Comfy UI).
- No explanations. Only lyrics.

Begin creative workflow immediately."""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=90
            )
            response.raise_for_status()
            state["lyrics"] = response.json().get("response", "").strip()
        except Exception as e:
            state["lyrics"] = "[intro]\nError generating lyrics."
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

    def refiner_node(self, state):
        """Node: Final polish and cleaning."""
        raw_lyrics = state["lyrics"]
        # Basic regex cleanup as per n8n
        cleaned = self.clean_lyrics(raw_lyrics)
        
        # Secondary LLM refine (Raw/Rebellious factor from n8n RAG AI Agent2)
        refine_prompt = f"Review these lyrics and make them more raw, improve them, make them more street. Only return the lyrics:\n\n{cleaned}"
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": refine_prompt, "stream": False},
                timeout=60
            )
            response.raise_for_status()
            state["cleaned_lyrics"] = response.json().get("response", "").strip()
        except:
            state["cleaned_lyrics"] = cleaned
            
        return state
