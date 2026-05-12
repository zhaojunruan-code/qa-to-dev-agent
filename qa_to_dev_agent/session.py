from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .project_scan import ProjectContext
from .safety import validate_readable_user_file


@dataclass
class PendingQuestion:
    question_id: str
    text: str


@dataclass
class InteractiveSessionState:
    project_path: Path | None = None
    qa_input: str = ""
    docs_files: list[Path] = field(default_factory=list)
    docs_urls: list[str] = field(default_factory=list)
    docs_timeout: int = 15
    max_files: int = 80
    project_context: ProjectContext | None = None
    supplemental_materials: str | None = None
    pending_questions: list[PendingQuestion] = field(default_factory=list)
    answered_questions: dict[str, str] = field(default_factory=dict)
    generated_prompt: str | None = None
    generated_task: str | None = None
    output_path: Path | None = None
    issue_title: str | None = None
    issue_repository: str | None = None
    local_only: bool = False
    dirty: bool = False

    def append_input(self, text: str) -> None:
        cleaned = text.strip()
        if not cleaned:
            return
        self.qa_input = f"{self.qa_input.rstrip()}\n{cleaned}".strip()
        self.mark_stale()

    def set_project(self, path: str) -> None:
        self.project_path = Path(path).expanduser().resolve()
        self.mark_stale()

    def add_doc_file(self, path: str) -> None:
        self.docs_files.append(validate_readable_user_file(path, "supplemental document"))
        self.mark_stale()

    def add_doc_url(self, url: str) -> None:
        self.docs_urls.append(url)
        self.mark_stale()

    def remove_doc(self, index: int) -> str:
        docs = self.docs_files + [Path(url) for url in self.docs_urls]
        if index < 1 or index > len(docs):
            raise ValueError("Document index out of range")
        if index <= len(self.docs_files):
            removed = str(self.docs_files.pop(index - 1))
        else:
            removed = self.docs_urls.pop(index - len(self.docs_files) - 1)
        self.mark_stale()
        return removed

    def mark_stale(self) -> None:
        self.project_context = None
        self.supplemental_materials = None
        self.pending_questions = []
        self.generated_prompt = None
        self.generated_task = None
        self.dirty = True

    def mark_generated(self, task: str) -> None:
        self.generated_task = task
        self.dirty = False

    def reset(self) -> None:
        self.__dict__.update(InteractiveSessionState().__dict__)

    def status_lines(self) -> list[str]:
        return [
            "Session",
            f"- Project: {self.project_path if self.project_path else 'not selected'}",
            f"- QA input: {len(self.qa_input)} chars",
            f"- Docs: {len(self.docs_files)} files, {len(self.docs_urls)} URLs",
            f"- Scan: {'ready' if self.project_context else 'not run'}",
            f"- Pending questions: {len(self.pending_questions)}",
            f"- Generated task: {'yes' if self.generated_task else 'no'}",
        ]


class InteractiveSession(InteractiveSessionState):
    def __init__(self, project: str | None = None, last_result: str | None = None) -> None:
        super().__init__()
        if project:
            self.project_path = Path(project).expanduser().resolve()
        self.generated_task = last_result

    @property
    def project(self) -> str | None:
        return str(self.project_path) if self.project_path else None

    @property
    def context(self) -> ProjectContext | None:
        return self.project_context

    @property
    def last_result(self) -> str | None:
        return self.generated_task

    @last_result.setter
    def last_result(self, value: str | None) -> None:
        self.generated_task = value
