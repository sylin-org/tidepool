"""Writing results.

Every run writes, under results/<model>/<timestamp>/:
  <measure>.jsonl   one line per item: prompts, raw outputs, judge verdicts
  summary.json      the numbers
  summary.md        the numbers, readable

Raw outputs are the point. Scores without outputs are a feeling with decimals.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", s.lower()).strip("-") or "model"


class RunDir:
    def __init__(self, root: Path, model_name: str, judge_name: str | None):
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.path = root / slug(model_name) / stamp
        self.path.mkdir(parents=True, exist_ok=True)
        self.meta = {
            "model": model_name,
            "judge": judge_name,
            "started": stamp,
            "measures": {},
        }

    def write_items(self, measure: str, rows: list[dict[str, Any]]) -> None:
        with (self.path / f"{measure}.jsonl").open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def record(self, measure: str, summary: dict[str, Any]) -> None:
        self.meta["measures"][measure] = summary

    def finish(self) -> Path:
        (self.path / "summary.json").write_text(
            json.dumps(self.meta, indent=2, ensure_ascii=False), encoding="utf-8")
        (self.path / "summary.md").write_text(self.markdown(), encoding="utf-8")
        return self.path

    def markdown(self) -> str:
        m = self.meta
        lines = [
            f"# Ruler results: `{m['model']}`",
            "",
            f"- judge: `{m['judge']}`",
            f"- run: `{m['started']}`",
            "",
            "| measure | headline | n | notes |",
            "|---|---|---|---|",
        ]
        for name, s in m["measures"].items():
            lines.append(
                f"| {name} | **{s.get('headline', '')}** | {s.get('n', '')} | {s.get('notes', '')} |")
        lines += ["", "Raw outputs are in the `.jsonl` files beside this summary. Read them.", ""]
        return "\n".join(lines)


def pct(num: int, den: int) -> str:
    return "n/a" if den == 0 else f"{100.0 * num / den:.1f}%"
