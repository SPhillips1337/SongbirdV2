# Songbird V2

Songbird is a local agentic workflow for AI-driven song creation, V2 is migrated from the N8N V1 original version to **LangGraph**. It orchestrates multiple specialized agents to generate artist personas, musical direction, and ACE-formatted lyrics, ultimately submitting prompts to ComfyUI for audio generation.

## Project Structure

```text
songbird/
├── agents/             # Specialized AI agents (Artist, Music, Lyrics)
├── tools/              # Client wrappers for external services (ComfyUI, LightRAG, Perplexity)
├── output/             # Local directory for generated assets
├── .env                # Configuration for API keys and endpoints
├── app.py              # Main LangGraph orchestrator
├── state.py            # Workflow state definitions
├── AGENTS.md           # Detailed documentation of the agentic architecture
└── USAGE.md            # Instructions for setup and execution
```

## Quick Start

1. **Configure Environment**: Set up your `.env` file with the required API keys and local service URLs.
2. **Install Dependencies**:
   ```bash
   pip install langgraph requests python-dotenv psycopg2-binary
   ```
3. **Run the Workflow**:
   ```bash
   # Default run (POP)
   python app.py

   # Custom genre and direction
   python app.py --genre JAZZ --direction "A smooth noir jazz track about rainy city streets" --verbose
   ```

Refer to [USAGE.md](USAGE.md) for detailed CLI options and setup instructions.
