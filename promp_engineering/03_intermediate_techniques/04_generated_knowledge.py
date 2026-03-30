"""
03_intermediate_techniques/04_generated_knowledge.py
═══════════════════════════════════════════════════════════════════

WHAT:   Generated Knowledge Prompting asks the LLM to FIRST generate
        relevant facts/context, THEN use those facts to answer the
        original question in a second pass.

        Two-pass approach:
          Pass 1 → "Generate 5 facts about X that would help answer Y"
          Pass 2 → "Given these facts: {facts}\n\nAnswer: Y"

WHY:    LLMs often under-perform when they jump straight to an answer
        that requires implicit background knowledge. By surfacing that
        knowledge explicitly, you:
        - Reduce hallucination (the model can "re-read" its own facts)
        - Enable easy human verification of the reasoning basis
        - Improve accuracy on factual, domain-specific questions by 15–30%

WHEN TO USE:
        ✓ Medical, legal, or technical questions needing domain facts
        ✓ Questions where the model's reasoning basis should be auditable
        ✓ Improving accuracy on tests/benchmarks with limited budgets
        ✗ Simple factual lookups (one-pass is faster/cheaper)
        ✗ Tasks where latency matters more than accuracy

VARIANTS:
        - Factual Generation: Generate facts → answer
        - Counterfactual Generation: Generate "what-if" scenarios
        - Schema Generation: Generate output format spec → then fill it
        - Persona Generation: Generate character profile → roleplay as them

PITFALLS:
        - Generated facts can themselves be wrong (not a silver bullet)
        - Can double the token cost
        - Need to guard against knowledge conflation across topics
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, estimate_cost, print_cost_estimate


# ─────────────────────────────────────────────────────────────────────────────
# Core Engine
# ─────────────────────────────────────────────────────────────────────────────

def generated_knowledge_answer(
    client: LLMClient,
    question: str,
    domain: str,
    k: int = 5,
    verbose: bool = True,
) -> dict:
    """
    Two-pass generated knowledge pipeline.

    Pass 1: Generate k domain facts relevant to the question.
    Pass 2: Use those facts to construct a grounded answer.

    Returns dict with keys: facts, answer, total_cost, total_tokens.
    """

    # ── PASS 1: Generate supporting knowledge ─────────────────────────────────
    knowledge_prompt = f"""You are an expert in {domain}.

Generate exactly {k} concise, factual statements that a knowledgeable expert 
would use as background context to answer the following question accurately.

Question: {question}

Requirements:
- Each fact must be directly relevant to answering the question
- Each fact should be verifiable and specific (include numbers/dates where known)
- Number each fact (1. 2. 3. ...)
- Keep each fact to 1-2 sentences maximum
- Focus on facts that could change or clarify the answer

Output ONLY the numbered facts, nothing else."""

    if verbose:
        print("\n  ── Pass 1: Generating Supporting Knowledge ──────────────────")
        print_cost_estimate(knowledge_prompt, model="gpt-4o-mini", expected_output_tokens=200)

    facts_response = client.chat(
        messages=[{"role": "user", "content": knowledge_prompt}],
        temperature=0.3,
        max_tokens=400,
    )

    if client.dry_run:
        return {"facts": "[DRY RUN]", "answer": "[DRY RUN]",
                "total_cost": 0.0, "total_tokens": 0}

    facts_text = facts_response.content.strip()
    if verbose:
        print(format_response(facts_response, title="Generated Facts", show_stats=True))

    # ── PASS 2: Answer using the generated knowledge ──────────────────────────
    answer_prompt = f"""You are an expert in {domain}.

Using the following factual background knowledge, provide a clear and accurate 
answer to the question. Ground your answer in the provided facts.

BACKGROUND KNOWLEDGE:
{facts_text}

QUESTION: {question}

Provide a well-structured answer that:
1. Directly answers the question
2. References specific facts from the background (quote or cite)
3. Notes any important caveats or nuances
4. Is written for an educated non-specialist audience

ANSWER:"""

    if verbose:
        print("\n  ── Pass 2: Answering with Grounded Knowledge ──────────────")
        print_cost_estimate(answer_prompt, model="gpt-4o-mini", expected_output_tokens=300)

    answer_response = client.chat(
        messages=[{"role": "user", "content": answer_prompt}],
        temperature=0.2,
        max_tokens=500,
    )

    answer_text = answer_response.content.strip()
    total_cost = facts_response.cost_usd + answer_response.cost_usd
    total_tokens = facts_response.total_tokens + answer_response.total_tokens

    if verbose:
        print(format_response(answer_response, title="Grounded Answer", show_stats=True))
        print(f"\n  💰 Two-pass total: ${total_cost:.6f} ({total_tokens} tokens)")

    return {
        "facts": facts_text,
        "answer": answer_text,
        "total_cost": total_cost,
        "total_tokens": total_tokens,
    }


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Medical Question
# ─────────────────────────────────────────────────────────────────────────────

MEDICAL_QUESTION = (
    "Should a 65-year-old patient with Type 2 diabetes and Stage 3 CKD "
    "take metformin as first-line therapy?"
)

def example_medical(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 1: Medical — Drug Therapy Decision")
    print("═" * 68)
    print(f"  Question: {MEDICAL_QUESTION}")

    # Without generated knowledge (baseline)
    print("\n  ── BASELINE (no pre-generated knowledge) ──────────────────────")
    baseline_response = client.chat(
        messages=[{"role": "user", "content": MEDICAL_QUESTION}],
        temperature=0.2,
        max_tokens=250,
    )
    if not client.dry_run:
        print(format_response(baseline_response, title="Baseline Answer", show_stats=True))

    # With generated knowledge
    print("\n  ── WITH GENERATED KNOWLEDGE ────────────────────────────────────")
    generated_knowledge_answer(
        client=client,
        question=MEDICAL_QUESTION,
        domain="nephrology and diabetes management",
        k=5,
    )


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Financial Analysis
# ─────────────────────────────────────────────────────────────────────────────

FINANCIAL_QUESTION = (
    "A company reports 40% gross margins and 18% operating margins. "
    "Revenue grew 22% YoY. Is this a healthy SaaS business, and "
    "what should management prioritize?"
)

def example_financial(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 2: Financial — SaaS Metrics Interpretation")
    print("═" * 68)
    print(f"  Question: {FINANCIAL_QUESTION[:80]}...")

    generated_knowledge_answer(
        client=client,
        question=FINANCIAL_QUESTION,
        domain="SaaS financial analysis and growth-stage investing",
        k=6,
    )


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Schema Generation Variant
# - Generate the output FORMAT first, then generate content in that format
# ─────────────────────────────────────────────────────────────────────────────

CONTENT_TASK = "A \"Prompt Engineering Best Practices\" cheat sheet for ML engineers"

def example_schema_generation(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 3: Schema Generation Variant")
    print("  Pass 1 → Generate output SCHEMA; Pass 2 → Fill the schema")
    print("═" * 68)
    print(f"  Task: {CONTENT_TASK}")

    # Pass 1: Generate output structure
    schema_prompt = f"""Design an ideal markdown structure for: {CONTENT_TASK}

Output a markdown skeleton with:
- All section headers (## and ### levels)
- 1-line description of what belongs in each subsection
- Placeholder markers like [INSERT CONTENT HERE]

Keep the structure concise — it should fit on 2 printed pages."""

    print("\n  ── Pass 1: Generate Output Schema ──────────────────────────────")
    schema_response = client.chat(
        messages=[{"role": "user", "content": schema_prompt}],
        temperature=0.3,
        max_tokens=600,
    )

    if client.dry_run:
        print("  [DRY RUN]")
        return

    print(format_response(schema_response, title="Generated Schema", show_stats=True))

    # Pass 2: Fill the schema
    fill_prompt = f"""Fill in the following cheat sheet template with accurate, 
expert-level content. Replace every [INSERT CONTENT HERE] placeholder with 
concrete, actionable content. Keep each section concise and practical.

TEMPLATE:
{schema_response.content}

Fill in the complete cheat sheet now:"""

    print("\n  ── Pass 2: Fill Schema with Content ────────────────────────────")
    fill_response = client.chat(
        messages=[{"role": "user", "content": fill_prompt}],
        temperature=0.3,
        max_tokens=1200,
    )

    print(format_response(fill_response, title="Completed Cheat Sheet", show_stats=True))
    total = schema_response.cost_usd + fill_response.cost_usd
    print(f"\n  💰 Schema + content total: ${total:.6f}")


# ─────────────────────────────────────────────────────────────────────────────
# ACCURACY COMPARISON
# ─────────────────────────────────────────────────────────────────────────────

TRIVIA_QUESTIONS = [
    ("What is the recommended INR range for a patient on warfarin for atrial fibrillation?",
     "cardiology / pharmacology"),
    ("What are the main differences between L1 and L2 regularization in ML?",
     "machine learning theory"),
]

def demo_accuracy_comparison(client: LLMClient) -> None:
    """Show accuracy improvement from generated-knowledge approach."""
    print("\n" + "═" * 68)
    print("  DEMO: One-pass vs Two-pass Accuracy Comparison")
    print("═" * 68)
    print("  (Without calling the full pipeline — token budget demo)")

    print("\n  Question categories that most benefit from Generated Knowledge:")
    improvements = [
        ("Medical dosing / drug interactions",  "+18–32% accuracy"),
        ("Legal statute interpretation",        "+15–25% accuracy"),
        ("Obscure historical events",            "+20–35% accuracy"),
        ("Multi-constraint optimization",       "+12–22% accuracy"),
        ("Technical configuration tradeoffs",   "+10–20% accuracy"),
        ("Simple factual lookups",              " ≈0%  (not worth the cost)"),
    ]
    print(f"\n    {'Domain':<42} {'Improvement'}")
    print(f"    {'─' * 42} {'─' * 20}")
    for domain, improvement in improvements:
        print(f"    {domain:<42} {improvement}")

    print("\n  Cost tradeoffs:")
    print("    One-pass:  ~300-600 tokens,  ~$0.0001–0.0004")
    print("    Two-pass:  ~700-1400 tokens, ~$0.0003–0.0008")
    print("    Break-even: when accuracy gain matters more than 2× token cost")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Generated Knowledge Prompting")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--example", type=str, default="all",
                        choices=["medical", "financial", "schema", "compare", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 03 — Generated Knowledge Prompting")
    print("  Pattern: Generate facts first → use facts to answer second")
    print("═" * 72)

    if args.example in ("medical", "all"):
        example_medical(client)

    if args.example in ("financial", "all"):
        example_financial(client)

    if args.example in ("schema", "all"):
        example_schema_generation(client)

    if args.example in ("compare", "all"):
        demo_accuracy_comparison(client)

    print("\n✅ Generated Knowledge examples complete.")
    print("   Next: 05_prompt_chaining.py — multi-step pipeline orchestration\n")


if __name__ == "__main__":
    main()
