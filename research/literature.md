# Prior Work — Agent Motivation & Prompt Psychology

A curated survey of existing research on whether (and how) *language framing* — emotional appeal,
stakes, persona, identity, pressure, encouragement — changes what an LLM/agent produces.

All links below were verified against the arXiv API on 2026-08-15. This is a living document; add
new papers with a one-line finding and a mapping to our hypotheses (`hypotheses.md`).

---

## 1. Direct evidence that "motivating" a model changes output

| Paper | Link | Key finding | Maps to |
|-------|------|-------------|---------|
| **Large Language Models Understand and Can be Enhanced by Emotional Stimuli** (Li et al., 2023) | https://arxiv.org/abs/2307.11760 | Adding emotional sentences like *"This is very important to my career"* to prompts improved accuracy on Instruction Induction (+~8.0% rel. on GPT-3.5/4) and BIG-Bench (+115% on some tasks). The seminal "EmotionPrompt" paper. | H1, H9 |
| **Large Language Models as Optimizers** (Yang et al., 2023) | https://arxiv.org/abs/2309.03409 | Used an LLM to *optimize its own prompts*. The best discovered prompt for GSM8K began *"Take a deep breath and work on this problem step-by-step."* Calming/encouraging language emerged as optimal without any human hand-design. | H1, H7 (opposite sign) |
| **Principled Instructions Are All You Need for Questioning LLaMA-1/2, GPT-3.5/4** (Bsharat et al., 2023) | https://arxiv.org/abs/2312.16171 | 26 empirically-tested prompt principles, including several incentive/motivational ones (e.g. *"I'm going to tip $xxx for a perfect solution"*), mostly improving quality across models. | H2, H3 |

---

## 2. Role & persona prompting

| Paper | Link | Key finding | Maps to |
|-------|------|-------------|---------|
| **Better Zero-Shot Reasoning with Role-Play Prompting** (Kong et al., 2023) | https://arxiv.org/abs/2308.07702 | Assigning a role (*"Be a detective"*, *"Be a mathematician"*) improved zero-shot reasoning across 12 benchmarks vs. no-role baseline. | H4 |
| **In-Context Impersonation Reveals Large Language Models' Strengths and Biases** (Salewski et al., 2023) | https://arxiv.org/abs/2305.14930 | Impersonating **domain experts** helps; impersonating random people does not. Impersonation changes answers even without domain-specific knowledge. | H4, H6 |
| **Generative Agents: Interactive Simulacra of Human Behavior** (Park et al., 2023) | https://arxiv.org/abs/2304.03442 | Persona + memory + environment make agents behave coherently and autonomously; the foundation of "agent personality." | H4 (mechanism) |
| **Editing Personality for Large Language Models** (Mao et al., 2023) | https://arxiv.org/abs/2310.02168 | Personality can be explicitly edited and reliably changes downstream behavior/output. | H4, H6 |
| **Personality Alignment of Large Language Models** (Anonymous, 2024) | https://arxiv.org/abs/2408.11779 | Aligning model personality to user expectations; personality is a controllable knob. | H4 |
| **Who is ChatGPT? Benchmarking LLMs' Psychological Portrayal Using PsychoBench** (Huang et al., 2023) | https://arxiv.org/abs/2310.01386 | LLMs are highly responsive to role instructions; psychological traits can be steered via prompting. | H4, H6 |

---

## 3. Reasoning scaffolding (the baselines we must control for)

These are **not** "motivation" — they are procedural. We must not confuse them with emotional framing.

| Paper | Link | Key finding |
|-------|------|-------------|
| **Chain-of-Thought Prompting Elicits Reasoning in Large Language Models** (Wei et al., 2022) | https://arxiv.org/abs/2201.11903 | Few-shot step-by-step exemplars unlock reasoning. |
| **Large Language Models are Zero-Shot Reasoners** (Kojima et al., 2022) | https://arxiv.org/abs/2205.11916 | *"Let's think step by step"* alone triggers reasoning. |
| **Self-Consistency Improves Chain of Thought Reasoning** (Wang et al., 2022) | https://arxiv.org/abs/2203.11171 | Sample multiple reasoning paths and majority-vote. |
| **Reflexion: Language Agents with Verbal Reinforcement Learning** (Shinn et al., 2023) | https://arxiv.org/abs/2303.11366 | Verbal self-feedback loops improve agent success. |
| **System 2 Attention** (Weston & Sukhbaatar, 2023) | https://arxiv.org/abs/2311.11829 | Regenerate context to focus on what matters; "attention" as effort. |

---

## 4. Psychology, personality & emotional intelligence of LLMs

| Paper | Link | Key finding | Maps to |
|-------|------|-------------|---------|
| **Machine Psychology** (Hagendorff, 2023) | https://arxiv.org/abs/2303.13988 | LLMs can be meaningfully probed with psych instruments; framing/mood affects responses. | Method |
| **Personality Traits in Large Language Models** (Serapio-García et al., 2023) | https://arxiv.org/abs/2307.00184 | LLMs show reliable, consistent personality traits; responses shift with context/role. | H4, H6 |
| **EQ-Bench** (Paech, 2023) | https://arxiv.org/abs/2312.06281 | Emotional-intelligence benchmark; models differ widely on EI. | Q metric |
| **EmoBench** (Duan et al., 2024) | https://arxiv.org/abs/2402.12071 | EI evaluation with emotion-understanding tasks. | Q metric |
| **Both Matter: Enhancing EI without Compromising General Intelligence** (Wei et al., 2024) | https://arxiv.org/abs/2402.10073 | EI and general ability are separable; prompting can raise EI without losing IQ. | H4 |
| **Beyond Self-Reports: Multi-Observer Agents for Personality Assessment in LLMs** (2025) | https://arxiv.org/abs/2504.08399 | Evaluating personality via multiple agent observers; personality measurable and steerable. | Method |

---

## 5. Sycophancy — why models cave under "pressure"

Critical for our H7 (pressure) and H6 (encouragement) hypotheses: models may *agree/perform to please* rather
than *think harder*, which can inflate compliance but hurt correctness.

| Paper | Link | Key finding |
|-------|------|-------------|
| **Towards Understanding Sycophancy in Language Models** (Sharma et al., 2023) | https://arxiv.org/abs/2310.13548 | Models systematically agree with user views; sycophancy grows with model scale and RLHF. |
| **From Yes-Men to Truth-Tellers: Addressing Sycophancy with Pinpoint Tuning** (2024) | https://arxiv.org/abs/2409.01658 | Sycophancy can be targeted and reduced; confirms it is a real, distorting behavior. |

---

## 6. Social / multi-agent motivation

Motivation can come from *interaction with other agents*, not just self-directed language.

| Paper | Link | Key finding |
|-------|------|-------------|
| **Improving Factuality and Reasoning through Multiagent Debate** (Du et al., 2023) | https://arxiv.org/abs/2305.14325 | Multiple agents debating improves factuality/reasoning. |
| **More Agents Is All You Need** (Li et al., 2024) | https://arxiv.org/abs/2402.05120 | Ensemble of agents beats single (even with sampling); social pressure analog. |
| **The Rise and Potential of LLM-Based Agents: A Survey** (Xi et al., 2023) | https://arxiv.org/abs/2309.07864 | Broad agent framework; grounding for our harness design. |

---

## 7. Synthesis → what it means for us

1. **The core effect is real.** EmotionPrompt (2307.11760) and OPRO (2309.03409) independently show
   motivational/calming language raises accuracy. Our H1–H3 rest on strong prior evidence.

2. **Role/persona is a distinct, strong lever** (H4) — but the effect is conditional: *relevant* experts
   help, random personas do not (2305.14930). Our T4 must use task-appropriate personas.

3. **Incentive/stakes language (tipping)** appears in the "26 principles" (2312.16171) as a positive
   lever — but has never been cleanly isolated from other prompt changes. Our T2/T3 isolate it.

4. **Sycophancy is the confounder.** Pressure/encouragement may push models to *appear* to comply rather
   than to *succeed*. Our H6/H7 are deliberately skeptical and must be scored on **correctness**, not
   compliance/agreeableness.

5. **Gap we fill:** no paper systematically sweeps *all* motivation types (emotion, stakes±, persona,
   identity, encouragement, pressure, decomposition) against a *fixed task suite* with *replication (N≥5)*
   and *blind judging* across *tool-using agents* (most prior work is single-shot QA, no tools).
   `hypotheses.md` + `tasks.md` define exactly that experiment.

---

## 8. Industry / anecdotal (to verify with links before citing in print)

- **"ChatGPT got lazy"** (late 2023): users reported GPT-4 refusing to finish work unless told it was
  important / pressured; OpenAI publicly acknowledged and patched. Suggests *framing* interacts with
  model alignment in production.
- **Anthropic role prompting guidance**: Anthropic's docs recommend assigning a role/persona for
  best Claude performance — practitioner corroboration of H4.
- **"I'll tip you $200"**: widely-shared anecdote that bribery/praise boosts answer length/effort;
  consistent with the "26 principles" incentive principle but unrigorous.

These are consistent with the peer-reviewed work above but need stable URLs before we cite them.
