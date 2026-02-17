import requests
import os
import logging


from tools.cache import CacheManager


class RAGTool:
    def __init__(self):
        self.lightrag_url = os.getenv("LIGHTRAG_URL", "http://localhost:9621")
        self.cache = CacheManager()

    def query_lightrag(self, query):
        # Check cache first
        cache_key = f"rag:{query}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        api_key = os.getenv("LIGHTRAG_API_KEY")
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key if api_key else ""
        }
        
        payload = {
            "query": query,
            "mode": "mix",
            "only_need_context": False, # We want the actual answer
            "response_type": "string"
        }
        
        try:
            response = requests.post(
                f"{self.lightrag_url}/query", 
                json=payload, 
                headers=headers,
                timeout=180 # Increased to 30s
            )
            response.raise_for_status()
            result = response.json().get("output", "")
            if result:
                self.cache.set(cache_key, result)
            return result
        except requests.exceptions.Timeout:
            logging.error(f"Error querying LightRAG: Connection timed out after 30s. Check if the server at {self.lightrag_url} is reachable.")
            return "Connection timeout"
        except Exception as e:
            logging.error(f"Error querying LightRAG: {e}")
            return str(e)

    def query_pgvector(self, query):
        # Placeholder for PGVector logic using psycopg2 or langchain
        return "Vector results for: " + query
