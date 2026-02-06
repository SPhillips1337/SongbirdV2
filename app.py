from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

from state import SongState
from agents.artist import ArtistAgent
from agents.music import MusicAgent
from agents.lyrics import LyricsAgent
from tools.comfy import ComfyClient

class SongbirdWorkflow:
    def __init__(self):
        self.artist_agent = ArtistAgent()
        self.music_agent = MusicAgent()
        self.lyrics_agent = LyricsAgent()
        self.comfy = ComfyClient()
        
        # Build the graph
        workflow = StateGraph(SongState)
        
        # Define nodes
        workflow.add_node("create_artist", self.node_create_artist)
        workflow.add_node("create_music_direction", self.node_create_music)
        workflow.add_node("research_lyrics", self.lyrics_agent.research_node)
        workflow.add_node("write_lyrics", self.lyrics_agent.writer_node)
        workflow.add_node("refine_lyrics", self.lyrics_agent.refiner_node)
        workflow.add_node("generate_audio", self.node_generate_audio)
        
        # Define edges
        workflow.set_entry_point("create_artist")
        workflow.add_edge("create_artist", "create_music_direction")
        workflow.add_edge("create_music_direction", "research_lyrics")
        workflow.add_edge("research_lyrics", "write_lyrics")
        workflow.add_edge("write_lyrics", "refine_lyrics")
        workflow.add_edge("refine_lyrics", "generate_audio")
        workflow.add_edge("generate_audio", END)
        
        self.app = workflow.compile()

    def node_create_artist(self, state: SongState):
        state["artist_style"] = self.artist_agent.select_artist_style(state["genre"])
        state["artist_background"] = self.artist_agent.generate_persona(state["genre"])
        state["artist_name"] = "Sunny Skywind" # Placeholder for name extraction
        return state

    def node_create_music(self, state: SongState):
        state["musical_direction"] = self.music_agent.generate_direction(
            state["genre"], state["user_direction"]
        )
        return state

    def node_generate_audio(self, state: SongState):
        # We assume musical_direction might be a string or we can extract info if needed
        # For the prototype, we pass the direction as 'tags'
        result = self.comfy.submit_prompt(
            state["cleaned_lyrics"], 
            tags=state["musical_direction"],
            filename_prefix=f"{state['artist_name']}_song"
        )
        state["audio_path"] = result.get("prompt_id") if result else "error"
        return state

    def run(self, genre, user_direction):
        initial_state = {
            "genre": genre,
            "user_direction": user_direction,
            "artist_name": None,
            "artist_background": None,
            "artist_style": None,
            "musical_direction": None,
            "lyrics": None,
            "cleaned_lyrics": None,
            "audio_path": None,
            "research_notes": None,
            "history": []
        }
        return self.app.invoke(initial_state)

if __name__ == "__main__":
    flow = SongbirdWorkflow()
    final_state = flow.run("POP", "A catchy upbeat pop song in the style of Black Pink about freedom with powerful female vocals and a live drummer.")
    print("Workflow Complete!")
    print(f"Lyrics Preview: {final_state['cleaned_lyrics'][:100]}...")
