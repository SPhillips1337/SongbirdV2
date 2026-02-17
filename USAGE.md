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

`app.py` is a command-line tool. You can customize the song generation via arguments:

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--genre` | Top-level genre (POP, RAP, JAZZ, etc.) | `POP` |
| `--direction` | Detailed musical/thematic direction | (Catchy POP prompt) |
| `--output` | Directory to save generated assets | `output` |
| `--verbose` | Enable INFO level logging (otherwise WARNING) | `False` |
| `--vocals` | Vocal type (`female`, `male`, `duet`, `choir`, `instrumental`, `auto`) | `auto` |
| `--album` | Enable Album Mode | `False` |
| `--theme` | Album theme (required for Album Mode) | None |
| `--album-name` | Custom album name | (Auto-generated) |
| `--num-songs` | Number of songs in album | `6` |
| `--base-direction` | Shared constraints for every song in album | None |
| `--suggest` | Generate song idea based on history | `False` |
| `--trending` | Inject real-world trending data via Perplexity | `False` |
| `--artist` | Specific reference artist name | None |
| `--band` | Centralized band profile name (creates or loads) | None |
| `--poetic` | Enable poetry mode for elevated lyrics | `False` |

### Album Mode

Album mode allows you to generate a cohesive set of songs around a central theme. The system will:
1. Generate an album title (if not provided).
2. Create song titles that fit the narrative.
3. Ensure musical consistency while progressing the story/vibe through the tracklist.
4. Organize output into a dedicated album folder.

**Example Album Command:**
```bash
python app.py --album --theme "A space opera about a lost pilot" --genre "SYNTHWAVE" --num-songs 4
```

### Vocal Control

You can strictly enforce the type of vocals generated using the `--vocals` argument. This injects specific tags into the prompt to guide the audio generation.

**Options:**
- `female`, `male`
- `duet`, `choir`
- `instrumental` (forces no vocals)
- `auto` (default, lets the model decide based on genre)

**Example:**
```bash
python app.py --genre ROCK --vocals female --direction "Power ballad"
```

## Advanced Features

### Suggestion Engine
Get AI-powered song ideas based on your generation history:
```bash
python app.py --suggest
```

### Trending Intelligence
Inject real-world musical trends into your songs:
```bash
python app.py --trending --genre DUBSTEP --direction "heavy bass drop"
```

### Poetry Mode
Elevate lyrics to high-art poetry with concrete imagery and structural tension:
```bash
python app.py --poetic --genre INDIE --direction "A song about fading photographs"
```

### Centralized Band Manager
Create persistent virtual bands with tracked discography:

**Create a new band:**
```bash
python app.py --band "The Neon Ghosts" --album --theme "Cyberpunk rebellion" --genre SYNTHWAVE
```

**Re-use an existing band:**
```bash
python app.py --band "The Neon Ghosts" --album --theme "Digital uprising"
```

Band profiles are stored in `Output/Bands/` and include:
- Master seed (consistent sound)
- Biography and visual style
- Complete discography tracking

### Examples

**Basic Run:**
```bash
python app.py --genre RAP --direction "A hard-hitting boom bap track about city life"
```

**Verbose Output to Custom Directory:**
```bash
python app.py --verbose --output ./my_songs --genre JAZZ
```

## Logging
The system uses the standard Python `logging` module. Use the `--verbose` flag to see real-time progress of research, generation, and file downloads.

## Troubleshooting
- **API Errors**: Ensure all local IP addresses in `.env` are reachable.
- **Model Missing**: If Ollama fails to respond, verify the model is pulled (`ollama pull qwen3:14b`).
- **ComfyUI Verification**: Ensure the ACE Step safetensors are correctly loaded in your ComfyUI environment.
