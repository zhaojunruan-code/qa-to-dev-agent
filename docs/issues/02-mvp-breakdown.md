# MVP 功能拆分 Issue

## 背景

需要把 MVP 拆解成可开发、可测试、可验收的模块。

## 目标

完成从 QA 输入到结构化开发任务输出的闭环。

## 范围

- CLI、配置、扫描、Prompt、LLM、本地生成、输出、Issue 备份、文档、测试。

## 具体任务

- 支持 `--input`、`--input-file`、`--project`。
- 支持 `--print-prompt` 和 `--local-only`。
- 支持 `--docs-file` 和 `--docs-url`。
- 支持 `--output`、`--output-dir`。
- 支持本地 Issue Markdown 和远程 CLI fallback。

## 验收标准

- P0 功能均可通过 CLI 使用。
- 无网络时仍可本地生成任务。
- 远程 Issue 不可用时不中断流程。

## 风险点

- 功能过宽导致 MVP 失焦。
- 文档链接抓取受网络限制。

## 待确认问题

- 远程 Issue 是否需要 GitHub App API 深度集成。
