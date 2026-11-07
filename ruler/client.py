"""Chat clients.

ChatClient speaks the OpenAI-compatible /v1/chat/completions API, which is what
llama.cpp's server (`llama-server`), Ollama (`/v1`), vLLM, and most local
runners expose. No third-party dependencies: urllib only, so a newcomer can run
this with a bare Python.

StubClient is for proving the plumbing works without a model. It returns
canned text so the whole pipeline (prompts -> outputs -> judge -> report) can
be exercised in a second.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol


Message = dict[str, str]  # {"role": "...", "content": "..."}


class Chat(Protocol):
    name: str

    def complete(self, messages: list[Message], *, temperature: float = 0.0,
                 max_tokens: int = 1024) -> str: ...


@dataclass
class ChatClient:
    """OpenAI-compatible chat completions over HTTP."""

    base_url: str
    model: str
    api_key: str = "none"
    timeout: float = 600.0
    retries: int = 3
    extra: dict = field(default_factory=dict)  # passthrough body fields

    @property
    def name(self) -> str:
        return self.model

    def complete(self, messages: list[Message], *, temperature: float = 0.0,
                 max_tokens: int = 1024) -> str:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **self.extra,
        }
        data = json.dumps(body).encode("utf-8")
        url = self.base_url.rstrip("/") + "/chat/completions"
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = json.loads(resp.read().decode("utf-8"))
                return payload["choices"][0]["message"]["content"] or ""
            except (urllib.error.URLError, urllib.error.HTTPError, KeyError,
                    json.JSONDecodeError, TimeoutError) as e:  # pragma: no cover
                last = e
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"chat completion failed after {self.retries} tries: {last}")


@dataclass
class StubClient:
    """Canned responses, for exercising the pipeline without a model.

    `script` maps a substring of the last user message to a reply. Anything
    unmatched gets `default`. Keep it dumb; it exists to prove plumbing.
    """

    name: str = "stub"
    script: dict[str, str] = field(default_factory=dict)
    default: str = "I don't know."

    def complete(self, messages: list[Message], *, temperature: float = 0.0,
                 max_tokens: int = 1024) -> str:
        last = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        for key, reply in self.script.items():
            if key in last:
                return reply
        return self.default
