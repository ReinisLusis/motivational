"""Experiment orchestration: run the sweep, save artifacts, build summaries/charts/report."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from .analyze import make_df, summarize
from .charts import build_all
from .config import (
    load_judge_config,
    load_providers,
    load_tasks,
    load_treatments,
    resolve_judges,
)
from .models import make_client
from .report import build_report
from .runner import run_cell
from .scorer import score


def _select_tasks(all_tasks, flt):
    if not flt or "all" in flt:
        return all_tasks
    by_id = {t.id: t for t in all_tasks}
    return [by_id[i] for i in flt if i in by_id]


def _select_treatments(all_tr, flt):
    if not flt or "all" in flt:
        return all_tr
    by_id = {t.id: t for t in all_tr}
    return [by_id[i] for i in flt if i in by_id]


def run_experiment(
    provider_name: str,
    model: str | None = None,
    treatments: list[str] | None = None,
    tasks: list[str] | None = None,
    reps: int = 5,
    temperature: float | None = None,
    workers: int = 1,
    out: Path | None = None,
    seed: int = 42,
    judges: list[str] | None = None,
) -> Path:
    providers = load_providers()
    provider = providers[provider_name]
    if temperature is not None:
        provider.temperature = temperature

    judge_provs = resolve_judges(judges)
    judge_clients = [make_client(jp) for jp in judge_provs]
    jp_desc = ", ".join(f"{c.provider.name}/{c.model}" for c in judge_clients)

    subject_client = make_client(provider, model)

    all_tr = load_treatments()
    all_tasks = load_tasks()
    trs = _select_treatments(all_tr, treatments)
    tasks = _select_tasks(all_tasks, tasks)
    judge_cfg = load_judge_config()

    ts = time.strftime("%Y%m%d-%H%M%S")
    run_dir = (out or Path("results")) / f"{provider_name}-{subject_client.model}-{ts}"
    (run_dir / "responses").mkdir(parents=True, exist_ok=True)
    (run_dir / "figures").mkdir(parents=True, exist_ok=True)

    meta = {
        "provider": provider_name,
        "model": subject_client.model,
        "judges": [f"{c.provider.name}/{c.model}" for c in judge_clients],
        "reps": reps,
        "n_tasks": len(tasks),
        "n_treatments": len(trs),
        "temperature": provider.temperature,
        "seed": seed,
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "treatments": [t.id for t in trs],
        "tasks": [t.id for t in tasks],
    }
    (run_dir / "config.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    cells = [(task, tr, rep) for task in tasks for tr in trs for rep in range(reps)]

    records: list[dict] = []

    def run_one(cell):
        task, tr, rep = cell
        res = run_cell(subject_client, task, tr, run_index=rep)
        sc = score(judge_clients, judge_cfg, task, res)
        return task, tr, rep, res, sc

    print(f"Running {len(cells)} cells ({len(tasks)} tasks x {len(trs)} treatments x {reps} reps) "
          f"on {provider_name}/{subject_client.model}, judges={jp_desc}")

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(run_one, c): c for c in cells}
            for i, fut in enumerate(as_completed(futures), 1):
                records.append(_process_cell(fut.result(), run_dir))
                if i % 25 == 0:
                    print(f"  ...{i}/{len(cells)} done")
    else:
        for i, c in enumerate(cells, 1):
            records.append(_process_cell(run_one(c), run_dir))
            if i % 10 == 0 or i == len(cells):
                print(f"  ...{i}/{len(cells)} done")

    df = make_df(records)
    df.to_csv(run_dir / "records.csv", index=False)
    (run_dir / "records.json").write_text(
        json.dumps([{k: v for k, v in r.items() if k != "final_text"} for r in records], indent=2),
        encoding="utf-8",
    )

    summary = summarize(df)
    summary["treatment"].to_csv(run_dir / "summary_treatment.csv", index=False)
    summary["cell"].to_csv(run_dir / "summary_cell.csv", index=False)
    summary["delta"].to_csv(run_dir / "summary_delta.csv", index=False)

    figures = build_all(df, summary["cell"], summary["delta"], run_dir / "figures")
    report_path = build_report(summary, meta, figures, run_dir / "report.md")

    print(f"\nDone. Results in: {run_dir}")
    print(f"  report: {report_path.relative_to(run_dir.parent.parent) if run_dir.parent else report_path}")
    return run_dir


def _process_cell(bundle, run_dir: Path) -> dict:
    task, tr, rep, res, sc = bundle
    rec = {
        "task_id": task.id,
        "category": task.category,
        "difficulty": task.difficulty,
        "treatment_id": tr.id,
        "treatment_name": tr.name,
        "run_index": rep,
        "model": res.model,
        "scorer": task.scorer,
        "passed": sc.passed,
        "score": sc.score,
        "final_text": res.final_text,
        "error_msg": res.error_msg,
    }
    rec.update(res.metrics)

    fname = f"{task.id}__{tr.id}__r{rep}.json"
    (run_dir / "responses" / fname).write_text(
        json.dumps(
            {
                "task_id": task.id,
                "treatment_id": tr.id,
                "treatment_text": tr.text,
                "run_index": rep,
                "model": res.model,
                "result": res.to_dict(),
                "score": asdict(sc),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return rec
