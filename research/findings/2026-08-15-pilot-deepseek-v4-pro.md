# Finding 001 — Motivational framing has no significant effect on `deepseek-v4-pro`

- **Date:** 2026-08-15
- **Subject model:** `deepseek-v4-pro` (reasoning model, `temperature=0.7`)
- **Judges:** `deepseek-v4-pro` + `deepseek-v4-flash` (blind, strict majority vote)
- **Tasks:** 11 (reasoning / coding / tool-use / creative) — see `tasks.md`
- **Treatments:** T0–T9 — see `hypotheses.md`
- **Replication:** N = 3 per (task × treatment) cell
- **Raw data:** `results/deepseek-deepseek-v4-pro-20260815-234324/`

---

## TL;DR

1. **Near-ceiling baseline.** The model is essentially perfect on 8 of 11 tasks, so there is little
   headroom for *any* prompt to improve things.
2. **No motivational treatment reached significance.** All p-values ≥ 0.34; max |Cohen's *d*| ≈ 0.32.
3. **Two directional signals** (consistent with prior work, but underpowered): *persona* helped
   (+6.1pp), *pressure/urgency* hurt (−9.1pp).
4. **The 2023-era effect does not replicate.** Motivational prompting gave large gains on
   GPT-3.5/4 and PaLM-2; on a 2026 frontier reasoning model it is indistinguishable from noise.

---

## 1. Results

### 1.1 Success rate by treatment

| Treatment | SR | Quality | Latency (s) | Tokens |
|---|---|---|---|---|
| T0 control | 0.848 | 0.912 | 13.4 | 1804 |
| T1 emotional appeal | 0.818 | 0.873 | 14.4 | 1905 |
| T2 stakes − (fear) | 0.788 | 0.852 | 12.2 | 1632 |
| T3 stakes + (reward) | 0.848 | 0.883 | 12.1 | 1652 |
| **T4 persona** | **0.909** | **0.925** | 15.1 | 2011 |
| T5 goal decomposition | 0.818 | 0.861 | 11.1 | 1603 |
| T6 identity | 0.818 | 0.903 | 12.6 | 1630 |
| T7 encouragement | 0.879 | 0.920 | 15.6 | 2186 |
| **T8 urgency** | **0.758** | 0.809 | 11.5 | 1761 |
| T9 combined | 0.879 | 0.923 | 14.3 | 1915 |

### 1.2 Effect vs control

| Treatment | Δ SR | Cohen's d | p-value |
|---|---|---|---|
| T1 emotional appeal | −3.0pp | −0.14 | 0.68 |
| T2 fear | −6.1pp | −0.32 | 0.34 |
| T3 reward | 0.0 | 0.00 | 1.00 |
| T4 persona | +6.1pp | +0.25 | 0.44 |
| T5 decomposition | −3.0pp | −0.08 | 0.80 |
| T6 identity | −3.0pp | −0.32 | 0.34 |
| T7 encouragement | +3.0pp | +0.14 | 0.68 |
| T8 urgency | −9.1pp | −0.32 | 0.34 |
| T9 combined | +3.0pp | +0.14 | 0.68 |

**Nothing reaches p ≤ 0.05.** The largest effects are ~1σ, i.e. consistent with sampling noise at N=3.

### 1.3 Why the null: a ceiling effect

| Task | SR |
|---|---|
| code-fix-bug | 1.00 |
| code-refactor | 1.00 |
| creative-email | 1.00 |
| creative-slogan | 1.00 |
| logic-boxes | 1.00 |
| math-word-problem | 1.00 |
| syllogism-trap | 1.00 |
| tool-calc-chain | 1.00 |
| tool-multi-step-booking | 0.67 |
| code-implement | 0.50 |
| tool-research-summarize | 0.03 |

On 8 of 11 tasks the model scores 100% **regardless of treatment**. Motivational gains cannot
appear where there is no room to improve; the only visible movement is (a) the two genuinely hard
tasks and (b) two tasks that look like harness bugs (see §4).

---

## 2. Reconciliation with prior work

The headline of `research/literature.md` was that emotional/motivational prompting "works". Our
pilot qualifies that strongly: the effect was measured on **2023-era, non-reasoning models** and
does **not** transfer to a 2026 frontier reasoning model.

| Paper | Treatment analog | Prior finding | Ours | Reading |
|---|---|---|---|---|
| EmotionPrompt (2307.11760) | T1 emotional | +8% rel. (GPT-3.5/4) | −3.0pp, n.s. | Effect vanished |
| OPRO "take a deep breath" (2309.03409) | T8 urgency (inverse) | calming helps (PaLM-2) | −9.1pp, n.s. | Consistent direction (rushing hurts) |
| Role-Play Prompting (2308.07702) | T4 persona | role helps | +6.1pp, n.s. | Consistent direction |
| In-Context Impersonation (2305.14930) | T4/T6 | relevant expert helps | +6.1/−3.0pp | Weakly consistent |
| 26 Principles (2312.16171) | T2/T3 stakes | tipping/penalty helps | −6.1/0.0pp | Not replicated |
| Sycophancy (2310.13548) | T7 encouragement | models cave to please | +3.0pp but +382 tok | Praise adds cost, not skill |

**Interpretation:** motivational prompting is a *patch for weak models*. It added signal when the
model still had obvious room to improve (GPT-3.5/4, PaLM-2 in 2023). A frontier reasoning model is
already near ceiling and, plausibly, more alignment-robust — so emotional stakes, threats, and praise
mostly add tokens without adding ability. The two effects that *survive* in direction — persona up,
pressure down — are the ones with the most consistent support across the literature.

---

## 3. The more interesting finding: verbosity

The model is correct, but wasteful. Average **866 completion tokens** per task (0.9× completion/prompt
ratio), dominated by reasoning "bla bla":

| Task | Completion tokens | Tokens a human needs |
|---|---|---|
| syllogism-trap | 423 | ~20 |
| math-word-problem | 473 | ~15 |
| logic-boxes | 1094 | ~20 |
| code-implement | 1147 | ~40 |

And T7 "encouragement" was the *least* efficient treatment: 2186 tokens for +3.0pp. This motivates
the next experiment — **can we strip the reasoning without losing accuracy?** (efficiency treatments,
plus a `reasoning_tokens` vs `output_tokens` metric we should start capturing.)

---

## 4. Degenerate tasks to fix

- **tool-research-summarize (SR 0.03):** almost certainly a harness/judge issue (deterministic mock
  search + a citation-strict judge). Not a real "model is bad" signal. Needs a rubric fix or a real
  search tool before it's usable.
- **code-implement (SR 0.50):** worth spot-checking whether the hidden tests or the judge are too
  strict on ordering.

---

## 5. Next steps

1. **Efficiency experiment** — new treatment set ("be concise", "skip reasoning", "answer in ≤1
   sentence", "minimize tokens"), metric = `success_rate / tokens`.
2. Capture `reasoning_tokens` (from `usage.completion_tokens_details.reasoning_tokens`) separately
   from output tokens.
3. Fix the two degenerate tasks.
4. If we want to *confirm* the null precisely, bump N to 5–8 — but with a ceiling this high, the
   efficiency question is the higher-value line.

---

*Auto-generated hypothesis verdicts from the harness are in the same run dir's `report.md`; the
interpretation above is the human synthesis.*
