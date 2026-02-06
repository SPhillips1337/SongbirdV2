# Songbird Usage Guide

## Prerequisites

- **Python 3.10+**
- **Ollama**: Running locally with the models specified in `.env` (e.g., `qwen3:14b`).
- **ComfyUI**: Accessible on the local network with the Audio Custom Nodes (ACE Step) installed.
- **Services**: Access to LightRAG and a valid Perplexity API key.

## Installation

1. **Clone/Move to the directory**:
   ```bash
   cd /home/stephen/Documents/www/songbird
   ```
2. **Setup virtual environment (recommended)**:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
3. **Install requirements**:
   ```bash
   pip install langgraph requests python-dotenv psycopg2-binary
   ```

## Configuration

Edit the `.env` file to match your infrastructure requirements:

```env
PERPLEXITY_API_KEY=your_key_here
COMFYUI_URL=http://192.168.1.x:8188
LIGHTRAG_URL=http://192.168.1.y:9621
...
```

## Running the Workflow

The `app.py` script contains a main execution block. You can customize the input genre and user direction at the bottom of the file:

```python
if __name__ == "__main__":
    flow = SongbirdWorkflow()
    final_state = flow.run("POP", "A catchy upbeat anthem about freedom.")
```

Run the script:
```bash
python app.py
```

## Troubleshooting
- **API Errors**: Ensure all local IP addresses in `.env` are reachable.
- **Model Missing**: If Ollama fails to respond, verify the model is pulled (`ollama pull qwen3:14b`).
- **ComfyUI Verification**: Ensure the ACE Step safetensors are correctly loaded in your ComfyUI environment.
