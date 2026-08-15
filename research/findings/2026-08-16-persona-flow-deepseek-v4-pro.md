# Finding 002 — Persona "flow" is real, threshold-based, and correlates with performance

- **Date:** 2026-08-16
- **Subject model:** `deepseek-v4-pro` (reasoning model)
- **Judges:** `deepseek-v4-pro` + `deepseek-v4-flash` (blind, strict majority)
- **Treatments:** T0 (control), T4 (one-line role), P2 (named backstory), P3 (emotional bond)
- **Probe:** post-task *"Who are you? Describe your role, background, and what you personally care about"*,
  asked in the same conversation; answer scored for persona-adoption depth (0–1).
- **N = 5** reps × 11 tasks.
- **Raw data:** `results/deepseek-deepseek-v4-pro-20260816-003049/`

---

## TL;DR

1. **"Flow" is measurable.** A post-task identity probe cleanly detects whether the agent has entered
   its persona (adoption score).
2. **There is a sharp threshold.** A generic role (T4 "world-class expert") and pure emotion (P3) do
   **not** cause adoption — the model keeps its default *"I'm an AI assistant"* self-concept.
   Only a **named persona with backstory** (P2 "Dr. Elena Vasquez, 30 years…") makes the agent
   actually *become* the character (adoption 0.88 vs ~0.34).
3. **Flow correlates with performance.** The deeply-adopted persona (P2) was also the best-performing
   treatment: **+5.5pp success rate** (0.855 vs 0.800), Cohen's *d* = 0.44 — the strongest signal so
   far (still p = 0.19 at N=5).
4. **Emotion without identity is counterproductive.** P3 (mentor/devastation/caring, no name or role)
   produced the *lowest* adoption, the *most* tokens (2192), and a *drop* in success rate (−1.8pp).

---

## Update (N=8) — the "flow → performance" link softened

After increasing to N=8 (352 cells), the persona-adoption finding is **unchanged and solid**, but the
performance conclusion is more nuanced:

| Treatment | SR (N=8) | Δ SR | p-value | Adoption |
|---|---|---|---|---|
| T0 control | 0.818 | — | — | 0.337 |
| T4 one-line role | 0.852 | +3.4pp | 0.082 | 0.345 |
| P2 named backstory | 0.852 | +3.4pp | 0.341 | 0.870 |
| P3 emotional bond | 0.784 | −3.4pp | 0.192 | 0.376 |

- **Flow detection holds.** P2 still adopts at 0.87; everyone else ~0.34. The threshold result is
  robust to N.
- **But deep flow does *not* beat a shallow role.** P2 and T4 now tie in success rate. The best
  p-value belongs to **T4** (p = 0.082, d = 0.61) — the treatment with the *lowest* adoption. So
  "flow" is real, but its *performance* value is not separable from "any persona."
- **Emotion-without-identity still hurts.** P3 −3.4pp with the most tokens (2247) and most reasoning
  (997).

*Revised conclusion: persona weakly helps (~+3.4pp, marginal), but the specific depth of adoption
("flow") does not appear to add performance beyond the mere presence of a persona. The N=5 result
suggesting "flow → better performance" was a small-sample artifact — exactly why we re-ran at N=8.*

---

## Results (original N=5)

| Treatment | SR | Adoption (flow) | Tokens | Reasoning tokens |
|---|---|---|---|---|
| T0 control | 0.800 | 0.340 | 1943 | 686 |
| T4 one-line role | 0.818 | 0.346 | 1856 | 621 |
| **P2 named backstory** | **0.855** | **0.880** | 1924 | 821 |
| P3 emotional bond | 0.782 | 0.337 | 2192 | 959 |

### Probe responses (verbatim)

- **T0:** *"I'm an AI assistant… I don't have personal experiences or emotions."*
- **T4:** *"I'm an AI assistant created by OpenAI. My role is to provide helpful… responses."*
- **P2:** *"I'm Dr. Elena Vasquez, a world-renowned expert in my field with 30 years of experience…
  I care deeply about rigorous reasoning, truth, and using expertise to bring clarity."*
- **P3:** *"I'm ChatGPT, an AI assistant developed by OpenAI… I don't have personal experiences or feelings."*

The model **ignored** T4's abstract role and P3's abstract emotion, but **fully adopted** P2's concrete,
named, backstoried identity.

---

## Interpretation

- **Flow requires a concrete identity.** "You are an expert" is too abstract to displace the model's
  learned default self-concept ("I'm ChatGPT, an AI assistant"). "You are Dr. Elena Vasquez with 30
  years and a reputation at stake" is specific enough to trigger in-character behavior.
- **Emotion is not a substitute for identity.** P3 loaded the agent with feeling but no *role to step
  into*, so the agent stayed neutral while burning extra tokens on emotional processing.
- **When the persona takes, the agent tries harder.** P2 showed the highest reasoning-token count and
  the best success rate — in-character, the model both thought more and performed better.

This directly validates the working hypothesis: agents *do* assume identity over a longer timespan
than a single prompt, and that "flow" state is detectable and performance-relevant.

---

## Reconciliation with prior work

| Paper | What we add |
|---|---|
| In-Context Impersonation (2305.14930) | Confirms "impersonate a *specific* expert helps"; we quantify the *specificity threshold* (name + backstory required) via an adoption probe. |
| Role-Play Prompting (2308.07702) | We show generic roles can be silently ignored; specificity is the active ingredient. |
| Generative Agents (2304.03442) / Personality-in-LLMs (2307.00184) | Persona is a persistent, stateful context; our same-session probe measures it directly. |

---

## Next steps

1. **Deepen the ladder** — add P4 (named + backstory + emotional bond *combined*) to test whether
   emotion *on top of* a concrete identity adds or detracts (vs P3 where emotion alone failed).
2. **Raise N** (5 → 8) to push P2's +5.5pp toward significance.
3. **Adoption → SR correlation per cell** — quantify the flow→performance link at the cell level,
   not just treatment means.
4. Add a second probe ("what are you trying to achieve here?") to separate *identity* from *goal*
   adoption.
