from __future__ import annotations

from .llm_client import ChatMessage
from .project_scan import ProjectContext


OUTPUT_TEMPLATE = """# 开发任务标题

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
"""


SYSTEM_PROMPT = """你是 QA-to-Dev Prompt Agent。

你的职责是把测试工程师提供的简略说明转换成开发工程师或 AI 编程工具可以直接执行的结构化开发任务说明。

必须遵守：
- 默认只读分析，不要求直接修改代码。
- 不编造接口、字段、配置、业务规则或文件路径。
- 如果项目上下文不足，把不确定项放入“待确认问题”。
- 输出面向开发工程师，而不是只面向测试工程师。
- 保持固定 Markdown 结构。
- `Codex CLI Prompt` 必须是一段可直接交给 Codex CLI 的完整任务说明。
"""


def build_messages(qa_input: str, context: ProjectContext, extra_docs: str | None = None) -> list[ChatMessage]:
    user_prompt = build_user_prompt(qa_input=qa_input, context=context, extra_docs=extra_docs)
    return [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=user_prompt),
    ]


def build_user_prompt(qa_input: str, context: ProjectContext, extra_docs: str | None = None) -> str:
    docs_block = extra_docs.strip() if extra_docs and extra_docs.strip() else "无"
    return f"""请根据以下测试输入和当前项目上下文，生成结构化开发任务说明。

必须使用这个输出结构，不要删除章节：

{OUTPUT_TEMPLATE}

## 测试工程师输入

{qa_input.strip()}

## 补充文档或材料

{docs_block}

## 当前项目轻量扫描结果

{context.to_markdown()}
"""
