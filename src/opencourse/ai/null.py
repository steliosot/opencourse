from __future__ import annotations


class NullAIProvider:
    def answer(self, question: str, context: str | None = None) -> str:
        _ = question, context
        return (
            "AI help is optional and currently not configured. "
            "Use deterministic commands like quiz, lab, and test to continue learning."
        )
