from __future__ import annotations

import json
from urllib.error import URLError
from urllib.request import Request, urlopen


class OllamaProvider:
    def __init__(self, model: str, endpoint: str) -> None:
        self.model = model
        self.endpoint = endpoint.rstrip("/")

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
        }
        req = Request(
            url=f"{self.endpoint}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(req, timeout=30) as response:
                body = response.read().decode("utf-8")
        except URLError as exc:
            return f"AI request failed: {exc}. Run: opencourse ai status"
        except Exception as exc:  # noqa: BLE001
            return f"AI request failed: {exc}"

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            return "AI response parsing failed. Run: opencourse ai test"

        text = parsed.get("response", "").strip()
        if not text:
            return "AI returned an empty response. Run: opencourse ai test"
        return text
