import requests
import logging
import random
from config import ARTIST_STYLES, GENRE_ARTISTS, OLLAMA_BASE_URL, ARTIST_MODEL, DEFAULT_ARTIST_STYLE
from tools.perplexity import PerplexityClient
from tools.rag import RAGTool


class ArtistAgent:
    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.model = ARTIST_MODEL
        self.perplexity = PerplexityClient()
        self.rag = RAGTool()

    def research_artist(self, artist_name):
        """
        Researches the artist's style, history, and persona using Perplexity and RAG.
        Strictly focused on the reference artist.
        """
        if not artist_name:
            return "No specific reference artist."

        query = f"Provide a detailed biography and musical style overview of the artist: {artist_name}. Focus on their public persona, career highlights, and visual aesthetic."
        
        perplexity_results = ""
        try:
            perplexity_results = self.perplexity.search(query)
        except Exception as e:
            logging.error(f"Perplexity search failed in ArtistAgent: {e}")

        rag_results = self.rag.query_lightrag(f"Details about artist: {artist_name}")
        
        return f"Perplexity: {perplexity_results}\n\nGraphRAG: {rag_results}"

    def generate_persona(self, genre, user_direction=None, research_notes=None):
        prompt = f"""Generate a detailed character profile for a {genre} song protagonist. 
        The persona should be consistent with the following research notes about the reference artist.

        GENRE: {genre}
        USER DIRECTION: {user_direction if user_direction else "No specific direction provided."}
        ARTIST RESEARCH: {research_notes if research_notes else "General genre-based persona."}

        The profile must include:
        A classic, {genre} star two-part name like .

        Please generate a background story and persona that would fit the {genre} and strictly incorporate any specific character traits or vibes mentioned in the USER DIRECTION.

        The final output should be a single, descriptive paragraph summarizing this character's background, ready to be used as the basis for a song.

        Important: Do not include any additional text, explanations, or conversational phrases. Your final response must contain only the generated artist background persona."""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except Exception as e:
            logging.error(f"Error generating artist persona: {e}")
            return f"A mysterious singer in the {genre} scene."

    def select_artist_style(self, genre, user_direction=None):
        # 1. Check if we have a list of artists for this genre (Priority for variety)
        artists = GENRE_ARTISTS.get(genre.upper())
        if artists:
            return random.choice(artists)

        # 2. Check if we have a hardcoded style (Legacy fallback)
        if genre.upper() in ARTIST_STYLES:
             return ARTIST_STYLES[genre.upper()]

        # 3. Fallback
        return DEFAULT_ARTIST_STYLE
