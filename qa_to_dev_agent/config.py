from __future__ import annotations

import argparse
import os
from dataclasses import dataclass


DEFAULT_BASE_URL = "https://api.openai.com/v1"


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str | None
    model: str | None
    http_referer: str | None = None
    app_title: str | None = None

    @property
    def chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def require_ready(self) -> None:
        missing: list[str] = []
        if not self.api_key:
            missing.append("QADEV_LLM_API_KEY or --api-key")
        if not self.model:
            missing.append("QADEV_LLM_MODEL or --model")
        if missing:
            raise ConfigError("Missing required LLM setting(s): " + ", ".join(missing))


class ConfigError(RuntimeError):
    pass


def load_llm_config(args: argparse.Namespace) -> LlmConfig:
    return LlmConfig(
        base_url=args.base_url or os.getenv("QADEV_LLM_BASE_URL") or DEFAULT_BASE_URL,
        api_key=args.api_key or os.getenv("QADEV_LLM_API_KEY"),
        model=args.model or os.getenv("QADEV_LLM_MODEL"),
        http_referer=args.http_referer or os.getenv("QADEV_LLM_HTTP_REFERER"),
        app_title=args.app_title or os.getenv("QADEV_LLM_APP_TITLE"),
    )
