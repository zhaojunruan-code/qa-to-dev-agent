# Client Runtime App Contract

This contract defines the MVP client-first runtime for `qadev`. It is written so an OpenAI Developers or Agents SDK implementation can review the goal, inputs, tools, state, approval gates, and prove command before adding model calls or side effects.

## Agent Goal

Turn QA notes, acceptance goals, and read-only project context into a standardized, executable, reviewable development task prompt.

The runtime must preserve the current product boundary: it analyzes the target project in read-only mode, does not modify the target project, does not run target project commands, and does not invent missing API fields, routes, files, or business rules.

## Input Shape

Batch command:

```text
qadev run --project <path> --input <text> --local-only --print-prompt
```

Fields:

- `project`: required path to the target project for read-only scanning.
- `input`: required QA note or acceptance text.
- `localOnly`: required for MVP; no LLM request is sent.
- `printPrompt`: required for MVP; prints a structured prompt preview.
- `maxFiles`: optional positive integer; defaults to `80`.

Interactive command:

```text
qadev interactive
```

Session commands:

- `/project <path>` sets the read-only target project and marks scan/generated state stale.
- `/input <text>` appends QA input and marks scan/generated state stale.
- Plain text appends QA input and marks scan/generated state stale.
- `/scan` performs a read-only project scan.
- `/preview` prints the local prompt preview after a scan.
- `/status` prints non-secret session state.
- `/exit` exits the session.

## Expected Output

`qadev run --local-only --print-prompt` prints Markdown with:

- runtime status;
- QA input;
- current project context;
- safety boundary;
- developer task prompt.

The output must explicitly state that LLM requests are disabled in the MVP and that no target writes, target commands, shell commands, git commands, build commands, test commands, install commands, Issue creation, or remote side effects were performed.

Errors must exit non-zero and include:

- reason;
- next step the user can run.

## Tools

### `scan_project`

Input:

```json
{
  "project": "string path",
  "qaInput": "string",
  "maxFiles": 80
}
```

Output:

```json
{
  "root": "absolute string path",
  "fileCount": 0,
  "signals": ["string"],
  "sampleTree": ["relative/path"],
  "techStack": ["string"],
  "entryFiles": ["relative/path"],
  "buildScripts": ["string"],
  "testScripts": ["string"],
  "keyCodeLocations": ["relative/path"]
}
```

Side effects: none.

Safety:

- ignores `.env*`, `.git`, `lib`, `generated`, `dependency`, `dependencies`, `node_modules`, `vendor`, and IDE/cache directories;
- does not execute package scripts;
- does not read protected files for content extraction in the MVP.

### `build_prompt_preview`

Input:

```json
{
  "qaInput": "string",
  "projectContext": "scan_project output"
}
```

Output:

```json
{
  "markdown": "string"
}
```

Side effects: none.

Safety:

- must not include secrets;
- must represent missing context as open work for the developer, not as invented facts.

### Future Tools Not Enabled In MVP

The following tools are contract placeholders only and require explicit approval gates before implementation:

- `request_llm_generation`;
- `write_markdown_output`;
- `create_local_issue`;
- `create_remote_issue`;
- `run_target_command`;
- `git_operation`.

## State

Interactive session state:

```json
{
  "project": "absolute path or null",
  "input": "string",
  "scan": "scan_project output or null",
  "generated": false
}
```

State rules:

- changing `project` or `input` marks `scan` and `generated` stale;
- `/status` must not print API keys, `.env` values, document bodies, or full secret-like values;
- MVP state is memory-only and is not persisted to the target project.

## Approval Gates

MVP has no approval prompts because it has no side effects beyond stdout/stderr.

Future gates:

- LLM request: show provider, model, input summary, network/cost warning, then require confirmation.
- Local file write: show absolute target path and overwrite status, then require confirmation.
- Local Issue Markdown: show title and output path, then require confirmation.
- Remote Issue: show repo, title, body summary, then require typed confirmation.
- Shell/git/build/test/install: disabled by default; any future implementation must show the exact command and require explicit confirmation.

## Prove Command

```powershell
node bin/qadev.mjs run --project . --input "verify client-first CLI runtime can produce a standardized development task" --local-only --print-prompt
```

This command must:

- start from the Node.js client entry;
- make no LLM request;
- write no files;
- create no Issue;
- run no target project commands;
- print a structured prompt preview.

Recommended full local verification:

```powershell
node bin/qadev.mjs --help
node bin/qadev.mjs --version
node bin/qadev.mjs run --project . --input "verify client-first CLI runtime can produce a standardized development task" --local-only --print-prompt
npm test
python -m unittest discover -v
```
