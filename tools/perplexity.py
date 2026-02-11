import requests
import os
import logging


class PerplexityClient:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexica_url = os.getenv("PERPLEXICA_URL")
        
        # Priority: If PERPLEXICA_URL is set, use it. Otherwise default to Perplexity AI.
        if self.perplexica_url:
            base_url = self.perplexica_url.rstrip('/')
            # Perplexica uses /api/search endpoint, not /chat/completions
            self.url = f"{base_url}/api/search"
            self.is_perplexica = True
        else:
            self.url = "https://api.perplexity.ai/chat/completions"
            self.is_perplexica = False

    def search(self, query, system_prompt=None):
        if not self.api_key and not self.perplexica_url:
            return "Configuration missing: PERPLEXITY_API_KEY or PERPLEXICA_URL must be set."

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        # Different request formats for Perplexica vs Perplexity AI
        if self.is_perplexica:
            # Perplexica API format
            data = {
                "focusMode": "webSearch",
                "query": query,
                "history": []
            }
        else:
            # Perplexity AI API format
            data = {
                "model": "sonar",
                "messages": [
                    {"role": "system", "content": system_prompt or "You are a specialized songwriting researcher."},
                    {"role": "user", "content": query}
                ]
            }

        try:
            response = requests.post(self.url, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            
            # Different response formats
            if self.is_perplexica:
                return response.json().get("message", "")
            else:
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Error querying Perplexity: {e}")
            return f"Research error: {e}"
