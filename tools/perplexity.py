import requests
import os
import logging
import time
from tools.cache import CacheManager

class PerplexityClient:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexica_url = os.getenv("PERPLEXICA_URL")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL")
        self.perplexica_chat_model = os.getenv("PERPLEXICA_CHAT_MODEL", os.getenv("ALBUM_MODEL", "qwen2.5:7b-instruct-q4_K_M"))
        self.perplexica_embedding_model = os.getenv("PERPLEXICA_EMBEDDING_MODEL", "nomic-embed-text:latest")
        self.perplexica_optimization_mode = os.getenv("PERPLEXICA_OPTIMIZATION_MODE", "speed")
        self.cache = CacheManager()
        # Configure endpoints
        self.cloud_url = "https://api.perplexity.ai/chat/completions"
        if self.perplexica_url:
             self.local_url = f"{self.perplexica_url.rstrip('/')}/api/search"
        else:
             self.local_url = None

    def search(self, query, system_prompt=None):
        # Check cache first
        cache_key = f"perplexity:{query}:{system_prompt or ''}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        error_messages = []
        result = None
        
        # 1. Try Cloud API first if available
        if self.api_key:
            try:
                logging.info("Attempting to query Perplexity Cloud API...")
                result = self._query_cloud(query, system_prompt)
            except Exception as e:
                msg = f"Perplexity Cloud API failed: {e}"
                logging.warning(msg)
                error_messages.append(msg)
        else:
            error_messages.append("Values for PERPLEXITY_API_KEY not found.")

        # 2. Fallback to Local Perplexica if available
        if not result and self.local_url:
            try:
                logging.info("Attempting to query Local Perplexica instance...")
                result = self._query_local(query)
            except Exception as e:
                msg = f"Local Perplexica instance failed: {e}"
                logging.error(msg)
                error_messages.append(msg)
        elif not self.local_url:
             error_messages.append("Values for PERPLEXICA_URL not found.")

        if result:
            self.cache.set(cache_key, result)
            return result

        return f"Research failed. Errors: {'; '.join(error_messages)}"

    def _query_cloud(self, query, system_prompt):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        data = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": system_prompt or "You are a specialized songwriting researcher."},
                {"role": "user", "content": query}
            ]
        }
        response = requests.post(self.cloud_url, json=data, headers=headers, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _query_local(self, query):
        headers = {"Content-Type": "application/json"}
        data = {
            "chatModel": {
                "provider": "ollama",
                "model": self.perplexica_chat_model
            },
            "embeddingModel": {
                "provider": "ollama",
                "model": self.perplexica_embedding_model
            },
            "optimizationMode": self.perplexica_optimization_mode,
            "focusMode": "webSearch",
            "query": query,
            "history": []
        }
        if self.ollama_base_url:
            logging.info(f"Local Perplexica configured for Ollama base URL: {self.ollama_base_url}")
        # Local instances might be slower or on different network conditions
        response = requests.post(self.local_url, json=data, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json().get("message", "")
