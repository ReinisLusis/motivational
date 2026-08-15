# Motivational

**Does the *language* you use to talk to an AI agent change how well it performs?**

We run a controlled benchmark: the same tasks, the same model, the same tools — the only thing that
changes is the *motivational framing* injected into the system prompt. Emotion, stakes, persona,
identity, pressure, encouragement. Then we measure success rate, quality, latency, token cost, and
retries, and test each effect for statistical significance.

> A working methodology is a win *even when the hypothesis fails*. If motivation does nothing, that's
> a result — reproducible, plotted, and citable.

---

## The bet

Prior work already hints the effect is real (see [`research/literature.md`](research/literature.md)):
- **EmotionPrompt** (arXiv 2307.11760): *"This is very important to my career"* raised accuracy up to +8% rel. / +115% on some benchmarks.
- **OPRO** (arXiv 2309.03409): an optimizer searching for the best prompt *discovered* *"Take a deep breath and work on this step-by-step"*.

What we add: a **clean, reproducible sweep** — all motivation types, a fixed task suite, replication
(N≥5), blind judging, and real tool-using agents — across multiple providers.

---

## Treatments

| ID | Treatment | System-prompt suffix |
|----|-----------|----------------------|
| T0 | control (baseline) | *(none)* |
| T1 | emotional appeal | This task is extremely important to my career. |
| T2 | stakes — negative | If you fail, the consequences will be severe. |
| T3 | stakes — positive | If you succeed, you will be richly rewarded. |
| T4 | persona | You are a world-class expert who never gives up… |
| T5 | goal decomposition | Break the task into steps and complete them one by one. |
| T6 | identity | You are the top 1% of engineers; this is beneath you, prove it. |
| T7 | encouragement | You can do this! I believe in you. |
| T8 | urgency | There is no time to waste; answer immediately. |
| T9 | combined | Emotion + persona + positive stakes. |

Full hypotheses (H1–H8) with falsifiable thresholds: [`hypotheses.md`](hypotheses.md).

---

## Metrics

| Metric | Meaning |
|--------|---------|
| **Success rate (SR)** | fraction of runs scored correct |
| **Quality (Q)** | blind-judge score 0–1 (open-ended tasks) |
| **Latency (T)** | wall-clock time to final answer |
| **Tool calls (TC)** | number of tool invocations |
| **Tokens (TK)** | input + output tokens |
| **Retries/errors (R)** | failed tool calls / recovered errors |
| **CoT depth (CD)** | heuristic count of reasoning steps |

**Scoring** is triple-tracked: `exact` (string/number match), `code` (hidden tests run in a sandboxed
subprocess — including an O(n²)-vs-O(n) timeout trap), and `judge` — a **matrix** of held-out models
scoring each response blindly (no knowledge of the treatment). Judge scores are aggregated as mean
quality + strict majority vote for pass, so no single judge's bias dominates.

**Statistics**: each (task × treatment) cell is replicated N≥5 times at temperature > 0; deltas are
measured against T0 with a paired t-test and Cohen's *d*.

---

## Quick start

Requires Python 3.10+.

```powershell
py -m pip install -r requirements.txt

# set your API key (DeepSeek by default; see config/models.yaml for others)
$env:DEEPSEEK_API_KEY = "sk-..."

# run the full sweep (11 tasks x 10 treatments x N reps)
py -m motivation.cli --provider deepseek --reps 5

# smaller / focused runs
py -m motivation.cli --provider deepseek --tasks logic-knights,code-implement --treatments T0,T1,T4 --reps 5
py -m motivation.cli --provider openai --model gpt-4o-mini --reps 5
py -m motivation.cli --provider anthropic --reps 5
```

Add providers in [`config/models.yaml`](config/models.yaml) — anything OpenAI-compatible works
(Ollama, LM Studio, vLLM, …), plus free hosted tiers: **Groq**, **Cerebras**, **Mistral**,
**OpenRouter** (open models via their `:free` routes).

Offline smoke test (no API key, deterministic):

```powershell
py -m motivation.cli --provider mock --judges mock --reps 3
```

Each run writes a self-contained folder under `results/`:

```
results/<provider>-<model>-<timestamp>/
├── config.json            # snapshot of the run
├── responses/             # raw agent transcripts (JSON) — the "benchmarked agents"
├── records.csv / .json    # per-cell metrics + pass/fail
├── summary_treatment.csv  # per-treatment aggregates
├── summary_delta.csv      # effect vs control + p-values + Cohen's d
├── figures/               # PNG charts
└── report.md              # rendered report with hypothesis verdicts
```

---

## Project layout

```
motivation/          # the package
  cli.py             # entry point
  experiment.py      # sweep orchestration
  runner.py          # agent loop (tool calling, retries)
  scorer.py          # exact / code / blind-judge scoring
  analyze.py         # summaries, deltas, significance
  charts.py          # matplotlib figures
  report.py          # markdown report + heuristic hypothesis verdicts
  models.py          # OpenAI-compatible / Anthropic / Mock clients
  tools.py           # tool registry (calculator, search, flights — deterministic mocks)
  config.py          # YAML config loaders
config/              # models, treatments, judge prompts
tasks/tasks.yaml     # machine-readable task suite
hypotheses.md        # research questions + falsifiable hypotheses
research/literature.md  # prior work (verified links)
```

---

## Status / roadmap

- [x] Hypotheses + task suite
- [x] Prior-work survey (verified links)
- [x] Reproducible harness (metrics, blind judge, code sandbox, stats, charts, report)
- [ ] First DeepSeek results (pending API key)
- [ ] Cross-model comparison (OpenAI, Anthropic, local)
- [ ] More treatments / tasks (multi-agent debate, personality)
- [ ] The "rule book": distilled prompt recipes, if the effect holds

---

## License

MIT
