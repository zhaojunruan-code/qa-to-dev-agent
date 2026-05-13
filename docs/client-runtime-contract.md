# Client Runtime App Contract

This contract defines the MVP client-first runtime for `qadev`. It is written so an OpenAI Developers or Agents SDK implementation can review the goal, inputs, tools, state, approval gates, and prove command before adding model calls or side effects.

## Agent Goal

Turn QA notes, acceptance goals, and read-only project context into a standardized, executable, reviewable development task prompt.

The runtime must preserve the current product boundary: it analyzes the target project in read-only mode, does not modify the target project, does not run target project commands, and does not invent missing API fields, routes, files, or business rules.

## Input Shape

Batch command:

```text
qadev run --project <path> --input <text> --print-prompt --base-url <url> --api-key <key> --model <name>
```

Fields:

- `project`: required path to the target project for read-only scanning.
- `input`: required QA note or acceptance text.
- `localOnly`: optional compatibility flag; no LLM generation request is sent.
- `printPrompt`: required for MVP; prints a structured prompt preview.
- `maxFiles`: optional positive integer; defaults to `80`.
- `baseURL`: OpenAI-compatible base URL; may come from `QADEV_LLM_BASE_URL`.
- `apiKey`: provider API key; may come from `QADEV_LLM_API_KEY`.
- `model`: provider model name; may come from `QADEV_LLM_MODEL`.

Interactive command:

```text
qadev interactive --base-url <url> --api-key <key> --model <name>
```

Session commands:

- `/project <path>` sets the read-only target project and marks scan/generated state stale.
- `/input <text>` appends QA input and marks scan/generated state stale.
- Plain text appends QA input and marks scan/generated state stale.
- `/scan` performs a read-only project scan.
- `/preview` prints the local prompt preview after a scan. It must include a developer task skeleton and priority code locations, and must not send QA input or scan context to the model.
- `/generate` sends the QA input and read-only scan context to the configured OpenAI-compatible `/chat/completions` endpoint and prints the returned structured Markdown task.
- `/status` prints non-secret session state.
- `/exit` exits the session.

`run` and `interactive` must resolve LLM configuration and complete a connection preflight before scanning a project or accepting project input. The preflight calls `<baseURL>/chat/completions` with a fixed health-check message only. It must not send QA notes, generated prompts, document bodies, file names, project code, or project paths to the provider. Interactive `/generate` is the explicit opt-in generation command and may send QA input plus scan context after preflight.

## Expected Output

`qadev run --print-prompt` and interactive `/preview` print Markdown with:

- runtime status;
- LLM preflight status and selected model;
- QA input;
- current project context;
- priority code locations to investigate first;
- a developer task skeleton;
- safety boundary;
- developer task prompt.

The preview output must explicitly state that no LLM generation request was sent by the preview command and that no target writes, target commands, shell commands, git commands, build commands, test commands, install commands, Issue creation, or target-project side effects were performed. It may mention the preflight chat completions endpoint but must never include API keys or secret-like values.

Errors must exit non-zero and include:

- reason;
- next step the user can run.

LLM configuration errors must name the missing setting without printing secret values. Connection errors must include the HTTP status or sanitized transport reason without printing the API key.

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
  "sampleTree": ["priority relative/path"],
  "techStack": ["string"],
  "entryFiles": ["relative/path"],
  "buildScripts": ["string"],
  "testScripts": ["string"],
  "keyCodeLocations": ["relative/path"]
}
```

Side effects: none.

Safety:

- ignores `.env*`, `.git`, `lib`, `generated`, `dependency`, `dependencies`, `node_modules`, `vendor`, `.pnpm-store`, `unpackage`, package cache/build output directories, and IDE/cache directories;
- prioritizes `pages.json`, `src/pages`, `src/components`, `src/api`, `src/store`, `src/router`, and `src/utils` before low-signal files;
- expands common Chinese and English requirement terms such as `订单/order/orders`, `我的/mine/user/profile`, and `状态/status/tab/tabs/switch/filter` when ranking requirement-related candidates;
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

### `llm_connection_preflight`

Input:

```json
{
  "baseURL": "string absolute http(s) URL",
  "apiKey": "string secret",
  "model": "string"
}
```

Configuration sources:

- CLI options: `--base-url`, `--api-key`, `--model`;
- environment variables: `QADEV_LLM_BASE_URL`, `QADEV_LLM_API_KEY`, `QADEV_LLM_MODEL`;
- `.env` files are not read by the Node client.

Behavior:

- build `<baseURL>/chat/completions` while preserving provider path prefixes such as `/api/v1`;
- reject base URLs that contain username or password credentials;
- send `POST` with `Authorization: Bearer <apiKey>`, configured `model`, and a fixed health-check message that asks for `OK`;
- use the response only to prove provider reachability, authentication, model availability, and OpenAI-compatible response shape;
- do not send QA input, project context, prompts, documents, target paths, file names, or source code.

Output:

```json
{
  "provider": "origin string",
  "model": "configured model",
  "preflightEndpoint": "sanitized endpoint URL without secrets"
}
```

Side effects: one provider network request to the chat completions endpoint with fixed health-check text.

Safety:

- API keys are never printed, persisted, or included in generated Markdown;
- failure messages are sanitized and must not include `Authorization` header values;
- preflight must complete before `scan_project` in `run`;
- preflight must complete before the interactive prompt accepts commands in `interactive`.

### `request_llm_generation`

Enabled only for interactive `/generate`.

Input:

```json
{
  "qaInput": "string",
  "projectContext": "scan_project output",
  "baseURL": "string absolute http(s) URL",
  "apiKey": "string secret",
  "model": "string"
}
```

Behavior:

- uses the same OpenAI-compatible `/chat/completions` endpoint and optional provider metadata headers as preflight;
- sends the QA input, scan context, and required Markdown structure only after the user explicitly enters `/generate`;
- prints the model response as Markdown;
- does not modify the target project, write files, create Issues, run commands, or persist state.

Safety:

- API keys are never printed or included in generated output by the client;
- provider errors are sanitized before display;
- `/preview`, `/scan`, `/status`, and `run --print-prompt` must not call this tool.

### Future Tools Not Enabled In MVP

The following tools are contract placeholders only and require explicit approval gates before implementation:

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
  "generated": false,
  "llm": "preflight output without secrets"
}
```

State rules:

- changing `project` or `input` marks `scan` and `generated` stale;
- `/status` may print provider origin and model, but must not print API keys, `.env` values, document bodies, or full secret-like values;
- MVP state is memory-only and is not persisted to the target project.

## Approval Gates

MVP has no typed approval prompts in the Node client. The required startup preflight is automatic and sends only provider configuration plus fixed health-check text. Interactive `/generate` is an explicit command gate: QA input and scan context are sent only when the user types `/generate`.

Future gates:

- Local file write: show absolute target path and overwrite status, then require confirmation.
- Local Issue Markdown: show title and output path, then require confirmation.
- Remote Issue: show repo, title, body summary, then require typed confirmation.
- Shell/git/build/test/install: disabled by default; any future implementation must show the exact command and require explicit confirmation.

## Prove Command

```powershell
$env:QADEV_LLM_BASE_URL="https://openrouter.ai/api/v1"
$env:QADEV_LLM_API_KEY="<provider-key>"
$env:QADEV_LLM_MODEL="<model-name>"
node bin/qadev.mjs run --project . --input "verify client-first CLI runtime can produce a standardized development task" --print-prompt
```

This command must:

- start from the Node.js client entry;
- complete the `/chat/completions` LLM preflight before scanning;
- make no LLM generation request;
- write no files;
- create no Issue;
- run no target project commands;
- print a structured prompt preview.

Recommended full local verification:

```powershell
node bin/qadev.mjs --help
node bin/qadev.mjs --version
node bin/qadev.mjs run --project . --input "verify client-first CLI runtime can produce a standardized development task" --print-prompt
npm test
python -m unittest discover -v
```
