"""
06_evaluation_and_testing/04_regression_testing.py
═══════════════════════════════════════════════════════════════════

WHAT: Maintain a "golden dataset" of (input → expected output) pairs and
      run it against multiple prompt versions, detecting regressions.

WHY:  When you improve a prompt for one case, you can accidentally break
      others. Regression tests catch this before deployment.

WHEN: Before merging a prompt change. Ideal in a CI/CD pipeline.

PITFALLS:
  - Golden answers must be created with care; wrong references produce
    misleading results.
  - Metric thresholds need tuning for your domain (e.g., ROUGE-1 > 0.5
    may be too strict for creative tasks, too loose for factual ones).
  - Non-deterministic models need multiple runs or fixed temperature=0.

Usage:
    python 04_regression_testing.py
    python 04_regression_testing.py --dry-run
    python 04_regression_testing.py --show-diff
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass, asdict
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# Minimal ROUGE-1 (no dependencies)
# ─────────────────────────────────────────────────────────────────────────────

def rouge1_f1(ref: str, hyp: str) -> float:
    def tok(t):return Counter(re.findall(r'\w+', t.lower()))
    r, h = tok(ref), tok(hyp)
    match = sum((r & h).values())
    p = match / sum(h.values()) if h else 0.0
    rc = match / sum(r.values()) if r else 0.0
    return 2 * p * rc / (p + rc) if (p + rc) else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# Golden Dataset
# ─────────────────────────────────────────────────────────────────────────────

GOLDEN_SET = [
    {
        "id": "REG-001",
        "input": "Summarize in one sentence: Our Q3 revenue grew 23% YoY to $4.2M, driven by enterprise deals.",
        "reference": "Q3 revenue grew 23% year-over-year to $4.2M, driven by enterprise deals.",
        "min_rouge1": 0.45,
        "required_keywords": ["revenue", "23%", "4.2"],
    },
    {
        "id": "REG-002",
        "input": "Classify the sentiment of: 'The product is absolutely fantastic, exceeded all expectations!'",
        "reference": "positive",
        "min_rouge1": 0.3,
        "required_keywords": ["positive"],
    },
    {
        "id": "REG-003",
        "input": "Extract the company name from: 'Acme Corp reported record profits of $10M last quarter.'",
        "reference": "Acme Corp",
        "min_rouge1": 0.5,
        "required_keywords": ["acme"],
    },
    {
        "id": "REG-004",
        "input": "Translate to French: 'Good morning, how are you?'",
        "reference": "Bonjour, comment allez-vous?",
        "min_rouge1": 0.3,
        "required_keywords": ["bonjour"],
    },
    {
        "id": "REG-005",
        "input": "What programming language is known as 'the language of the web' for browser scripting?",
        "reference": "JavaScript",
        "min_rouge1": 0.5,
        "required_keywords": ["javascript"],
    },
    {
        "id": "REG-006",
        "input": "In one sentence, describe what a REST API is.",
        "reference": "A REST API is a web service interface that uses HTTP methods to allow clients to create, read, update, and delete resources.",
        "min_rouge1": 0.3,
        "required_keywords": ["api", "http"],
    },
    {
        "id": "REG-007",
        "input": "List 3 benefits of unit testing. Be brief.",
        "reference": "Unit testing catches bugs early, documents expected behavior, and makes refactoring safer.",
        "min_rouge1": 0.2,
        "required_keywords": ["bug", "test"],
    },
    {
        "id": "REG-008",
        "input": "What does SOLID stand for in software engineering?",
        "reference": "SOLID stands for Single responsibility, Open-closed, Liskov substitution, Interface segregation, and Dependency inversion.",
        "min_rouge1": 0.35,
        "required_keywords": ["single", "open", "liskov"],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Versions
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_V1 = "Answer the following question or complete the task:\n\n{input}"

PROMPT_V2 = (
    "You are a knowledgeable assistant. Answer the following question or "
    "complete the task concisely. Be accurate and direct.\n\n{input}"
)


# ─────────────────────────────────────────────────────────────────────────────
# Regression Runner
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RegressionResult:
    item_id: str
    version: str
    input_text: str
    reference: str
    output: str
    rouge1: float
    has_required_keywords: bool
    missing_keywords: list[str]
    passed: bool
    cost_usd: float


def run_version(
    client: LLMClient,
    prompt_template: str,
    version_name: str,
) -> list[RegressionResult]:
    results = []
    for item in GOLDEN_SET:
        prompt = prompt_template.format(input=item["input"])
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=100,
        )
        output = response.content.strip() if not client.dry_run else item["reference"]
        score = rouge1_f1(item["reference"], output)
        output_lower = output.lower()
        missing = [kw for kw in item["required_keywords"] if kw not in output_lower]
        has_kw = len(missing) == 0
        passed = score >= item["min_rouge1"] and has_kw
        results.append(RegressionResult(
            item_id=item["id"],
            version=version_name,
            input_text=item["input"][:60] + "...",
            reference=item["reference"],
            output=output,
            rouge1=score,
            has_required_keywords=has_kw,
            missing_keywords=missing,
            passed=passed,
            cost_usd=response.cost_usd,
        ))
    return results


def _passed_ids(results: list[RegressionResult]) -> set[str]:
    return {r.item_id for r in results if r.passed}


def print_comparison(v1: list[RegressionResult], v2: list[RegressionResult], show_diff: bool) -> None:
    v1_pass = _passed_ids(v1)
    v2_pass = _passed_ids(v2)
    regressions = v1_pass - v2_pass      # passed in v1, failed in v2
    improvements = v2_pass - v1_pass     # failed in v1, passed in v2
    total_cost = sum(r.cost_usd for r in v1 + v2)

    print("\n" + "─" * 72)
    print("  REGRESSION TEST REPORT")
    print("─" * 72)
    print(f"  {'ID':<10} {'V1 ROUGE':>9} {'V2 ROUGE':>9} {'V1':>4} {'V2':>4} {'Status':<12}")
    print("  " + "─" * 56)

    v1_by_id = {r.item_id: r for r in v1}
    v2_by_id = {r.item_id: r for r in v2}

    for item in GOLDEN_SET:
        r1 = v1_by_id[item["id"]]
        r2 = v2_by_id[item["id"]]
        if item["id"] in regressions:
            status = "⚠️  REGRESSION"
        elif item["id"] in improvements:
            status = "✅ IMPROVEMENT"
        else:
            status = "— stable"
        print(
            f"  {item['id']:<10} "
            f"{r1.rouge1:>9.3f} {r2.rouge1:>9.3f} "
            f"{'✅' if r1.passed else '❌':>4} {'✅' if r2.passed else '❌':>4} "
            f"{status}"
        )

    print("  " + "─" * 56)
    print(f"  v1 passed: {len(v1_pass)}/{len(GOLDEN_SET)}")
    print(f"  v2 passed: {len(v2_pass)}/{len(GOLDEN_SET)}")
    print(f"  Regressions (v1 pass → v2 fail): {len(regressions)}")
    print(f"  Improvements (v1 fail → v2 pass): {len(improvements)}")

    if regressions:
        print(f"\n  ❌ DEPLOY BLOCKED: {len(regressions)} regression(s) detected in v2!")
        for rid in sorted(regressions):
            r2 = v2_by_id[rid]
            print(f"     {rid}: ROUGE {r2.rouge1:.3f} (need ≥ {[i['min_rouge1'] for i in GOLDEN_SET if i['id']==rid][0]:.2f})")
            if r2.missing_keywords:
                print(f"       Missing keywords: {r2.missing_keywords}")
    else:
        print(f"\n  ✅ No regressions — v2 is safe to deploy")

    if show_diff and regressions:
        print("\n  REGRESSION DETAILS")
        for rid in sorted(regressions):
            r2 = v2_by_id[rid]
            print(f"\n  [{rid}]")
            print(f"  Input:     {r2.input_text}")
            print(f"  Reference: {r2.reference}")
            print(f"  v2 Output: {r2.output}")

    if total_cost > 0:
        print(f"\n  Total cost: ${total_cost:.5f}")
    print("─" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Regression Testing for Prompts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--show-diff", action="store_true",
                        help="Print input/output details for failed regressions")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 06 — Evaluation: Regression Testing")
    print("══════════════════════════════════════════════════════════════════════")
    print(f"  Golden set: {len(GOLDEN_SET)} items")
    print("  Comparing Prompt v1 vs Prompt v2")

    print("\n  Running v1...", end=" ", flush=True)
    v1_results = run_version(client, PROMPT_V1, "v1")
    print("done.")

    print("  Running v2...", end=" ", flush=True)
    v2_results = run_version(client, PROMPT_V2, "v2")
    print("done.")

    print_comparison(v1_results, v2_results, args.show_diff)
    print("\n✅ Regression testing complete.\n")


if __name__ == "__main__":
    main()
