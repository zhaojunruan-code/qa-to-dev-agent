# 新增终端交互模式

## 背景

当前 QA-to-Dev Prompt Agent 是 Python CLI MVP，主要通过一次性参数调用，将测试工程师输入、文档链接和项目上下文转换为开发任务说明。现有模式适合脚本化使用，但对于测试工程师的真实工作流，多轮补充需求、选择项目、查看扫描结果、处理待确认问题、确认是否生成 Markdown 或 Issue，使用参数模式成本较高。

需要新增类似 Claude Code CLI / Codex CLI 的终端交互能力，但保持项目当前定位：只读分析型 Agent，不修改目标项目代码，不自动执行危险命令。

## 目标

实现 `qa-to-dev --interactive` 交互模式，使用户可以在终端内完成：

- 多轮输入 QA 需求；
- 选择目标项目；
- 补充本地文档和 URL 文档；
- 执行只读项目扫描；
- 查看扫描摘要和候选代码位置；
- 处理待确认问题；
- 预览 Prompt 或任务草案；
- 确认生成 Markdown；
- 确认创建本地或远程 Issue。

## 范围

MVP 包含：

- 新增 `--interactive` / `-i` 参数；
- 新增 REPL 主循环；
- 支持 `/help`、`/status`、`/project`、`/input`、`/input-file`、`/docs`、`/scan`、`/context`、`/questions`、`/preview`、`/generate`、`/save`、`/issue`、`/reset`、`/exit`；
- 复用现有扫描、文档收集、Prompt 构建、本地生成、LLM 调用、Markdown 保存、Issue 创建能力；
- 写文件、请求 LLM、创建 Issue 前必须确认；
- 远程 Issue 创建需要二次确认；
- 保持目标项目只读。

## 具体任务

- 拆分现有 batch 流程为 `run_batch(args)`。
- 新增 `run_interactive(args)`。
- 新增会话状态对象和 slash command 解析。
- 新增确认机制。
- 新增待确认问题管理。
- 调整 argparse：交互模式不要求 `--project`，batch 模式仍校验项目和输入。
- 补充交互模式 README 说明。
- 补充单元测试和集成测试。

## 非目标

本 Issue 不实现：

- 自动修改代码；
- 自动运行目标项目构建或测试；
- 自动 commit / push / PR；
- 全屏 TUI；
- 多会话长期记忆；
- 插件系统；
- 深度语义调用链分析。

## 安全要求

- 不修改目标项目代码；
- 不读取 `.env*`；
- 不扫描 `lib`；
- 不执行目标项目命令；
- 不自动创建远程 Issue；
- 不输出 API Key；
- 不支持 `file://` 文档 URL；
- 所有写入操作必须确认；
- 远程 Issue 创建必须二次确认。

## 验收标准

- `qa-to-dev --interactive` 可以启动交互模式；
- 直接输入文本会追加到 QA 输入；
- `/project <path>` 可以设置项目；
- `/docs add-file <path>` 和 `/docs add-url <url>` 可以补充文档；
- `/scan` 可以执行只读扫描并展示摘要；
- `/questions` 可以展示并记录待确认问题；
- `/preview prompt` 可以预览 Prompt；
- `/generate --local` 可以生成 Markdown 任务；
- `/save <path>` 在确认后保存 Markdown；
- `/issue local` 在确认后创建本地 Issue Markdown；
- `/issue remote --repo owner/name` 在二次确认后尝试创建远程 Issue，并保留本地备份；
- `/status` 可以展示当前会话状态；
- `/exit` 可以退出；
- 原有参数模式行为不变；
- 原有测试继续通过。

## 风险点

- 交互模式可能膨胀为通用编码 Agent，偏离只读分析定位。
- 终端流程过复杂会降低 MVP 易用性。
- 会话状态和参数模式可能出现重复逻辑。
- 用户可能误以为静态扫描已证明真实调用链。
- 远程 Issue 创建可能泄露敏感上下文。
- Windows 终端编码问题可能影响中文展示。

## 待确认问题

- 交互模式默认使用 local-only 还是 LLM？
- 是否允许保存 session？
- 远程 Issue 首期是 GitHub-only 还是继续 `gh` / `glab` 双支持？
- 待确认问题由规则生成还是 LLM 生成？
- `/generate --llm` 前是否必须 `/preview prompt`？
- 是否需要 URL 域名白名单？
- 输出语言是否跟随用户输入？
