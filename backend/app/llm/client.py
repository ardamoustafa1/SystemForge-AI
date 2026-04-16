import httpx

from app.core.config import get_settings


class LLMClientError(Exception):
    pass


async def create_structured_response(system_prompt: str, user_prompt: str) -> tuple[str, int]:
    """
    Calls an OpenAI-compatible Chat Completions API and returns the assistant message text (JSON string).
    Works with OpenAI, Groq, Together, Mistral (OpenAI mode), Ollama (/v1), and similar providers.
    """
    settings = get_settings()
    base = settings.openai_base_url.rstrip("/")
    url = f"{base}/chat/completions"
    request_body = {
        "model": settings.openai_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=settings.generation_timeout_seconds) as client:
        response = await client.post(url, headers=headers, json=request_body)
    if response.status_code >= 400:
        detail = response.text[:500]
        raise LLMClientError(f"LLM request failed with status {response.status_code}: {detail}")

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {}) if isinstance(data, dict) else {}
        total_tokens = int(
            usage.get("total_tokens")
            or ((usage.get("prompt_tokens") or 0) + (usage.get("completion_tokens") or 0))
            or 0
        )
        return content, total_tokens
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMClientError("LLM response format is invalid (expected choices[0].message.content)") from exc
