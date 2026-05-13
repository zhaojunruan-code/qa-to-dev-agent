# Client-First CLI Runtime Product Plan

## 1. 背景

当前 QA-to-Dev Prompt Agent 已具备只读扫描、QA 输入整理、结构化开发任务生成、Codex CLI Prompt 输出、Markdown 保存与 Issue 创建能力。现有实现与仓库形态以 Python 为主，用户反馈它更像一个服务端或后端脚本工具，而不是面向开发者日常工作的客户端终端产品。

新需求是在当前分支 `feature/client-first-cli-runtime` 上规划客户端优先的 CLI runtime：产品形态应从“运行一个 Python 工具生成文档”升级为“生活在终端里的 agentic coding workflow 客户端”。该客户端仍以 QA-to-Dev 为核心场景，但运行方式、安装方式、交互方式、工具边界、安全审批、状态管理和 OpenAI Agents SDK 合规性都要按客户端 runtime 重新设计。

本方案只定义产品需求和交付边界，不要求本次修改代码实现。

## 2. 用户原话摘要

- 当前项目“全是 Python”，产品感受更像服务端。
- 需要创建新分支并参考 Claude Code 技术栈，转向客户端为主的终端 CLI agent。
- 当前分支已是 `feature/client-first-cli-runtime`，无需再次创建分支。
- 新 runtime 必须满足 OpenAI Developers / Agents SDK 规范。
- 产品经理输出的需求说明质量会直接决定后续开发、测试、审核代理执行效果，所以需求必须标准化、可执行、无歧义。

## 3. 产品目标

1. 将 QA-to-Dev Prompt Agent 定位为客户端优先的终端 CLI agent runtime。
2. 保留既有 QA-to-Dev 核心价值：把 QA 输入、项目上下文、验收目标和风险约束转化为开发可执行任务。
3. 引入面向终端用户的安装、启动、会话、状态、审批、工具调用和输出体验。
4. 让后续开发代理能基于明确 contract 实现 runtime，而不是自行解释产品意图。
5. 让测试代理能基于验收标准验证 CLI 行为、状态流转、工具边界和安全审批。
6. 让审核代理能基于 OpenAI Agents SDK 要求检查 agent goal、input shape、expected output、tools、state、approval gates 和 prove command。
7. 兼容现有 Python 能力，但不把 Python 服务端脚本形态作为最终产品体验。

## 4. 非目标

- 不在本阶段实现 IDE 插件、GitHub App、Web 控制台或桌面 GUI。
- 不在本阶段自动修改目标项目代码、自动提交、自动推送或自动创建 PR。
- 不在本阶段把所有现有 Python 模块重写为 TypeScript。
- 不在本阶段引入长期后台服务作为默认运行方式。
- 不在本阶段默认启用 sandbox agent。只有当需要 workspace isolation 或 resumable filesystem state 时，才允许使用 sandbox agent。
- 不在本阶段支持无限制 shell 执行、任意文件写入或无审批远程副作用。
- 不在本阶段承诺完整复刻 Claude Code，只借鉴其客户端 CLI 产品形态和工程组织思路。

## 5. 客户端优先技术栈建议

### 5.1 推荐分层

| 层级 | 建议技术 | 职责 | 说明 |
| --- | --- | --- | --- |
| CLI 客户端入口 | TypeScript / Node.js | 命令解析、终端交互、安装分发、跨平台体验 | 更接近现代终端客户端生态，便于 npm、Homebrew、WinGet、shell installer 分发 |
| Agent runtime contract | OpenAI Agents SDK | agent 定义、工具 schema、审批 gate、状态约束、prove command | 必须按 SDK 规范先定义 contract，再实现工具 |
| 现有能力适配层 | Python 或本地子进程 | 复用现有扫描、Markdown 生成、Issue fallback 等能力 | MVP 可通过受控子进程或模块边界复用，后续再评估迁移 |
| 配置与状态 | 本地配置文件 + 会话状态文件 | 保存非敏感偏好、最近项目、会话草稿、输出路径 | API key 不得明文写入仓库或日志 |
| 安装分发 | shell script、Homebrew、Windows PowerShell、WinGet、npm 包 | 用户获取与升级 CLI | 参考 Claude Code 多安装通道，但 MVP 可先定义规范 |
| 测试与验收 | CLI smoke、contract tests、tool safety tests、golden Markdown tests | 证明 runtime 行为稳定 | prove command 必须可自动执行 |

### 5.2 语言与边界建议

- CLI shell 应优先面向 TypeScript / Node.js 设计，因为客户端分发、终端交互、跨平台二进制包装和 npm 生态更自然。
- 现有 Python 能力不应立即废弃。MVP 可以把 Python 作为内部 engine，但必须通过清晰、稳定的 CLI/JSON contract 调用。
- 所有跨语言边界必须使用结构化 JSON 输入输出，不允许依赖非结构化 stdout 文案解析。
- Python engine 的职责应收敛到确定性任务：项目扫描、上下文摘要、Markdown 生成、Issue 文件写入等。
- TypeScript CLI 的职责应收敛到用户体验：命令、交互、状态、审批、调用 OpenAI Agents SDK runtime、展示结果。

## 6. Claude Code 可借鉴点

已核实事实：Claude Code 是 “lives in your terminal” 的 agentic coding tool，支持终端、IDE、GitHub，安装方式包括 shell script、Homebrew、Windows PowerShell、WinGet，仓库语言包含 Shell、Python、TypeScript、PowerShell、Dockerfile。

本项目可借鉴以下方向：

1. 终端为主入口：用户应通过一个短命令进入 agent 工作流，而不是先理解 Python 模块结构。
2. 多平台安装意识：产品文档和后续实现应预留 shell script、Homebrew、Windows PowerShell、WinGet 等安装路径。
3. 多语言工程组织：允许 Shell / TypeScript / Python / PowerShell / Dockerfile 共存，但每种语言必须有明确职责。
4. Agentic workflow：CLI 不只是参数解析器，还应管理会话、上下文、工具调用、审批和输出。
5. 生态扩展方向：MVP 聚焦终端，但架构上保留未来对 IDE、GitHub、CI 审核场景的扩展点。
6. 本地优先体验：默认在用户本机运行、读取本地项目上下文、生成本地工件，并显式审批任何外部副作用。

不可直接照搬的点：

- 不默认具备代码编辑权限。
- 不默认运行目标项目命令。
- 不默认把 QA-to-Dev 变成通用 coding agent。
- 不为了“像 Claude Code”牺牲当前产品的只读、安全、需求标准化优势。

## 7. OpenAI Developers 合规要求

### 7.1 App Contract 必填项

后续开发在写代码前，必须先在实现文档或代码注释中固定以下 app contract：

| Contract 字段 | 本项目要求 |
| --- | --- |
| agent goal | 将 QA 输入和项目上下文转化为标准化、可执行、可审核的开发任务说明 |
| input shape | QA 文本、目标项目路径、可选文档文件、可选文档 URL、输出模式、Issue 选项、审批选项 |
| expected output | 结构化 Markdown 任务、Codex/agent 执行提示、待确认问题、风险点、可选 Issue Markdown |
| tools | 只读项目扫描、文档收集、Prompt 构建、LLM 生成、Markdown 写入、Issue 写入、可选远程 Issue 创建 |
| state | 当前项目、QA 草稿、文档列表、扫描摘要、待确认问题、生成结果、审批记录、输出路径 |
| approval gates | LLM 请求、本地写文件、本地 Issue、远程 Issue、任何 shell 或 git 行为 |
| prove command | 一条可在本地执行的 smoke/test 命令，证明 CLI runtime contract 可用 |

### 7.2 Tool 规范

- 工具副作用必须窄。每个工具只做一类事，例如 scan、collect docs、generate、write markdown、create issue。
- 工具 schema 必须清晰。输入字段、必填字段、可选字段、默认值、错误码和输出结构都要可测试。
- 工具输出必须结构化。跨 runtime 通信使用 JSON，不允许测试依赖人类文案。
- 文件写入工具必须限制目标目录，并拒绝写入被分析项目的敏感目录。
- 远程 Issue 创建必须先展示 repo、title、body 摘要，并要求强确认。
- 任何危险行为必须有 guardrails 和 human review，包括 shell、git、网络写操作、批量文件写入、删除、覆盖。

### 7.3 Sandbox Agent 使用条件

默认不使用 sandbox agent。只有满足以下至少一项时才允许引入：

- 需要隔离 workspace 来运行不可信项目分析。
- 需要可恢复的文件系统状态。
- 需要在隔离环境中生成或比较多份工件。
- 需要把 agent 的文件副作用限制在独立 workspace 中。

即使使用 sandbox agent，也必须继续遵守人类审批和最小权限原则。

## 8. 功能说明书写标准

产品经理输出的需求说明必须作为后续代理的执行 contract。每个功能条目必须包含以下字段：

```markdown
### 功能名称

- 用户目标：
- 触发方式：
- 输入：
- 前置条件：
- 主流程：
- 异常流程：
- 输出：
- 状态变化：
- 工具调用：
- 审批要求：
- 安全边界：
- 验收标准：
- 非目标：
```

写作规则：

- 使用可观察行为描述，不写“优化体验”“智能处理”等模糊词。
- 所有 CLI 命令、参数、状态名、文件路径、输出字段必须明确。
- 涉及 API 或工具调用时，必须写清输入 shape 和 expected output。
- 涉及副作用时，必须写清 approval gate。
- 涉及失败时，必须写清错误展示和是否保留会话状态。
- 涉及缺失信息时，必须进入“待确认问题”，不得让模型自行编造。
- 涉及跨平台行为时，必须列出 Windows PowerShell、POSIX shell 的差异。
- 涉及后续开发任务时，必须给出可执行 prove command。
- 测试代理必须能从文档中直接提取测试用例。
- 审核代理必须能从文档中直接检查安全边界和 OpenAI Agents SDK contract。

## 9. MVP 功能范围

### 9.1 必须包含

1. 客户端 CLI 入口规划：统一命令名，例如 `qadev`。
2. Batch 模式兼容：保留现有非交互命令能力。
3. Interactive 模式升级：以终端会话管理 QA 输入、项目、文档、扫描、预览、生成、保存和 Issue。
4. App contract 文件：明确 agent goal、input shape、expected output、tools、state、approval gates、prove command。
5. 工具 schema 设计：为扫描、文档收集、生成、写入、Issue 创建定义结构化输入输出。
6. 客户端状态模型：定义 session state、stale state、approval record、generated artifact。
7. OpenAI Agents SDK 适配策略：先以单 agent + 明确工具为主，不提前拆多 agent。
8. 受控 Python engine 复用策略：保留现有能力，但必须通过结构化 contract 调用。
9. 安全审批：LLM 请求、写文件、创建 Issue、远程副作用必须确认。
10. Prove command：提供至少一条本地命令证明 CLI runtime 可启动、可生成本地任务、不会修改目标项目。
11. 文档输出标准：生成任务仍必须包含背景、测试输入摘要、当前项目上下文、关键代码位置、开发目标、实现要求、验收标准、风险点、待确认问题和 agent prompt。

### 9.2 暂不包含

- IDE 插件。
- GitHub App。
- 自动代码修改。
- 自动 PR。
- 长期后台 daemon。
- 多 agent 协作编排。
- 完整 sandbox workspace。
- 云端同步。
- 用户账号系统。

## 10. 开发任务拆分

### P0：Contract 与架构冻结

- 新增 runtime app contract 文档。
- 定义 CLI 命令、参数、状态机和工具 schema。
- 明确 TypeScript CLI 与 Python engine 的边界。
- 明确 OpenAI Agents SDK 入口方式、单 agent 指令、工具列表和审批 gate。
- 定义 prove command 和最小 smoke 测试。

### P0：客户端 CLI 骨架

- 提供 `qadev --help`、`qadev --version`、`qadev run`、`qadev interactive` 的命令规划。
- 确认 Windows PowerShell 和 POSIX shell 下的调用格式。
- 输出错误必须包含原因、下一步建议和非零退出码。
- 不得要求用户理解 Python 模块路径才能使用核心功能。

### P0：结构化工具适配

- 将现有扫描、文档收集、prompt 构建、本地生成、Markdown 写入、Issue 写入封装为结构化工具。
- 每个工具必须有 JSON input、JSON output、错误结构和测试用例。
- 文件读写工具必须继续忽略 `.git`、`.env*`、`lib`、依赖目录和生成目录。

### P0：交互式 runtime 状态

- 定义 session state：project、input、docs、scan、questions、generated、approvals、artifacts。
- 修改输入、项目或文档后，scan 与 generated 必须标记为 stale。
- `/status` 不得展示密钥、完整敏感文档或不可公开路径内容。

### P0：审批与安全

- LLM 请求前必须展示 provider、model、输入摘要和费用/网络提示。
- 本地写文件前必须展示目标路径和是否覆盖。
- 本地 Issue 前必须展示 issue title 和输出路径。
- 远程 Issue 前必须展示 repo、title、body 摘要，并要求 typed confirmation。
- 默认禁止自动 shell、git、build、test、install、commit、push。

### P1：安装与分发规划

- 定义 shell installer、Homebrew、Windows PowerShell、WinGet、npm 包的目标体验。
- MVP 可先实现一种安装方式，但文档必须保留多通道策略。
- 安装后用户应能运行 `qadev --help`。

### P1：Agents SDK 增强

- 在单 agent 证明可行后，再评估 structured output、handoff、eval harness 或 sandbox agent。
- 增加 agent eval cases：happy path、缺失证据、禁止工具调用、审批 gate、远程 Issue 失败 fallback。

### P2：生态扩展

- IDE 集成。
- GitHub issue/PR 审核工作流。
- CI 中的需求质量检查。
- 会话恢复和历史记录。
- 可插拔 provider 和工具市场。

## 11. 验收标准

### 11.1 文档验收

- `docs/client-first-runtime-plan.md` 存在。
- 文档包含背景、用户原话摘要、产品目标、非目标、客户端优先技术栈建议、Claude Code 可借鉴点、OpenAI Developers 合规要求、功能说明书写标准、MVP 功能范围、开发任务拆分、验收标准、风险点、待确认问题、给开发工程师代理的执行说明。
- 文档明确当前分支为 `feature/client-first-cli-runtime`。
- 文档明确本阶段不改代码实现。
- 文档明确产品需求必须标准化、可执行、无歧义。

### 11.2 后续实现验收

- 用户可以通过客户端 CLI 命令进入 batch 或 interactive 工作流。
- CLI 不要求用户直接运行 Python 模块才能完成主流程。
- App contract 中的 agent goal、input shape、expected output、tools、state、approval gates、prove command 均已落地。
- 每个工具都有清晰 schema、窄副作用和结构化错误。
- 默认不修改目标项目代码。
- 默认不运行目标项目 build、test、install、git 命令。
- 所有写文件、LLM 请求和远程副作用均有审批 gate。
- `prove command` 能在本地证明：CLI 可启动、可用本地模式生成任务、目标项目未被修改。
- 测试覆盖命令解析、状态流转、stale 标记、审批 gate、工具 schema、错误路径、安全边界。
- 审核报告能明确列出是否符合 OpenAI Agents SDK contract。

## 12. 风险点

- TypeScript CLI 与 Python engine 并存会增加构建、安装、测试复杂度。
- 如果 contract 不稳定，后续开发代理可能把 stdout 文案当接口，导致测试脆弱。
- 如果过早引入多 agent 或 sandbox agent，会增加复杂度并模糊 MVP 验收。
- 如果为了客户端体验放宽文件写入或 shell 权限，会破坏当前产品的安全定位。
- 如果 OpenAI Agents SDK 适配只停留在“能调用模型”，而没有工具 schema、审批 gate 和 prove command，则不满足合规目标。
- 多平台安装会带来路径、权限、shell quoting、Windows PowerShell 编码等差异。
- 远程 Issue、URL 文档、LLM 请求都依赖外部网络和认证，必须有本地 fallback。
- 需求说明如果继续使用模糊词，会直接降低开发、测试、审核代理的执行质量。

## 13. 待确认问题

1. 最终 CLI 命令名是否确定为 `qadev`，还是继续使用现有包入口名。
2. MVP 是否必须实现 TypeScript CLI，还是先规划 TypeScript shell、暂以 Python CLI 验证 contract。
3. OpenAI Agents SDK 适配优先使用 Python SDK 还是 TypeScript SDK。
4. 是否要求第一版安装方式支持 Windows PowerShell，还是先支持 npm / pip editable。
5. 是否允许 interactive session 写入用户级配置目录，例如 `%APPDATA%` 或 `~/.config`。
6. 是否需要会话恢复，还是 MVP 只保留内存状态。
7. 远程 Issue 第一版是否继续依赖 `gh` / `glab`，还是改为内置 API client。
8. 后续是否允许在用户显式审批后运行目标项目测试命令。
9. 是否需要把生成任务质量做成单独 eval gate，阻止低质量需求进入开发代理。
10. 是否需要为中文、英文或双语输出分别定义模板。

## 14. 给开发工程师代理的执行说明

开发工程师代理在实现本需求时必须遵守以下顺序：

1. 先阅读本文件、`docs/product-plan.md`、`docs/terminal-interactive-mode-plan.md` 和 `README.md`。
2. 不要先写代码。先产出或更新 app contract，明确 agent goal、input shape、expected output、tools、state、approval gates、prove command。
3. 识别真实入口、命令路径、现有 Python engine 能力和测试结构。
4. 冻结 CLI 命令与工具 schema 后，再实现客户端 runtime。
5. 优先保证 batch 兼容和 interactive 基础状态流，不要先做 IDE、GitHub App 或 sandbox agent。
6. 每增加一个工具，必须同时增加 schema、错误结构、审批要求和测试。
7. 每增加一个副作用，必须证明有 human review 或 typed confirmation。
8. 不得修改 `./lib` 目录。
9. 不得把 API key、token、`.env` 内容写入日志、Issue、Markdown 输出或测试 fixture。
10. 不得默认运行目标项目 build、test、install、git、shell 命令。
11. 实现完成后必须运行 prove command，并在交付说明中写明验证结果、未验证项和剩余风险。
12. 如果发现产品文档与现有实现冲突，先更新设计说明或提出待确认问题，不要自行扩大实现范围。

建议首个 prove command 形式如下，具体命令可按最终包管理器调整：

```powershell
qadev run --project . --input "验证客户端优先 CLI runtime 是否能生成标准化开发任务" --local-only --print-prompt
```

该命令必须满足：

- 不发起 LLM 请求。
- 不修改被分析项目。
- 不创建 Issue。
- 输出结构化 prompt 或任务预览。
- 失败时返回非零退出码并展示可执行下一步。
