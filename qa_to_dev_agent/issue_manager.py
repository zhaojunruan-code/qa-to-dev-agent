from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


ISSUE_TEMPLATE = """# {title}

## 背景

{background}

## 目标

{goal}

## 范围

{scope}

## 具体任务

{tasks}

## 验收标准

{acceptance}

## 风险点

{risks}

## 待确认问题

{questions}
"""


@dataclass(frozen=True)
class IssueResult:
    local_path: Path
    remote_url: str | None
    note: str


def write_local_issue(
    docs_dir: str,
    title: str,
    body: str,
    slug: str | None = None,
) -> Path:
    target_dir = Path(docs_dir).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{slug or _slugify(title)}.md"
    target = target_dir / filename
    target.write_text(body, encoding="utf-8")
    return target


def create_issue(
    title: str,
    body: str,
    docs_dir: str,
    slug: str | None = None,
    mode: str = "local",
    repository: str | None = None,
) -> IssueResult:
    local_path = write_local_issue(docs_dir=docs_dir, title=title, body=body, slug=slug)
    if mode == "local":
        return IssueResult(local_path=local_path, remote_url=None, note="Created local Markdown issue only.")
    if mode not in {"auto", "remote"}:
        return IssueResult(local_path=local_path, remote_url=None, note=f"Unknown issue mode `{mode}`; kept local Markdown issue.")

    remote = _create_remote_issue(title=title, body=body, repository=repository)
    if remote:
        return IssueResult(local_path=local_path, remote_url=remote, note="Created remote issue and local Markdown backup.")
    return IssueResult(local_path=local_path, remote_url=None, note="Remote issue creation unavailable; kept local Markdown issue.")


def _create_remote_issue(title: str, body: str, repository: str | None) -> str | None:
    if shutil.which("gh") and repository:
        command = ["gh", "issue", "create", "--repo", repository, "--title", title, "--body", body]
        return _run_issue_command(command)
    if shutil.which("glab") and repository:
        command = ["glab", "issue", "create", "--repo", repository, "--title", title, "--description", body]
        return _run_issue_command(command)
    return None


def _run_issue_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=60)
    except (subprocess.SubprocessError, OSError):
        return None
    output = completed.stdout.strip()
    return output.splitlines()[-1] if output else None


def _slugify(title: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in title)
    compact = "-".join(part for part in safe.split("-") if part)
    prefix = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{compact[:60] or 'issue'}"
