import requests
import os
import logging
import time

class PerplexityClient:
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.perplexica_url = os.getenv("PERPLEXICA_URL")
        # Configure endpoints
        self.cloud_url = "https://api.perplexity.ai/chat/completions"
        if self.perplexica_url:
             self.local_url = f"{self.perplexica_url.rstrip('/')}/api/search"
        else:
             self.local_url = None

    def search(self, query, system_prompt=None):
        error_messages = []
        
        # 1. Try Cloud API first if available
        if self.api_key:
            try:
                logging.info("Attempting to query Perplexity Cloud API...")
                return self._query_cloud(query, system_prompt)
            except Exception as e:
                msg = f"Perplexity Cloud API failed: {e}"
                logging.warning(msg)
                error_messages.append(msg)
        else:
            error_messages.append("Values for PERPLEXITY_API_KEY not found.")

        # 2. Fallback to Local Perplexica if available
        if self.local_url:
            try:
                logging.info("Attempting to query Local Perplexica instance...")
                return self._query_local(query)
            except Exception as e:
                msg = f"Local Perplexica instance failed: {e}"
                logging.error(msg)
                error_messages.append(msg)
        else:
             error_messages.append("Values for PERPLEXICA_URL not found.")

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
            "focusMode": "webSearch",
            "query": query,
            "history": []
        }
        # Local instances might be slower or on different network conditions
        response = requests.post(self.local_url, json=data, headers=headers, timeout=120)
        response.raise_for_status()
        return response.json().get("message", "")
