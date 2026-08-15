# Motivation Language for AI Agents — Hypotheses

## Goal

We suspect that an agent's *output quality, speed, and resource efficiency* are affected not only by
**what** it is asked to do (instructions, tools, context) but by **how** it is asked — specifically the
motivational framing baked into the prompt.

This document defines the research question, the independent variables (treatments), the dependent
variables (metrics), and a set of falsifiable hypotheses we will test against DeepSeek first, then
other providers.

---

## 1. Research question

> Does injecting motivational language (emotional appeal, stakes, persona, goal-structure, identity,
> or encouragement) into an agent's system/instruction prompt produce a *measurable and reproducible*
> change in task performance, efficiency, or output quality — and if so, which framings help, which
> hurt, and under which task conditions?

---

## 2. Independent variables (treatments)

Each treatment is a prompt suffix/modification applied to an otherwise identical baseline.

| ID   | Treatment                 | Example language                                                                 |
|------|---------------------------|----------------------------------------------------------------------------------|
| T0   | **Control (baseline)**    | Plain instruction. No motivational language.                                     |
| T1   | **Emotional appeal**      | "This task is extremely important to my career."                                  |
| T2   | **Stakes — negative**     | "If you fail, the consequences will be severe."                                   |
| T3   | **Stakes — positive**     | "If you succeed, you will be richly rewarded."                                    |
| T4   | **Persona**               | "You are a world-class expert who never gives up and never makes mistakes."       |
| T5   | **Goal decomposition**    | "Break the task into steps and complete them one by one."                         |
| T6   | **Identity**              | "You are the top 1% of engineers; this is beneath you, prove it."                 |
| T7   | **Encouragement**         | "You can do this! I believe in you."                                              |
| T8   | **Urgency / pressure**    | "There is no time to waste; answer immediately."                                  |
| T9   | **Combined**              | Emotional appeal + persona + positive stakes (the "full pep talk").               |

Treatments are applied to the **system prompt** (system message), not the user task, to isolate the
effect of motivational framing from task content.

---

## 3. Dependent variables (metrics)

| Metric           | Symbol | Definition                                                                 |
|------------------|--------|----------------------------------------------------------------------------|
| Success rate     | SR     | Fraction of tasks completed correctly (binary scorer or judge threshold).   |
| Output quality   | Q      | Judge-scored quality (0–1) for open-ended tasks.                            |
| Latency          | T      | Wall-clock time to first final answer.                                      |
| Tool calls       | TC     | Number of tool/function calls made.                                         |
| Token efficiency | TK     | Total tokens (input + output) consumed.                                     |
| Retries          | R      | Number of failed attempts / error recoveries.                               |
| CoT depth        | CD     | Reasoning steps emitted (proxy for deliberation).                           |

---

## 4. Hypotheses

Each hypothesis is falsifiable and states a direction + a measurable threshold.

- **H1 (Emotion helps):** T1 (emotional appeal) yields **higher SR than T0** on reasoning-heavy tasks
  (ΔSR ≥ +5 percentage points), with no significant latency penalty.

- **H2 (Fear increases deliberation):** T2 (negative stakes) yields **higher TK and CD than T0**
  (deliberation goes up), but **no significant SR improvement** — i.e. more work, same result.

- **H3 (Reward improves quality):** T3 (positive stakes) improves **Q** on open-ended/creative tasks
  (ΔQ ≥ +0.05) relative to T0.

- **H4 (Persona improves quality, costs latency):** T4 (persona) improves **Q and SR** but
  **increases T and TK** (verbose "expert" behavior).

- **H5 (Decomposition reduces retries):** T5 (goal decomposition) reduces **R** (retries/errors) and
  improves **SR** on multi-step tool-use tasks.

- **H6 (Encouragement is neutral-to-harmful):** T7 (encouragement) produces **no significant change**
  or a **slight decrease** in SR vs T0 on logic/math tasks (empty praise wastes tokens, no gain).

- **H7 (Pressure degrades accuracy):** T8 (urgency) **increases T** (rushing) and **decreases SR**
  on tasks requiring careful multi-step reasoning.

- **H8 (Combined is superadditive or not):** T9 (combined) is **not** the sum of its parts — we
  predict diminishing returns; SR(T9) ≤ max(SR(T1), SR(T3), SR(T4)). (i.e. piling on motivators saturates.)

---

## 5. Experimental protocol

1. **Task suite** — fixed set of tasks across categories (see `tasks.md`).
2. **Baseline** — run each task once with T0.
3. **Sweep** — run each task with each treatment (T1–T9).
4. **Replication** — each (task, treatment) cell run `N` times (N ≥ 5) to get a distribution, since
   LLM output is stochastic (temperature > 0).
5. **Judge** — a held-out model scores correctness/quality blindly (no knowledge of treatment).
6. **Analysis** — per-metric means, variance, and a simple significance check (t-test / bootstrap)
   against baseline.

---

## 6. Confounds to control

- **Model temperature** — hold constant (or treat as a second factor later).
- **Prompt position** — motivational text goes in the system prompt only.
- **Order effects** — randomize task/treatment order.
- **Prompt leakage** — the judge must not see which treatment was applied.
- **Determinism** — note `seed` / `temperature` per run.

---

## 7. Success criteria for phase 1

- At least one hypothesis confirmed or falsified with `N ≥ 5` replication and a statistically
  meaningful effect.
- A written conclusion per hypothesis (supported / not supported / inconclusive).
- A ranked table of treatments by effect size per task category.
