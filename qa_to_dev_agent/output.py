from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path


def save_markdown_output(content: str, output_path: str | None, output_dir: str | None) -> Path | None:
    if output_path:
        target = Path(output_path).expanduser().resolve()
    elif output_dir:
        directory = Path(output_dir).expanduser().resolve()
        target = directory / f"qa-to-dev-task-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.md"
    else:
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
