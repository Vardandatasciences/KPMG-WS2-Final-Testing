from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, *, model: str, temperature: float, timeout: int, retries: int) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_json(self, prompt: str, *, model: str, temperature: float, timeout: int, retries: int) -> Any:
        raise NotImplementedError

    @abstractmethod
    def embed(self, text: str, *, model: str | None = None, timeout: int = 60) -> list[float]:
        raise NotImplementedError
