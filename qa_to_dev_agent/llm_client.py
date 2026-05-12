from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import LlmConfig


class LlmError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


class OpenAICompatibleClient:
    """Small dependency-free client for OpenAI-compatible chat completions."""

    def __init__(self, config: LlmConfig, timeout_seconds: int = 90) -> None:
        self._config = config
        self._timeout_seconds = timeout_seconds

    def complete(self, messages: list[ChatMessage], temperature: float = 0.2) -> str:
        self._config.require_ready()
        payload = {
            "model": self._config.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature,
        }
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        if self._config.http_referer:
            headers["HTTP-Referer"] = self._config.http_referer
        if self._config.app_title:
            headers["X-Title"] = self._config.app_title

        request = urllib.request.Request(
            self._config.chat_completions_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = _read_error_body(exc)
            raise LlmError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LlmError(f"LLM request failed: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise LlmError("LLM response was not valid JSON") from exc

        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError("LLM response did not include choices[0].message.content") from exc


def _read_error_body(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        return "<unable to read response body>"
    return body[:2000] if body else "<empty response body>"
