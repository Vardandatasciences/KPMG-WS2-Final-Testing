import json
import re
from typing import Any


class JSONResponseParser:
    @staticmethod
    def _extract_first_balanced_json(text: str) -> str:
        """
        Extract the first balanced JSON object/array from free-form model output.
        Handles prefixes/suffixes and ignores bracket-like chars inside strings.
        """
        if not text:
            return ""

        start = -1
        start_ch = ""
        for i, ch in enumerate(text):
            if ch in ("{", "["):
                start = i
                start_ch = ch
                break
        if start < 0:
            return text.strip()

        end_ch = "}" if start_ch == "{" else "]"
        depth = 0
        in_string = False
        escape = False

        for j in range(start, len(text)):
            ch = text[j]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
                continue

            if ch == '"':
                in_string = True
                continue
            if ch == start_ch:
                depth += 1
            elif ch == end_ch:
                depth -= 1
                if depth == 0:
                    return text[start:j + 1].strip()

        return text[start:].strip()

    @staticmethod
    def parse_json_block(text: str) -> Any:
        cleaned = (text or "").strip()
        if not cleaned:
            raise RuntimeError("Empty AI response")

        # Use balanced extraction instead of greedy regex to avoid "Extra data" errors
        # when model returns multiple JSON fragments or prose around JSON.
        block = JSONResponseParser._extract_first_balanced_json(cleaned)
        block = re.sub(r",(\s*[}\]])", r"\1", block)

        try:
            return json.loads(block)
        except json.JSONDecodeError as e1:
            print(f"[AI-PARSER] parse_json_block: first parse failed ({e1}), retrying with comments stripped")
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
