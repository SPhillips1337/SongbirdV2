# Songbird V2

Songbird is a local agentic workflow for AI-driven song creation, V2 is migrated from the N8N V1 original version to **LangGraph**. It orchestrates multiple specialized agents to generate artist personas, musical direction, and ACE-formatted lyrics, ultimately submitting prompts to ComfyUI for audio generation.

**New in v2.1 (Virtual Artist Upgrade):**
- **Suggestion Engine**: GraphRAG-powered song ideas based on your history
- **Trending Intelligence**: Real-world trend injection via Perplexity
- **Virtual Band Persistence**: Re-usable artist personas across albums
- **Poetry Mode**: Elevated lyricism based on Hollis Robbins' principles
- **Smart Caching**: Reduced API usage for research steps

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


## Pre-requisites & Installation
SongbirdV2 is designed as a distributed system. While you can run everything on a single powerful machine (e.g., NVIDIA 5090), for best performance we recommend splitting the workload across dedicated nodes.

Below is the setup guide for each node in the cluster.

**1. Audio Generation Node (The Studio)**
Hosted on a machine with a powerful GPU (e.g., NVIDIA 4090/5090)

This node handles the heavy lifting of audio synthesis using ComfyUI.

**Install Stability Matrix**: Download and install Stability Matrix (the recommended package manager for ComfyUI).

**Install ComfyUI**: Use Stability Matrix to install a fresh instance of ComfyUI.

**Install ACE-Step 1.5**:

Search for and install the Ace-Step 1.5 models via the Stability Matrix model browser (or download from HuggingFace).

Import the Workflow: Copy the workflow_acestep_1.5.json from this repository's workflows/ folder and load it into ComfyUI.

**Install Custom Nodes**:

If the workflow complains about missing nodes, use the ComfyUI Manager to "Install Missing Custom Nodes."

**Critical**: Ensure you have the ComfyUI-SaveAudio or equivalent node configured to save outputs to a specific directory.

**2. LLM Intelligence Node (The Brain)**
Hosted on a machine with decent VRAM (16GB+) or high system RAM

This node runs the local LLMs that act as the Lyricist, Musical Director, and Persona builder.

**Install Ollama**: Download from ollama.com.

Pull Required Models:
Open a terminal and run the following commands to download the specific models Songbird relies on:

Bash
ollama pull qwen3:14b           # General intelligence & logic
ollama pull ALIENTELLIGENCE/lyricist  # Specialized lyric writing agent
Start the Server: Ensure Ollama is running (ollama serve) and accessible on port 11434.

Note: If running on a different machine than the script, launch with OLLAMA_HOST=0.0.0.0 to allow network connections.

**3. Knowledge Base Node (The Memory)**
Hosted on a machine with fast storage (NVMe recommended)

This node hosts the Graph Retrieval-Augmented Generation (GraphRAG) database, allowing Songbird to "remember" themes, lyrics, and musical history.

**Install LightRAG**:
Clone and setup a local LightRAG instance (or a Postgres Vector DB enabled with pgvector).

Bash
git clone https://github.com/HKUDS/LightRAG
cd LightRAG
pip install -r requirements.txt
Ingest Data: (Optional) If you have existing song data or lore, use the ingestion script to populate the graph: python lightrag_ingest.py --dir ./my_lyrics_corpus.

**4. Controller Node (The Script)**
This is your main Dev PC where you run Songbird.

**Clone the Repo**:

Bash
git clone https://github.com/SPhillips1337/SongbirdV2
cd SongbirdV2
pip install -r requirements.txt
**Get External API Keys**:

Perplexity API: Required for the "Trending" and "Research" agents. Get a key at perplexity.ai/api.

**Configure the Environment**:
Rename .env.example to .env and configure your IP addresses. Crucial: If your services are on different PCs, use their LAN IPs (e.g., 192.168.1.x) instead of localhost.

# .env Configuration

# --- Node 1: Audio ---
COMFY_URL=http://192.168.1.10:8188

# --- Node 2: Intelligence ---
OLLAMA_HOST=http://192.168.1.11:11434
LLM_MODEL=qwen3:14b
LYRIC_MODEL=ALIENTELLIGENCE/lyricist

# --- Node 3: Memory ---
RAG_HOST=http://192.168.1.12:9621

# --- External APIs ---
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxx
Once configured, verify connectivity by running:
python app.py --test-connection

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

   # Generate a full concept album
   python app.py --album --theme "Cyberpunk dystopia" --genre "SYNTHWAVE" --num-songs 4

   # Specific vocal type
   python app.py --genre ROCK --vocals female --direction "An anthem about breaking free"
   # New Features
   python app.py --suggest  # Get a song idea based on history
   python app.py --trending --genre DUBSTEP  # Inject real-world trends
   python app.py --poetic --direction "about time travel"  # High-level poetry
   python app.py --band output/MyBand/band_profile.json  # Re-use a virtual band
   ```

Refer to [USAGE.md](USAGE.md) for detailed CLI options and setup instructions.
