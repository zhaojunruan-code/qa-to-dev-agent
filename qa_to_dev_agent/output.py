from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .safety import ensure_not_inside_project


def save_markdown_output(
    content: str,
    output_path: str | None,
    output_dir: str | None,
    protected_project: str | Path | None = None,
) -> Path | None:
    if output_path:
        target = ensure_not_inside_project(Path(output_path), protected_project, "Markdown output")
    elif output_dir:
        directory = Path(output_dir).expanduser().resolve()
        target = ensure_not_inside_project(
            directory / f"qa-to-dev-task-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.md",
            protected_project,
            "Markdown output",
        )
    else:
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
