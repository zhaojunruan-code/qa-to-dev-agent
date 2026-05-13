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
- `/preview` prints the local prompt preview after a scan.
- `/status` prints non-secret session state.
- `/exit` exits the session.

`run` and `interactive` must resolve LLM configuration and complete a connection preflight before scanning a project or accepting project input. The preflight calls `<baseURL>/chat/completions` with a fixed health-check message only. It must not send QA notes, generated prompts, document bodies, file names, project code, or project paths to the provider.

## Expected Output

`qadev run --print-prompt` prints Markdown with:

- runtime status;
- LLM preflight status and selected model;
- QA input;
- current project context;
- safety boundary;
- developer task prompt.

The output must explicitly state that LLM generation requests are disabled in the MVP and that no target writes, target commands, shell commands, git commands, build commands, test commands, install commands, Issue creation, or remote side effects were performed. It may mention the preflight chat completions endpoint but must never include API keys or secret-like values.

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
  "generated": false,
  "llm": "preflight output without secrets"
}
```

State rules:

- changing `project` or `input` marks `scan` and `generated` stale;
- `/status` may print provider origin and model, but must not print API keys, `.env` values, document bodies, or full secret-like values;
- MVP state is memory-only and is not persisted to the target project.

## Approval Gates

MVP has no approval prompts because the only remote side effect is the required LLM `/chat/completions` preflight. The preflight is mandatory for `run` and `interactive`, uses only provider configuration plus fixed health-check text, and sends no QA or project context.

Future gates:

- LLM request: show provider, model, input summary, network/cost warning, then require confirmation.
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
