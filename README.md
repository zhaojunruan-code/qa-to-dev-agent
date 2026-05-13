# QA-to-Dev Prompt Agent

QA-to-Dev Prompt Agent is a read-only CLI assistant for turning QA-style change notes into developer-ready task prompts.

It is designed for test engineers who can describe expected behavior, defects, acceptance goals, or document links, but may not know the exact implementation entrypoint. The agent scans a target project in read-only mode, summarizes relevant context, and generates a stable Markdown task for developers or Codex CLI.

## Feature Scope

MVP includes:

- QA input from `--input` or `--input-file`;
- terminal interactive mode from `--interactive` / `-i`;
- target project path from `--project`;
- optional local documents via `--docs-file`;
- optional document links via `--docs-url`;
- read-only project structure scanning;
- technology stack, entry file, build script, and test script hints;
- requirement-related code candidate discovery;
- package/cache noise filtering such as `.pnpm-store`, `.vite`, `.cache`, `unpackage`, `dist`, and `build`;
- interactive `/preview` with developer task skeleton and priority investigation files;
- interactive `/generate` for explicit LLM-backed structured development task generation;
- stable structured Markdown output;
- local generation mode with `--local-only`;
- OpenAI-compatible LLM mode with custom base URL and API key;
- Markdown output saving with `--output` or `--output-dir`;
- local Issue Markdown generation and optional remote Issue creation through `gh` or `glab` when available.

Non-MVP:

- no automatic code modification in the analyzed project;
- no automatic commit or push in the analyzed project;
- no dangerous command execution;
- no secret file reading;
- no guarantee of full semantic call-chain recovery from static scan alone.

## Installation

From the repository root:

The client-first CLI entry is `qadev`. During the MVP you can run it directly with Node.js without installing dependencies:

```powershell
$env:QADEV_LLM_BASE_URL="https://openrouter.ai/api/v1"
$env:QADEV_LLM_API_KEY="your-provider-key"
$env:QADEV_LLM_MODEL="your-model-name"
# Optional for gateways that require application metadata:
$env:QADEV_LLM_HTTP_REFERER="https://example.local"
$env:QADEV_LLM_APP_TITLE="QA-to-Dev Prompt Agent"
node bin/qadev.mjs --help
node bin/qadev.mjs --version
node bin/qadev.mjs run --project . --input "verify client-first CLI runtime" --print-prompt
node bin/qadev.mjs interactive
```

After package installation, the package exposes this binary:

```powershell
qadev --help
```

The Node.js client is the preferred user-facing entry direction. This MVP is a zero-dependency client shell/prototype; the existing Python implementation remains available as the internal/reference engine and compatibility path.

Local verification scripts:

```powershell
npm run test:node
npm run test:python
npm test
```

Python editable install remains supported:

```powershell
python -m pip install -e .
```

You can also run the module directly without installation:

```powershell
python -m qa_to_dev_agent.cli --help
```

## Configuration

The Node client must complete an LLM connection preflight before `run` scans a project or `interactive` accepts project input. The preflight calls the OpenAI-compatible `/chat/completions` endpoint with a fixed health-check message and does not send QA notes, prompts, project paths, or project code context.

The same settings are used by interactive `/generate` through official OpenAI, OpenRouter, or a private OpenAI-compatible relay.

```powershell
$env:QADEV_LLM_BASE_URL="https://openrouter.ai/api/v1"
$env:QADEV_LLM_API_KEY="your-provider-key"
$env:QADEV_LLM_MODEL="your-model-name"
```

You can also pass these values to the Node client:

```powershell
node bin/qadev.mjs run `
  --project . `
  --input "verify client-first CLI runtime" `
  --print-prompt `
  --base-url "https://openrouter.ai/api/v1" `
  --api-key $env:QADEV_LLM_API_KEY `
  --model "your-model-name"
```

The CLI does not print API keys, does not store API keys, and does not read `.env` automatically. Export variables in your shell or pass command-line options.
Do not put credentials in `QADEV_LLM_BASE_URL`; the Node client rejects base URLs containing usernames or passwords.
When a provider rejects the preflight with an HTTP error, the Node client prints the provider error detail when available and redacts the configured API key from that message.

## Node Interactive Mode

Start the terminal REPL:

```powershell
node bin/qadev.mjs interactive
```

Interactive mode accepts normal text as QA input and slash commands for stateful work:

```text
/project C:\path\to\target-project
/input 我的订单状态筛选需要修复
/scan
/preview
/generate
/exit
```

Useful commands:

- `/help`: show commands.
- `/status`: show session state without secrets.
- `/project <path>`: select target project.
- `/scan`: run read-only project scan.
- `/preview`: print a local prompt preview only. It includes a developer task skeleton and priority code locations, but sends no QA input or scan context to the model.
- `/generate`: call the configured OpenAI-compatible `/chat/completions` endpoint and send the QA input plus read-only scan context to generate a structured development task.

The Node REPL does not read `.env`, does not scan `lib`, does not modify the target project, and does not run commands in the target project. The only generation network request that can include QA input or scanned context is the explicit `/generate` command after startup preflight has already succeeded.
Local input files and supplemental document files from `.env*`, `lib`, dependency, or generated directories are rejected. Markdown output and Issue backups are also rejected when the target path is inside the selected target project.

## Batch Usage

Preview the local Node prompt without sending QA input or scan context to the model:

```powershell
node bin/qadev.mjs run `
  --project "C:\path\to\target-project" `
  --input "我的订单状态筛选需要修复" `
  --print-prompt
```

`qadev run` currently keeps generation in preview mode. Batch LLM generation is not enabled in the Node client in this iteration; use interactive `/generate` when you explicitly want to send QA input and scan context to the configured provider.

Python compatibility path examples:

```powershell
python -m qa_to_dev_agent.cli `
  --project "C:\path\to\target-project" `
  --input "登录页按钮文案需要按验收标准调整" `
  --print-prompt
```

Generate a structured task locally without a model request:

```powershell
python -m qa_to_dev_agent.cli `
  --project "C:\path\to\target-project" `
  --input "登录页按钮文案需要按验收标准调整" `
  --local-only `
  --output ".\docs\generated-task.md"
```

Call an OpenAI-compatible endpoint:

```powershell
python -m qa_to_dev_agent.cli `
  --project "C:\path\to\target-project" `
  --input-file ".\qa-note.md" `
  --base-url "https://openrouter.ai/api/v1" `
  --api-key $env:QADEV_LLM_API_KEY `
  --model "your-model-name"
```

Create a local Issue Markdown from the generated task:

```powershell
python -m qa_to_dev_agent.cli `
  --project "C:\path\to\target-project" `
  --input "订单列表筛选条件需要保留" `
  --local-only `
  --create-issue `
  --issue-title "订单列表筛选条件保留"
```

If remote Issue creation is unavailable, the CLI keeps a Markdown backup in `docs/issues/` and continues.

## Arguments

- `--interactive`, `-i`: start the terminal REPL.
- `--project`: target project path to inspect in read-only mode.
- `--input`: inline QA note.
- `--input-file`: file containing the QA note.
- `--docs-file`: optional local document, repeatable.
- `--docs-url`: optional remote document URL, repeatable. Only `http` and `https` are allowed.
- `--print-prompt`: print the model prompt and make no model request.
- `--local-only`: keep generation local after the required `/chat/completions` preflight; no QA input or project context is sent to the model beyond the fixed health-check text.
- `--base-url`: OpenAI-compatible API base URL for the Node client; also available as `QADEV_LLM_BASE_URL`.
- `--api-key`: provider API key for the Node client; also available as `QADEV_LLM_API_KEY`.
- `--model`: model name for the Node client; also available as `QADEV_LLM_MODEL`.
- `--http-referer`: optional provider metadata header; also available as `QADEV_LLM_HTTP_REFERER`.
- `--app-title`: optional provider metadata header; also available as `QADEV_LLM_APP_TITLE`.
- `--output`: save generated Markdown to a specific file.
- `--output-dir`: save generated Markdown with a timestamped filename.
- `--create-issue`: create an Issue from the generated task.
- `--issue-mode`: `local`, `auto`, or `remote`.
- `--issue-dir`: local Markdown backup directory.
- `--issue-repository`: remote repository in `owner/name` form.

## Output Structure

Generated tasks use this fixed Markdown structure:

```markdown
# 开发任务标题
## 背景
## 测试输入摘要
## 当前项目上下文
## 已识别的关键代码位置
## 当前调用链理解
## 开发目标
## 实现要求
## 需要保留的现有逻辑
## 禁止事项
## 错误处理要求
## 配置与环境要求
## 数据与接口影响
## 前端影响
## 后端影响
## 验收标准
## 回归范围
## 待确认问题
## 风险点
## Codex CLI Prompt
```

## Safety Principles

- The analyzed project is scanned in read-only mode.
- `lib`, `.git`, `.env*`, IDE folders, dependency folders, `.pnpm-store`, package cache folders, `unpackage`, build output, and generated folders are ignored.
- Local file inputs from `.env*`, `lib`, dependency folders, and generated folders are rejected.
- Markdown output and Issue backups cannot be written inside the selected target project.
- The tool does not execute target project build scripts automatically.
- Missing context is recorded as open questions instead of being invented.
- API keys and secrets must not be placed in README, Issues, reports, or generated tasks.
- `qadev run` and `qadev interactive` must complete the `/chat/completions` LLM preflight before project scanning or interactive project input.
- The LLM preflight must not include QA notes, generated prompts, target project paths, or project code context.
- Node interactive `/generate` is the explicit opt-in that sends QA input and scan context to the configured `/chat/completions` endpoint.

## Limitations

- Static scanning can only identify candidates, not prove every runtime call chain.
- Remote document fetching depends on network access, permissions, and document format.
- Remote Issue creation depends on `gh` or `glab` installation and authentication.
- Provider compatibility may vary across OpenAI-compatible gateways.
