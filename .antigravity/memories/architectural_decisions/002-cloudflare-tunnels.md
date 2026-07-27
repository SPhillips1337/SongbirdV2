# ADR 002: Cloudflare Tunnels for Remote ComfyUI Access

## Context
Running high-performance audio generation workflows requires Nvidia GPUs with significant VRAM. Many developer machines lack these, necessitating a link to a remote server.

## Decision
Use **Cloudflare Tunnels** (`cloudflared`) to expose the remote ComfyUI instance's port securely without opening firewall ports.

## Status: Active

## Tradeoffs
- **Pros**: Dynamic IP handling, secure encryption, easy setup on Ubuntu/Linux servers.
- **Cons**: Introducing a network intermediary can lead to latency spikes or connection timeouts. SSL certificates are ephemeral/self-signed by the tunnel, causing validation friction.

## Consequences
- The `ComfyClient` must implement robust reconnection and timeout logic.
- SSL verification must be bypassed for internal tunnel domains (`trycloudflare.com`) to avoid "certificate unknown" errors.
