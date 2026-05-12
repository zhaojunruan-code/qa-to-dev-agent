from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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


@dataclass(frozen=True)
class ProjectContext:
    root: Path
    file_count: int
    signals: list[str]
    sample_tree: list[str]

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
        return "\n".join(lines)


def scan_project(project_root: str, max_files: int = 80) -> ProjectContext:
    root = Path(project_root).expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project path does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {root}")

    files: list[Path] = []
    for current_root, dirs, names in os.walk(root):
        dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
        for name in names:
            relative = Path(current_root, name).relative_to(root)
            if any(part in IGNORED_DIRS for part in relative.parts):
                continue
            files.append(relative)
            if len(files) >= max_files:
                break
        if len(files) >= max_files:
            break

    signals = _detect_signals(root, files)
    sample_tree = [path.as_posix() for path in files[:max_files]]
    return ProjectContext(root=root, file_count=len(files), signals=signals, sample_tree=sample_tree)


def _detect_signals(root: Path, files: list[Path]) -> list[str]:
    file_set = {path.as_posix() for path in files}
    signals: list[str] = []
    for signal_path, description in SIGNAL_FILES.items():
        normalized = Path(signal_path).as_posix()
        if normalized in file_set or (root / signal_path).exists():
            signals.append(f"`{signal_path}`: {description}")
    return signals
