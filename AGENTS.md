# Songbird Agent Architecture

Songbird utilizes a multi-agent system built on **LangGraph**. Each agent is a specialized Python class that interacts with local LLMs (Ollama) or external APIs.

## Available Agents

### 1. Artist Agent (`agents/artist.py`)
- **Responsibility**: Generates fictional female artist personas (20s-30s) and selects stylistic inspirations based on the song genre.
- **Tools**: Ollama (Artist Model).

### 2. Music Agent (`agents/music.py`)
- **Responsibility**: Determines the musical direction (BPM, mood, instruments, key) by synthesizing genre requirements and user instructions.
- **Tools**: Ollama (Lyric Model).

### 3. Lyrics Agent (`agents/lyrics.py`)
- **Responsibility**: A multi-stage pipeline for lyric generation.
- **Workflow**:
    - **Research**: Queries Perplexity (Deep Research) and LightRAG for topical and stylistic context.
    - **Drafting**: Generates raw lyrics in the ACE Step format.
    - **Refinement**: Iteratively improves lyrics for better flow and "street" or "raw" quality as per the original n8n logic.
- **Tools**: Perplexity API, LightRAG Client, Ollama.

## Governance & State
All agents share the `SongState` (defined in `state.py`), ensuring that context (like artist background and musical mood) is consistently applied throughout the lyric writing and audio generation process.
