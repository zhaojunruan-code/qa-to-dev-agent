# QA-to-Dev Prompt Agent

QA-to-Dev Prompt Agent is a read-only CLI assistant for turning QA-style change notes into developer-ready task prompts.

It is designed for test engineers who can describe expected behavior, defects, acceptance goals, or document links, but may not know the exact implementation entrypoint. The agent scans a target project in read-only mode, summarizes relevant context, and generates a stable Markdown task for developers or Codex CLI.

## Feature Scope

MVP includes:

- QA input from `--input` or `--input-file`;
- target project path from `--project`;
- optional local documents via `--docs-file`;
- optional document links via `--docs-url`;
- read-only project structure scanning;
- technology stack, entry file, build script, and test script hints;
- requirement-related code candidate discovery;
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

```powershell
python -m pip install -e .
```

You can also run the module directly without installation:

```powershell
python -m qa_to_dev_agent.cli --help
```

## Configuration

The LLM client uses OpenAI-compatible `/chat/completions` endpoints. This allows official OpenAI, OpenRouter, or a private relay.

```powershell
$env:QADEV_LLM_BASE_URL="https://openrouter.ai/api/v1"
$env:QADEV_LLM_API_KEY="your-provider-key"
$env:QADEV_LLM_MODEL="your-model-name"
```

Supported variables:

- `QADEV_LLM_BASE_URL`: provider base URL, defaults to `https://api.openai.com/v1`;
- `QADEV_LLM_API_KEY`: provider API key;
- `QADEV_LLM_MODEL`: model name;
- `QADEV_LLM_HTTP_REFERER`: optional header used by some providers;
- `QADEV_LLM_APP_TITLE`: optional header used by some providers.

The CLI does not print API keys and does not read `.env` automatically. Export variables in your shell or pass command-line options.

## Usage

Preview the prompt sent to the model:

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

Include supplemental documents:

```powershell
python -m qa_to_dev_agent.cli `
  --project "C:\path\to\target-project" `
  --input "根据接口文档补充错误提示" `
  --docs-file ".\acceptance-notes.md" `
  --docs-url "https://example.com/api-doc" `
  --local-only
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

Create a remote Issue when GitHub CLI or GitLab CLI is installed and authenticated:

```powershell
python -m qa_to_dev_agent.cli `
  --project "C:\path\to\target-project" `
  --input "订单列表筛选条件需要保留" `
  --local-only `
  --create-issue `
  --issue-mode auto `
  --issue-repository "owner/repo"
```

If remote Issue creation is unavailable, the CLI keeps a Markdown backup in `docs/issues/` and continues.

## Arguments

- `--project`: target project path to inspect in read-only mode.
- `--input`: inline QA note.
- `--input-file`: file containing the QA note.
- `--docs-file`: optional local document, repeatable.
- `--docs-url`: optional remote document URL, repeatable.
- `--print-prompt`: print the model prompt and make no model request.
- `--local-only`: generate a deterministic local task without a model request.
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
- `lib`, `.git`, `.env*`, IDE folders, dependency folders, and generated folders are ignored.
- The tool does not execute target project build scripts automatically.
- Missing context is recorded as open questions instead of being invented.
- API keys and secrets must not be placed in README, Issues, reports, or generated tasks.

## Limitations

- Static scanning can only identify candidates, not prove every runtime call chain.
- Remote document fetching depends on network access, permissions, and document format.
- Remote Issue creation depends on `gh` or `glab` installation and authentication.
- Provider compatibility may vary across OpenAI-compatible gateways.
