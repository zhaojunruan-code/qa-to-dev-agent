from __future__ import annotations

from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def collect_supplemental_materials(paths: list[str], urls: list[str], timeout_seconds: int = 15) -> str | None:
    blocks: list[str] = []
    for path in paths:
        blocks.append(_read_local_doc(path))
    for url in urls:
        blocks.append(_fetch_url(url, timeout_seconds=timeout_seconds))
    return "\n\n".join(block for block in blocks if block.strip()) or None


def _read_local_doc(path: str) -> str:
    source = Path(path).expanduser()
    text = source.read_text(encoding="utf-8", errors="replace")
    return f"### Local document: {source}\n\n{text[:8000]}"


def _fetch_url(url: str, timeout_seconds: int) -> str:
    request = Request(url, headers={"User-Agent": "qa-to-dev-prompt-agent/0.1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read(12000).decode("utf-8", errors="replace")
    except HTTPError as exc:
        return f"### Document URL: {url}\n\nUnable to fetch document. HTTP status: {exc.code}."
    except URLError as exc:
        return f"### Document URL: {url}\n\nUnable to fetch document. Reason: {exc.reason}."
    except OSError as exc:
        return f"### Document URL: {url}\n\nUnable to fetch document. Reason: {exc}."
    return f"### Document URL: {url}\n\nContent-Type: {content_type}\n\n{body}"
