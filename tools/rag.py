import requests
import psycopg2
import os


class RAGTool:
    def __init__(self):
        self.lightrag_url = os.getenv("LIGHTRAG_URL", "http://localhost:9621")
        self.db_params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "database": "n8n", # Typical n8n db name
            "user": "n8n",
            "password": "" # Assuming no password for local dev or handle via env
        }

    def query_lightrag(self, query):
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
                timeout=30 # Increased to 30s
            )
            response.raise_for_status()
            return response.json().get("output", "")
        except requests.exceptions.Timeout:
            print(f"Error querying LightRAG: Connection timed out after 30s. Check if the server at {self.lightrag_url} is reachable.")
            return "Connection timeout"
        except Exception as e:
            print(f"Error querying LightRAG: {e}")
            return str(e)

    def query_pgvector(self, query):
        # Placeholder for PGVector logic using psycopg2 or langchain
        # In a full implementation, we'd use local embeddings (ollama) to vector search
        return "Vector results for: " + query
