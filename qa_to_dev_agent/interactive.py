from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from .commands import HELP_TEXT, Command, parse_command
from .confirm import confirm_phrase, confirm_typed, confirm_yes_no
from .config import ConfigError, load_llm_config
from .documents import collect_supplemental_materials
from .issue_manager import create_issue
from .llm_client import LlmError, OpenAICompatibleClient
from .local_generator import generate_local_task
from .output import save_markdown_output
from .project_scan import scan_project
from .prompt_builder import build_messages, build_user_prompt
from .questions import answered_questions_block, generate_pending_questions
from .runner import read_file
from .session import InteractiveSessionState


InputFunc = Callable[[str], str]


def handle_interactive_line(
    state: InteractiveSessionState,
    args: argparse.Namespace,
    line: str,
    input_func: InputFunc = input,
    output_func=print,
) -> bool:
    command = parse_command(line)
    if command is None:
        state.append_input(line)
        output_func(f"appended QA input ({len(state.qa_input)} chars)")
        return False
    return _handle_command_for_tests(command, state, args, input_func, output_func)


def _handle_command_for_tests(
    command: Command,
    state: InteractiveSessionState,
    args: argparse.Namespace,
    input_func: InputFunc,
    output_func,
) -> bool:
    name = command.name
    if name in {"exit", "quit"}:
        output_func("bye")
        return True
    if name == "project":
        _require_args(command, 1, "/project <path>")
        state.set_project(" ".join(command.args))
        output_func(f"project set: {state.project_path}")
    elif name == "scan":
        _handle_scan(command.args, state, _OutputAdapter(output_func))
        output_func("scanned")
    elif name == "generate":
        _ensure_project_input_and_scan_for_test(state)
        mode = "--local" if not command.args else command.args[0]
        if mode == "--local":
            state.mark_generated(generate_local_task(state.qa_input, state.project_context, state.supplemental_materials))
            output_func(state.generated_task)
        elif mode == "--llm":
            if not confirm_typed("Request configured LLM provider?", "yes", input_func, output_func):
                output_func("cancelled")
                return False
            config = load_llm_config(args)
            messages = build_messages(state.qa_input, state.project_context, state.supplemental_materials)
            state.mark_generated(OpenAICompatibleClient(config).complete(messages))
            output_func(state.generated_task)
        else:
            raise ValueError("Usage: /generate --local|--llm")
    else:
        return handle_command(command, state, args, input_func, _OutputAdapter(output_func))
    return False


class _OutputAdapter:
    def __init__(self, output_func) -> None:
        self._output_func = output_func

    def write(self, text: str) -> int:
        stripped = text.rstrip("\n")
        if stripped:
            self._output_func(stripped)
        return len(text)

    def flush(self) -> None:
        return None


def _ensure_project_input_and_scan_for_test(state: InteractiveSessionState) -> None:
    if not state.project_context:
        _require_project_and_input(state)
        state.supplemental_materials = collect_supplemental_materials(
            paths=[str(path) for path in state.docs_files],
            urls=state.docs_urls,
            timeout_seconds=state.docs_timeout,
        )
        state.project_context = scan_project(str(state.project_path), qa_input=state.qa_input, max_files=state.max_files)
        generate_pending_questions(state)


def run_interactive(
    args: argparse.Namespace,
    input_func: InputFunc | None = None,
    output: TextIO | None = None,
    error: TextIO | None = None,
) -> int:
    input_func = input_func or input
    output = output or sys.stdout
    error = error or sys.stderr
    state = InteractiveSessionState(
        docs_timeout=args.docs_timeout,
        max_files=args.max_files,
        local_only=args.local_only,
        issue_repository=args.issue_repository,
    )
    if args.project:
        state.set_project(args.project)
    if args.input:
        state.append_input(args.input)
    if args.input_file:
        state.append_input(read_file(args.input_file))
    for path in args.docs_file:
        state.add_doc_file(path)
    for url in args.docs_url:
        state.add_doc_url(url)

    print_welcome(state, output)
    while True:
        try:
            line = input_func("qa-to-dev> ")
        except EOFError:
            print("bye", file=output)
            return 0
        if not line.strip():
            continue
        command = parse_command(line)
        try:
            if command is None:
                state.append_input(line)
                print(f"Added QA input. Total: {len(state.qa_input)} chars", file=output)
                continue
            if handle_command(command, state, args, input_func, output):
                return 0
        except (ConfigError, FileNotFoundError, NotADirectoryError, LlmError, OSError, ValueError) as exc:
            print(f"error: {exc}", file=error)
    return 0


def print_welcome(state: InteractiveSessionState, output: TextIO) -> None:
    print("QA-to-Dev Prompt Agent Interactive", file=output)
    print("", file=output)
    print("Mode: read-only analysis", file=output)
    print(f"Target project: {state.project_path if state.project_path else 'not selected'}", file=output)
    print(f"Input: {len(state.qa_input)} chars", file=output)
    print(f"Docs: {len(state.docs_files)} files, {len(state.docs_urls)} URLs", file=output)
    print("Type /help for commands. Paste text directly to add QA input.", file=output)


def handle_command(
    command: Command,
    state: InteractiveSessionState,
    args: argparse.Namespace,
    input_func: InputFunc,
    output: TextIO,
) -> bool:
    name = command.name
    if name in {"exit", "quit"}:
        print("bye", file=output)
        return True
    if name == "help" or name == "":
        print(HELP_TEXT, file=output)
    elif name == "status":
        print("\n".join(state.status_lines()), file=output)
    elif name == "project":
        _require_args(command, 1, "/project <path>")
        state.set_project(" ".join(command.args))
        print(f"Project set: {state.project_path}", file=output)
    elif name == "input":
        if command.args:
            state.append_input(" ".join(command.args))
        else:
            _read_multiline_input(state, input_func, output)
        print(f"QA input: {len(state.qa_input)} chars", file=output)
    elif name == "input-file":
        _require_args(command, 1, "/input-file <path>")
        state.append_input(read_file(" ".join(command.args)))
        print(f"QA input: {len(state.qa_input)} chars", file=output)
    elif name == "docs":
        _handle_docs(command.args, state, output)
    elif name == "scan":
        _handle_scan(command.args, state, output)
    elif name == "context":
        _require_context(state)
        print(state.project_context.to_markdown(), file=output)
    elif name == "questions":
        _handle_questions(state, output)
    elif name == "answer":
        _require_args(command, 2, "/answer <question-id> <answer>")
        state.answered_questions[command.args[0]] = " ".join(command.args[1:])
        print(f"Recorded answer for {command.args[0]}", file=output)
    elif name == "preview":
        _handle_preview(command.args, state, output)
    elif name == "generate":
        _handle_generate(command.args, state, args, input_func, output)
    elif name == "save":
        _require_args(command, 1, "/save <path>")
        _require_generated(state)
        target = " ".join(command.args)
        if confirm_yes_no(f"Save Markdown to {target}?", input_func, output):
            saved = save_markdown_output(
                state.generated_task or "",
                output_path=target,
                output_dir=None,
                protected_project=state.project_path,
            )
            state.output_path = saved
            print(f"Saved output: {saved}", file=output)
        else:
            print("Save cancelled.", file=output)
    elif name == "issue":
        _handle_issue(command.args, state, args, input_func, output)
    elif name == "reset":
        if confirm_yes_no("Reset current session?", input_func, output):
            state.reset()
            print("Session reset.", file=output)
    else:
        print(f"Unknown command: /{name}. Type /help.", file=output)
    return False


def _read_multiline_input(state: InteractiveSessionState, input_func: InputFunc, output: TextIO) -> None:
    print("Enter QA input. Use /done to finish or /cancel to cancel.", file=output)
    lines: list[str] = []
    while True:
        line = input_func("")
        if line.strip() == "/done":
            state.append_input("\n".join(lines))
            return
        if line.strip() == "/cancel":
            return
        lines.append(line)


def _handle_docs(args: list[str], state: InteractiveSessionState, output: TextIO) -> None:
    _require_args(Command("docs", args), 1, "/docs add-file|add-url|list|remove")
    action = args[0]
    if action == "add-file":
        if len(args) < 2:
            raise ValueError("Usage: /docs add-file <path>")
        state.add_doc_file(" ".join(args[1:]))
        print(f"Added doc file: {state.docs_files[-1]}", file=output)
    elif action == "add-url":
        if len(args) < 2:
            raise ValueError("Usage: /docs add-url <url>")
        state.add_doc_url(args[1])
        print(f"Added doc URL: {state.docs_urls[-1]}", file=output)
    elif action == "list":
        if not state.docs_files and not state.docs_urls:
            print("No docs added.", file=output)
            return
        index = 1
        for path in state.docs_files:
            print(f"{index}. file {path}", file=output)
            index += 1
        for url in state.docs_urls:
            print(f"{index}. url {url}", file=output)
            index += 1
    elif action == "remove":
        if len(args) != 2:
            raise ValueError("Usage: /docs remove <index>")
        removed = state.remove_doc(int(args[1]))
        print(f"Removed doc: {removed}", file=output)
    else:
        raise ValueError("Usage: /docs add-file|add-url|list|remove")


def _handle_scan(args: list[str], state: InteractiveSessionState, output: TextIO) -> None:
    _require_project_and_input(state)
    max_files = state.max_files
    if args:
        if len(args) != 2 or args[0] != "--max-files":
            raise ValueError("Usage: /scan [--max-files N]")
        max_files = int(args[1])
        state.max_files = max_files
    state.supplemental_materials = collect_supplemental_materials(
        paths=[str(path) for path in state.docs_files],
        urls=state.docs_urls,
        timeout_seconds=state.docs_timeout,
    )
    state.project_context = scan_project(str(state.project_path), qa_input=state.qa_input, max_files=max_files)
    generate_pending_questions(state)
    print("Scan Result", file=output)
    print(state.project_context.to_markdown(), file=output)


def _handle_questions(state: InteractiveSessionState, output: TextIO) -> None:
    if not state.pending_questions:
        generate_pending_questions(state)
    if not state.pending_questions:
        print("No pending questions.", file=output)
        return
    for question in state.pending_questions:
        answer = state.answered_questions.get(question.question_id)
        suffix = f" Answer: {answer}" if answer else ""
        print(f"{question.question_id}: {question.text}{suffix}", file=output)


def _handle_preview(args: list[str], state: InteractiveSessionState, output: TextIO) -> None:
    _require_args(Command("preview", args), 1, "/preview prompt|task")
    _ensure_scanned(state)
    if args[0] == "prompt":
        prompt = build_user_prompt(state.qa_input, state.project_context, _extra_docs_with_answers(state))
        state.generated_prompt = prompt
        print(prompt, file=output)
    elif args[0] == "task":
        print(generate_local_task(state.qa_input, state.project_context, _extra_docs_with_answers(state)), file=output)
    else:
        raise ValueError("Usage: /preview prompt|task")


def _handle_generate(
    args_list: list[str],
    state: InteractiveSessionState,
    cli_args: argparse.Namespace,
    input_func: InputFunc,
    output: TextIO,
) -> None:
    _ensure_scanned(state)
    mode = "--local" if not args_list else args_list[0]
    if mode == "--local":
        state.mark_generated(generate_local_task(state.qa_input, state.project_context, _extra_docs_with_answers(state)))
        print(state.generated_task, file=output)
    elif mode == "--llm":
        if not confirm_yes_no("Request configured LLM provider with scanned context?", input_func, output):
            print("LLM generation cancelled.", file=output)
            return
        config = load_llm_config(cli_args)
        messages = build_messages(state.qa_input, state.project_context, _extra_docs_with_answers(state))
        state.mark_generated(OpenAICompatibleClient(config).complete(messages))
        print(state.generated_task, file=output)
    else:
        raise ValueError("Usage: /generate --local|--llm")


def _handle_issue(
    args: list[str],
    state: InteractiveSessionState,
    cli_args: argparse.Namespace,
    input_func: InputFunc,
    output: TextIO,
) -> None:
    _require_generated(state)
    if not args:
        raise ValueError("Usage: /issue local|remote --repo owner/name")
    if args[0] == "local":
        if not confirm_yes_no("Create local Issue Markdown backup?", input_func, output):
            print("Issue creation cancelled.", file=output)
            return
        issue = create_issue(
            title=state.issue_title or "QA-to-Dev generated development task",
            body=state.generated_task or "",
            docs_dir=cli_args.issue_dir,
            mode="local",
            protected_project=state.project_path,
        )
        print(f"Issue backup: {issue.local_path}", file=output)
        return
    if args[0] == "remote":
        if len(args) != 3 or args[1] != "--repo":
            raise ValueError("Usage: /issue remote --repo owner/name")
        repository = args[2]
        if not confirm_phrase(
            f"Create remote Issue in {repository}? A local backup will also be created.",
            "create issue",
            input_func,
            output,
        ):
            print("Remote Issue creation cancelled.", file=output)
            return
        issue = create_issue(
            title=state.issue_title or "QA-to-Dev generated development task",
            body=state.generated_task or "",
            docs_dir=cli_args.issue_dir,
            mode="auto",
            repository=repository,
            protected_project=state.project_path,
        )
        print(f"Issue backup: {issue.local_path}", file=output)
        if issue.remote_url:
            print(f"Remote issue: {issue.remote_url}", file=output)
        else:
            print(issue.note, file=output)
        return
    raise ValueError("Usage: /issue local|remote --repo owner/name")


def _extra_docs_with_answers(state: InteractiveSessionState) -> str | None:
    block = answered_questions_block(state)
    if not state.supplemental_materials:
        return block or None
    return f"{state.supplemental_materials}\n\n{block}".strip()


def _require_args(command: Command, count: int, usage: str) -> None:
    if len(command.args) < count:
        raise ValueError(f"Usage: {usage}")


def _require_project_and_input(state: InteractiveSessionState) -> None:
    if not state.project_path:
        raise ValueError("Set a project first with /project <path>")
    if not state.qa_input.strip():
        raise ValueError("Add QA input first by typing text or using /input")


def _require_context(state: InteractiveSessionState) -> None:
    if not state.project_context:
        raise ValueError("Run /scan first")


def _require_generated(state: InteractiveSessionState) -> None:
    if not state.generated_task:
        raise ValueError("Generate a task first with /generate --local or /generate --llm")


def _ensure_scanned(state: InteractiveSessionState) -> None:
    if not state.project_context:
        raise ValueError("Run /scan first")
