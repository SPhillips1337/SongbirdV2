import requests
import os
import logging


class RAGTool:
    def __init__(self):
        self.lightrag_url = os.getenv("LIGHTRAG_URL", "http://localhost:9621")

    def query_lightrag(self, query, only_need_context=False, mode="mix"):
        api_key = os.getenv("LIGHTRAG_API_KEY")
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
            "X-API-Key": api_key if api_key else ""
        }

        payload = {
            "query": query,
            "mode": mode,
            # True returns retrieved chunks/context without asking the LLM to invent an answer.
            "only_need_context": bool(only_need_context),
            "response_type": "string",
        }

        try:
            response = requests.post(
                f"{self.lightrag_url}/query",
                json=payload,
                headers=headers,
                timeout=180,
            )
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return str(data).strip()

            text = data.get("response") or data.get("output") or data.get("context") or ""
            if not isinstance(text, str):
                text = str(text)
            text = text.strip()

            refs = data.get("references") or data.get("ref_list") or []
            if refs and isinstance(refs, list):
                ref_lines = []
                for r in refs[:12]:
                    if isinstance(r, dict):
                        ref_lines.append(
                            r.get("file_path")
                            or r.get("path")
                            or r.get("content")
                            or str(r)
                        )
                    else:
                        ref_lines.append(str(r))
                if ref_lines:
                    text = (text + "\n\nReferences:\n- " + "\n- ".join(ref_lines)).strip()

            return text
        except requests.exceptions.Timeout:
            logging.error(
                f"Error querying LightRAG: Connection timed out after 180s. "
                f"Check if the server at {self.lightrag_url} is reachable."
            )
            return "Connection timeout"
        except Exception as e:
            logging.error(f"Error querying LightRAG: {e}")
            return str(e)

    def query_pgvector(self, query):
        # Placeholder for PGVector logic using psycopg2 or langchain
        return "Vector results for: " + query
