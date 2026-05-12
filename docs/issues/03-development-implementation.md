# 开发实现 Issue

## 背景

当前仓库已有 Python CLI 骨架，需要补齐 MVP 所需开发功能。

## 目标

实现可运行、可保存、可生成 Issue 备份的 QA-to-Dev Prompt Agent。

## 范围

- `qa_to_dev_agent/cli.py`
- `qa_to_dev_agent/project_scan.py`
- `qa_to_dev_agent/prompt_builder.py`
- `qa_to_dev_agent/local_generator.py`
- `qa_to_dev_agent/documents.py`
- `qa_to_dev_agent/output.py`
- `qa_to_dev_agent/issue_manager.py`

## 具体任务

- 修复 Prompt 模板编码和章节结构。
- 增强项目扫描上下文。
- 增加本地任务生成。
- 增加 Markdown 输出保存。
- 增加 Issue 本地备份和远程 CLI fallback。
- 增加基础测试。

## 验收标准

- CLI 可运行。
- 输出包含固定章节。
- 本地 Issue 可生成。
- 无 key 时 `--local-only` 和 `--print-prompt` 可用。

## 风险点

- 静态扫描命中质量有限。
- 远程 Issue 依赖外部 CLI 和权限。

## 待确认问题

- 是否要把目标项目的 `AGENTS.md` 加入扫描优先级。
