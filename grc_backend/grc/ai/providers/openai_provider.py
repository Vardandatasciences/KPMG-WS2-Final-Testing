import requests

from ..config import OPENAI_API_KEY, OPENAI_API_URL, OPENAI_MODEL
from ..processing.parser import JSONResponseParser
from .base import AIProvider


class OpenAIProvider(AIProvider):
    def __init__(self):
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        }

    def generate_text(self, prompt: str, *, model: str, temperature: float, timeout: int, retries: int) -> str:
        m = model or OPENAI_MODEL
        print(f"[AI-PROVIDER] OpenAI generate_text: model={m} prompt_len={len(prompt)}")
        payload = {
            "model": m,
            "messages": [
                {"role": "system", "content": "You are a GRC AI assistant. Follow the requested format exactly."},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
        }

        last_error = None
        for _ in range(max(retries, 1)):
            try:
                response = requests.post(OPENAI_API_URL, json=payload, headers=self._headers(), timeout=timeout)
                response.raise_for_status()
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"[AI-PROVIDER] OpenAI generate_text DONE: response_len={len(content)}")
                return content
            except Exception as exc:  # pragma: no cover
                last_error = exc
        raise RuntimeError(f"OpenAI request failed: {last_error}")

    def generate_json(self, prompt: str, *, model: str, temperature: float, timeout: int, retries: int):
        text = self.generate_text(prompt, model=model, temperature=temperature, timeout=timeout, retries=retries)
        return JSONResponseParser.parse_json_block(text)

    def embed(self, text: str, *, model: str | None = None, timeout: int = 60) -> list[float]:
        embed_model = model or "text-embedding-3-small"
        payload = {"model": embed_model, "input": text}
        response = requests.post(
            "https://api.openai.com/v1/embeddings",
            json=payload,
            headers=self._headers(),
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", [{}])[0].get("embedding", [])
