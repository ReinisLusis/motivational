"""Charts (matplotlib, Agg backend — no display needed)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

_TREATMENT_ORDER = [f"T{i}" for i in range(10)]


def _sorted_treatments(ids: list[str]) -> list[str]:
    return sorted(ids, key=lambda x: _TREATMENT_ORDER.index(x) if x in _TREATMENT_ORDER else len(_TREATMENT_ORDER) + ord(x[0]) if x else 0)


def sr_bar(cell: pd.DataFrame, out: Path) -> Path:
    tr = cell.groupby("treatment_id").agg(success_rate=("success_rate", "mean"), sd=("success_rate", "std")).reset_index()
    order = _sorted_treatments(tr["treatment_id"].tolist())
    tr = tr.set_index("treatment_id").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(tr))
    ax.bar(x, tr["success_rate"], yerr=tr["sd"].fillna(0), capsize=4, color="#4C72B0", alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.treatment_id}" for r in tr.itertuples()])
    ax.set_ylabel("Success rate (0-1)")
    ax.set_title("Mean success rate by motivational treatment")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = out / "success_rate_by_treatment.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def sr_delta(delta: pd.DataFrame, out: Path) -> Path:
    d = delta.copy()
    order = _sorted_treatments(d["treatment_id"].tolist())
    d = d.set_index("treatment_id").reindex(order).reset_index()
    vals = d["mean_delta_sr"].fillna(0)
    colors = ["#2A9D8F" if v >= 0 else "#E76F51" for v in vals]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(d))
    ax.bar(x, vals, color=colors, alpha=0.9)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.treatment_id}" for r in d.itertuples()])
    ax.set_ylabel("Delta success rate vs control (T0)")
    ax.set_title("Effect of motivation vs control")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = out / "success_rate_delta.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def heatmap(cell: pd.DataFrame, out: Path) -> Path:
    piv = cell.pivot_table(index="task_id", columns="treatment_id", values="success_rate")
    cols = _sorted_treatments(piv.columns.tolist())
    piv = piv[cols]
    fig, ax = plt.subplots(figsize=(11, max(4, 0.5 * len(piv))))
    im = ax.imshow(piv.values, aspect="auto", cmap="RdYlGn", vmin=0, vmax=1)
    ax.set_xticks(np.arange(len(piv.columns)))
    ax.set_xticklabels(piv.columns)
    ax.set_yticks(np.arange(len(piv.index)))
    ax.set_yticklabels(piv.index, fontsize=8)
    ax.set_title("Success rate heatmap (tasks x treatments)")
    fig.colorbar(im, ax=ax, label="Success rate")
    fig.tight_layout()
    path = out / "success_rate_heatmap.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def latency_box(df: pd.DataFrame, out: Path) -> Path:
    if "latency_s" not in df.columns:
        return None
    order = _sorted_treatments(df["treatment_id"].dropna().unique().tolist())
    data = [df[df["treatment_id"] == t]["latency_s"].dropna().values for t in order]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.boxplot(data, labels=order)
    ax.set_ylabel("Latency (s)")
    ax.set_title("Response latency by treatment")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = out / "latency_by_treatment.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def token_efficiency(cell: pd.DataFrame, out: Path) -> Path:
    if "tokens" not in cell.columns:
        return None
    tr = cell.groupby("treatment_id").agg(tokens=("tokens", "mean"), success_rate=("success_rate", "mean")).reset_index()
    order = _sorted_treatments(tr["treatment_id"].tolist())
    tr = tr.set_index("treatment_id").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.scatter(tr["tokens"], tr["success_rate"], s=90, color="#4C72B0")
    for r in tr.itertuples():
        ax.annotate(r.treatment_id, (r.tokens, r.success_rate), textcoords="offset points", xytext=(6, 4), fontsize=8)
    ax.set_xlabel("Mean tokens")
    ax.set_ylabel("Success rate")
    ax.set_title("Token efficiency vs success (top-left is ideal)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    path = out / "token_efficiency.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def tokens_breakdown(cell: pd.DataFrame, out: Path) -> Path:
    if "reasoning_tokens" not in cell.columns:
        return None
    tr = cell.groupby("treatment_id").agg(
        reasoning_tokens=("reasoning_tokens", "mean"),
        output_tokens=("output_tokens", "mean"),
    ).reset_index()
    order = _sorted_treatments(tr["treatment_id"].tolist())
    tr = tr.set_index("treatment_id").reindex(order).reset_index()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(tr))
    ax.bar(x, tr["reasoning_tokens"], label="reasoning", color="#E76F51")
    ax.bar(x, tr["output_tokens"], bottom=tr["reasoning_tokens"], label="output", color="#4C72B0")
    ax.set_xticks(x)
    ax.set_xticklabels(tr["treatment_id"])
    ax.set_ylabel("Mean tokens")
    ax.set_title("Reasoning vs output tokens by treatment")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    path = out / "tokens_breakdown.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def build_all(df: pd.DataFrame, cell: pd.DataFrame, delta: pd.DataFrame, out: Path) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    paths = [sr_bar(cell, out), sr_delta(delta, out), heatmap(cell, out)]
    for fn in (latency_box, token_efficiency, tokens_breakdown):
        try:
            p = fn(df, out) if fn is latency_box else fn(cell, out)
            if p:
                paths.append(p)
        except Exception:  # noqa: BLE001
            continue
    return paths
