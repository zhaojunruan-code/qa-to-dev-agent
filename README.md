# QA-to-Dev Prompt Agent

Read-only CLI agent for turning QA-style change notes into developer-ready task prompts.

The first MVP is intentionally conservative:

- it reads project context;
- it generates a structured development task;
- it can call any OpenAI-compatible chat completions endpoint;
- it does not edit the target project.

## Configuration

Use neutral endpoint variables so the agent can call official OpenAI, OpenRouter, or a private relay.

```powershell
$env:QADEV_LLM_BASE_URL="https://openrouter.ai/api/v1"
$env:QADEV_LLM_API_KEY="your-provider-key"
$env:QADEV_LLM_MODEL="your-model-name"
```

Copy `.env.example` for the supported variables. The CLI does not load `.env` files automatically yet; export variables in your shell or pass command-line options.

## Usage

Preview the prompt without making a network request:

```powershell
qa-to-dev --project "C:\path\to\project" --input "QA change note here" --print-prompt
```

Call the configured OpenAI-compatible endpoint:

```powershell
qa-to-dev --project "C:\path\to\project" --input "QA change note here"
```

You can override endpoint settings per command:

```powershell
qa-to-dev `
  --project "C:\path\to\project" `
  --input-file ".\qa-note.md" `
  --base-url "https://openrouter.ai/api/v1" `
  --api-key $env:QADEV_LLM_API_KEY `
  --model "your-model-name"
```

## Output

The generated task keeps a stable Markdown shape:

- background;
- QA input summary;
- current project context;
- identified code locations;
- call-chain understanding;
- development goal;
- implementation requirements;
- preserved behavior;
- forbidden changes;
- error handling;
- configuration and environment requirements;
- data and API impact;
- frontend and backend impact;
- acceptance criteria;
- regression scope;
- open questions;
- risks;
- Codex CLI prompt.
