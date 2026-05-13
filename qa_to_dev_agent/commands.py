from __future__ import annotations

import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class Command:
    name: str
    args: list[str]


HELP_TEXT = """Commands:
  /help
  /status
  /project <path>
  /input [text]
  /input-file <path>
  /docs add-file <path>
  /docs add-url <url>
  /docs list
  /docs remove <index>
  /scan [--max-files N]
  /context
  /questions
  /answer <question-id> <answer>
  /preview prompt
  /preview task
  /generate --local
  /generate --llm
  /save <path>
  /issue local
  /issue remote --repo owner/name
  /reset
  /exit

Plain text is appended to the QA input draft.
"""


def parse_command(line: str) -> Command | None:
    stripped = line.strip()
    if not stripped.startswith("/"):
        return None
    body = stripped[1:].strip()
    if not body:
        return Command(name="", args=[])
    if " " not in body:
        return Command(name=body.lower(), args=[])
    name, rest = body.split(maxsplit=1)
    lower_name = name.lower()
    if lower_name in {"project", "input-file", "save", "input"}:
        return Command(name=lower_name, args=[rest])
    if lower_name == "docs":
        if rest.startswith("add-file "):
            return Command(name=lower_name, args=["add-file", rest[len("add-file "):]])
        if rest.startswith("add-url "):
            return Command(name=lower_name, args=["add-url", rest[len("add-url "):]])
    return Command(name=lower_name, args=shlex.split(rest, posix=False))
