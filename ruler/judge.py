"""The judge.

Two of the four measures (grind, datacenter) need a reader with a rubric. For
volume that is a model; for trust it should be a different model from the one
being measured, and the raw outputs are always published so a human can
re-judge.

The judge is asked for strict JSON. We parse defensively: models wrap JSON in
prose and code fences no matter how nicely you ask.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from .client import Chat, Message


JUDGE_SYSTEM = (
    "You are a careful, literal grader. You will be given a rubric and a "
    "transcript. Answer ONLY with a single JSON object matching the rubric's "
    "requested fields. No prose before or after. Do not reward length or tone; "
    "grade only what the rubric asks."
)


def extract_json(text: str) -> dict[str, Any] | None:
    """Find the first JSON object in text, tolerating code fences and prose."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
        start = text.find("{", start + 1)
    return None


@dataclass
class Judge:
    client: Chat

    @property
    def name(self) -> str:
        return self.client.name

    def grade(self, rubric: str, transcript: str, *, fields: dict[str, str]) -> dict[str, Any]:
        """Ask the judge to fill `fields` ({name: description}) as JSON."""
        want = "\n".join(f'  "{k}": <{v}>' for k, v in fields.items())
        prompt = (
            f"RUBRIC:\n{rubric}\n\n"
            f"TRANSCRIPT:\n{transcript}\n\n"
            f"Respond with exactly this JSON shape:\n{{\n{want}\n}}"
        )
        messages: list[Message] = [
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": prompt},
        ]
        raw = self.client.complete(messages, temperature=0.0, max_tokens=512)
        parsed = extract_json(raw)
        if parsed is None:
            return {"_error": "unparseable judge output", "_raw": raw}
        parsed["_raw"] = raw
        return parsed


def as_int(v: Any, default: int = 0) -> int:
    try:
        if isinstance(v, bool):
            return int(v)
        return int(round(float(v)))
    except (TypeError, ValueError):
        return default


def as_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() in {"true", "yes", "1", "y"}
    return False
