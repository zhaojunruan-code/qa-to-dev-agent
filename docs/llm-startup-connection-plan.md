# LLM Startup Connection Plan

## Background

QA-to-Dev Prompt Agent depends on LLM capability. A client that starts without proving an LLM connection creates a false-ready state: users can enter the workflow, but the core agent capability may fail later.

This change makes LLM connectivity a startup requirement for the Node client runtime.

## Product Goal

Before `qadev run` scans a target project, and before `qadev interactive` accepts project input, the client must validate that the configured OpenAI-compatible provider can authenticate and return a minimal model response.

## User Value

- Fail early when `baseURL`, `apiKey`, or `model` is missing or invalid.
- Support OpenRouter, official OpenAI, and private OpenAI-compatible gateways.
- Avoid sending project code, QA notes, or prompts during startup validation.
- Keep API keys out of logs, generated Markdown, Issues, and status output.

## Configuration Standard

Required configuration:

- `baseURL`: OpenAI-compatible API base URL, such as `https://openrouter.ai/api/v1`.
- `apiKey`: provider API key.
- `model`: provider model name, passed through without normalization.

Supported sources:

- CLI flags: `--base-url`, `--api-key`, `--model`.
- Environment variables: `QADEV_LLM_BASE_URL`, `QADEV_LLM_API_KEY`, `QADEV_LLM_MODEL`.

The Node client must not read `.env` automatically and must not persist API keys.

## Startup Flow

1. Parse command arguments.
2. Validate required non-LLM arguments.
3. Resolve LLM configuration from CLI flags or environment variables.
4. Validate `baseURL` is an absolute `http` or `https` URL.
5. Reject `baseURL` values that contain username or password credentials.
6. Send a fixed health-check request to `<baseURL>/chat/completions`.
7. Require an OpenAI-compatible response with at least one choice.
8. Continue to project scan or interactive prompt only after success.
9. Stop with an actionable, sanitized error on missing config or connection failure.

## Health Check Contract

The startup preflight sends only fixed health-check text and the configured model name. It must not include:

- QA input.
- Generated prompts.
- Target project paths.
- File names.
- Project source code.
- Local document contents.

## Error Standard

- Missing config: name the missing setting and the related flag/env var.
- Invalid URL: explain that an absolute `http` or `https` URL is required.
- HTTP failure: show the sanitized HTTP status.
- Timeout or network failure: show a sanitized transport message.
- Incompatible response: explain that the provider did not return OpenAI-compatible chat completions output.

Errors must never print the API key or `Authorization` header value.

## Acceptance Criteria

- `qadev run` fails before scanning when LLM config is missing.
- `qadev run` completes preflight before scanning when config is present.
- `qadev interactive` completes preflight before accepting commands.
- CLI flags override environment variables.
- API keys are not printed in stdout, stderr, prompt previews, README examples, or Issue backups.
- Tests use a local mock server and do not contact real providers.

## Risks

- Startup now depends on network availability and provider latency.
- OpenAI-compatible gateways may differ in error format.
- The health check proves basic model response, not long-context performance or future tool-calling support.

## Open Questions

- Whether to add optional OpenRouter headers such as `HTTP-Referer` and `X-Title`.
- Whether future UI clients should persist credentials in OS secure storage.
- Whether to add multiple named provider profiles.
