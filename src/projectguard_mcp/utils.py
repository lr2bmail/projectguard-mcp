from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import PurePosixPath


def normalize_text(value: str | None) -> str:
    return (value or "").strip()


def contains_any(text: str, keywords: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def count_words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))


def safe_path_parts(path: str) -> tuple[str, ...]:
    clean = str(PurePosixPath(path.replace("\\", "/")))
    return tuple(part for part in clean.split("/") if part and part != ".")


def file_ext(path: str) -> str:
    name = safe_path_parts(path)[-1] if safe_path_parts(path) else path
    if "." not in name:
        return ""
    return name.rsplit(".", 1)[-1].lower()
