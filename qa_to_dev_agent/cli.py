from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigError, load_llm_config
from .llm_client import LlmError, OpenAICompatibleClient
from .project_scan import scan_project
from .prompt_builder import build_messages, build_user_prompt


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        qa_input = _read_input(args)
        extra_docs = _read_optional_file(args.docs_file)
        context = scan_project(args.project, max_files=args.max_files)
        config = load_llm_config(args)

        if args.print_prompt:
            print(build_user_prompt(qa_input=qa_input, context=context, extra_docs=extra_docs))
            return 0

        messages = build_messages(qa_input=qa_input, context=context, extra_docs=extra_docs)
        result = OpenAICompatibleClient(config).complete(messages)
        print(result)
        return 0
    except (ConfigError, FileNotFoundError, NotADirectoryError, LlmError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qa-to-dev",
        description="Generate developer-ready task prompts from QA input.",
    )
    parser.add_argument("--project", required=True, help="Target project path to scan in read-only mode.")
    parser.add_argument("--input", help="QA change note text.")
    parser.add_argument("--input-file", help="Path to a file containing QA change notes.")
    parser.add_argument("--docs-file", help="Optional local document excerpt to include.")
    parser.add_argument("--max-files", type=int, default=80, help="Maximum files to include in lightweight tree scan.")
    parser.add_argument("--print-prompt", action="store_true", help="Print the LLM prompt without making a request.")
    parser.add_argument("--base-url", help="OpenAI-compatible base URL. Env: QADEV_LLM_BASE_URL.")
    parser.add_argument("--api-key", help="OpenAI-compatible API key. Env: QADEV_LLM_API_KEY.")
    parser.add_argument("--model", help="Model name for the configured provider. Env: QADEV_LLM_MODEL.")
    parser.add_argument("--http-referer", help="Optional HTTP-Referer header. Env: QADEV_LLM_HTTP_REFERER.")
    parser.add_argument("--app-title", help="Optional X-Title header. Env: QADEV_LLM_APP_TITLE.")
    return parser


def _read_input(args: argparse.Namespace) -> str:
    if bool(args.input) == bool(args.input_file):
        raise ValueError("Provide exactly one of --input or --input-file")
    if args.input:
        return args.input
    return _read_file(args.input_file)


def _read_optional_file(path: str | None) -> str | None:
    if not path:
        return None
    return _read_file(path)


def _read_file(path: str) -> str:
    return Path(path).expanduser().read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
