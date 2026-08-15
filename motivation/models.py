"""Provider-agnostic chat clients (OpenAI-compatible, Anthropic, Mock)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from .config import Provider


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class Completion:
    text: str = ""
    reasoning_content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    finish_reason: str = ""
    raw: Any = None


class ChatClient:
    """Base interface. `complete` returns a Completion for a single model call.

    `messages` excludes the system message (passed separately so Anthropic and
    OpenAI-compatible providers can be handled uniformly).
    """

    def __init__(self, provider: Provider, model: str | None = None):
        self.provider = provider
        self.model = model or provider.default_model

    def complete(
        self, system: str, messages: list[dict], tools: list[dict] | None = None
    ) -> Completion:
        raise NotImplementedError

    def is_mock(self) -> bool:
        return False


class OpenAICompatClient(ChatClient):
    _retries = 5

    def __init__(self, provider: Provider, model: str | None = None):
        super().__init__(provider, model)
        from openai import OpenAI

        key = os.environ.get(provider.api_key_env or "", "")
        self._client = OpenAI(api_key=key or "missing", base_url=provider.base_url)

    def complete(self, system, messages, tools=None):
        from openai import AuthenticationError

        last = None
        for attempt in range(self._retries):
            try:
                return self._complete_once(system, messages, tools)
            except AuthenticationError:
                raise
            except Exception as exc:  # noqa: BLE001 - retry transient/rate-limit errors
                last = exc
                time.sleep(min(2 ** attempt, 20))
        raise last

    def _complete_once(self, system, messages, tools=None):
        full = [{"role": "system", "content": system}] + list(messages)
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=full,
            temperature=self.provider.temperature,
            max_tokens=self.provider.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        resp = self._client.chat.completions.create(**kwargs)
        msg = resp.choices[0].message

        tool_calls = []
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        usage = Usage()
        if getattr(resp, "usage", None):
            usage = Usage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
            )

        return Completion(
            text=msg.content or "",
            reasoning_content=getattr(msg, "reasoning_content", "") or "",
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=resp.choices[0].finish_reason or "",
            raw=resp,
        )


class AnthropicClient(ChatClient):
    def __init__(self, provider: Provider, model: str | None = None):
        super().__init__(provider, model)
        import anthropic

        key = os.environ.get(provider.api_key_env or "", "")
        self._client = anthropic.Anthropic(api_key=key or "missing")

    @staticmethod
    def _to_anthropic_tools(tools):
        out = []
        for t in tools:
            fn = t["function"]
            out.append(
                {
                    "name": fn["name"],
                    "description": fn.get("description", ""),
                    "input_schema": fn.get("parameters", {"type": "object"}),
                }
            )
        return out

    def complete(self, system, messages, tools=None):
        user_msgs = []
        for m in messages:
            if m["role"] in ("user", "assistant"):
                user_msgs.append({"role": m["role"], "content": m.get("content", "")})

        kwargs: dict[str, Any] = dict(
            model=self.model,
            system=system,
            messages=user_msgs,
            max_tokens=self.provider.max_tokens,
            temperature=self.provider.temperature,
        )
        if tools:
            kwargs["tools"] = self._to_anthropic_tools(tools)

        resp = self._client.messages.create(**kwargs)

        text = ""
        tool_calls = []
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.id, name=block.name, arguments=dict(block.input or {}))
                )

        usage = Usage()
        if getattr(resp, "usage", None):
            usage = Usage(
                prompt_tokens=resp.usage.input_tokens or 0,
                completion_tokens=resp.usage.output_tokens or 0,
            )

        return Completion(
            text=text,
            tool_calls=tool_calls,
            usage=usage,
            finish_reason=str(getattr(resp, "stop_reason", "") or ""),
            raw=resp,
        )


class MockClient(ChatClient):
    """Deterministic, offline client for testing the pipeline without an API key."""

    def complete(self, system, messages, tools=None):
        time.sleep(0.001)
        return Completion(
            text="This is a deterministic mock response.",
            tool_calls=[],
            usage=Usage(prompt_tokens=10, completion_tokens=5),
            finish_reason="stop",
        )

    def is_mock(self) -> bool:
        return True


def make_client(provider: Provider, model: str | None = None) -> ChatClient:
    if provider.type == "mock":
        return MockClient(provider, model)
    if provider.type == "anthropic":
        return AnthropicClient(provider, model)
    return OpenAICompatClient(provider, model)
