"""Agent loop: run one (task, treatment) cell and collect a RunResult."""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field

from .config import Task, Treatment
from .models import ChatClient, Usage
from .tools import execute_tool, make_tool_specs

BASE_SYSTEM = "You are a helpful assistant. Answer the user's task to the best of your ability."

_MAX_STEPS = 8


@dataclass
class RunResult:
    task_id: str
    treatment_id: str
    model: str
    run_index: int
    final_text: str = ""
    transcript: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    wall_time: float = 0.0
    errors: int = 0
    cot_depth: int = 0
    error_msg: str = ""

    @property
    def metrics(self) -> dict:
        return {
            "latency_s": round(self.wall_time, 3),
            "tokens": self.usage.total,
            "prompt_tokens": self.usage.prompt_tokens,
            "completion_tokens": self.usage.completion_tokens,
            "tool_calls": len(self.tool_calls),
            "errors": self.errors,
            "cot_depth": self.cot_depth,
        }

    def to_dict(self) -> dict:
        d = asdict(self)
        d["usage"] = {
            "prompt_tokens": self.usage.prompt_tokens,
            "completion_tokens": self.usage.completion_tokens,
        }
        return d


def _system_prompt(treatment: Treatment) -> str:
    if treatment.text:
        return BASE_SYSTEM + "\n\n" + treatment.text
    return BASE_SYSTEM


def _count_steps(text: str) -> int:
    n = 0
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^\d+[\.\)]", s):
            n += 1
        elif re.match(r"^(step\s*\d+|[-*•]\s*step\b)", s, re.IGNORECASE):
            n += 1
    return n


def run_cell(
    client: ChatClient, task: Task, treatment: Treatment, run_index: int = 0
) -> RunResult:
    result = RunResult(
        task_id=task.id,
        treatment_id=treatment.id,
        model=client.model,
        run_index=run_index,
    )

    if task.tools and client.provider.type == "anthropic":
        result.error_msg = "Anthropic tool-use not yet supported"
        result.errors = 1
        return result

    system = _system_prompt(treatment)
    messages: list[dict] = [{"role": "user", "content": task.prompt}]
    tools = make_tool_specs(task.tools) if task.tools else None

    start = time.time()
    try:
        for _ in range(_MAX_STEPS):
            comp = client.complete(system, messages, tools)
            result.usage.prompt_tokens += comp.usage.prompt_tokens
            result.usage.completion_tokens += comp.usage.completion_tokens

            if comp.tool_calls:
                assistant_msg = {
                    "role": "assistant",
                    "content": comp.text or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                        }
                        for tc in comp.tool_calls
                    ],
                }
                messages.append(assistant_msg)
                result.transcript.append(
                    {"role": "assistant", "text": comp.text, "tool_calls": [asdict(tc) for tc in comp.tool_calls]}
                )
                for tc in comp.tool_calls:
                    try:
                        out = execute_tool(tc.name, tc.arguments)
                        result.tool_calls.append(
                            {"name": tc.name, "arguments": tc.arguments, "result": out}
                        )
                    except Exception as exc:  # noqa: BLE001
                        result.errors += 1
                        out = f"ERROR: {exc}"
                        result.tool_calls.append(
                            {"name": tc.name, "arguments": tc.arguments, "error": str(exc)}
                        )
                    messages.append({"role": "tool", "tool_call_id": tc.id, "content": out})
            else:
                result.final_text = comp.text or ""
                result.transcript.append({"role": "assistant", "content": result.final_text})
                break
        else:
            result.final_text = result.final_text or "(no final answer produced within step limit)"
    except Exception as exc:  # noqa: BLE001
        result.errors += 1
        result.error_msg = str(exc)
        if not result.final_text:
            result.final_text = "(error)"

    result.wall_time = time.time() - start
    result.cot_depth = _count_steps(result.final_text)
    return result
