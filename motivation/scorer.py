"""Scoring: exact, code (hidden tests), and blind-judge evaluators."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import Task
from .models import ChatClient
from .runner import RunResult


@dataclass
class Score:
    score: float          # 0..1 (quality)
    passed: bool          # success (SR)
    reason: str
    method: str
    judge_details: dict | None = None  # per-judge breakdown for judge matrix


# --- exact ----------------------------------------------------------------

def _exact(gt: str, text: str) -> Score:
    got = text.strip()
    want = str(gt).strip()
    if re.fullmatch(r"[+-]?\d+(\.\d+)?", want):
        nums = re.findall(r"[+-]?\d+(?:\.\d+)?", got)
        if nums:
            try:
                ok = abs(float(nums[-1]) - float(want)) < 1e-6
                return Score(1.0 if ok else 0.0, ok, f"numeric match: {nums[-1]}", "exact")
            except ValueError:
                pass
    ok = got.lower() == want.lower()
    return Score(1.0 if ok else 0.0, ok, "string match" if ok else "mismatch", "exact")


# --- code (hidden tests in subprocess) ------------------------------------

_NORMALIZERS = {
    "identity": "def _norm(x):\n    return x\n",
    "anagram_groups": "def _norm(x):\n    return sorted([sorted(g) for g in x])\n",
}


def _extract_function(text: str, name: str) -> str | None:
    candidates: list[str] = []
    sources = [text]
    for block in re.findall(r"```(?:python|py)?\s*(.*?)```", text, re.DOTALL):
        sources.append(block)
    for src in sources:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
                candidates.append(ast.unparse(node))
    return candidates[-1] if candidates else None


def _run_code_case(func_source: str, test: dict) -> tuple[bool, str]:
    norm = _NORMALIZERS.get(test.get("normalizer", "identity"), _NORMALIZERS["identity"])
    func_name = re.search(r"def\s+(\w+)\s*\(", func_source).group(1)
    if "input_expr" in test:
        input_src = test["input_expr"]  # raw Python expression, e.g. "(list(range(10000)), 19997)"
    else:
        input_src = repr(test["input"])
    script = (
        func_source
        + "\n\n"
        + norm
        + "\n"
        + f"_input = {input_src}\n"
        + f"_expected = {test['expected']!r}\n"
        + "import sys\n"
        + "try:\n"
        + f"    _out = _norm({func_name}(*_input))\n"
        + "except Exception as _e:\n"
        + "    print('FAIL: exception: ' + repr(_e))\n"
        + "    sys.exit(0)\n"
        + "if _out == _norm(_expected):\n"
        + "    print('PASS')\n"
        + "else:\n"
        + "    print('FAIL: got ' + repr(_out) + ' expected ' + repr(_expected))\n"
    )
    timeout = float(test.get("timeout", 8.0))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        tmp = fh.name
    try:
        proc = subprocess.run(
            [sys.executable, tmp], capture_output=True, text=True, timeout=timeout
        )
        out = (proc.stdout or "").strip()
        if proc.returncode != 0:
            return False, f"crash: {(proc.stderr or '').strip()[:120]}"
        if out.startswith("PASS"):
            return True, "pass"
        return False, out.replace("FAIL: ", "")[:200]
    except subprocess.TimeoutExpired:
        return False, f"timeout ({timeout}s)"
    finally:
        Path(tmp).unlink(missing_ok=True)


def _code(task: Task, text: str) -> Score:
    gt = task.ground_truth
    fn = _extract_function(text, gt["function_name"])
    if fn is None:
        return Score(0.0, False, "function not found in response", "code")
    results = [_run_code_case(fn, t) for t in gt["tests"]]
    passed = all(ok for ok, _ in results)
    reasons = "; ".join(f"{i+1}:{r}" for i, (_, r) in enumerate(results))
    return Score(1.0 if passed else 0.0, passed, reasons, "code")


# --- judge ----------------------------------------------------------------

def _judge_one(client: ChatClient, cfg: dict, task: Task, text: str) -> Score:
    if client.is_mock():
        return Score(0.5, True, "mock judge", "judge")

    prompt = cfg["prompt"].format(
        task=task.prompt, ground_truth=task.ground_truth, response=text
    )
    comp = client.complete(cfg["system"], [{"role": "user", "content": prompt}])
    raw = comp.text.strip()
    obj = None
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                obj = json.loads(m.group(0))
            except json.JSONDecodeError:
                obj = None
    if obj is None:
        return Score(0.0, False, "unparseable judge output", "judge")
    score = min(max(float(obj.get("score", 0.0)), 0.0), 1.0)
    passed = bool(obj.get("pass", False))
    return Score(score, passed, str(obj.get("reason", ""))[:200], "judge")


def _judge(clients: list[ChatClient], cfg: dict, task: Task, text: str) -> Score:
    if not clients:
        return Score(0.0, False, "no judges configured", "judge")

    details: dict = {}
    votes = 0
    total_score = 0.0
    for c in clients:
        s = _judge_one(c, cfg, task, text)
        key = f"{c.provider.name}/{c.model}"
        details[key] = {"score": s.score, "pass": s.passed, "reason": s.reason}
        total_score += s.score
        votes += 1 if s.passed else 0

    n = len(clients)
    passed = votes > n / 2  # strict majority (even-count ties fall to fail)
    agg = total_score / n
    reason = f"{votes}/{n} votes; " + "; ".join(
        f"{k}:{'pass' if v['pass'] else 'fail'}" for k, v in details.items()
    )
    return Score(agg, passed, reason, "judge", judge_details=details)


def score(judge_clients: list[ChatClient], judge_cfg: dict, task: Task, result: RunResult) -> Score:
    text = result.final_text
    if task.scorer == "exact":
        return _exact(str(task.ground_truth), text)
    if task.scorer == "code":
        return _code(task, text)
    return _judge(judge_clients, judge_cfg, task, text)
