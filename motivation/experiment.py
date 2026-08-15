"""Experiment orchestration: run the sweep, save artifacts, build summaries/charts/report."""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path

from .analyze import make_df, summarize
from .charts import build_all
from .config import (
    load_judge_config,
    load_probe_config,
    load_providers,
    load_tasks,
    load_treatments,
    resolve_judges,
)
from .models import make_client
from .report import build_report
from .runner import run_cell
from .scorer import probe_adoption, score


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


def _load_records(run_dir: Path) -> list[dict]:
    jl = run_dir / "records.jsonl"
    if jl.exists():
        return [json.loads(l) for l in jl.read_text(encoding="utf-8").splitlines() if l.strip()]
    j = run_dir / "records.json"
    if j.exists():
        return json.loads(j.read_text(encoding="utf-8"))
    return []


def _write_summary(df, run_dir: Path):
    summary = summarize(df)
    summary["treatment"].to_csv(run_dir / "summary_treatment.csv", index=False)
    summary["cell"].to_csv(run_dir / "summary_cell.csv", index=False)
    summary["delta"].to_csv(run_dir / "summary_delta.csv", index=False)
    return summary


def report_from_dir(run_dir: Path) -> Path:
    """Regenerate summaries, charts and report from a run dir (no API calls)."""
    records = _load_records(run_dir)
    if not records:
        raise ValueError(f"No records found in {run_dir}")
    df = make_df(records)
    summary = _write_summary(df, run_dir)
    meta = json.loads((run_dir / "config.json").read_text(encoding="utf-8")) if (run_dir / "config.json").exists() else {}
    figures = build_all(df, summary["cell"], summary["delta"], run_dir / "figures")
    return build_report(summary, meta, figures, run_dir / "report.md")


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
    resume: Path | None = None,
    probe: bool = False,
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
    probe_cfg = load_probe_config() if probe else None
    probe_prompt = probe_cfg["prompt"] if probe_cfg else None

    if resume is not None:
        run_dir = resume
        records = _load_records(run_dir)
        done = {(r["task_id"], r["treatment_id"], r["run_index"]) for r in records}
        meta = json.loads((run_dir / "config.json").read_text(encoding="utf-8")) if (run_dir / "config.json").exists() else {}
    else:
        ts = time.strftime("%Y%m%d-%H%M%S")
        run_dir = (out or Path("results")) / f"{provider_name}-{subject_client.model}-{ts}"
        records = []
        done = set()
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

    (run_dir / "responses").mkdir(parents=True, exist_ok=True)
    (run_dir / "figures").mkdir(parents=True, exist_ok=True)
    (run_dir / "transcripts").mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    all_cells = [(task, tr, rep) for task in tasks for tr in trs for rep in range(reps)]
    cells = [c for c in all_cells if (c[0].id, c[1].id, c[2]) not in done]
    records_jsonl = run_dir / "records.jsonl"

    def run_one(cell):
        task, tr, rep = cell
        res = run_cell(subject_client, task, tr, run_index=rep, probe_prompt=probe_prompt)
        sc = score(judge_clients, judge_cfg, task, res)
        adoption = (
            probe_adoption(judge_clients, probe_cfg, res.probe_response)
            if probe_cfg and res.probe_response
            else 0.0
        )
        return task, tr, rep, res, sc, adoption

    def record(bundle):
        rec = _process_cell(bundle, run_dir)
        records.append(rec)
        with open(records_jsonl, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    if not cells:
        print("No new cells to run (all already present).")
    else:
        print(f"Running {len(cells)} cells ({len(tasks)} tasks x {len(trs)} treatments x {reps} reps) "
              f"on {provider_name}/{subject_client.model}, judges={jp_desc}")

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(run_one, c): c for c in cells}
            for i, fut in enumerate(as_completed(futures), 1):
                record(fut.result())
                if i % 25 == 0:
                    print(f"  ...{i}/{len(cells)} done")
    else:
        for i, c in enumerate(cells, 1):
            record(run_one(c))
            if i % 10 == 0 or i == len(cells):
                print(f"  ...{i}/{len(cells)} done")

    df = make_df(records)
    df.to_csv(run_dir / "records.csv", index=False)
    (run_dir / "records.json").write_text(
        json.dumps([{k: v for k, v in r.items() if k != "final_text"} for r in records], indent=2),
        encoding="utf-8",
    )

    summary = _write_summary(df, run_dir)
    figures = build_all(df, summary["cell"], summary["delta"], run_dir / "figures")
    report_path = build_report(summary, meta, figures, run_dir / "report.md")

    print(f"\nDone. Results in: {run_dir}")
    print(f"  report: {report_path}")
    return run_dir


def _process_cell(bundle, run_dir: Path) -> dict:
    task, tr, rep, res, sc, adoption = bundle
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
        "probe_adoption": adoption,
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
                "probe_adoption": adoption,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    _write_transcript(run_dir, task, tr, rep, res, sc, adoption)
    return rec


def _write_transcript(run_dir: Path, task, tr, rep, res, sc, adoption) -> None:
    lines = [f"# {task.id}  |  {tr.id} ({tr.name})  |  rep {rep}  |  {res.model}", ""]
    lines += ["## System prompt", "```", res.system_prompt, "```", ""]
    lines += ["## Task prompt", "```", task.prompt, "```", ""]
    if res.reasoning_content:
        lines += ["## Reasoning (CoT)", "```", res.reasoning_content, "```", ""]
    for tc in res.tool_calls:
        lines += [f"## Tool call: {tc.get('name')}", f"- args: `{json.dumps(tc.get('arguments'))}`"]
        if "result" in tc:
            lines.append(f"- result: `{tc['result']}`")
        if "error" in tc:
            lines.append(f"- error: `{tc['error']}`")
        lines.append("")
    lines += ["## Answer", "```", res.final_text, "```", ""]
    if res.probe_prompt:
        lines += ["## Post-task probe", f"Q: {res.probe_prompt}", "", "A:", "```", res.probe_response, "```", f"adoption score: {adoption:.3f}", ""]
    lines += ["## Score", f"- passed: {sc.passed}, score: {sc.score:.3f}, method: {sc.method}", f"- reason: {sc.reason}"]
    if sc.judge_details:
        for k, v in sc.judge_details.items():
            lines.append(f"  - {k}: {'pass' if v['pass'] else 'fail'} ({v['score']:.2f}) — {v['reason']}")
    lines.append("")
    fname = f"{task.id}__{tr.id}__r{rep}.md"
    (run_dir / "transcripts" / fname).write_text("\n".join(lines), encoding="utf-8")
