# Mandatory LLM Startup Preflight

## Background

The Node client must prove that the configured LLM provider is reachable before any project workflow starts. Users may use OpenAI-compatible providers such as OpenRouter, official OpenAI, or a private relay.

## Scope

- Support `--base-url`, `--api-key`, and `--model` on `qadev run` and `qadev interactive`.
- Support `QADEV_LLM_BASE_URL`, `QADEV_LLM_API_KEY`, and `QADEV_LLM_MODEL`.
- Call `<baseURL>/chat/completions` with a fixed health-check message before project scanning or interactive command handling.
- Do not send QA input, prompts, project paths, file names, or project code during preflight.
- Do not print or persist plaintext API keys.

## Acceptance Criteria

- Missing base URL, API key, or model fails before scanning with a clear message.
- Connection failures report sanitized HTTP or transport details without leaking keys.
- Successful preflight allows prompt preview and interactive workflows to continue.
- Tests use a local mock HTTP server and never contact real providers.

## Verification

- `npm run test:node`
- Optional manual run with a real OpenAI-compatible provider after exporting the three `QADEV_LLM_*` variables.
