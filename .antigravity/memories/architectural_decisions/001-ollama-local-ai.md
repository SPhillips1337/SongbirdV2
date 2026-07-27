# ADR 001: Choosing Ollama for Local Hybrid AI

## Context
The project requires high-frequency LLM inference for persona generation, musical direction analysis, and narrative drafting. External API costs and latency for these smaller, frequent tasks were a concern.

## Decision
Utilize **Ollama** running locally (or on a dedicated local server) to host models like Llama3 or Mistral.

## Status: Active

## Tradeoffs
- **Pros**: Zero cost per token, offline capability, high privacy, low latency for small context windows.
- **Cons**: Requires local hardware (GPU), slower than large-scale provider APIs for very high-quant models.

## Consequences
- Every agent must have a configurable `base_url` for Ollama.
- Timeouts must be handled explicitly as local loads can spike.
