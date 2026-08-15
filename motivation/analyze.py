"""Analysis: assemble records, compute summaries, deltas vs baseline, significance."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

METRIC_COLS = [
    "latency_s",
    "tokens",
    "prompt_tokens",
    "completion_tokens",
    "reasoning_tokens",
    "output_tokens",
    "tool_calls",
    "errors",
    "cot_depth",
    "probe_adoption",
]


def make_df(records: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(records)


def per_cell_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Mean metrics per (task, treatment), averaged over replication runs."""
    group = df.groupby(
        ["task_id", "category", "difficulty", "treatment_id", "treatment_name"]
    )
    agg: dict[str, str] = {m: "mean" for m in METRIC_COLS if m in df.columns}
    agg["passed"] = "mean"
    agg["score"] = "mean"
    s = group.agg(agg).reset_index()
    s = s.rename(columns={"passed": "success_rate", "score": "quality"})
    s = s.round(4)
    return s


def per_treatment_summary(cell: pd.DataFrame) -> pd.DataFrame:
    """Equal weight per task (robust to differing task counts)."""
    agg: dict[str, tuple[str, str]] = {
        "success_rate": ("success_rate", "mean"),
        "quality": ("quality", "mean"),
        "latency_s": ("latency_s", "mean"),
        "tokens": ("tokens", "mean"),
        "tool_calls": ("tool_calls", "mean"),
        "errors": ("errors", "mean"),
        "cot_depth": ("cot_depth", "mean"),
    }
    for c in ("reasoning_tokens", "output_tokens", "probe_adoption"):
        if c in cell.columns:
            agg[c] = (c, "mean")
    g = cell.groupby(["treatment_id", "treatment_name"]).agg(**agg).reset_index()
    g["sr_per_1k_tokens"] = (g["success_rate"] / g["tokens"] * 1000).round(3)
    return g.round(4)


def treatment_deltas(cell: pd.DataFrame) -> pd.DataFrame:
    """Per-treatment delta in success_rate vs T0, with paired significance across tasks.

    The paired t-test compares the treatment's per-task success rate against the
    baseline (T0) success rate for the same tasks.
    """
    base = cell[cell["treatment_id"] == "T0"]
    base_map = dict(zip(base["task_id"], base["success_rate"]))

    rows = []
    for tid, grp in cell.groupby("treatment_id"):
        name = grp.iloc[0]["treatment_name"]
        tr_sr: list[float] = []
        base_sr: list[float] = []
        for _, g2 in grp.groupby("task_id"):
            b = base_map.get(g2["task_id"].iloc[0])
            if b is None:
                continue
            tr_sr.append(float(g2["success_rate"].iloc[0]))
            base_sr.append(float(b))

        tr = np.array(tr_sr)
        bs = np.array(base_sr)
        d_sr = tr - bs

        p = np.nan
        if tid != "T0" and len(tr) > 1:
            p = float(stats.ttest_rel(tr, bs).pvalue)

        d = float(np.mean(d_sr) / np.std(d_sr)) if len(d_sr) > 1 and np.std(d_sr) > 0 else float("nan")
        rows.append(
            {
                "treatment_id": tid,
                "treatment_name": name,
                "mean_delta_sr": round(float(np.mean(d_sr)), 4) if len(d_sr) else np.nan,
                "cohens_d": round(d, 3),
                "p_value": round(p, 4) if not np.isnan(p) else np.nan,
                "n_tasks": int(len(d_sr)),
            }
        )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    cell = per_cell_summary(df)
    tr = per_treatment_summary(cell)
    delta = treatment_deltas(cell)
    return {"cell": cell, "treatment": tr, "delta": delta}
