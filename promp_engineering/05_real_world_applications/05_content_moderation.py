"""
05_real_world_applications/05_content_moderation.py
═══════════════════════════════════════════════════════════════════

Multi-stage content moderation pipeline:
Stage 1: Fast binary filter (safe / potentially-unsafe)
Stage 2: Category classification (spam, harassment, NSFW, misinformation, etc.)
Stage 3: Severity + context analysis (nuance, satire, false positives)
Stage 4: Action recommendation with confidence + rationale

Uses: Classification, CoT reasoning, few-shot, structured output
"""

import sys
import os
import json
import argparse
from dataclasses import dataclass
from typing import Literal, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response


# ─────────────────────────────────────────────────────────────────────────────
# Test Content
# ─────────────────────────────────────────────────────────────────────────────

TEST_ITEMS = [
    {
        "id": "001",
        "content": "Make $5000 from home every day! No experience needed! Click here: http://clickme.xyz/earn",
        "context": "Product review",
        "expected": "REMOVE",
    },
    {
        "id": "002",
        "content": "Your code is terrible and honestly you should quit programming. Completely useless.",
        "context": "Stack Overflow comment",
        "expected": "REMOVE",
    },
    {
        "id": "003",
        "content": "This product has some minor quality issues but overall does what it promises for the price.",
        "context": "Product review",
        "expected": "APPROVE",
    },
    {
        "id": "004",
        "content": "Scientists are lying to you about vaccines. The real data shows they cause autism. Share this!",
        "context": "Forum post",
        "expected": "REMOVE",
    },
    {
        "id": "005",
        "content": "I'm so angry right now, I could kill for a good cup of coffee.",
        "context": "Social platform post",
        "expected": "APPROVE",  # Idiomatic expression, not literal threat
    },
    {
        "id": "006",
        "content": "Great tutorial! Fixed my issue in 10 minutes. Check out my related tool: github.com/user/tool",
        "context": "Forum comment",
        "expected": "APPROVE",  # Self-promotion but not spam
    },
    {
        "id": "007",
        "content": "As the CEO of this company, I'm disappointed by your negative review. You're clearly wrong.",
        "context": "Business review response",
        "expected": "REVIEW",  # Needs human review (unprofessional but not clear remove)
    },
]


@dataclass
class ModerationResult:
    content_id: str
    stage1_safe: bool
    category: Optional[str]
    severity: Optional[str]
    action: str          # APPROVE / REMOVE / REVIEW
    confidence: float
    rationale: str
    false_positive_risk: str


# ─────────────────────────────────────────────────────────────────────────────
# Stage Prompts
# ─────────────────────────────────────────────────────────────────────────────

def stage1_binary_check(client: LLMClient, content: str) -> bool:
    """Fast binary check: is this content clearly safe?"""
    response = client.chat(
        messages=[{"role": "user", "content": (
            "Does this content contain ANY of the following: spam links, explicit threats, "
            "hate speech, NSFW content, or obvious misinformation?\n\n"
            f"Content: {content}\n\nAnswer ONLY: SAFE or UNSAFE"
        )}],
        temperature=0.0,
        max_tokens=5,
    )
    if client.dry_run:
        return True  # Assume safe in dry run
    result = response.content.strip().upper()
    return "SAFE" in result


def stage2_classify(client: LLMClient, content: str, context: str) -> dict:
    """Deeper classification with categories."""
    response = client.chat(
        messages=[{"role": "user", "content": (
            f"Classify this content from a {context}.\n\n"
            f"Content: {content}\n\n"
            "Output ONLY JSON:\n"
            '{"category": "spam|harassment|hate_speech|misinformation|self_promotion|off_topic|clean", '
            '"confidence": 0.0-1.0, "reason": "brief reason"}'
        )}],
        temperature=0.0,
        max_tokens=100,
    )
    if client.dry_run:
        return {"category": "clean", "confidence": 0.9, "reason": "[DRY RUN]"}
    try:
        return json.loads(response.content.strip())
    except json.JSONDecodeError:
        return {"category": "unknown", "confidence": 0.5, "reason": response.content[:60]}


def stage3_context_analysis(client: LLMClient, content: str, category: str) -> dict:
    """Nuanced analysis considering context, satire, idioms."""
    response = client.chat(
        messages=[{"role": "user", "content": (
            f"Analyze this content flagged as '{category}'. Consider: "
            "Is it satire? An idiom? Misidentified? False positive?\n\n"
            f"Content: {content}\n\n"
            "Output ONLY JSON:\n"
            '{"severity": "low|medium|high|critical", '
            '"false_positive_likely": true|false, '
            '"context_notes": "brief analysis", '
            '"recommended_action": "APPROVE|REMOVE|REVIEW"}'
        )}],
        temperature=0.1,
        max_tokens=150,
    )
    if client.dry_run:
        return {
            "severity": "low",
            "false_positive_likely": False,
            "context_notes": "[DRY RUN]",
            "recommended_action": "APPROVE"
        }
    try:
        return json.loads(response.content.strip())
    except json.JSONDecodeError:
        return {"severity": "unknown", "false_positive_likely": False,
                "context_notes": "", "recommended_action": "REVIEW"}


def moderate_content(
    client: LLMClient,
    item: dict,
    verbose: bool = True,
) -> ModerationResult:
    """Run full 3-stage moderation pipeline on one content item."""
    content_id = item["id"]
    content = item["content"]
    context = item.get("context", "user post")

    if verbose:
        print(f"\n  Processing: {content_id} | {content[:55]}...")

    # Stage 1: Fast check
    is_safe = stage1_binary_check(client, content)
    if verbose:
        print(f"    Stage 1 (binary): {'SAFE' if is_safe else 'UNSAFE'}")

    if is_safe and not client.dry_run:
        # Short-circuit: clearly safe content skips stages 2-3
        return ModerationResult(
            content_id=content_id,
            stage1_safe=True,
            category="clean",
            severity="none",
            action="APPROVE",
            confidence=0.95,
            rationale="Passed fast binary safety check",
            false_positive_risk="low",
        )

    # Stage 2: Classification
    classification = stage2_classify(client, content, context)
    category   = classification.get("category", "unknown")
    confidence = classification.get("confidence", 0.5)
    if verbose:
        print(f"    Stage 2 (classify): {category} ({confidence:.0%})")

    # Stage 3: Context analysis
    analysis = stage3_context_analysis(client, content, category)
    severity  = analysis.get("severity", "unknown")
    action    = analysis.get("recommended_action", "REVIEW")
    fp_likely = analysis.get("false_positive_likely", False)
    notes     = analysis.get("context_notes", "")

    if verbose:
        print(f"    Stage 3 (context): {severity} severity → {action}")
        if fp_likely:
            print(f"    ⚠️  False positive likely: {notes[:60]}")

    return ModerationResult(
        content_id=content_id,
        stage1_safe=is_safe,
        category=category,
        severity=severity,
        action=action,
        confidence=confidence,
        rationale=notes or classification.get("reason", ""),
        false_positive_risk="high" if fp_likely else "low",
    )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Content Moderation Pipeline")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--item", type=str, default="all",
                        help="Content ID to test, or 'all'")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 05 — Real World: Content Moderation Pipeline")
    print("  3 stages: Binary → Category → Context → Action")
    print("═" * 72)

    items = TEST_ITEMS
    if args.item != "all":
        items = [i for i in TEST_ITEMS if i["id"] == args.item]
        if not items:
            print(f"  Item {args.item} not found")
            return

    results = []
    for item in items:
        result = moderate_content(client, item, verbose=True)
        results.append(result)

    # Results table
    print("\n  ── Results Summary ───────────────────────────────────────────")
    print(f"\n  {'ID':<6} {'Action':<10} {'Category':<18} {'Severity':<10} {'Expected':<10} {'Match?'}")
    print(f"  {'─' * 6} {'─' * 10} {'─' * 18} {'─' * 10} {'─' * 10} {'─' * 7}")

    correct = 0
    for result, item in zip(results, items):
        expected  = item.get("expected", "?")
        match     = "✅" if result.action == expected else "❌"
        if result.action == expected:
            correct += 1
        print(f"  {result.content_id:<6} {result.action:<10} "
              f"{(result.category or '?'):<18} {(result.severity or '?'):<10} "
              f"{expected:<10} {match}")

    if not client.dry_run and results:
        accuracy = correct / len(results)
        print(f"\n  Accuracy vs expected: {correct}/{len(results)} = {accuracy:.0%}")
        print("\n  Note: False positive check helps reduce 'REMOVE' on idioms/satire")

    print("\n✅ Content moderation pipeline complete.\n")


if __name__ == "__main__":
    main()
