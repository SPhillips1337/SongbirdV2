import unittest
from unittest.mock import MagicMock
import sys
import os

# Patch ALL dependencies globally before importing anything
sys.modules["requests"] = MagicMock()
sys.modules["langgraph"] = MagicMock()
sys.modules["langgraph.graph"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["psycopg2"] = MagicMock()
sys.modules["tools.rag"] = MagicMock()
sys.modules["config"] = MagicMock()

# Setup config mock values
config_mock = sys.modules["config"]
config_mock.DEFAULT_ARTIST_STYLE = "Adele"
config_mock.ARTIST_STYLES = {
    "RAP": "Eminem",
    "POP": "Taylor Swift",
    "JAZZ": "Norah Jones",
    "ROCK": "Guns N Roses",
    "COUNTRY": "Dolly Parton",
    "R&B": "Alicia Keys",
    "ELECTRONIC": "Daft Punk",
    "FUNK": "James Brown",
    "SOUL": "Aretha Franklin",
    "CYBERPUNK": "Vangelis",
    "DUBSTEP": "Skrillex",
    "METAL": "Metallica",
    "LATIN": "Shakira",
    "AMBIENT": "Brian Eno",
    "PHONK": "Kordhell"
}
config_mock.MUSIC_PROMPTS = {
    "RAP": "...",
    "POP": "...",
    # Add keys as needed by tests, or just generic dict
    "JAZZ": "...", "ROCK": "...", "COUNTRY": "...", "R&B": "...",
    "ELECTRONIC": "...", "FUNK": "...", "SOUL": "...", "CYBERPUNK": "...",
    "DUBSTEP": "...", "METAL": "...", "LATIN": "...", "AMBIENT": "...", "PHONK": "..."
}
config_mock.OLLAMA_BASE_URL = "http://localhost:11434"
config_mock.ALBUM_MODEL = "llama3"

# Also patch specific submodules if needed by deep imports
sys.modules["langchain_core"] = MagicMock()
sys.modules["langchain_core.messages"] = MagicMock()
sys.modules["langchain_community"] = MagicMock()
sys.modules["langchain_community.vectorstores"] = MagicMock()

if __name__ == "__main__":
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests'
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    if not result.wasSuccessful():
        sys.exit(1)
