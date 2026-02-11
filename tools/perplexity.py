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
            self.url = f"{base_url}/chat/completions"
        else:
            self.url = "https://api.perplexity.ai/chat/completions"

    def search(self, query, system_prompt=None):
        if not self.api_key and not self.perplexica_url:
            return "Configuration missing: PERPLEXITY_API_KEY or PERPLEXICA_URL must be set."

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        data = {
            "model": "sonar", # Updated to current default
            "messages": [
                {"role": "system", "content": system_prompt or "You are a specialized songwriting researcher."},
                {"role": "user", "content": query}
            ]
        }

        try:
            response = requests.post(self.url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logging.error(f"Error querying Perplexity: {e}")
            return f"Research error: {e}"
