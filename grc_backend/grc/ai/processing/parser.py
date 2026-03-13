import json
import re
from typing import Any


class JSONResponseParser:
    @staticmethod
    def parse_json_block(text: str) -> Any:
        cleaned = re.sub(r"```json\s*", "", text or "", flags=re.I)
        cleaned = re.sub(r"```\s*", "", cleaned)
        cleaned = cleaned.strip()
        if not cleaned:
            raise RuntimeError("Empty AI response")

        match = re.search(r"(\[.*\]|\{.*\})", cleaned, flags=re.S)
        block = match.group(1) if match else cleaned
        block = re.sub(r",(\s*[}\]])", r"\1", block)

        try:
            return json.loads(block)
        except json.JSONDecodeError:
            block = re.sub(r"//.*?$", "", block, flags=re.M)
            block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
            block = re.sub(r",(\s*[}\]])", r"\1", block)
            try:
                return json.loads(block)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Failed to parse JSON response: {exc}") from exc


class SchemaValidator:
    @staticmethod
    def validate_or_repair(
        payload: Any,
        required_keys: list[str] | None = None,
        default_factory: type | None = None,
    ) -> Any:
        if payload is None and default_factory is not None:
            return default_factory()

        if required_keys and isinstance(payload, dict):
            for key in required_keys:
                payload.setdefault(key, None)
        return payload
