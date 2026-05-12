from __future__ import annotations

import argparse
import sys

from .config import load_llm_config
from .documents import collect_supplemental_materials
from .issue_manager import create_issue
from .local_generator import generate_local_task
from .llm_client import LlmError, OpenAICompatibleClient
from .output import save_markdown_output
from .project_scan import scan_project
from .prompt_builder import build_messages, build_user_prompt
from .safety import validate_readable_user_file


def run_batch(args: argparse.Namespace) -> int:
    qa_input = read_input(args)
    if not args.project:
        raise ValueError("Batch mode requires --project")
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

    saved_path = save_markdown_output(
        result,
        output_path=args.output,
        output_dir=args.output_dir,
        protected_project=args.project,
    )
    if args.create_issue:
        issue = create_issue(
            title=args.issue_title or "QA-to-Dev generated development task",
            body=result,
            docs_dir=args.issue_dir,
            mode=args.issue_mode,
            repository=args.issue_repository,
            protected_project=args.project,
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


def read_input(args: argparse.Namespace) -> str:
    if bool(args.input) == bool(args.input_file):
        raise ValueError("Provide exactly one of --input or --input-file")
    value = args.input if args.input is not None else read_file(args.input_file)
    if not value.strip():
        raise ValueError("Input cannot be empty")
    return value


def read_file(path: str) -> str:
    return validate_readable_user_file(path, "input").read_text(encoding="utf-8")
