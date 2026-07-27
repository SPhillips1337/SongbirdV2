# Codebase Insight: ComfyUI Integration

## Hidden Knowledge: Why This Exists?
The `ComfyClient` in `tools/comfy.py` (and relevant wrappers) handles the synthesis of audio using remote ComfyUI workers. It exists because high-fidelity audio generation (e.g., stable-audio-1.5) is too heavy for most local developer machines and benefits from remote high-VRAM acceleration.

## Critical Dependencies
- **Cloudflare Tunnels**: Often used to bridge local agents to remote GPU instances.
- **KSampler Parameters**: Specific settings for `cfg`, `steps`, and `denoise` are tuned to prevent "underwater" audio artifacts.

## Non-Obvious Logic
- **SSL Bypass**: The client includes a mechanism to bypass SSL verification when connecting to `trycloudflare.com` domains to handle ephemeral certificate issues common in dev tunnels.
- **ACE Step Audio 1.5**: The integration is specifically tailored for this model, requiring a very particular JSON payload structure for lyrics-to-audio sync.
