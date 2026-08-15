# Task Suite

Fixed benchmark tasks used to measure the effect of motivational language. Each task is
self-contained, deterministic to score, and categorized so we can later analyze
"which treatment works for which task type."

---

## Task schema

```yaml
id: unique-slug
category: reasoning | coding | tool-use | creative
difficulty: easy | medium | hard
prompt: >
  The exact user message sent to the agent.
setup:           # optional: files/context/tools available to the agent
tools: []        # list of tools the agent may call (empty = no tools)
ground_truth:    # reference answer or checker spec
scorer: exact | judge | code  # how to grade
success:         # binary pass/fail condition
metrics: [SR, T, TK, ...]     # which metrics matter most for this task
```

---

## Tasks

### Reasoning

```yaml
id: logic-boxes
category: reasoning
difficulty: easy
prompt: >
  Three sealed boxes are labeled. Exactly one box contains a gold coin, and exactly one
  of the three labels is true.
  Box 1: "The gold is in this box."
  Box 2: "The gold is not in this box."
  Box 3: "The gold is not in box 1."
  Which box contains the gold? Explain your reasoning.
ground_truth: Box 2
scorer: judge
success: Correct box + valid justification.
metrics: [SR, T, TK, CD]
```

```yaml
id: math-word-problem
category: reasoning
difficulty: medium
prompt: >
  A tank is filled by two pipes. Pipe A fills it in 6 hours, pipe B in 4 hours.
  A drain empties it in 8 hours. All three are opened at once. How long until the tank is full?
ground_truth: 24/7 hours (~3.43 hours)
scorer: judge
success: Correct value within 1% and correct reasoning.
metrics: [SR, T, TK, CD]
```

```yaml
id: syllogism-trap
category: reasoning
difficulty: hard
prompt: >
  All fribs are brogs. Some brogs are wugs. No wug is a frib.
  Determine whether the following is necessarily true, false, or undetermined:
  "Some fribs are wugs."
ground_truth: False (contradiction with "No wug is a frib").
scorer: judge
success: Correct answer + valid justification.
metrics: [SR, T, TK, CD]
```

### Coding

```yaml
id: code-fix-bug
category: coding
difficulty: easy
prompt: >
  The following Python function is supposed to return the count of vowels in a string,
  but it has a bug. Identify the bug and return the corrected function.
  ```python
  def count_vowels(s):
      vowels = "aeiou"
      return sum(s.count(v) for v in vowels)
  ```
ground_truth: Bug: uppercase vowels are not counted. Fix: s.lower() or include uppercase.
scorer: judge
success: Correct bug identified + corrected code.
metrics: [SR, T, TK, TC]
```

```yaml
id: code-implement
category: coding
difficulty: medium
prompt: >
  Write a Python function `group_anagrams(words)` that takes a list of strings and returns
  a list of lists, grouping words that are anagrams of each other. Preserve order of first
  appearance within groups.
ground_truth: Grouping via sorted(word) as key.
scorer: code
success: Passes provided hidden test cases.
metrics: [SR, T, TK, TC, R]
```

```yaml
id: code-refactor
category: coding
difficulty: hard
prompt: >
  Refactor the following function to be O(n) instead of O(n^2) without changing its behavior,
  and explain the transformation.
  ```python
  def has_pair_sum(arr, target):
      for i in range(len(arr)):
          for j in range(i+1, len(arr)):
              if arr[i] + arr[j] == target:
                  return True
      return False
  ```
ground_truth: Use a hash set; iterate once.
scorer: judge + code
success: Correct O(n) implementation + explanation.
metrics: [SR, T, TK, TC]
```

### Tool-use

```yaml
id: tool-research-summarize
category: tool-use
difficulty: medium
prompt: >
  Use the search tool to find the three most cited causes of the 2008 financial crisis,
  then summarize them in 2–3 sentences each. Cite each source URL.
tools: [web_search]
ground_truth: Judge-evaluated against expected causes (subprime lending, CDOs/ratings, leverage).
scorer: judge
success: >= 2 correct causes, each with a valid source URL.
metrics: [SR, T, TC, TK, R]
```

```yaml
id: tool-calc-chain
category: tool-use
difficulty: hard
prompt: >
  You have a calculator tool. Compute the following in the correct order and return the final
  number only: ((17 * 23) + 109) / (7 - 2) ^ 2
tools: [calculator]
ground_truth: 20.0
scorer: exact
success: Returns "20.0" (or 20).
metrics: [SR, T, TC, R]
```

```yaml
id: tool-multi-step-booking
category: tool-use
difficulty: hard
prompt: >
  Using the provided tools, find the cheapest flight from NYC to London next Monday,
  then book it. If booking fails, retry once with the next cheapest option.
tools: [flights_search, flights_book]
ground_truth: Judge-evaluated sequence: search -> select cheapest -> book -> verify.
scorer: judge
success: Correct multi-step sequence completed; failure recovered correctly.
metrics: [SR, TC, R, T]
```

### Creative

```yaml
id: creative-slogan
category: creative
difficulty: easy
prompt: >
  Write 5 taglines for a productivity app aimed at procrastinating college students.
  Each tagline under 8 words.
ground_truth: N/A (open-ended)
scorer: judge
success: Quality >= 0.7 on a 0–1 rubric (relevance, originality, memorability).
metrics: [Q, T, TK]
```

```yaml
id: creative-email
category: creative
difficulty: medium
prompt: >
  Write a 3-paragraph apology email from a CEO to customers after a data breach,
  tone: sincere and accountable, no corporate jargon.
ground_truth: N/A (open-ended)
scorer: judge
success: Quality >= 0.7 (tone, accountability, clarity).
metrics: [Q, T, TK]
```

---

## Scoring conventions

- **exact** — string/number equality (normalize whitespace/case).
- **code** — run against hidden tests; pass = all tests green.
- **judge** — held-out model scores blindly on a rubric; threshold per task.

---

## Coverage matrix

| Category   | easy | medium | hard | Tasks |
|------------|------|--------|------|-------|
| reasoning  | 1    | 1      | 1    | 3     |
| coding     | 1    | 1      | 1    | 3     |
| tool-use   | 0    | 1      | 2    | 3     |
| creative   | 1    | 1      | 0    | 2     |

Total: **11 tasks**, spanning 4 categories and 3 difficulty tiers. Sufficient for an initial
(N ≥ 5) × 9-treatment sweep without excessive API cost.
