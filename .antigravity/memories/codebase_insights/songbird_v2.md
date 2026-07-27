# Codebase Insight: Songbird V2 Architecture

## Hidden Knowledge: Why This Exists?
Songbird V2 was refactored from a linear script approach to a **LangGraph-based** multi-agent architecture to allow for iterative refining and more complex "loops" (e.g., the Narrative agent informing the Lyric agent).

## Core Orchestration
- **SongState**: A Pydantic model (`state.py`) that serves as the "source of truth". Every agent must read from and write to this state.
- **Artist -> Narrative -> Music -> Lyrics**: The standard directed acyclic graph (DAG) flow.

## Hidden Complexities
- **Implicit Context**: The `NarrativeAgent` creates "World Building" which isn't always directly visible in the final lyrics but standardizes the "Band Persona" across tracks in an album.
- **Perplexity Deep Research**: The `LyricsAgent` uses a two-pass research strategy to avoid generic rhymes.
