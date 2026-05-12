from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
import tomllib


IGNORED_DIRS = {
    ".ace-tool",
    ".git",
    ".idea",
    ".venv",
    ".vscode",
    "__pycache__",
    "dist",
    "lib",
    "node_modules",
    "vendor",
}

SIGNAL_FILES = {
    "package.json": "Node.js or frontend project",
    "pnpm-lock.yaml": "pnpm package manager",
    "package-lock.json": "npm package manager",
    "yarn.lock": "Yarn package manager",
    "pyproject.toml": "Python project",
    "requirements.txt": "Python dependencies",
    "composer.json": "PHP project",
    "think": "ThinkPHP or FastAdmin command entry",
    "vite.config.ts": "Vite frontend",
    "vite.config.js": "Vite frontend",
    "src/main.ts": "frontend entry candidate",
    "src/main.js": "frontend entry candidate",
    "app/admin/controller": "FastAdmin admin controllers",
    "application/admin/controller": "ThinkPHP admin controllers",
}

SAFE_TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".php",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".vue",
    ".yaml",
    ".yml",
}

SENSITIVE_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".npmrc",
    ".pypirc",
}

COMMON_ENTRY_CANDIDATES = {
    "main.py",
    "app.py",
    "server.py",
    "src/main.ts",
    "src/main.js",
    "src/App.tsx",
    "src/App.jsx",
    "pages.json",
    "manifest.json",
    "application/admin/controller",
    "app/admin/controller",
}


@dataclass(frozen=True)
class ProjectContext:
    root: Path
    file_count: int
    signals: list[str]
    sample_tree: list[str]
    tech_stack: list[str]
    entry_files: list[str]
    build_scripts: list[str]
    test_scripts: list[str]
    key_code_locations: list[str]
    code_excerpts: list[str]

    def to_markdown(self) -> str:
        lines = [
            f"- Project root: `{self.root}`",
            f"- Scanned files: {self.file_count}",
        ]
        if self.signals:
            lines.append("- Detected signals:")
            lines.extend(f"  - {signal}" for signal in self.signals)
        else:
            lines.append("- Detected signals: none from the lightweight scanner")
        if self.sample_tree:
            lines.append("- Sample tree:")
            lines.extend(f"  - `{item}`" for item in self.sample_tree)
        if self.tech_stack:
            lines.append("- Technology stack:")
            lines.extend(f"  - {item}" for item in self.tech_stack)
        if self.entry_files:
            lines.append("- Entry files:")
            lines.extend(f"  - `{item}`" for item in self.entry_files)
        if self.build_scripts:
            lines.append("- Build scripts:")
            lines.extend(f"  - {item}" for item in self.build_scripts)
        if self.test_scripts:
            lines.append("- Test scripts:")
            lines.extend(f"  - {item}" for item in self.test_scripts)
        if self.key_code_locations:
            lines.append("- Requirement-related code candidates:")
            lines.extend(f"  - `{item}`" for item in self.key_code_locations)
        if self.code_excerpts:
            lines.append("- Safe code excerpts:")
            lines.extend(self.code_excerpts)
        return "\n".join(lines)


def scan_project(project_root: str, qa_input: str = "", max_files: int = 80, max_excerpt_chars: int = 1200) -> ProjectContext:
    root = Path(project_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {root}")

    files: list[Path] = []
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in names:
            if _is_sensitive_file_name(name):
                continue
            relative = Path(current_root, name).relative_to(root)
            if any(part in IGNORED_DIRS for part in relative.parts):
                continue
            files.append(relative)
            if len(files) >= max_files:
                break
        if len(files) >= max_files:
            break

    signals = _detect_signals(root, files)
    tech_stack, build_scripts, test_scripts = _detect_project_metadata(root)
    entry_files = _detect_entry_files(root, files)
    key_code_locations = _find_related_files(files, qa_input)
    code_excerpts = _read_safe_excerpts(root, entry_files + key_code_locations, max_excerpt_chars=max_excerpt_chars)
    sample_tree = [path.as_posix() for path in files[:max_files]]
    return ProjectContext(
        root=root,
        file_count=len(files),
        signals=signals,
        sample_tree=sample_tree,
        tech_stack=tech_stack,
        entry_files=entry_files,
        build_scripts=build_scripts,
        test_scripts=test_scripts,
        key_code_locations=key_code_locations,
        code_excerpts=code_excerpts,
    )


def _detect_signals(root: Path, files: list[Path]) -> list[str]:
    file_set = {path.as_posix() for path in files}
    signals: list[str] = []
    for signal_path, description in SIGNAL_FILES.items():
        normalized = Path(signal_path).as_posix()
        if normalized in file_set or (root / signal_path).exists():
            signals.append(f"`{signal_path}`: {description}")
    return signals


def _detect_project_metadata(root: Path) -> tuple[list[str], list[str], list[str]]:
    tech_stack: list[str] = []
    build_scripts: list[str] = []
    test_scripts: list[str] = []

    package_json = root / "package.json"
    if package_json.exists():
        tech_stack.append("Node.js")
        try:
            data = json.loads(package_json.read_text(encoding="utf-8-sig"))
            scripts = data.get("scripts", {})
            for name, command in scripts.items():
                item = f"`npm run {name}`: `{command}`"
                if "build" in name:
                    build_scripts.append(item)
                if "test" in name or name in {"lint", "check"}:
                    test_scripts.append(item)
        except (OSError, json.JSONDecodeError):
            tech_stack.append("Node.js metadata unreadable")

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        tech_stack.append("Python")
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            scripts = data.get("project", {}).get("scripts", {})
            for name, target in scripts.items():
                build_scripts.append(f"`{name}` console script: `{target}`")
        except (OSError, tomllib.TOMLDecodeError):
            tech_stack.append("Python metadata unreadable")

    if (root / "requirements.txt").exists():
        tech_stack.append("Python requirements.txt")
    if (root / "composer.json").exists():
        tech_stack.append("PHP Composer")
    if (root / "think").exists():
        tech_stack.append("ThinkPHP/FastAdmin candidate")
    if (root / "pnpm-lock.yaml").exists():
        tech_stack.append("pnpm")

    return tech_stack, build_scripts, test_scripts


def _detect_entry_files(root: Path, files: list[Path]) -> list[str]:
    file_set = {path.as_posix() for path in files}
    entries: list[str] = []
    for candidate in COMMON_ENTRY_CANDIDATES:
        if candidate in file_set or (root / candidate).exists():
            entries.append(candidate)
    return entries


def _find_related_files(files: list[Path], qa_input: str, limit: int = 8) -> list[str]:
    terms = _tokenize(qa_input)
    if not terms:
        return []

    scored: list[tuple[int, str]] = []
    for path in files:
        if not _is_safe_text_path(path):
            continue
        haystack = path.as_posix().lower()
        score = sum(1 for term in terms if term in haystack)
        if score:
            scored.append((score, path.as_posix()))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [path for _, path in scored[:limit]]


def _tokenize(text: str) -> list[str]:
    raw = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [part for part in raw.split() if len(part) >= 2][:20]


def _read_safe_excerpts(root: Path, paths: list[str], max_excerpt_chars: int) -> list[str]:
    excerpts: list[str] = []
    seen: set[str] = set()
    for path_text in paths:
        if path_text in seen:
            continue
        seen.add(path_text)
        relative = Path(path_text)
        if not _is_safe_text_path(relative):
            continue
        absolute = (root / relative).resolve()
        if not str(absolute).startswith(str(root)):
            continue
        if not absolute.exists() or not absolute.is_file():
            continue
        try:
            text = absolute.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        trimmed = text[:max_excerpt_chars].strip()
        if trimmed:
            excerpts.append(f"  - `{path_text}` excerpt:\n\n```text\n{trimmed}\n```")
    return excerpts


def _is_safe_text_path(path: Path) -> bool:
    if _is_sensitive_file_name(path.name):
        return False
    return path.suffix.lower() in SAFE_TEXT_SUFFIXES


def _is_sensitive_file_name(name: str) -> bool:
    return name in SENSITIVE_FILE_NAMES or name.startswith(".env")
