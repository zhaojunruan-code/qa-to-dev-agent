from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import ConfigError, load_llm_config
from .documents import collect_supplemental_materials
from .issue_manager import create_issue
from .local_generator import generate_local_task
from .llm_client import LlmError, OpenAICompatibleClient
from .output import save_markdown_output
from .project_scan import scan_project
from .prompt_builder import build_messages, build_user_prompt


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        qa_input = _read_input(args)
        extra_docs = collect_supplemental_materials(
            paths=args.docs_file,
            urls=args.docs_url,
            timeout_seconds=args.docs_timeout,
        )
        context = scan_project(args.project, qa_input=qa_input, max_files=args.max_files)
        config = load_llm_config(args)

        if args.print_prompt:
            print(build_user_prompt(qa_input=qa_input, context=context, extra_docs=extra_docs))
            return 0

        if args.local_only:
            result = generate_local_task(qa_input=qa_input, context=context, extra_docs=extra_docs)
        else:
            messages = build_messages(qa_input=qa_input, context=context, extra_docs=extra_docs)
            result = OpenAICompatibleClient(config).complete(messages)

        saved_path = save_markdown_output(result, output_path=args.output, output_dir=args.output_dir)
        if args.create_issue:
            issue = create_issue(
                title=args.issue_title or "QA-to-Dev generated development task",
                body=result,
                docs_dir=args.issue_dir,
                mode=args.issue_mode,
                repository=args.issue_repository,
            )
            print(f"Issue backup: {issue.local_path}", file=sys.stderr)
            if issue.remote_url:
                print(f"Remote issue: {issue.remote_url}", file=sys.stderr)
            else:
                print(issue.note, file=sys.stderr)
        if saved_path:
            print(f"Saved output: {saved_path}", file=sys.stderr)
        print(result)
        return 0
    except (ConfigError, FileNotFoundError, NotADirectoryError, LlmError, OSError, ValueError) as exc:
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


def _read_input(args: argparse.Namespace) -> str:
    if bool(args.input) == bool(args.input_file):
        raise ValueError("Provide exactly one of --input or --input-file")
    value = args.input if args.input is not None else _read_file(args.input_file)
    if not value.strip():
        raise ValueError("Input cannot be empty")
    return value


def _read_file(path: str) -> str:
    return Path(path).expanduser().read_text(encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
