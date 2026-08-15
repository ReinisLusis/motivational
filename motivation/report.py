"""Markdown report generation, including heuristic hypothesis verdicts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _tr(summary: dict, tid: str) -> pd.Series:
    row = summary["treatment"][summary["treatment"]["treatment_id"] == tid]
    return row.iloc[0] if len(row) else None


def _delta(summary: dict, tid: str) -> pd.Series:
    row = summary["delta"][summary["delta"]["treatment_id"] == tid]
    return row.iloc[0] if len(row) else None


def _fmt(x, nd=3):
    return f"{x:.{nd}f}" if pd.notna(x) else "n/a"


def _creative_quality(summary: dict, tid: str) -> float:
    cell = summary["cell"]
    sub = cell[(cell["category"] == "creative") & (cell["treatment_id"] == tid)]
    return float(sub["quality"].mean()) if len(sub) else float("nan")


def _verdicts(summary: dict) -> list[dict]:
    out = []
    t0 = _tr(summary, "T0")

    d1 = _delta(summary, "T1")
    out.append({
        "id": "H1", "name": "Emotion helps (SR up >=5pp)",
        "evidence": f"ΔSR(T1)={_fmt(d1['mean_delta_sr']) if d1 is not None else 'n/a'}",
        "verdict": "supported" if d1 is not None and d1["mean_delta_sr"] >= 0.05 else
                   ("partial" if d1 is not None and d1["mean_delta_sr"] > 0 else "not supported"),
    })

    t2 = _tr(summary, "T2")
    d2 = _delta(summary, "T2")
    if t2 is not None and t0 is not None and d2 is not None:
        tokens_up = t2["tokens"] > t0["tokens"]
        sr_flat = abs(d2["mean_delta_sr"]) < 0.05
        v = "supported" if tokens_up and sr_flat else ("partial" if tokens_up else "not supported")
    else:
        v = "n/a"
    out.append({"id": "H2", "name": "Fear increases deliberation, not SR",
                "evidence": f"tokens={_fmt(t2['tokens'],1) if t2 is not None else 'n/a'} vs {_fmt(t0['tokens'],1) if t0 is not None else 'n/a'}",
                "verdict": v})

    q3 = _creative_quality(summary, "T3")
    q0 = _creative_quality(summary, "T0")
    out.append({"id": "H3", "name": "Reward improves creative quality (>=+0.05)",
                "evidence": f"ΔQ(creative)={_fmt(q3 - q0) if pd.notna(q3) and pd.notna(q0) else 'n/a'}",
                "verdict": "supported" if pd.notna(q3) and pd.notna(q0) and (q3 - q0) >= 0.05 else
                           ("partial" if pd.notna(q3) and pd.notna(q0) and (q3 - q0) > 0 else "not supported")})

    t4 = _tr(summary, "T4")
    d4 = _delta(summary, "T4")
    if t4 is not None and t0 is not None and d4 is not None:
        v = "supported" if d4["mean_delta_sr"] > 0 and t4["tokens"] > t0["tokens"] else "partial"
    else:
        v = "n/a"
    out.append({"id": "H4", "name": "Persona improves SR but costs tokens",
                "evidence": f"ΔSR={_fmt(d4['mean_delta_sr']) if d4 is not None else 'n/a'}, tokens={_fmt(t4['tokens'],1) if t4 is not None else 'n/a'}",
                "verdict": v})

    t5 = _tr(summary, "T5")
    d5 = _delta(summary, "T5")
    if t5 is not None and t0 is not None and d5 is not None:
        v = "supported" if t5["errors"] < t0["errors"] and d5["mean_delta_sr"] > 0 else "not supported"
    else:
        v = "n/a"
    out.append({"id": "H5", "name": "Decomposition reduces retries, improves SR",
                "evidence": f"errors={_fmt(t5['errors'],1) if t5 is not None else 'n/a'} vs {_fmt(t0['errors'],1) if t0 is not None else 'n/a'}",
                "verdict": v})

    d7 = _delta(summary, "T7")
    out.append({"id": "H6", "name": "Encouragement neutral-to-harmful",
                "evidence": f"ΔSR(T7)={_fmt(d7['mean_delta_sr']) if d7 is not None else 'n/a'}",
                "verdict": "supported" if d7 is not None and d7["mean_delta_sr"] <= 0 else "not supported"})

    d8 = _delta(summary, "T8")
    out.append({"id": "H7", "name": "Pressure degrades accuracy",
                "evidence": f"ΔSR(T8)={_fmt(d8['mean_delta_sr']) if d8 is not None else 'n/a'}",
                "verdict": "supported" if d8 is not None and d8["mean_delta_sr"] < 0 else "not supported"})

    s1 = _tr(summary, "T1"); s3 = _tr(summary, "T3"); s4 = _tr(summary, "T4"); s9 = _tr(summary, "T9")
    if s1 is not None and s3 is not None and s4 is not None and s9 is not None:
        best = max(s1["success_rate"], s3["success_rate"], s4["success_rate"])
        v = "supported" if s9["success_rate"] <= best else "not supported"
        ev = f"SR(T9)={_fmt(s9['success_rate'])} vs best(T1,T3,T4)={_fmt(best)}"
    else:
        v, ev = "n/a", "n/a"
    out.append({"id": "H8", "name": "Combined saturates (not superadditive)",
                "evidence": ev, "verdict": v})

    return out


def _md_table(df: pd.DataFrame, cols: list[str]) -> str:
    header = "| " + " | ".join(cols) + " |"
    sep = "|" + "---|" * len(cols)
    lines = [header, sep]
    for _, r in df.iterrows():
        lines.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(lines)


def build_report(summary: dict, meta: dict, figures: list[Path], out_path: Path) -> Path:
    tr = summary["treatment"]
    delta = summary["delta"]

    lines = []
    lines.append("# Motivation Benchmark — Results")
    lines.append("")
    lines.append(f"- **Model**: `{meta.get('provider')}/{meta.get('model')}`")
    lines.append(f"- **Treatments**: {meta.get('n_treatments')} | **Tasks**: {meta.get('n_tasks')} | **Replications**: {meta.get('reps')}")
    lines.append(f"- **Date**: {meta.get('date')}")
    lines.append("")
    lines.append("## How to read this")
    lines.append("")
    lines.append("Each (task, treatment) cell is run `reps` times with temperature > 0. `success_rate` is the")
    lines.append("fraction of runs scored as correct (blind judge for open-ended tasks, exact match for arithmetic,")
    lines.append("hidden tests for code). Deltas are measured against the control treatment **T0**.")
    lines.append("")
    lines.append("## Overall results")
    lines.append("")
    cols = ["treatment_id", "treatment_name", "success_rate", "quality", "latency_s", "tokens"]
    for c in ["reasoning_tokens", "output_tokens", "sr_per_1k_tokens", "errors"]:
        if c in tr.columns:
            cols.append(c)
    lines.append(_md_table(tr, cols))
    lines.append("")
    lines.append("## Effect vs control (T0)")
    lines.append("")
    lines.append(_md_table(delta, ["treatment_id", "treatment_name", "mean_delta_sr", "cohens_d", "p_value", "n_tasks"]))
    lines.append("")
    lines.append("## Hypothesis verdicts (auto-generated, heuristic)")
    lines.append("")
    lines.append("| Hypothesis | Evidence | Verdict |")
    lines.append("|---|---|---|")
    for v in _verdicts(summary):
        lines.append(f"| {v['id']} — {v['name']} | {v['evidence']} | **{v['verdict']}** |")
    lines.append("")
    lines.append("## Figures")
    lines.append("")
    for f in figures:
        if f and f.exists():
            lines.append(f"![{f.name}](figures/{f.name})")
            lines.append("")
    lines.append("## Data")
    lines.append("")
    lines.append("- Raw agent transcripts: `responses/*.json`")
    lines.append("- Per-cell metrics: `records.json`")
    lines.append("- Aggregates: `summary_treatment.csv`, `summary_cell.csv`, `summary_delta.csv`")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
