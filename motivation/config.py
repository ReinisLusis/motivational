"""Config loading: providers, treatments, judge settings, tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
TASKS_DIR = ROOT / "tasks"


def _load(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass
class Provider:
    name: str
    type: str
    base_url: str | None
    api_key_env: str | None
    default_model: str
    temperature: float
    max_tokens: int


@dataclass
class Treatment:
    id: str
    name: str
    text: str


@dataclass
class Task:
    id: str
    category: str
    difficulty: str
    prompt: str
    tools: list[str]
    ground_truth: Any
    scorer: str
    extra: dict = field(default_factory=dict)

    @property
    def uses_tools(self) -> bool:
        return bool(self.tools)


def load_providers() -> dict[str, Provider]:
    raw = _load(CONFIG_DIR / "models.yaml")
    providers: dict[str, Provider] = {}
    for name, p in raw["providers"].items():
        providers[name] = Provider(
            name=name,
            type=p["type"],
            base_url=p.get("base_url"),
            api_key_env=p.get("api_key_env"),
            default_model=p.get("default_model", ""),
            temperature=float(p.get("temperature", 0.7)),
            max_tokens=int(p.get("max_tokens", 2048)),
        )
    return providers


def _resolve_judge_providers(raw: dict, providers: dict[str, Provider]) -> list[Provider]:
    """Build the judge matrix (list of judge providers with resolved models)."""
    resolved: list[Provider] = []
    judges = raw.get("judges")
    if judges:
        for j in judges:
            pname = j["provider"]
            base = providers[pname]
            resolved.append(
                Provider(
                    name=pname,
                    type=base.type,
                    base_url=base.base_url,
                    api_key_env=base.api_key_env,
                    default_model=j.get("model") or base.default_model,
                    temperature=0.0,
                    max_tokens=1024,
                )
            )
    else:
        pname = raw.get("judge_provider", "deepseek")
        base = providers[pname]
        model = raw.get("judge_model") or base.default_model
        resolved.append(
            Provider(
                name=pname,
                type=base.type,
                base_url=base.base_url,
                api_key_env=base.api_key_env,
                default_model=model,
                temperature=0.0,
                max_tokens=1024,
            )
        )
    return resolved


def load_judges() -> list[Provider]:
    raw = _load(CONFIG_DIR / "models.yaml")
    return _resolve_judge_providers(raw, load_providers())


def resolve_judges(specs: list[str] | None) -> list[Provider]:
    """Resolve CLI judge specs of the form 'provider' or 'provider:model'."""
    providers = load_providers()
    if not specs:
        return load_judges()
    out: list[Provider] = []
    for spec in specs:
        parts = spec.split(":", 1)
        pname = parts[0].strip()
        model = parts[1].strip() if len(parts) == 2 else None
        base = providers[pname]
        out.append(
            Provider(
                name=pname,
                type=base.type,
                base_url=base.base_url,
                api_key_env=base.api_key_env,
                default_model=model or base.default_model,
                temperature=0.0,
                max_tokens=1024,
            )
        )
    return out


def load_treatments() -> list[Treatment]:
    raw = _load(CONFIG_DIR / "treatments.yaml")
    return [
        Treatment(id=t["id"], name=t["name"], text=t.get("text", ""))
        for t in raw["treatments"]
    ]


def load_judge_config() -> dict[str, str]:
    raw = _load(CONFIG_DIR / "judge.yaml")
    return {"system": raw["system"], "prompt": raw["prompt"]}


def load_probe_config() -> dict[str, str]:
    raw = _load(CONFIG_DIR / "probe.yaml")
    return {
        "prompt": raw["prompt"],
        "score_system": raw["score_system"],
        "score_prompt": raw["score_prompt"],
    }


def load_tasks() -> list[Task]:
    raw = _load(TASKS_DIR / "tasks.yaml")
    tasks = []
    for t in raw["tasks"]:
        tasks.append(
            Task(
                id=t["id"],
                category=t["category"],
                difficulty=t["difficulty"],
                prompt=t["prompt"],
                tools=t.get("tools", []),
                ground_truth=t["ground_truth"],
                scorer=t["scorer"],
            )
        )
    return tasks
