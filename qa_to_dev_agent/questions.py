from __future__ import annotations

from .session import InteractiveSessionState, PendingQuestion


def generate_pending_questions(state: InteractiveSessionState) -> list[PendingQuestion]:
    questions: list[PendingQuestion] = []
    context = state.project_context
    if not state.qa_input.strip():
        questions.append(PendingQuestion("q1", "请补充测试工程师的需求、问题描述或验收目标。"))
    if context and not context.entry_files:
        questions.append(PendingQuestion("q2", "当前扫描未识别明确入口文件，请确认目标页面、模块或运行入口。"))
    if context and not context.key_code_locations:
        questions.append(PendingQuestion("q3", "当前扫描未命中需求相关代码文件，请补充页面名、接口名、字段名或关键词。"))
    if state.docs_urls and state.supplemental_materials and "Unable to fetch document" in state.supplemental_materials:
        questions.append(PendingQuestion("q4", "存在无法访问的文档链接，请确认是否需要粘贴关键内容或更换链接。"))
    state.pending_questions = questions
    return questions


def answered_questions_block(state: InteractiveSessionState) -> str:
    if not state.answered_questions:
        return ""
    lines = ["## 用户已回答的待确认问题"]
    for question_id, answer in state.answered_questions.items():
        lines.append(f"- {question_id}: {answer}")
    return "\n".join(lines)
