import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import SongbirdWorkflow

class TestSongbirdWorkflow(unittest.TestCase):

    @patch('requests.post')
    @patch('requests.get')
    def test_full_workflow(self, mock_get, mock_post):
        # Mock responses

        def side_effect_post(url, json=None, **kwargs):
            # Ollama Generate
            if "api/generate" in url:
                prompt = json.get("prompt", "")
                if "character profile" in prompt:
                    return MagicMock(json=lambda: {"response": "A cool artist persona."})
                if "musical direction" in prompt:
                    # Return JSON string as expected by new logic
                    return MagicMock(json=lambda: {"response": '{"tags": "dark, moody", "bpm": 140, "keyscale": "D minor"}'})
                if "Role: Expert AI Songwriter" in prompt:
                    return MagicMock(json=lambda: {"response": "[Intro]\nYeah yeah\n[Verse]\nLyrics here\n[Chorus]\nSing it loud"})
                return MagicMock(json=lambda: {"response": "Generic response"})

            # ComfyUI Prompt
            if "/prompt" in url:
                return MagicMock(json=lambda: {"prompt_id": "test_id_123"})

            return MagicMock()

        def side_effect_get(url, params=None, **kwargs):
            # ComfyUI History
            if "/history/test_id_123" in url:
                return MagicMock(json=lambda: {
                    "test_id_123": {
                        "outputs": {
                            "104": [
                                {"filename": "test_song.mp3", "subfolder": "audio", "type": "output"}
                            ]
                        }
                    }
                })

            # ComfyUI View (Download)
            if "/view" in url:
                mock_resp = MagicMock()
                mock_resp.content = b"fake audio content"
                return mock_resp

            return MagicMock()

        mock_post.side_effect = side_effect_post
        mock_get.side_effect = side_effect_get

        workflow = SongbirdWorkflow()

        # Mocking internal tools of agents
        workflow.lyrics_agent.perplexity.search = MagicMock(return_value="Mock search results")
        workflow.lyrics_agent.rag.query_lightrag = MagicMock(return_value="Mock RAG results")

        # Run workflow
        final_state = workflow.run("POP", "Make a hit")

        # Assertions
        print("Final State Keys:", final_state.keys())
        print("Musical Direction:", final_state.get("musical_direction"))
        print("Cleaned Lyrics:", final_state.get("cleaned_lyrics"))
        print("Audio Path:", final_state.get("audio_path"))

        self.assertEqual(final_state["artist_background"], "A cool artist persona.")
        self.assertEqual(final_state["musical_direction"], {"tags": "dark, moody", "bpm": 140, "keyscale": "D minor"})
        self.assertIn("[Verse]", final_state["cleaned_lyrics"])
        self.assertIn("test_song.mp3", final_state["audio_path"])
        self.assertTrue(os.path.exists(final_state["audio_path"]))

        # Cleanup
        if os.path.exists(final_state["audio_path"]):
            os.remove(final_state["audio_path"])

if __name__ == '__main__':
    unittest.main()
