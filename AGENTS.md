# Songbird Agent Architecture

Songbird utilizes a multi-agent system built on **LangGraph**. Each agent is a specialized Python class that interacts with local LLMs (Ollama) or external APIs.

## Available Agents

### 1. Artist Agent (`agents/artist.py`)
- **Responsibility**: Generates fictional female artist personas (20s-30s) and selects stylistic inspirations based on the song genre.
- **Specialization**: Conducting deep research *strictly* on the reference artist's biography, visual style, and public persona.
- **Tools**: Ollama (Artist Model), Perplexity (Artist Research), LightRAG (Artist Context).

### 2. Music Agent (`agents/music.py`)
- **Responsibility**: Determines the musical direction (BPM, mood, instruments, key) by synthesizing genre requirements and user instructions.
- **Specialization**: Researching technical production styles, music theory, and genre-specific instrumentation.
- **Tools**: Ollama (Lyric Model), Perplexity (Technical Research), LightRAG (Genre Context).

### 3. Lyrics Agent (`agents/lyrics.py`)
- **Responsibility**: A multi-stage pipeline for lyric generation.
- **Specialization**: focusing *strictly* on lyrical themes, trending topics, and poetic structures (Poetry Mode).
- **Workflow**:
    - **Research**: Queries Perplexity and LightRAG for thematic inspiration and trending topics (if enabled).
    - **Drafting**: Generates raw lyrics in the ACE Step format or Poetry Mode (Hollis Robbins approach).
    - **Refinement**: Iteratively improves lyrics for better flow and authentic quality.
- **Tools**: Perplexity API, LightRAG Client, Ollama.

## Governance & State
All agents share the `SongState` (defined in `state.py`), ensuring that context (like artist background and musical mood) is consistently applied throughout the lyric writing and audio generation process.
