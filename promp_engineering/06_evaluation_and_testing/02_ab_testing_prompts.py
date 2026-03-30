"""
06_evaluation_and_testing/02_ab_testing_prompts.py
═══════════════════════════════════════════════════════════════════

WHAT: A/B test two prompt variants on the same labelled dataset,
      compare them with mean score, paired t-test, and win rate.

WHY:  "Prompt B feels better" isn't evidence. A/B testing with a
      fixed test set and a statistical significance check turns
      intuition into a defensible decision.

WHEN: Before replacing a prompt in production.

PITFALLS:
  - Use the SAME test set for both variants (paired comparison).
  - At least 30 examples for meaningful statistics.
  - p < 0.05 doesn't mean the difference is practially important;
    check the mean delta and effect size too.
  - Automatic metrics can differ from human preference — validate
    with a small human review when the stakes are high.

Usage:
    python 02_ab_testing_prompts.py
    python 02_ab_testing_prompts.py --dry-run
"""

import sys
import os
import re
import math
import argparse
import random
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# Helpers: ROUGE-1 F1 (standalone, no external libs)
# ─────────────────────────────────────────────────────────────────────────────

def _tokens(text: str) -> list[str]:
    return re.findall(r'\w+', text.lower())


def rouge1_f1(reference: str, hypothesis: str) -> float:
    from collections import Counter
    ref = Counter(_tokens(reference))
    hyp = Counter(_tokens(hypothesis))
    match = sum((ref & hyp).values())
    prec = match / sum(hyp.values()) if hyp else 0.0
    rec  = match / sum(ref.values()) if ref else 0.0
    return 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def stdev(vals: list[float]) -> float:
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / len(vals)) if len(vals) > 1 else 0.0


def paired_ttest_pvalue(a: list[float], b: list[float]) -> float:
    """Two-tailed paired t-test. Returns p-value approximation via t-distribution."""
    diffs = [x - y for x, y in zip(a, b)]
    n = len(diffs)
    if n < 2:
        return 1.0
    m = mean(diffs)
    s = stdev(diffs)
    if s == 0:
        return 0.0 if m != 0 else 1.0
    t = abs(m) / (s / math.sqrt(n))
    # Approximation for degrees of freedom = n-1 using rational approximation
    df = n - 1
    x = df / (df + t * t)
    # Regularized incomplete beta function approximation
    # For small df this is imprecise but sufficient for demonstration
    p_approx = _ibeta(x, df / 2, 0.5)
    return min(1.0, max(0.0, p_approx))


def _ibeta(x: float, a: float, b: float) -> float:
    """Very rough regularised incomplete beta (for p-value demonstration only)."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    # Use log-space continued fraction approximation (simple)
    try:
        lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        return math.exp(a * math.log(x) + b * math.log(1 - x) - lbeta) / (a * (1 + (1 - b) / (a + 1) * x))
    except (ValueError, OverflowError):
        return 0.5  # fallback


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Variants
# ─────────────────────────────────────────────────────────────────────────────

PROMPT_A = """\
Summarize the following customer support ticket in one sentence.

Ticket:
{ticket}

Summary:"""

PROMPT_B = """\
You are a customer support analyst. Read the ticket below and write \
a single concise sentence that captures the customer's core issue and urgency.

Ticket:
{ticket}

One-sentence summary:"""

# ─────────────────────────────────────────────────────────────────────────────
# Test Dataset: (ticket, reference_summary) pairs
# ─────────────────────────────────────────────────────────────────────────────

TEST_SET = [
    {
        "ticket": "I've been trying to log in for three days. I reset my password twice and still get an 'invalid credentials' error. This is urgent — my entire team is blocked.",
        "reference": "Customer cannot log in despite two password resets and the issue is blocking their team.",
    },
    {
        "ticket": "I accidentally deleted a folder with three months of project files. Is there any way to restore it? We're launching Thursday.",
        "reference": "Customer urgently needs to restore an accidentally deleted folder before a Thursday launch.",
    },
    {
        "ticket": "The desktop app keeps crashing whenever I try to open a file larger than 1GB. The web version works fine.",
        "reference": "Desktop app crashes when opening files over 1GB, while the web version works correctly.",
    },
    {
        "ticket": "I was charged twice for my subscription this month. Please refund one charge and fix the billing.",
        "reference": "Customer was double-charged this month and requests a refund and billing fix.",
    },
    {
        "ticket": "How do I add a new team member? I went to Settings > Team but I don't see an invite button.",
        "reference": "Customer cannot find the invite button in Settings > Team to add a new member.",
    },
    {
        "ticket": "Our SSO stopped working after we migrated to a new Okta tenant. Users get a 403 error on redirect.",
        "reference": "SSO is broken after Okta tenant migration, resulting in 403 errors on redirect.",
    },
    {
        "ticket": "Can I export all workspace data including version history? We need this for a compliance audit.",
        "reference": "Customer needs to export workspace data with version history for a compliance audit.",
    },
    {
        "ticket": "The mobile app shows stale files from yesterday. Sync doesn't seem to be working on iOS.",
        "reference": "iOS mobile app is showing stale files and sync is not updating correctly.",
    },
]

random.seed(42)


@dataclass
class ABResult:
    variant: str
    item_id: int
    ticket: str
    reference: str
    output: str
    score: float
    cost_usd: float


def run_variant(client: LLMClient, template: str, variant_name: str) -> list[ABResult]:
    results = []
    for i, item in enumerate(TEST_SET):
        prompt = template.format(ticket=item["ticket"])
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=80,
        )
        output = response.content.strip() if not client.dry_run else item["reference"]
        score = rouge1_f1(item["reference"], output)
        results.append(ABResult(
            variant=variant_name,
            item_id=i + 1,
            ticket=item["ticket"][:60] + "...",
            reference=item["reference"],
            output=output,
            score=score,
            cost_usd=response.cost_usd,
        ))
    return results


def print_comparison(a_results: list[ABResult], b_results: list[ABResult]) -> None:
    a_scores = [r.score for r in a_results]
    b_scores = [r.score for r in b_results]
    a_wins = sum(1 for a, b in zip(a_scores, b_scores) if a > b)
    b_wins = sum(1 for a, b in zip(a_scores, b_scores) if b > a)
    ties   = len(a_scores) - a_wins - b_wins
    p_val  = paired_ttest_pvalue(a_scores, b_scores)
    total_cost = sum(r.cost_usd for r in a_results + b_results)

    print("\n" + "─" * 72)
    print("  A/B TEST RESULTS")
    print("─" * 72)
    print(f"  {'Item':<6} {'Prompt A':>9} {'Prompt B':>9} {'Winner':<8}")
    print("  " + "─" * 36)
    for a, b in zip(a_results, b_results):
        winner = "A" if a.score > b.score else ("B" if b.score > a.score else "TIE")
        print(f"  {a.item_id:<6} {a.score:>9.3f} {b.score:>9.3f} {winner:<8}")
    print("  " + "─" * 36)
    print(f"  {'MEAN':<6} {mean(a_scores):>9.3f} {mean(b_scores):>9.3f}")
    print(f"  {'STDEV':<6} {stdev(a_scores):>9.3f} {stdev(b_scores):>9.3f}")
    print("─" * 72)
    print(f"  Win rates: A wins {a_wins}, B wins {b_wins}, Ties {ties}")
    delta = mean(b_scores) - mean(a_scores)
    print(f"  Mean delta (B - A): {delta:+.3f} ROUGE-1 F1")
    print(f"  Paired t-test p-value: {p_val:.3f}  {'(significant at α=0.05)' if p_val < 0.05 else '(not significant)'}")
    winner_str = "Prompt B" if mean(b_scores) > mean(a_scores) else ("Prompt A" if mean(a_scores) > mean(b_scores) else "TIE")
    print(f"  Recommendation: {winner_str}")
    if total_cost > 0:
        print(f"  Total A/B test cost: ${total_cost:.5f}")
    print("─" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="A/B Test Prompt Variants")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 06 — Evaluation: A/B Testing Prompts")
    print("══════════════════════════════════════════════════════════════════════")
    print(f"  Test set: {len(TEST_SET)} examples")

    print("\n  PROMPT A:")
    print("  " + PROMPT_A.split("\n")[0])
    print("\n  PROMPT B:")
    print("  " + PROMPT_B.split("\n")[0])

    print("\n  Running Prompt A...", end=" ", flush=True)
    a_results = run_variant(client, PROMPT_A, "A")
    print("done.")

    print("  Running Prompt B...", end=" ", flush=True)
    b_results = run_variant(client, PROMPT_B, "B")
    print("done.")

    print_comparison(a_results, b_results)

    print("\n  SAMPLE OUTPUT COMPARISON (item 1)")
    print(f"  Ticket: {TEST_SET[0]['ticket'][:80]}...")
    print(f"  Reference: {TEST_SET[0]['reference']}")
    print(f"  Prompt A output: {a_results[0].output}")
    print(f"  Prompt B output: {b_results[0].output}")

    print("\n✅ A/B testing complete.\n")


if __name__ == "__main__":
    main()
