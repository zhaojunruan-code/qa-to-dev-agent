# QA-to-Dev Prompt Agent Product Plan

## Product Goal

Build a read-only CLI agent for test engineers. The agent converts QA notes, acceptance goals, defect descriptions, document links, and project context into structured development tasks for developers or Codex CLI.

## MVP Scope

- Accept QA input from inline text or file.
- Accept a target project path.
- Accept optional local documents and document URLs.
- Scan the target project in read-only mode.
- Identify technology stack, entry files, build scripts, test scripts, and relevant code candidates.
- Generate a structured Markdown development task.
- Generate a Codex CLI prompt.
- Save generated output to Markdown.
- Create local Issue Markdown and optionally remote GitHub/GitLab Issues when CLI permissions exist.
- Support OpenAI-compatible LLM endpoints with custom base URL, API key, and model.

## Non-MVP Scope

- Automatic code modification in the analyzed project.
- Automatic commit, push, PR, or MR in the analyzed project.
- Full semantic indexing or vector search.
- Automatic long-running multi-agent development execution.
- Full external project management integrations beyond issue creation fallback.

## Users

- Test engineer: provides the QA description and uses generated acceptance criteria.
- Developer: implements from the generated task.
- Codex CLI operator: copies the generated Codex prompt into a coding agent.
- Tech lead: reviews risk, scope, and release readiness.

## Core Flow

1. QA provides a short change note, issue description, acceptance goal, or document link.
2. User runs the CLI with target project path and input.
3. Agent scans project context in read-only mode.
4. Agent builds or generates a structured task.
5. Agent saves Markdown and optionally creates an Issue.
6. Developer or Codex CLI uses the task for implementation.

## Functional Modules

- CLI argument parsing.
- LLM/provider configuration.
- Supplemental material collection.
- Read-only project scanner.
- Prompt builder.
- Local deterministic task generator.
- OpenAI-compatible LLM client.
- Markdown output writer.
- Issue writer with local fallback.

## Priority

P0:

- CLI starts and validates inputs.
- Read-only scan works.
- Stable output structure exists.
- Local generation and prompt preview work without network.
- LLM mode supports custom base URL, API key, and model.
- Local Issue fallback works.

P1:

- Better related file matching.
- More project framework signals.
- More robust document extraction.
- Remote Issue support through available CLI/auth.
- Terminal interactive mode for multi-turn QA input, project selection, scan review, clarification, and confirmed output actions.

P2:

- Multi-turn clarification.
- Rich semantic code indexing.
- GitHub/GitLab app-native issue creation from inside the CLI.
- Evaluation harness.

## Milestones

- M1: CLI, configuration, prompt preview.
- M2: read-only scanner and structured context.
- M3: local structured task generation and Markdown saving.
- M4: Issue backup and remote CLI fallback.
- M5: test report and release review.
- M6: terminal interactive mode planning and implementation.

## Acceptance Criteria

- CLI can run with `--print-prompt`.
- CLI can run with `--local-only`.
- Missing input and missing project path produce clear errors.
- Output includes all required Markdown sections.
- The target project is not modified by default.
- README documents installation, configuration, usage, output structure, Issue behavior, and safety principles.
- Tests cover CLI, scanning, local generation, and error paths.

## Risks

- Static scans may miss dynamic runtime paths.
- LLM output can infer too much unless strongly constrained.
- Remote docs may be inaccessible.
- Remote Issue creation depends on local auth and tooling.
- Different OpenAI-compatible providers may vary in behavior.

## Open Questions

- Should the next version use GitHub/GitLab API tokens directly, or continue requiring `gh`/`glab`?
- Should output be bilingual?
- Should generated tasks be stored in a history directory by default?
- Should the scanner read `AGENTS.md` from target projects when present?
