from __future__ import annotations

import argparse
import sys

from .config import ConfigError
from .interactive import run_interactive
from .llm_client import LlmError
from .runner import run_batch


def main(argv: list[str] | None = None) -> int:
    _configure_console_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.interactive:
            return run_interactive(args)
        return run_batch(args)
    except (ConfigError, FileNotFoundError, NotADirectoryError, LlmError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qa-to-dev",
        description="Generate developer-ready task prompts from QA input.",
    )
    parser.add_argument("--interactive", "-i", action="store_true", help="Start terminal interactive mode.")
    parser.add_argument("--project", help="Target project path to scan in read-only mode.")
    parser.add_argument("--input", help="QA change note text.")
    parser.add_argument("--input-file", help="Path to a file containing QA change notes.")
    parser.add_argument("--docs-file", action="append", default=[], help="Optional local document excerpt to include. Can be repeated.")
    parser.add_argument("--docs-url", action="append", default=[], help="Optional document URL to fetch and include. Can be repeated.")
    parser.add_argument("--docs-timeout", type=int, default=15, help="Timeout in seconds for each document URL fetch.")
    parser.add_argument("--max-files", type=int, default=80, help="Maximum files to include in lightweight tree scan.")
    parser.add_argument("--print-prompt", action="store_true", help="Print the LLM prompt without making a request.")
    parser.add_argument("--local-only", action="store_true", help="Generate a local structured task without calling an LLM.")
    parser.add_argument("--output", help="Save generated Markdown to this file.")
    parser.add_argument("--output-dir", help="Save generated Markdown into this directory with a timestamped name.")
    parser.add_argument("--create-issue", action="store_true", help="Create an issue from the generated task.")
    parser.add_argument("--issue-mode", choices=["local", "auto", "remote"], default="local", help="Issue creation mode.")
    parser.add_argument("--issue-dir", default="docs/issues", help="Directory for local issue Markdown backups.")
    parser.add_argument("--issue-title", help="Title to use when creating an issue.")
    parser.add_argument("--issue-repository", help="Repository in owner/name form for remote issue creation.")
    parser.add_argument("--base-url", help="OpenAI-compatible base URL. Env: QADEV_LLM_BASE_URL.")
    parser.add_argument("--api-key", help="OpenAI-compatible API key. Env: QADEV_LLM_API_KEY.")
    parser.add_argument("--model", help="Model name for the configured provider. Env: QADEV_LLM_MODEL.")
    parser.add_argument("--http-referer", help="Optional HTTP-Referer header. Env: QADEV_LLM_HTTP_REFERER.")
    parser.add_argument("--app-title", help="Optional X-Title header. Env: QADEV_LLM_APP_TITLE.")
    return parser


def _configure_console_encoding() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    raise SystemExit(main())
