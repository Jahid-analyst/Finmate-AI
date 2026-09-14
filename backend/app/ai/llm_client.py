"""
Thin wrapper around an OpenAI-compatible chat completions endpoint.

Design principle (see master spec section 30/31/36):
- The rest of the app NEVER talks to the LLM directly.
- If no API key is configured, or the call fails/times out, this returns
  None so callers can fall back to deterministic logic. The core app must
  keep working without AI.
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger("finmate.ai")


def is_configured() -> bool:
    return settings.ai_enabled


def chat_completion(system_prompt: str, user_prompt: str, json_mode: bool = False, timeout: float = 12.0) -> str | None:
    """Returns the assistant's raw text, or None on any failure/misconfiguration."""
    if not is_configured():
        return None

    url = f"{settings.llm_base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": settings.llm_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, headers=headers, json=body)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as exc:  # network error, rate limit, malformed response, etc.
        logger.warning("LLM call failed, falling back to rule-based logic: %s", exc)
        return None


def chat_completion_json(system_prompt: str, user_prompt: str) -> dict | None:
    raw = chat_completion(system_prompt, user_prompt, json_mode=True)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("LLM returned non-JSON output, falling back to rule-based logic")
        return None
