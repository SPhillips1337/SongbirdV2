# Patterns & Lessons

## Success Patterns (Anti-Gravity)

### 1. The Git Ratchet Protocol
- **Pattern**: Commit immediately after passing a logical unit of work and verifying it (e.g., PR #8 fixes, Narrative agent addition).
- **Result**: High velocity and clear recovery points. Reduces "Drag" when experimentation fails.

### 2. Multi-Agent Modularity (LangGraph)
- **Pattern**: Splitting logical domains into distinct agents (`Artist`, `Music`, `Lyrics`, `Narrative`).
- **Result**: Easier to debug and improve specific outputs (e.g., improving "street" quality in lyrics without affecting music BPM logic).

### 3. Bulk Operations in Database
- **Pattern**: Using bulk creates/updates (from PR #8 lesson).
- **Result**: Significant performance gains and reduced database contention.

---

## Failure Lessons (High Gravity)

### 1. Synchronous LLM Timeouts
- **Failure**: Ollama calls initially had short or default timeouts, causing crashes during heavy load.
- **Lesson**: Standardize long timeouts (e.g., 120s) and implement robust retry/fallback logic across all agent classes.

### 2026-03-13 - Local Perplexica timeouts caused by implicit provider defaults
- **Failure**: [`tools/perplexity.py`](tools/perplexity.py) posted only minimal search fields to Perplexica, allowing the remote instance to use its own default provider configuration.
- **Observation**: The Perplexica instance at `PERPLEXICA_URL` was reachable on its UI and [`/api/config`](tools/perplexity.py:18), but Songbird's `POST` to [`PerplexityClient._query_local()`](tools/perplexity.py:79) consistently timed out until the request explicitly specified Ollama-backed `chatModel`, `embeddingModel`, and `optimizationMode`.
- **Lesson**: Remote Perplexica calls must send explicit provider/model configuration instead of relying on server defaults, especially when the instance has multiple providers configured.

### 2. Remote ComfyUI SSL/Tunnel Friction
- **Failure**: Connecting to ComfyUI over Cloudflare tunnels often failed due to SSL validation errors of the ephemeral tunnel host.
- **Lesson**: Implement an explicit SSL bypass or custom verification logic when operating in tunnel-based developer environments.

### 3. Missing user_direction Weighting
- **Failure**: Agents initially ignored specific user CLI instructions in favor of genre defaults.
- **Lesson**: Explicitly inject and "boost" user instructions in the system prompts to ensure the AI follows the specific creative direction.
