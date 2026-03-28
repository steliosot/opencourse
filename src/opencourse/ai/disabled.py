from __future__ import annotations


class DisabledAIProvider:
    def generate(self, prompt: str) -> str:
        _ = prompt
        return "AI not configured. Run: opencourse setup-ai"
