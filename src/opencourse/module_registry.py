from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .config import OpenCourseConfig


class ModuleManifest(BaseModel):
    id: str
    title: str
    version: str
    spec_version: str
    entry_coursepack: str
    openclaw_compatible: bool = True


class RegisteredModule(BaseModel):
    id: str
    git_url: str
    ref: str = "main"
    resolved_commit: str
    local_path: Path
    local_coursepack_path: Path
    title: str
    spec_version: str


class ModuleRegistryData(BaseModel):
    modules: dict[str, RegisteredModule] = Field(default_factory=dict)


class ModuleRegistry:
    def __init__(self, config: OpenCourseConfig | None = None) -> None:
        self.config = config or OpenCourseConfig()
        self.config.ensure_dirs()
        self.root = self.config.user_home / "modules"
        self.repos_dir = self.root / "repos"
        self.registry_file = self.root / "registry.yaml"
        self.root.mkdir(parents=True, exist_ok=True)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> ModuleRegistryData:
        if not self.registry_file.exists():
            return ModuleRegistryData()
        data = yaml.safe_load(self.registry_file.read_text(encoding="utf-8")) or {}
        return ModuleRegistryData.model_validate(data)

    def save(self, data: ModuleRegistryData) -> None:
        payload = data.model_dump(mode="json")
        self.registry_file.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")

    def list(self) -> dict[str, RegisteredModule]:
        return self.load().modules

    def add(self, git_url: str, ref: str = "main") -> RegisteredModule:
        repo_dir = self.repos_dir / _repo_slug(git_url)
        if not repo_dir.exists():
            _run(["git", "clone", git_url, str(repo_dir)])
        else:
            _run(["git", "-C", str(repo_dir), "fetch", "--all", "--tags"])

        _run(["git", "-C", str(repo_dir), "checkout", ref])
        _run(["git", "-C", str(repo_dir), "pull", "--ff-only"], allow_fail=True)

        manifest = validate_module_repo(repo_dir)
        resolved_commit = _capture(["git", "-C", str(repo_dir), "rev-parse", "HEAD"]).strip()
        coursepack_path = repo_dir / "coursepacks" / manifest.entry_coursepack

        entry = RegisteredModule(
            id=manifest.id,
            git_url=git_url,
            ref=ref,
            resolved_commit=resolved_commit,
            local_path=repo_dir,
            local_coursepack_path=coursepack_path,
            title=manifest.title,
            spec_version=manifest.spec_version,
        )

        data = self.load()
        data.modules[entry.id] = entry
        self.save(data)
        return entry

    def update(self, module_id: str) -> RegisteredModule:
        data = self.load()
        if module_id not in data.modules:
            raise ValueError(f"Unknown module: {module_id}")
        entry = data.modules[module_id]
        _run(["git", "-C", str(entry.local_path), "fetch", "--all", "--tags"])
        _run(["git", "-C", str(entry.local_path), "checkout", entry.ref])
        _run(["git", "-C", str(entry.local_path), "pull", "--ff-only"], allow_fail=True)

        manifest = validate_module_repo(entry.local_path)
        resolved_commit = _capture(["git", "-C", str(entry.local_path), "rev-parse", "HEAD"]).strip()
        entry.title = manifest.title
        entry.spec_version = manifest.spec_version
        entry.resolved_commit = resolved_commit
        entry.local_coursepack_path = entry.local_path / "coursepacks" / manifest.entry_coursepack
        data.modules[module_id] = entry
        self.save(data)
        return entry

    def update_all(self) -> dict[str, RegisteredModule]:
        updated: dict[str, RegisteredModule] = {}
        for module_id in list(self.load().modules.keys()):
            updated[module_id] = self.update(module_id)
        return updated

    def remove(self, module_id: str) -> None:
        data = self.load()
        if module_id not in data.modules:
            raise ValueError(f"Unknown module: {module_id}")
        entry = data.modules.pop(module_id)
        self.save(data)
        if entry.local_path.exists():
            shutil.rmtree(entry.local_path)

    def sync(self) -> dict[str, str]:
        out: dict[str, str] = {}
        data = self.load()
        for module_id, entry in data.modules.items():
            if not entry.local_path.exists():
                out[module_id] = "missing local clone"
                continue
            _run(["git", "-C", str(entry.local_path), "checkout", entry.resolved_commit], allow_fail=True)
            out[module_id] = entry.resolved_commit
        return out

    def doctor(self, module_id: str) -> list[str]:
        data = self.load()
        if module_id not in data.modules:
            return [f"Unknown module: {module_id}"]
        entry = data.modules[module_id]
        errors: list[str] = []
        if not entry.local_path.exists():
            errors.append(f"Missing local path: {entry.local_path}")
            return errors
        try:
            validate_module_repo(entry.local_path)
        except ValueError as exc:
            errors.append(str(exc))
        if not entry.local_coursepack_path.exists():
            errors.append(f"Missing coursepack path: {entry.local_coursepack_path}")
        return errors


def validate_module_repo(repo_path: Path) -> ModuleManifest:
    manifest_file = repo_path / "opencourse-module.yaml"
    if not manifest_file.exists():
        raise ValueError(f"Missing opencourse-module.yaml in {repo_path}")

    manifest_data = yaml.safe_load(manifest_file.read_text(encoding="utf-8")) or {}
    manifest = ModuleManifest.model_validate(manifest_data)

    if not manifest.openclaw_compatible:
        raise ValueError("openclaw_compatible must be true")

    coursepack_root = repo_path / "coursepacks" / manifest.entry_coursepack
    if not coursepack_root.exists():
        raise ValueError(f"Missing entry coursepack: {coursepack_root}")

    required = [
        coursepack_root / "course.yaml",
        coursepack_root / "weeks",
        coursepack_root / "skills",
    ]
    for path in required:
        if not path.exists():
            raise ValueError(f"Missing required path: {path}")

    return manifest


def _repo_slug(git_url: str) -> str:
    url = git_url.rstrip("/")
    name = url.split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    return name


def _run(args: list[str], allow_fail: bool = False) -> None:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0 and not allow_fail:
        err = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{err}")


def _capture(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        err = result.stderr.strip() or result.stdout.strip() or "unknown error"
        raise RuntimeError(f"Command failed: {' '.join(args)}\n{err}")
    return result.stdout
