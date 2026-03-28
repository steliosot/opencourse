from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .base import AIProvider
from .config import OpenCourseAIConfig, default_config_path, load_config, save_config
from .disabled import DisabledAIProvider
from .ollama import OllamaProvider

DEFAULT_MODEL = "llama3.2:3b"
FALLBACK_MODEL = "llama3.2:1b"
OPTIONAL_MODEL = "phi4-mini"


class AIManager:
    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path or default_config_path()

    def load(self) -> OpenCourseAIConfig:
        return load_config(self.config_path)

    def save(self, config: OpenCourseAIConfig) -> Path:
        return save_config(config, self.config_path)

    def get_provider(self) -> AIProvider:
        config = self.load()
        if not config.ai.enabled:
            return DisabledAIProvider()
        if config.ai.provider != "ollama":
            return DisabledAIProvider()
        return OllamaProvider(model=config.ai.model, endpoint=config.ai.endpoint)

    @staticmethod
    def detect_os() -> str:
        return platform.system()

    @staticmethod
    def run_command(args: list[str]) -> tuple[bool, str, str]:
        try:
            result = subprocess.run(args, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            return False, "", "command not found"
        except Exception as exc:  # noqa: BLE001
            return False, "", str(exc)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

    def ollama_installed(self) -> bool:
        ok, _, _ = self.run_command(["ollama", "--version"])
        return ok

    def endpoint_ok(self, endpoint: str | None = None) -> bool:
        target = (endpoint or self.load().ai.endpoint).rstrip("/")
        try:
            with urlopen(f"{target}/api/tags", timeout=3) as response:
                return response.status == 200
        except URLError:
            return False
        except Exception:  # noqa: BLE001
            return False

    def list_models(self) -> list[str]:
        ok, stdout, _stderr = self.run_command(["ollama", "list"])
        if not ok:
            return []
        models: list[str] = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("name"):
                continue
            model = line.split()[0]
            models.append(model)
        return models

    def ensure_model(self, model: str) -> tuple[bool, str]:
        if model in self.list_models():
            return True, f"Model ready ({model})"
        ok, stdout, stderr = self.run_command(["ollama", "pull", model])
        if ok:
            return True, f"Model pulled ({model})"
        return False, stderr or stdout or f"Failed to pull model {model}"

    def test_inference(self, prompt: str = "Say hello in one sentence.") -> tuple[bool, str]:
        provider = self.get_provider()
        text = provider.generate(prompt)
        if not text or text.lower().startswith("ai not configured") or text.lower().startswith("ai request failed"):
            return False, text
        return True, text

    def enable_ollama(self, model: str = DEFAULT_MODEL, endpoint: str = "http://localhost:11434") -> Path:
        config = self.load()
        config.ai.enabled = True
        config.ai.provider = "ollama"
        config.ai.model = model
        config.ai.endpoint = endpoint
        return self.save(config)

    def disable_ai(self) -> Path:
        config = self.load()
        config.ai.enabled = False
        return self.save(config)

    def use_model(self, model: str) -> Path:
        config = self.load()
        config.ai.provider = "ollama"
        config.ai.model = model
        return self.save(config)

    def status(self) -> dict[str, str]:
        config = self.load()
        installed = "yes" if self.ollama_installed() else "no"
        connection = "OK" if self.endpoint_ok(config.ai.endpoint) else "FAIL"
        return {
            "enabled": "yes" if config.ai.enabled else "no",
            "provider": config.ai.provider,
            "model": config.ai.model,
            "endpoint": config.ai.endpoint,
            "connection": connection,
            "ollama_installed": installed,
        }

    def tags_json(self) -> dict:
        config = self.load()
        endpoint = config.ai.endpoint.rstrip("/")
        with urlopen(f"{endpoint}/api/tags", timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
