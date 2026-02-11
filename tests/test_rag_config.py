import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock requests and psycopg2 before importing tools.rag
sys.modules['requests'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()

from tools.rag import RAGTool

class TestRAGToolConfig(unittest.TestCase):

    def test_default_config(self):
        """Test that RAGTool uses default values when no env vars are set."""
        with patch.dict(os.environ, {}, clear=True):
            rag = RAGTool()
            self.assertEqual(rag.db_params["host"], "localhost")
            self.assertEqual(rag.db_params["database"], "n8n")
            self.assertEqual(rag.db_params["user"], "n8n")
            self.assertEqual(rag.db_params["password"], "")

    def test_env_config(self):
        """Test that RAGTool uses environment variables when set."""
        env_vars = {
            "POSTGRES_HOST": "db.example.com",
            "POSTGRES_DB": "custom_db",
            "POSTGRES_USER": "custom_user",
            "POSTGRES_PASSWORD": "secure_password"
        }
        with patch.dict(os.environ, env_vars, clear=True):
            rag = RAGTool()
            self.assertEqual(rag.db_params["host"], "db.example.com")
            self.assertEqual(rag.db_params["database"], "custom_db")
            self.assertEqual(rag.db_params["user"], "custom_user")
            self.assertEqual(rag.db_params["password"], "secure_password")

if __name__ == '__main__':
    unittest.main()
