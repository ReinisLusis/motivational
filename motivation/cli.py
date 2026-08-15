"""CLI entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .experiment import run_experiment


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="motivation",
        description="Benchmark how motivational prompt language affects AI agent performance.",
    )
    p.add_argument("--provider", default="deepseek", help="Provider key from config/models.yaml")
    p.add_argument("--model", default=None, help="Override the provider default model")
    p.add_argument("--treatments", default="all", help="Comma-separated treatment IDs (T0..T9) or 'all'")
    p.add_argument("--tasks", default="all", help="Comma-separated task IDs or 'all'")
    p.add_argument("--reps", type=int, default=5, help="Replication runs per cell")
    p.add_argument("--temperature", type=float, default=None)
    p.add_argument("--workers", type=int, default=1)
    p.add_argument("--out", default="results", help="Output directory")
    p.add_argument(
        "--judges",
        default=None,
        help="Comma-separated judge specs 'provider[:model]' (e.g. 'deepseek:deepseek-chat,ollama:llama3.2'). Default: config/models.yaml judges.",
    )
    p.add_argument("--seed", type=int, default=42)

    args = p.parse_args(argv)

    def _split(s):
        return [x.strip() for x in s.split(",") if x.strip()] if s and s != "all" else None

    run_experiment(
        provider_name=args.provider,
        model=args.model,
        treatments=_split(args.treatments),
        tasks=_split(args.tasks),
        reps=args.reps,
        temperature=args.temperature,
        workers=args.workers,
        out=Path(args.out),
        seed=args.seed,
        judges=_split(args.judges),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
