"""Loading prompt sets.

Prompt sets live in prompts/ as JSONL (one item per line) or JSON. They are
part of the ruler and get edited in daylight like everything else. Keep them
small and legible; a ruler nobody reads is a ruler nobody trusts.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    items = []
    with path.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{n}: bad JSON: {e}") from e
    return items


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def normalize(s: str) -> str:
    """Loose normalization for answer matching: lowercase, strip, collapse spaces,
    drop commas/thousands separators and trailing punctuation."""
    s = s.strip().lower()
    s = s.replace(",", "")
    s = " ".join(s.split())
    return s.rstrip(".!?")


def contains_answer(text: str, answer: str) -> bool:
    """True if `answer` appears in `text` as a whole token.

    Word boundaries matter: the answer "1" must not match inside "12", and
    "Monday" must not match "Mondays" (it won't; that is a different word).
    Answers with symbols ("3/8", "11:15") are matched literally with boundaries
    on whichever ends are alphanumeric.
    """
    a = normalize(answer)
    t = normalize(text)
    if not a:
        return False
    pat = re.escape(a)
    if a[0].isalnum():
        pat = r"(?<![a-z0-9])" + pat
    if a[-1].isalnum():
        pat = pat + r"(?![a-z0-9])"
    return re.search(pat, t) is not None
