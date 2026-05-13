# Terminal Interactive Mode Plan

## Feature Positioning

Terminal interactive mode is the second entry point for QA-to-Dev Prompt Agent. It does not replace the existing batch CLI; it gives test engineers a guided terminal workspace for multi-turn input, project selection, document collection, read-only scanning, clarification, preview, Markdown generation, and Issue creation.

The experience should feel closer to Claude Code CLI / Codex CLI, but the capability boundary remains narrower: this agent generates developer-ready tasks. It does not edit target project code, run target project commands, commit, push, or create PRs.

## User Scenarios

1. A tester quickly turns a bug note into a developer task.
2. A QA lead adds PRD links, acceptance notes, and screenshots or local text extracts before creating an Issue.
3. A user is unsure which project/module is relevant and wants to scan before generating the final task.
4. A user wants to review pending questions before creating a remote Issue.
5. A user wants to keep uncertain fields explicit instead of letting the model invent them.

## Interaction Flow

1. Start interactive mode:

   ```powershell
   qa-to-dev --interactive
   qa-to-dev -i
   qa-to-dev --interactive --project "C:\target"
   ```

2. Show a welcome page with safety boundaries and current session status.
3. Collect QA input from direct text, `/input`, or `/input-file`.
4. Select target project with `/project <path>`.
5. Add supplemental materials through `/docs add-file <path>` and `/docs add-url <url>`.
6. Run `/scan` to produce a read-only project summary.
7. Show pending clarification questions through `/questions`.
8. Preview the prompt or local task through `/preview prompt` or `/preview task`.
9. Generate output through `/generate --local` or `/generate --llm`.
10. Confirm save or Issue creation.
11. Exit with `/exit`.

## Command Design

Interactive commands:

```text
/help
/status
/project <path>
/input
/input-file <path>
/docs add-file <path>
/docs add-url <url>
/docs list
/docs remove <index>
/scan
/scan --max-files 120
/context
/questions
/answer <question-id>
/preview prompt
/preview task
/generate --local
/generate --llm
/save <path>
/issue local
/issue remote --repo owner/name
/reset
/exit
```

Rules:

- Plain text appends to the QA input draft.
- Slash commands control the session.
- Writing files, requesting an LLM, and creating Issues require confirmation.
- Remote Issue creation requires stronger typed confirmation.
- Command failures should not exit the session.

## Session State

Recommended in-memory state:

```python
@dataclass
class InteractiveSessionState:
    project_path: Path | None
    qa_input: str
    docs_files: list[Path]
    docs_urls: list[str]
    docs_timeout: int
    max_files: int
    project_context: ProjectContext | None
    supplemental_materials: str | None
    pending_questions: list[PendingQuestion]
    answered_questions: dict[str, str]
    generated_prompt: str | None
    generated_task: str | None
    output_path: Path | None
    issue_title: str | None
    issue_repository: str | None
    local_only: bool
    dirty: bool
```

State flow:

```text
EMPTY -> HAS_INPUT -> HAS_PROJECT -> SCANNED -> QUESTIONS_REVIEWED -> GENERATED -> SAVED / ISSUE_CREATED
```

Rules:

- `/scan` requires project path and non-empty QA input.
- `/generate` should require a scan, or require confirmation to skip scanning.
- Changing input, project, or docs marks scan and generated output stale.
- Status output must never reveal API keys, `.env` contents, or full sensitive documents.

## Safety And Confirmation

Inherited safety principles:

- The target project is scanned read-only.
- No target project source files are modified.
- No target project build, test, install, git, or shell commands are executed.
- `.env*`, `.git`, `lib`, dependency folders, and generated folders remain ignored.
- Document URLs only allow `http` and `https`.
- API keys and tokens are never printed or written to Issues.

Confirmation levels:

```text
Low risk: status, docs list, prompt preview. No confirmation.
Medium risk: LLM request, local file save, local Issue. One confirmation.
High risk: remote Issue creation. Show repo/title/body summary and require typed confirmation.
Forbidden: code modification, target project command execution, git commit/push.
```

## Relationship To Batch CLI

Batch mode remains the stable automation entry point. Interactive mode is for guided human workflows.

Implementation should reuse existing core functions:

- `scan_project`
- `collect_supplemental_materials`
- `build_user_prompt`
- `build_messages`
- `generate_local_task`
- `OpenAICompatibleClient.complete`
- `save_markdown_output`
- `create_issue`

Recommended routing:

```python
def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.interactive:
        return run_interactive(args)
    return run_batch(args)
```

Because current `--project` is required at argparse level, implementation should move required validation into batch mode so interactive mode can start without a project.

## Terminal UI

Use standard input/output for MVP. Avoid full-screen TUI and extra dependencies unless later justified.

Welcome:

```text
QA-to-Dev Prompt Agent Interactive

Mode: read-only analysis
Target project: not selected
Input: empty
Docs: 0
Generated task: no

Type /help for commands. Paste text directly to add QA input.
```

Status:

```text
Session
- Project: C:\target-project
- QA input: 248 chars
- Docs: 2 files, 1 URL
- Scan: ready, 76 files scanned
- Pending questions: 3
- Generated task: not yet
```

Scan summary:

```text
Scan Result
- Stack: Python, Node.js
- Entry candidates:
  1. pyproject.toml
  2. src/main.ts
- Related files:
  1. src/pages/order/List.vue
  2. src/api/order.ts
- Build scripts:
  - npm run build
```

## Data And Artifacts

MVP artifacts:

- Generated Markdown task, only after confirmation.
- Local Issue Markdown, only after confirmation.
- Remote Issue, only after stronger confirmation, with local backup.

Session persistence is non-MVP by default. If added later, it must be explicit and should not silently write into the analyzed target project.

## Error Handling

Error categories:

- Missing input, missing project, incomplete command.
- File path not found, unreadable document.
- Unsupported URL scheme, timeout, HTTP error.
- Project path is not a directory.
- Missing API key, model, network failure, malformed LLM response.
- Missing repo, unavailable `gh` / `glab`, remote Issue failure.
- Stale session state or user cancellation.

Principles:

- Errors do not exit the session.
- Show short cause and next action.
- Preserve recoverable session state.
- Remote Issue failure keeps local Markdown backup.
- Document URL failure becomes explicit context instead of stopping the whole flow.

## MVP Scope

Must include:

- `--interactive` / `-i`.
- REPL loop with slash commands.
- QA text input.
- Project selection.
- Local and URL docs.
- Read-only scanning.
- Scan summary display.
- Prompt preview.
- Local task generation.
- LLM task generation.
- Save Markdown.
- Local Issue creation.
- Optional remote Issue through existing `gh` / `glab` path.
- Pending question list and answers.
- Confirmation mechanism.
- Tests for command parsing, state transitions, safety, and compatibility.

## Non-MVP Scope

Not included:

- Code modification.
- Running target project build/test/install.
- Git commit/push/PR automation.
- Full-screen TUI.
- Multi-session background restore.
- Plugin system.
- Vector database or long-term memory.
- Automatic GitHub/GitLab login.
- Browser preview.
- Multi-agent execution.
- Deep semantic call-chain analysis.
- File watching.
- Reading `.env` or secret files.

## Technical Implementation

Prefer zero new dependencies.

Suggested modules:

```text
qa_to_dev_agent/runner.py
qa_to_dev_agent/interactive.py
qa_to_dev_agent/session.py
qa_to_dev_agent/commands.py
qa_to_dev_agent/confirm.py
qa_to_dev_agent/questions.py
```

Responsibilities:

- `runner.py`: existing batch workflow.
- `interactive.py`: REPL loop and command dispatch.
- `session.py`: session state and stale-state marking.
- `commands.py`: slash command parsing and help text.
- `confirm.py`: yes/no and typed confirmations.
- `questions.py`: pending question generation and answer recording.

## Testing Strategy

Unit tests:

- Command parsing.
- Session state transitions.
- `/scan` blocked before project/input.
- Changing input marks generated output stale.
- Confirm defaults to no.
- Unsupported URL scheme is not fetched.
- `--interactive` does not require `--project`.
- Batch mode still requires `--project` and input.

Integration tests:

- Simulated stdin/stdout full local flow.
- Input, project, scan, generate, save.
- Local Issue fallback.
- Missing API key in LLM mode remains recoverable.
- Cancel save writes no file.

Safety tests:

- `.env*` not in scanner output.
- `lib` not scanned.
- `file://` not fetched.
- Remote Issue command not called without confirmation.
- No target project command execution.

## Acceptance Criteria

- `qa-to-dev --interactive` starts successfully.
- User can enter multi-turn QA input.
- `/project <path>` sets the target project.
- `/docs add-file` and `/docs add-url` add materials.
- `/scan` shows read-only context.
- `/questions` lists and records answers.
- `/preview prompt` shows the prompt.
- `/generate --local` generates structured Markdown.
- `/save <path>` confirms before writing.
- `/issue local` confirms before writing local Issue Markdown.
- `/issue remote --repo owner/name` requires typed confirmation and keeps local backup.
- `/status` shows session state.
- `/exit` exits cleanly.
- Existing batch CLI behavior remains compatible.
- Existing tests still pass.

## Risks

- Interactive mode may drift into a general coding agent.
- Too many commands can make MVP harder to use.
- Batch and interactive flows may duplicate logic.
- Users may over-trust static scan results.
- Remote Issue creation can leak sensitive context if confirmation is weak.
- Windows terminal encoding can affect Chinese text.
- Saving session by default can violate the target project read-only expectation.

## Open Questions

1. Should interactive mode default to local generation or LLM generation?
2. Should session persistence exist in MVP?
3. Should remote Issue support remain `gh` / `glab`, or GitHub-only first?
4. Should pending questions be rule-generated or LLM-generated?
5. Should `/generate --llm` require `/preview prompt` first?
6. Should document URLs support domain allowlists?
7. Should output language follow user input or always be Chinese?
8. Should target runtime/platform become a required clarification field?
9. Are lightweight dependencies like `prompt_toolkit` or `rich` acceptable later?
10. Should remote Issue body length be capped?
