"""
LLM router for OpenAI ↔ Ollama with fallback support.
Primary/secondary is controlled via settings.USE_OPENAI.
"""
import json
import logging
from typing import List, Optional, Tuple

import requests
from django.conf import settings

try:  # OpenAI client is optional
    from openai import OpenAI
except Exception:
    OpenAI = None

logger = logging.getLogger(__name__)


MODEL_MAP = {
    "gpt-4o-mini": {
        "openai": "gpt-4o-mini",
        "ollama": getattr(settings, "OLLAMA_MODEL_PHI", "phi3:3.8b"),
    },
    "gpt-3.5-turbo": {
        "openai": "gpt-3.5-turbo",
        "ollama": getattr(settings, "OLLAMA_MODEL_LLAMA", "llama3.1:8b"),
    },
}


class LLMRouter:
    def __init__(self):
        self.use_openai_primary = getattr(settings, "USE_OPENAI", True)
        self.openai_api_key = getattr(settings, "OPENAI_API_KEY", "") or None
        self.openai_model_default = getattr(settings, "OPENAI_MODEL", "gpt-4o-mini")
        self.ollama_base_url = getattr(
            settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434"
        ).rstrip("/")
        self.ollama_embed_model = getattr(
            settings, "OLLAMA_EMBED_MODEL", "llama3.1:8b"
        )
        self._openai_client = None
        if self.openai_api_key and OpenAI is not None:
            try:
                self._openai_client = OpenAI(api_key=self.openai_api_key)
            except Exception as exc:  # pragma: no cover
                logger.warning("Failed to init OpenAI client: %s", exc)
                self._openai_client = None

    def _pick_models(self, preferred: str) -> Tuple[str, str]:
        mapping = MODEL_MAP.get(preferred) or MODEL_MAP.get(self.openai_model_default)
        if not mapping:
            # Fallback: use provided preferred for openai and phi for ollama
            return preferred, getattr(settings, "OLLAMA_MODEL_PHI", "phi3:3.8b")
        return mapping["openai"], mapping["ollama"]

    # ------------ Chat ------------
    def chat(
        self,
        messages: List[dict],
        preferred_model: Optional[str] = None,
        temperature: float = 0.2,
        response_format: Optional[dict] = None,
        timeout: int = 120,
    ) -> Tuple[str, str]:
        """
        Execute chat completion with automatic provider selection and fallback.
        Returns (content, provider) where provider is 'openai' or 'ollama'.
        """
        model_pref = preferred_model or self.openai_model_default
        openai_model, ollama_model = self._pick_models(model_pref)
        providers = ["openai", "ollama"] if self.use_openai_primary else ["ollama", "openai"]
        last_err = None

        for provider in providers:
            try:
                if provider == "openai":
                    content = self._chat_openai(
                        messages, openai_model, temperature, response_format, timeout
                    )
                else:
                    content = self._chat_ollama(
                        messages, ollama_model, temperature, timeout
                    )
                return content, provider
            except Exception as exc:  # pragma: no cover
                last_err = exc
                logger.warning("Provider %s failed: %s", provider, exc)
                continue
        raise RuntimeError(f"All providers failed: {last_err}")

    def _chat_openai(
        self,
        messages: List[dict],
        model: str,
        temperature: float,
        response_format: Optional[dict],
        timeout: int,
    ) -> str:
        if not self._openai_client or not self.openai_api_key:
            raise RuntimeError("OpenAI client not configured")
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format
        resp = self._openai_client.chat.completions.create(timeout=timeout, **kwargs)
        return resp.choices[0].message.content

    def _chat_ollama(
        self,
        messages: List[dict],
        model: str,
        temperature: float,
        timeout: int,
    ) -> str:
        url = f"{self.ollama_base_url}/api/chat"
        payload = {"model": model, "messages": messages, "options": {"temperature": temperature}}
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        # Ollama returns a streaming-like aggregate; content usually on "message"
        if "message" in data and isinstance(data["message"], dict):
            return data["message"].get("content", "")
        # Fallback if data is list of responses
        return data.get("response") or json.dumps(data)

    # ------------ Embeddings ------------
    def embed(self, text: str, preferred_model: Optional[str] = None, timeout: int = 60) -> List[float]:
        """
        Generate embeddings with provider fallback.
        """
        openai_model, ollama_model = self._pick_models(preferred_model or self.openai_model_default)
        providers = ["openai", "ollama"] if self.use_openai_primary else ["ollama", "openai"]
        last_err = None
        for provider in providers:
            try:
                if provider == "openai":
                    vec = self._embed_openai(text, openai_model, timeout)
                else:
                    vec = self._embed_ollama(text, ollama_model or self.ollama_embed_model, timeout)
                if vec:
                    return vec
            except Exception as exc:  # pragma: no cover
                last_err = exc
                logger.warning("Embedding via %s failed: %s", provider, exc)
                continue
        raise RuntimeError(f"Embedding failed: {last_err}")

    def _embed_openai(self, text: str, model: str, timeout: int) -> List[float]:
        if not self._openai_client or not self.openai_api_key:
            raise RuntimeError("OpenAI client not configured")
        resp = self._openai_client.embeddings.create(model=model, input=text, timeout=timeout)
        return resp.data[0].embedding

    def _embed_ollama(self, text: str, model: str, timeout: int) -> List[float]:
        url = f"{self.ollama_base_url}/api/embeddings"
        payload = {"model": model, "prompt": text}
        resp = requests.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding") or data.get("data") or []


# Singleton router helper
router = LLMRouter()


def chat_completion(messages: List[dict], preferred_model: Optional[str] = None, **kwargs) -> str:
    """Convenience wrapper returning only text."""
    content, _provider = router.chat(messages, preferred_model=preferred_model, **kwargs)
    return content


def embedding(text: str, preferred_model: Optional[str] = None, **kwargs) -> List[float]:
    return router.embed(text, preferred_model=preferred_model, **kwargs)







