import requests

from ..config import OLLAMA_BASE_URL, OLLAMA_SEED
from ..processing.parser import JSONResponseParser
from .base import AIProvider


class OllamaProvider(AIProvider):
    def generate_text(self, prompt: str, *, model: str, temperature: float, timeout: int, retries: int) -> str:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2000,
                "seed": OLLAMA_SEED,
                "repeat_penalty": 1.1,
            },
        }

        last_error = None
        for _ in range(max(retries, 1)):
            try:
                response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "")
            except Exception as exc:  # pragma: no cover
                last_error = exc
        raise RuntimeError(f"Ollama request failed: {last_error}")

    def generate_json(self, prompt: str, *, model: str, temperature: float, timeout: int, retries: int):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": 40,
                "num_predict": 2000,
                "seed": OLLAMA_SEED,
                "repeat_penalty": 1.1,
            },
        }

        last_error = None
        for _ in range(max(retries, 1)):
            try:
                response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                return JSONResponseParser.parse_json_block(data.get("response", ""))
            except Exception as exc:  # pragma: no cover
                last_error = exc
        raise RuntimeError(f"Ollama JSON request failed: {last_error}")

    def embed(self, text: str, *, model: str | None = None, timeout: int = 60) -> list[float]:
        payload = {"model": model, "prompt": text}
        response = requests.post(f"{OLLAMA_BASE_URL}/api/embeddings", json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        return data.get("embedding") or data.get("data") or []
