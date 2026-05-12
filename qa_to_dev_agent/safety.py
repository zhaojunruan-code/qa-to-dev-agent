from __future__ import annotations

from pathlib import Path


BLOCKED_READ_DIRS = {
    ".git",
    "__pycache__",
    "dependencies",
    "dependency",
    "dist",
    "generated",
    "lib",
    "node_modules",
    "vendor",
}


def validate_readable_user_file(path: str, purpose: str) -> Path:
    source = Path(path).expanduser().resolve()
    if _is_sensitive_file_name(source.name):
        raise ValueError(f"Refusing to read sensitive {purpose} file: {source}")
    blocked = next((part for part in source.parts if part.lower() in BLOCKED_READ_DIRS), None)
    if blocked:
        raise ValueError(f"Refusing to read {purpose} file from ignored directory `{blocked}`: {source}")
    return source


def ensure_not_inside_project(target: Path, project_root: str | Path | None, purpose: str) -> Path:
    resolved_target = target.expanduser().resolve()
    if not project_root:
        return resolved_target
    root = Path(project_root).expanduser().resolve()
    if resolved_target == root or _is_relative_to(resolved_target, root):
        raise ValueError(f"Refusing to write {purpose} inside target project: {resolved_target}")
    return resolved_target


def _is_sensitive_file_name(name: str) -> bool:
    return name.lower().startswith(".env")


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
