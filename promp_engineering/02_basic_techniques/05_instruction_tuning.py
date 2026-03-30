"""
02_basic_techniques/05_instruction_tuning.py
═══════════════════════════════════════════════════════════════════

WHAT:   The art of writing clear, specific, unambiguous instructions
        that reliably produce the output you intend.

WHY:    The model does EXACTLY what you say — including the gaps and
        ambiguities you didn't intend. Imprecise language is the root
        cause of 80% of "bad" LLM outputs in production.

THE 10 RULES OF CLEAR INSTRUCTIONS:
    1. Use ACTION VERBS — "Extract" not "Look at"
    2. Be SPECIFIC about scope — "Top 3" not "key points"
    3. Specify AUDIENCE — "for a non-technical manager"
    4. Set LENGTH constraints — "in exactly 2 sentences"
    5. State what to DO, not just what to AVOID
    6. Use ORDERED LISTS for multi-step instructions
    7. Define EDGE CASES explicitly
    8. Include DESIRABLE behaviors, not just restrictions
    9. Use EXAMPLES for complex formats (→ few-shot)
    10. Test with ADVERSARIAL inputs to find gaps

COMMON PITFALLS:
        - "Analyze" (analyze HOW? format? depth? audience?)
        - "Be concise" (how concise? 1 sentence? 100 words?)
        - "Return the most important things" (most important by what measure?)
        - Stacking negatives: "Don't not do X" → just say "Do X"
        - Instructions that contradict each other
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response


# ─────────────────────────────────────────────────────────────────────────────
# THE 10 RULES — side-by-side comparisons
# ─────────────────────────────────────────────────────────────────────────────

INSTRUCTION_IMPROVEMENTS = [
    {
        "rule": "Use ACTION VERBS with clear scope",
        "bad":  "Look at this contract and tell me about it.",
        "good": "Identify all clauses where the customer's liability exceeds $50,000. "
                "For each, quote the exact clause and explain the financial risk in plain English.",
    },
    {
        "rule": "Specify LENGTH constraints explicitly",
        "bad":  "Give me a short summary of this earnings call.",
        "good": "Summarize this earnings call in exactly 3 bullet points. "
                "Each bullet must be ≤ 15 words and start with a noun.",
    },
    {
        "rule": "Define AUDIENCE and expertise level",
        "bad":  "Explain machine learning.",
        "good": "Explain what machine learning is to a CFO who has a finance background "
                "but no technical knowledge. Use a financial analogy. Maximum 4 sentences.",
    },
    {
        "rule": "State the OUTPUT FORMAT explicitly",
        "bad":  "What are the main risks in this paragraph?",
        "good": "Extract all risks from the paragraph below. "
                "Return a JSON array of objects with keys: "
                "risk (string), severity (HIGH|MEDIUM|LOW), likelihood (HIGH|MEDIUM|LOW).",
    },
    {
        "rule": "Order multi-step instructions as a numbered list",
        "bad":  "Read the email, figure out what the person wants, write a draft reply that addresses everything, then check if it's professional.",
        "good": (
            "Process this customer email in the following order:\n"
            "1. Identify the core request (one sentence)\n"
            "2. List all sub-requests as bullet points\n"
            "3. Assess the urgency: CRITICAL | HIGH | MEDIUM | LOW\n"
            "4. Draft a reply addressing all points, in professional tone\n"
            "5. End with a specific next-step commitment and timeline"
        ),
    },
    {
        "rule": "Define EDGE CASES explicitly",
        "bad":  "Extract the price from the invoice text.",
        "good": "Extract the total invoice amount.\n"
                "- Return only the numeric value as a float (no $ or commas)\n"
                "- If multiple amounts exist, return the one labeled 'Total Due' or 'Grand Total'\n"
                "- If no amount is found, return null\n"
                "- If the amount is in a non-USD currency, still return the numeric value",
    },
    {
        "rule": "Include DESIRABLE behaviors, not just restrictions",
        "bad":  "Don't use jargon, don't be too long, don't be vague.",
        "good": "Write clearly for a general audience, in exactly 2 paragraphs of ≤ 5 sentences each, "
                "with a specific and concrete recommendation at the end.",
    },
    {
        "rule": "Specify TONE alongside content requirements",
        "bad":  "Reply to this negative review.",
        "good": "Write a response to this negative customer review. "
                "Tone: empathetic but professional. Length: 60–80 words. "
                "Structure: (1) Acknowledge the issue, (2) Apologize sincerely, "
                "(3) Explain what you're doing to fix it, (4) Offer concrete resolution.",
    },
]


def demo_instruction_improvements(client: LLMClient) -> None:
    """Show bad vs good instructions side-by-side on real examples."""

    print("\n" + "═" * 72)
    print("  THE 10 RULES: Bad → Good Instruction Comparisons")
    print("═" * 72)

    # Show a few comparisons with live API calls
    live_examples = [
        {
            "rule": "Specify LENGTH + FORMAT",
            "bad_instruction": "Summarize this annual report section.",
            "good_instruction": (
                "Summarize this annual report section as a JSON object with keys:\n"
                "- headline: one sentence (≤ 15 words)\n"
                "- key_metrics: list of up to 4 {metric, value, change_yoy} objects\n"
                "- risks: list of up to 3 strings\n"
                "- outlook: one sentence\n"
                "Return ONLY the JSON, no markdown or explanation."
            ),
            "input": (
                "Revenue for the fiscal year reached $4.2B, a 23% increase year-over-year, "
                "driven primarily by enterprise subscription growth (+41%) offsetting a "
                "decline in legacy perpetual licenses (-18%). Operating margin expanded "
                "200 basis points to 28%. However, rising cloud infrastructure costs and "
                "intensifying competition in the mid-market segment represent key headwinds. "
                "Management guided for $4.8–5.0B in FY2025 revenue."
            ),
        },
    ]

    for ex in live_examples:
        print(f"\n  Rule: {ex['rule']}")
        print(f"\n  ❌ Bad instruction:  {ex['bad_instruction']}")
        print(f"  ✅ Good instruction: {ex['good_instruction'][:80]}...")

        if not client.dry_run:
            print("\n  --- Running bad instruction ---")
            resp_bad = client.chat(
                user_message=f"{ex['bad_instruction']}\n\n```\n{ex['input']}\n```",
                temperature=0.2,
                max_tokens=250,
            )
            print(f"  Bad output:\n  {resp_bad.content.strip()[:300]}")

            print("\n  --- Running good instruction ---")
            resp_good = client.chat(
                user_message=f"{ex['good_instruction']}\n\n```\n{ex['input']}\n```",
                temperature=0.2,
                max_tokens=300,
            )
            format_response(resp_good, title="Good Instruction Output — Structured & Predictable")


def print_all_rules() -> None:
    """Print all 10 rules with bad/good examples."""

    print("\n" + "═" * 72)
    print("  10 RULES FOR WRITING CLEAR INSTRUCTIONS")
    print("═" * 72)

    for i, improvement in enumerate(INSTRUCTION_IMPROVEMENTS, 1):
        print(f"\n  Rule {i}: {improvement['rule']}")
        print(f"\n  ❌ Bad:  {improvement['bad'][:120]}")
        print(f"  ✅ Good: {improvement['good'][:120]}...")

    print("\n" + "═" * 72)


# ─────────────────────────────────────────────────────────────────────────────
# INSTRUCTION AUDIT TOOL — Analyze any instruction for weaknesses
# ─────────────────────────────────────────────────────────────────────────────

def audit_instruction(instruction: str) -> dict:
    """
    Score an instruction across the 10 rules.
    Returns a dict with scores and improvement suggestions.
    
    This is a rule-based heuristic; in production you'd use an LLM to audit.
    """
    issues = []
    score = 10  # Start at 10, deduct for violations

    lower = instruction.lower()

    # Rule 1: Action verb
    action_verbs = ["extract", "summarize", "classify", "identify", "list",
                    "generate", "write", "analyze", "compare", "translate",
                    "convert", "evaluate", "score", "rank", "explain"]
    if not any(v in lower for v in action_verbs):
        issues.append("⚠️  No clear action verb found. Use: extract, summarize, classify, etc.")
        score -= 2

    # Rule 2: Length constraint
    length_signals = ["sentence", "word", "bullet", "paragraph", "char",
                      "max", "minimum", "exactly", "at most", "no more"]
    if not any(s in lower for s in length_signals):
        issues.append("⚠️  No length constraint. Add: 'in exactly X sentences' or '≤ N words'")
        score -= 1

    # Rule 3: Output format
    format_signals = ["json", "csv", "markdown", "table", "bullet", "list",
                      "numbered", "format:", "output:"]
    if not any(s in lower for s in format_signals):
        issues.append("⚠️  No output format specified. Add: 'Return as JSON...' or 'Use a numbered list'")
        score -= 2

    # Rule 4: Audience
    audience_signals = ["audience", "for a", "assuming", "expert", "non-technical",
                        "beginner", "manager", "developer", "customer"]
    if not any(s in lower for s in audience_signals):
        issues.append("ℹ️  No audience specified. Consider: 'for a [role] with [background]'")
        score -= 1

    # Rule 5: Vague terms
    vague_terms = [" analyze ", " think about ", " consider ", " look at ",
                   " understand ", " good ", " nice "]
    found_vague = [v.strip() for v in vague_terms if v in f" {lower} "]
    if found_vague:
        issues.append(f"⚠️  Vague terms found: {found_vague}. Replace with specific action verbs.")
        score -= 1

    # Rule 6: Edge cases
    edge_signals = ["if ", "when ", "unless ", "null", "none", "missing",
                    "not found", "empty", "error", "edge"]
    if not any(s in lower for s in edge_signals):
        issues.append("ℹ️  No edge cases covered. What should happen if input is empty or ambiguous?")
        score -= 1

    score = max(0, score)

    return {
        "score": score,
        "grade": "A" if score >= 9 else "B" if score >= 7 else "C" if score >= 5 else "D",
        "issues": issues,
        "character_count": len(instruction),
        "word_count": len(instruction.split()),
    }


def demo_instruction_audit() -> None:
    """Demonstrate the instruction audit tool on real examples."""

    instructions = [
        {
            "label": "Vague (production anti-pattern)",
            "text": "Analyze this customer feedback and tell me what's important.",
        },
        {
            "label": "Improved version",
            "text": (
                "Extract the top 3 most critical product issues from the customer "
                "feedback below. For each, output: {issue: str, frequency_mentioned: int, "
                "impact: HIGH|MEDIUM|LOW}. If fewer than 3 issues are mentioned, return only "
                "those found with frequency=1. Return valid JSON only."
            ),
        },
        {
            "label": "Gold standard (all rules satisfied)",
            "text": (
                "You are reviewing a SaaS product's customer feedback for a product manager.\n"
                "Task: Extract actionable product improvements.\n"
                "1. Identify all distinct product complaints mentioned\n"
                "2. Group similar complaints into themes\n"
                "3. Score each theme: frequency (1-10) × severity (1-10) = priority_score\n"
                "4. Return the top 5 themes ranked by priority_score as a JSON array: "
                "[{theme, complaints_count, priority_score, example_quote, "
                "suggested_action}]\n"
                "Edge cases: if fewer than 5 themes exist, return all. "
                "If the text has no complaints, return []."
            ),
        },
    ]

    print("\n" + "═" * 72)
    print("  INSTRUCTION AUDIT TOOL")
    print("  Scoring instructions across 10 quality dimensions")
    print("═" * 72)

    for inst in instructions:
        report = audit_instruction(inst["text"])
        print(f"\n  📋 Instruction: {inst['label']}")
        print(f"  Preview: {inst['text'][:80]}...")
        print(f"  Score: {report['score']}/10  Grade: {report['grade']}")
        print(f"  Length: {report['word_count']} words")
        if report["issues"]:
            for issue in report["issues"]:
                print(f"    {issue}")
        else:
            print("    ✅ No issues found — instruction is clear and complete!")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Instruction Tuning Examples and Audit Tool")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--audit", type=str, help="Audit a specific instruction string")
    args = parser.parse_args()

    # If --audit flag provided, just audit that instruction
    if args.audit:
        report = audit_instruction(args.audit)
        print(f"\nInstruction Audit Results:")
        print(f"  Score: {report['score']}/10  Grade: {report['grade']}")
        for issue in report["issues"]:
            print(f"  {issue}")
        return

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 02 — Instruction Tuning (Clear, Specific Instructions)")
    print("═" * 72)

    print_all_rules()
    demo_instruction_improvements(client)
    demo_instruction_audit()

    print("\n✅ Instruction tuning complete.")
    print("   Next: 06_output_formatting.py — control JSON, CSV, Markdown output\n")


if __name__ == "__main__":
    main()
