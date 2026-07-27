"""Small LLM transport adapter for Ollama and OpenAI-compatible servers."""

import os

import requests


def _base_url():
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def _is_openai_compatible():
    mode = os.getenv("LLM_API_MODE", "auto").lower()
    if mode in {"openai", "openai-compatible", "openai_compatible"}:
        return True
    if mode == "ollama":
        return False
    base = _base_url()
    return base.endswith("/v1") or ":1234" in base


def generate_text(model, prompt, timeout=60, temperature=None, json_mode=False):
    """Generate text through the configured Ollama or OpenAI-compatible API."""
    if _is_openai_compatible():
        url = f"{_base_url().removesuffix('/v1')}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        response = requests.post(url, json=payload, timeout=timeout)
        if response.status_code == 400 and json_mode and "response_format" in payload:
            payload.pop("response_format")
            response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        choice = response.json().get("choices", [{}])[0]
        message = choice.get("message", {})
        return (message.get("content") or "").strip()

    payload = {"model": model, "prompt": prompt, "stream": False}
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    if json_mode:
        payload["format"] = "json"
    response = requests.post(f"{_base_url()}/api/generate", json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json().get("response", "").strip()
