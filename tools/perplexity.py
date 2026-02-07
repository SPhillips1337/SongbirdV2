import requests
import os
import logging


class PerplexityClient:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexica_url = os.getenv("PERPLEXICA_URL")
        self.url = self.perplexica_url + "/chat/completions" if self.perplexica_url and not self.api_key else "https://api.perplexity.ai/chat/completions"

    def search(self, query, system_prompt=None):
        if not self.api_key:
            return "Perplexity API key missing."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
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
