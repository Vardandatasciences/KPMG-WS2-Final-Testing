import json


class ErrorResponseSanitizationMiddleware:
    """
    Framework-level safeguard to prevent verbose internals from leaking
    in JSON error responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return self._sanitize_response(response)

    def _sanitize_response(self, response):
        status_code = getattr(response, "status_code", 200)
        if status_code < 400:
            return response

        if getattr(response, "streaming", False):
            return response

        content_type = (response.get("Content-Type", "") or "").lower()
        if "application/json" not in content_type:
            return response

        try:
            charset = getattr(response, "charset", None) or "utf-8"
            payload = json.loads(response.content.decode(charset))
        except Exception:
            return response

        sanitized = self._sanitize_payload(payload, status_code)
        if sanitized == payload:
            return response

        encoded = json.dumps(sanitized, ensure_ascii=False).encode("utf-8")
        response.content = encoded
        response["Content-Length"] = str(len(encoded))
        return response

    def _sanitize_payload(self, value, status_code):
        if isinstance(value, dict):
            output = {}
            for key, item in value.items():
                key_l = str(key).lower()
                if key_l in {"traceback", "stack", "stacktrace", "exception", "exception_message"}:
                    continue

                if key_l == "details" and status_code >= 500:
                    output[key] = "Internal server error"
                    continue

                output[key] = self._sanitize_payload(item, status_code)
            return output

        if isinstance(value, list):
            return [self._sanitize_payload(item, status_code) for item in value]

        if isinstance(value, str) and status_code >= 500:
            if "traceback (most recent call last)" in value.lower():
                return "Internal server error"

        return value
