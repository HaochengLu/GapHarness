"""Small OpenAI-compatible chat client used by profiler experiments.

Secrets are read from environment variables only. Do not write API keys to
benchmark files, reports, or source-controlled configuration.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Tuple


class LLMClientError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ChatResponse:
    content: str
    model: str
    usage: Mapping[str, object]
    raw: Mapping[str, object]


class OpenAICompatibleClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: int = 90,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key or os.environ.get("GAPHARNESS_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.base_url = (
            base_url
            or os.environ.get("GAPHARNESS_BASE_URL")
            or os.environ.get("OPENAI_BASE_URL")
            or "https://api.openai.com"
        ).rstrip("/")
        self.model = model or os.environ.get("GAPHARNESS_MODEL") or "gpt-5.5"
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        if not self.api_key:
            raise LLMClientError("Missing GAPHARNESS_API_KEY or OPENAI_API_KEY.")

    def chat_json(
        self,
        messages: Iterable[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 1200,
        response_format: Optional[Mapping[str, object]] = None,
    ) -> ChatResponse:
        payload: Dict[str, object] = {
            "model": self.model,
            "messages": [message.__dict__ for message in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        data = self._post("/v1/chat/completions", payload)
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMClientError("Unexpected chat completion response: %s" % data) from exc
        return ChatResponse(
            content=content,
            model=str(data.get("model", self.model)),
            usage=data.get("usage", {}),
            raw=data,
        )

    def list_models(self) -> List[str]:
        data = self._get("/v1/models")
        return [str(item["id"]) for item in data.get("data", []) if "id" in item]

    def _get(self, path: str) -> Mapping[str, object]:
        request = urllib.request.Request(
            self.base_url + path,
            headers={"Authorization": "Bearer " + self.api_key},
        )
        return self._open_json(request)

    def _post(self, path: str, payload: Mapping[str, object]) -> Mapping[str, object]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        return self._open_json(request)

    def _open_json(self, request: urllib.request.Request) -> Mapping[str, object]:
        last_error: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                last_error = LLMClientError("HTTP %s: %s" % (exc.code, body[:1000]))
            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc
            if attempt < self.max_retries:
                time.sleep(1.5 * (attempt + 1))
        raise LLMClientError(str(last_error))


def parse_json_object(text: str) -> Mapping[str, object]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return value
