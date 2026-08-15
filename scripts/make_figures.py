"""Generate the headline figures for the README from data/*.csv.

Run:  py scripts/make_figures.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIG = ROOT / "figures"

plt.rcParams.update({"figure.dpi": 110, "font.size": 11, "axes.grid": True, "grid.alpha": 0.25})


def _bar(df, col, ylabel, title, fig_path, highlight=(), yerr_col=None, hline=None):
    fig, ax = plt.subplots(figsize=(9, 4.2))
    x = np.arange(len(df))
    colors = ["#2A9D8F" if tid in highlight else "#4C72B0" for tid in df["treatment_id"]]
    err = df[yerr_col].fillna(0) if yerr_col else None
    ax.bar(x, df[col], yerr=err, color=colors, alpha=0.9, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(df["treatment_id"])
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if hline is not None:
        ax.axhline(hline, color="black", lw=0.8, ls="--")
    fig.tight_layout()
    fig.savefig(fig_path)
    plt.close(fig)
    print("wrote", fig_path.name)


def main():
    FIG.mkdir(exist_ok=True)

    # 1. Motivation (Finding 001)
    m = pd.read_csv(DATA / "motivation_summary.csv")
    m = m.set_index("treatment_id").reindex([f"T{i}" for i in range(10)]).reset_index()
    _bar(m, "success_rate", "Success rate", "Motivational framing (vs control T0)",
         highlight=("T4",), fig_path=FIG / "motivation_sr.png", hline=m.loc[m.treatment_id == "T0", "success_rate"].iloc[0])

    # 2. Persona adoption (Finding 002)
    p = pd.read_csv(DATA / "persona_summary.csv")
    order = ["T0", "T4", "P2", "P3", "P4"]
    p = p.set_index("treatment_id").reindex(order).reset_index()
    _bar(p, "probe_adoption", "Persona adoption (flow)", "Does the agent 'enter' its persona? (probe)",
         highlight=("P2", "P4"), fig_path=FIG / "persona_adoption.png")

    # 3. Persona SR
    _bar(p, "success_rate", "Success rate", "Persona depth vs performance",
         highlight=("P2", "P4"), fig_path=FIG / "persona_sr.png",
         hline=p.loc[p.treatment_id == "T0", "success_rate"].iloc[0])

    # 4. Efficiency SR (Finding 003)
    e = pd.read_csv(DATA / "efficiency_summary.csv")
    order = ["T0"] + [f"E{i}" for i in range(1, 8)]
    e = e.set_index("treatment_id").reindex(order).reset_index()
    _bar(e, "success_rate", "Success rate", "Brevity treatments (vs control T0)",
         highlight=("E4", "E7"), fig_path=FIG / "efficiency_sr.png",
         hline=e.loc[e.treatment_id == "T0", "success_rate"].iloc[0])

    # 5. Efficiency scatter (SR vs tokens)
    fig, ax = plt.subplots(figsize=(9, 5))
    for tid in ("E4", "E7"):
        r = e[e.treatment_id == tid].iloc[0]
        ax.scatter(r.tokens, r.success_rate, s=180, color="#E76F51", zorder=3)
    others = e[~e.treatment_id.isin(("E4", "E7"))]
    ax.scatter(others.tokens, others.success_rate, s=140, color="#4C72B0", zorder=3)
    for _, r in e.iterrows():
        ax.annotate(r.treatment_id, (r.tokens, r.success_rate), textcoords="offset points",
                    xytext=(8, 4), fontsize=9)
    ax.set_xlabel("Mean tokens")
    ax.set_ylabel("Success rate")
    ax.set_title("Efficiency: success rate vs tokens (top-left = better & cheaper)")
    ax.invert_xaxis()
    fig.tight_layout()
    fig.savefig(FIG / "efficiency_scatter.png")
    plt.close(fig)
    print("wrote efficiency_scatter.png")


if __name__ == "__main__":
    main()
