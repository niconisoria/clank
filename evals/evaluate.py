#!/usr/bin/env python3
"""Model-graded evaluator for eval_dataset.json.

For each task: (1) generate a solution with the solution model, (2) grade it
against `solution_criteria` with a second Claude call acting as LLM judge.

Install: uv sync (deps pinned in uv.lock)
Auth: reads ANTHROPIC_API_KEY from a .env file (see .env.example) or the real
environment / `ant auth login` — no key hardcoded here.

Usage (from the repo root):
    uv run evals/evaluate.py
    uv run evals/evaluate.py --skill define
    uv run evals/evaluate.py --output results.json
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from functools import cache
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, field_validator

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
REPORT_PATH = SCRIPT_DIR / "report.json"
load_dotenv(SCRIPT_DIR / ".env")

MODEL = "claude-sonnet-5"  # used for both solution generation and grading
PASS_THRESHOLD = 7  # score is 1-10; >= this counts as a pass

# $/1M tokens (input, output) for MODEL — cost estimate only
INPUT_PRICE, OUTPUT_PRICE = 2.00, 10.00


@cache
def load_skill_text(skill: str) -> str:
    path = ROOT / "skills" / skill / "SKILL.md"
    if not path.exists():
        raise FileNotFoundError(f"no SKILL.md for skill {skill!r} at {path}")
    return path.read_text()


SOLUTION_SYSTEM = """You are operating under the following Claude Code skill definition. \
Follow its conventions, tone, output format, and decision rules exactly when producing your \
response. You have no file or bash tools in this evaluation — where the skill instructs you \
to run a command or write a file, simulate that outcome by directly emitting the resulting \
content (e.g. the file's new state). Do not narrate or announce the action taken (no lines \
like "status updated: X -> Y") — just show the result, exactly as the skill's own output \
format specifies.

--- SKILL DEFINITION: {skill} ---
{skill_text}
--- END SKILL DEFINITION ---

Now solve the task below. Output ONLY the requested artifact in the requested format — no \
preamble, no meta commentary about what you're about to do, unless the task itself asks for prose."""

GRADER_SYSTEM = "You are an expert code reviewer. Respond with JSON only."

GRADER_SCHEMA = {
    "type": "object",
    "properties": {
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
        "score": {"type": "integer"},
    },
    "required": ["strengths", "weaknesses", "reasoning", "score"],
    "additionalProperties": False,
}


def with_retry(
    fn, *, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 30.0
):
    """SDK already retries 429/5xx/connection errors internally (client's max_retries);
    this adds one more layer at the call site so a flaky call doesn't kill a whole run."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn()
        except anthropic.RateLimitError as e:
            last_exc = e
        except anthropic.APIStatusError as e:
            if e.status_code < 500:
                raise
            last_exc = e
        except anthropic.APIConnectionError as e:
            last_exc = e
        time.sleep(min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay))
    raise last_exc


@dataclass
class Task:
    skill: str
    task: str
    format: str
    solution_criteria: str

    @staticmethod
    def load(path: Path) -> list[Task]:
        return [Task(**t) for t in json.loads(path.read_text())]


@dataclass
class Usage:
    solution_input: int
    solution_output: int
    grader_input: int
    grader_output: int

    def cost(self) -> float:
        total_in = self.solution_input + self.grader_input
        total_out = self.solution_output + self.grader_output
        return total_in / 1e6 * INPUT_PRICE + total_out / 1e6 * OUTPUT_PRICE


@dataclass
class TaskResult:
    task: Task
    solution: str | None = None
    score: int = 0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    reasoning: str | None = None
    usage: Usage | None = None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and self.score >= PASS_THRESHOLD

    @property
    def status(self) -> str:
        return "ERROR" if self.error else ("PASS" if self.passed else "FAIL")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["task"] = asdict(self.task)
        d["passed"] = self.passed
        return d


class Grader:
    """Wraps the two Claude calls: generate a solution, then judge it."""

    def __init__(self, client: anthropic.Anthropic):
        self.client = client

    def generate_solution(self, task: Task) -> tuple[str, anthropic.types.Usage]:
        system = SOLUTION_SYSTEM.format(
            skill=task.skill, skill_text=load_skill_text(task.skill)
        )
        system += f"\n\nRequested format: {task.format}"
        response = with_retry(
            lambda: self.client.messages.create(
                model=MODEL,
                max_tokens=16000,
                system=system,
                messages=[{"role": "user", "content": task.task}],
            )
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return text, response.usage

    def grade(self, task: Task, solution: str) -> tuple[dict, anthropic.types.Usage]:
        prompt = f"""Evaluate the following AI-generated solution.
        Original Task:
        <task>
        {task.task}
        </task>

        What a good solution must satisfy:
        <solution_criteria>
        {task.solution_criteria}
        </solution_criteria>

        Solution to Evaluate:
        <solution>
        {solution}
        </solution>

        Judge against solution_criteria only — not general style preferences. Give
        1-3 strengths, 1-3 weaknesses, concise reasoning, and a score 1-10."""

        response = with_retry(
            lambda: self.client.messages.create(
                model=MODEL,
                max_tokens=4096,  # adaptive thinking is on by default; 1024 got truncated before any text block
                system=GRADER_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
                output_config={
                    "format": {"type": "json_schema", "schema": GRADER_SCHEMA}
                },
            )
        )
        text = next((b.text for b in response.content if b.type == "text"), None)
        if text is None:
            raise RuntimeError(
                f"grader returned no text block (stop_reason={response.stop_reason}); "
                "likely truncated by max_tokens before completing thinking + JSON"
            )
        verdict = json.loads(text)
        verdict["score"] = max(
            1, min(10, verdict["score"])
        )  # schema can't bound this; clamp
        return verdict, response.usage

    def evaluate(self, task: Task) -> TaskResult:
        try:
            solution, sol_usage = self.generate_solution(task)
            verdict, grade_usage = self.grade(task, solution)
            return TaskResult(
                task=task,
                solution=solution,
                score=verdict["score"],
                strengths=verdict["strengths"],
                weaknesses=verdict["weaknesses"],
                reasoning=verdict["reasoning"],
                usage=Usage(
                    solution_input=sol_usage.input_tokens,
                    solution_output=sol_usage.output_tokens,
                    grader_input=grade_usage.input_tokens,
                    grader_output=grade_usage.output_tokens,
                ),
            )
        except Exception as e:  # noqa: BLE001 — one bad task must not kill the batch
            return TaskResult(task=task, error=f"{type(e).__name__}: {e}")


class Evaluator:
    """Runs a Grader over a task set, concurrently, and reports results."""

    def __init__(self, grader: Grader, concurrency: int = 4):
        self.grader = grader
        self.concurrency = concurrency

    def run(self, tasks: list[Task]) -> list[TaskResult]:
        results: list[TaskResult | None] = [None] * len(tasks)
        with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
            futures = {
                pool.submit(self.grader.evaluate, t): i for i, t in enumerate(tasks)
            }
            for n, fut in enumerate(as_completed(futures), 1):
                i = futures[fut]
                results[i] = fut.result()
                r = results[i]
                print(
                    f"[{n}/{len(tasks)}] {r.status:5} {r.score}/10  {r.task.skill:10} {r.task.task[:60]!r}"
                )
        return results


class Report:
    """Summarizes a completed run: per-skill pass rate, cost, errors."""

    def __init__(self, results: list[TaskResult]):
        self.results = results

    def by_skill(self) -> dict[str, list[TaskResult]]:
        groups: dict[str, list[TaskResult]] = {}
        for r in self.results:
            groups.setdefault(r.task.skill, []).append(r)
        return groups

    def total_cost(self) -> float:
        return sum(r.usage.cost() for r in self.results if r.usage)

    def print_summary(self) -> None:
        print("\n--- Summary ---")
        for skill, rs in sorted(self.by_skill().items()):
            passed = sum(r.passed for r in rs)
            avg_score = sum(r.score for r in rs) / len(rs)
            print(
                f"{skill:12} {passed}/{len(rs)} passed (>= {PASS_THRESHOLD}/10), avg score {avg_score:.1f}/10"
            )

        overall_pass = sum(r.passed for r in self.results)
        print(f"{'TOTAL':12} {overall_pass}/{len(self.results)} passed")

        cost = self.total_cost()
        if cost:
            print(f"Estimated cost: ${cost:.4f}")

        errors = [r for r in self.results if r.error]
        if errors:
            print(f"\n{len(errors)} task(s) errored:", file=sys.stderr)
            for r in errors:
                print(f"  {r.task.skill}: {r.error}", file=sys.stderr)

    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    def summary(self) -> dict:
        by_skill = {
            skill: {
                "passed": sum(r.passed for r in rs),
                "total": len(rs),
                "avg_score": round(sum(r.score for r in rs) / len(rs), 2),
            }
            for skill, rs in sorted(self.by_skill().items())
        }
        return {
            "total": len(self.results),
            "passed": sum(r.passed for r in self.results),
            "cost_usd": round(self.total_cost(), 4),
            "by_skill": by_skill,
            "errors": [
                {"skill": r.task.skill, "error": r.error}
                for r in self.results
                if r.error
            ],
            "results": [
                {
                    "skill": r.task.skill,
                    "task": r.task.task,
                    "solution_criteria": r.task.solution_criteria,
                    "passed": r.passed,
                    "score": r.score,
                    "strengths": r.strengths,
                    "weaknesses": r.weaknesses,
                    "reasoning": r.reasoning,
                    "error": r.error,
                }
                for r in self.results
            ],
        }

    def save_summary(self, path: Path = REPORT_PATH) -> None:
        path.write_text(json.dumps(self.summary(), indent=2))
        print(f"Report written to {path}")

    def save(self, path: Path) -> None:
        path.write_text(json.dumps([r.to_dict() for r in self.results], indent=2))
        print(f"\nFull results (incl. solutions) written to {path}")


VALID_SKILLS = {"init", "define", "implement", "review", "validate", "gc", "yolo"}


class Args(BaseModel):
    """CLI arguments, validated together instead of via scattered if-checks."""

    dataset: Path = SCRIPT_DIR / "eval_dataset.json"
    skill: str | None = None
    concurrency: int = Field(default=4, gt=0)
    output: Path | None = None

    @field_validator("dataset")
    @classmethod
    def dataset_must_exist(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"dataset not found: {v}")
        return v

    @field_validator("skill")
    @classmethod
    def skill_must_be_known(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_SKILLS:
            raise ValueError(f"unknown skill {v!r}; choose from {sorted(VALID_SKILLS)}")
        return v


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        description="Model-graded evaluator for eval_dataset.json"
    )
    parser.add_argument("--dataset", default=str(SCRIPT_DIR / "eval_dataset.json"))
    parser.add_argument(
        "--skill",
        default=None,
        help="only run tasks for this skill (init/define/implement/review/validate/gc/yolo)",
    )
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument(
        "--output",
        default=None,
        help="write full results (incl. solutions) to this JSON file",
    )
    ns = parser.parse_args()
    try:
        return Args.model_validate(vars(ns))
    except ValidationError as e:
        for err in e.errors():
            print(f"argument error: {err['msg']}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    args = parse_args()

    tasks = Task.load(args.dataset)
    if args.skill:
        tasks = [t for t in tasks if t.skill == args.skill]
    if not tasks:
        print("No tasks matched.", file=sys.stderr)
        sys.exit(1)

    grader = Grader(anthropic.Anthropic())
    results = Evaluator(grader, concurrency=args.concurrency).run(tasks)

    report = Report(results)
    report.print_summary()
    report.save_summary()
    if args.output:
        report.save(args.output)

    sys.exit(0 if report.all_passed() else 1)


if __name__ == "__main__":
    main()
