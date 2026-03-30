"""
02_basic_techniques/03_few_shot_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   Few-shot prompting provides 2–10 labeled examples (demonstrations)
        to teach the model a pattern, style, or domain-specific behavior
        directly within the prompt.

WHY:    Few-shot is one of the most powerful and underutilized techniques.
        It's essentially free fine-tuning — you get model behavior changes
        without touching weights or spending on training.

WHEN TO USE:
        ✓ The task has a specific output pattern hard to describe in words
        ✓ Domain-specific labels or terminology (medical codes, legal terms)
        ✓ Custom tone/style that differs from the model's default
        ✓ Classification with non-standard label set
        ✗ Very long examples → token cost grows quickly
        ✗ When examples have high variance (may confuse the model)

EXAMPLE SELECTION STRATEGY:
        1. Cover edge cases, not just the easy cases
        2. Balance example distribution across classes
        3. Order: hardest examples LAST (closest to the query)
        4. Use diverse examples — don't use near-duplicates

COMMON PITFALLS:
        - Too few examples for complex patterns (< 3 for nuanced tasks)
        - Imbalanced examples (e.g., 4 POSITIVE, 1 NEGATIVE → biased predictions)
        - Examples that contradict each other → model gets confused
        - Not separating examples clearly → model treats them as one input
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_prompt_box, count_tokens


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — Few-Shot Sentiment Analysis (finance domain)
# ─────────────────────────────────────────────────────────────────────────────

# Financial news sentiment is different from general sentiment:
# "The company missed earnings by 3%" = NEGATIVE in finance, neutral in general
FEW_SHOT_SENTIMENT_EXAMPLES = [
    {
        "text": "TechCorp beats Q3 EPS by $0.15, raises full-year guidance.",
        "label": "BULLISH",
        "reasoning": "Beat + raised guidance = strong positive signal.",
    },
    {
        "text": "Probe launched into accounting irregularities at GlobalBank.",
        "label": "BEARISH",
        "reasoning": "Regulatory risk and fraud allegations = strong negative.",
    },
    {
        "text": "RetailChain reports flat same-store sales, in-line with consensus.",
        "label": "NEUTRAL",
        "reasoning": "Met expectations, no surprise either direction.",
    },
    {
        "text": "FDA grants accelerated approval for BioPharm's cancer drug.",
        "label": "BULLISH",
        "reasoning": "Regulatory milestone = significant revenue opportunity.",
    },
    {
        "text": "UtilityGroup raises dividend by 4%, citing stable cash flows.",
        "label": "BULLISH",
        "reasoning": "Dividend increase signals confidence in earnings stability.",
    },
    {
        "text": "ManuCo announces 2,000 layoffs amid slowing demand in China.",
        "label": "BEARISH",
        "reasoning": "Demand weakness + cost cutting = business deterioration.",
    },
]

TEST_HEADLINES = [
    "AutoMaker recalls 340,000 vehicles over brake defect — shares down 6%.",
    "CloudCo IPO priced at top of range, 3x oversubscribed.",
    "Federal Reserve signals pause in rate hikes at upcoming meeting.",
]


def task_financial_sentiment(client: LLMClient) -> None:
    """Classify financial news headlines using few-shot domain-specific examples."""

    # Build the few-shot prompt
    examples_text = ""
    for ex in FEW_SHOT_SENTIMENT_EXAMPLES:
        examples_text += f'Text: "{ex["text"]}"\nLabel: {ex["label"]}\nReasoning: {ex["reasoning"]}\n\n'

    system = ("You are a quantitative analyst at a hedge fund. "
              "Classify financial news headlines by their likely market sentiment.")

    def make_prompt(headline: str) -> str:
        return f"""Classify financial news headlines as BULLISH, BEARISH, or NEUTRAL.
Output format: Label: <LABEL> | Reasoning: <one sentence>

{examples_text}Text: "{headline}"
Label:"""

    print("\n" + "═" * 72)
    print("  TASK 1: Few-Shot Financial Sentiment Analysis")
    print(f"  Examples provided: {len(FEW_SHOT_SENTIMENT_EXAMPLES)} | Labels: BULLISH, BEARISH, NEUTRAL")
    print("═" * 72)

    # Show the full few-shot prompt for the first test case
    sample_prompt = make_prompt(TEST_HEADLINES[0])
    print(f"\n  Token count for full few-shot prompt: {count_tokens(sample_prompt)}")

    if not client.dry_run:
        for headline in TEST_HEADLINES:
            print(f"\n  📰 Headline: {headline}")
            response = client.chat(
                user_message=make_prompt(headline),
                system_message=system,
                temperature=0.0,
                max_tokens=80,
            )
            print(f"  → {response.content.strip()}")
    else:
        print_prompt_box(sample_prompt[:500] + "...", title="✅ Few-Shot Sentiment Prompt")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — Few-Shot Named Entity Recognition (NER)
# ─────────────────────────────────────────────────────────────────────────────

# Medical NER: extract medications, dosages, diagnoses from clinical notes
NER_EXAMPLES = [
    {
        "note": "Patient started on Metformin 500mg twice daily for newly diagnosed T2DM.",
        "entities": [
            {"text": "Metformin",   "type": "MEDICATION"},
            {"text": "500mg",       "type": "DOSAGE"},
            {"text": "twice daily", "type": "FREQUENCY"},
            {"text": "T2DM",        "type": "DIAGNOSIS"},
        ],
    },
    {
        "note": "Prescribed Lisinopril 10mg once daily for hypertension. Avoid in renal failure.",
        "entities": [
            {"text": "Lisinopril",   "type": "MEDICATION"},
            {"text": "10mg",         "type": "DOSAGE"},
            {"text": "once daily",   "type": "FREQUENCY"},
            {"text": "hypertension", "type": "DIAGNOSIS"},
            {"text": "renal failure","type": "CONTRAINDICATION"},
        ],
    },
    {
        "note": "Pt has known allergy to Penicillin. Started on Azithromycin 250mg for 5 days for pneumonia.",
        "entities": [
            {"text": "Penicillin",  "type": "ALLERGY"},
            {"text": "Azithromycin","type": "MEDICATION"},
            {"text": "250mg",       "type": "DOSAGE"},
            {"text": "5 days",      "type": "DURATION"},
            {"text": "pneumonia",   "type": "DIAGNOSIS"},
        ],
    },
]

TEST_NOTE = (
    "76yo male with COPD exacerbation. Salbutamol 2.5mg nebulizer every 4 hours "
    "and Prednisolone 40mg once daily for 5 days. Known allergy to Ibuprofen. "
    "Requires spirometry follow-up in 2 weeks."
)


def format_ner_examples(examples: list[dict]) -> str:
    """Format NER examples for few-shot prompt."""
    out = []
    for ex in examples:
        entities_str = ", ".join(
            f'{{"text": "{e["text"]}", "type": "{e["type"]}"}}'
            for e in ex["entities"]
        )
        out.append(
            f'Clinical note: "{ex["note"]}"\n'
            f'Entities: [{entities_str}]'
        )
    return "\n\n".join(out)


def task_medical_ner(client: LLMClient) -> None:
    """Extract named medical entities using few-shot examples."""

    examples_text = format_ner_examples(NER_EXAMPLES)

    prompt = f"""Extract all named medical entities from clinical notes.
Entity types: MEDICATION, DOSAGE, FREQUENCY, DURATION, DIAGNOSIS, ALLERGY, CONTRAINDICATION, PROCEDURE
Return a JSON array of {{"text": "...", "type": "..."}} objects.

{examples_text}

Clinical note: "{TEST_NOTE}"
Entities:"""

    print("\n" + "═" * 72)
    print("  TASK 2: Few-Shot Medical Named Entity Recognition (NER)")
    print("  Use case: Clinical notes → structured EHR data")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(user_message=prompt, temperature=0.0, max_tokens=400)
        format_response(response, title="Medical NER Results")
    else:
        print_prompt_box(prompt[:500] + "...", title="Few-Shot Medical NER Prompt")
        print(f"\n  Token count: {count_tokens(prompt)}")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — Few-Shot Style Transfer (formal → casual email)
# ─────────────────────────────────────────────────────────────────────────────

STYLE_EXAMPLES = [
    {
        "formal": "I am writing to formally request an extension on the project deadline. The unforeseen circumstances surrounding the vendor delays have significantly impacted our timeline.",
        "casual": "Hey! Quick heads-up — we need a bit more time on the project. The vendor has been slow and it's thrown off our schedule.",
    },
    {
        "formal": "Please be advised that the scheduled maintenance window has been postponed to the following Tuesday at 02:00 UTC due to operational constraints.",
        "casual": "FYI — we're moving the maintenance to next Tuesday at 2am UTC. Had some scheduling conflicts.",
    },
    {
        "formal": "I would like to bring to your attention that the aforementioned proposal has been reviewed and evaluated by our team. We have identified several areas that require clarification.",
        "casual": "Looked through the proposal — there are a few things we'd like to clarify before moving forward.",
    },
]

TEST_FORMAL = (
    "This is to formally notify you that your account has been flagged for review "
    "pursuant to our security protocols. We kindly request that you verify your "
    "identity by submitting the requisite documentation at your earliest convenience."
)


def task_style_transfer(client: LLMClient) -> None:
    """Rewrite formal corporate language as casual Slack-style messages."""

    examples_text = ""
    for ex in STYLE_EXAMPLES:
        examples_text += f'Formal: "{ex["formal"]}"\nCasual: "{ex["casual"]}"\n\n'

    prompt = f"""Rewrite formal corporate emails as casual, friendly Slack messages.
Keep all key information. Match the casual tone in the examples.

{examples_text}Formal: "{TEST_FORMAL}"
Casual:"""

    print("\n" + "═" * 72)
    print("  TASK 3: Few-Shot Style Transfer (Formal → Casual)")
    print("  Use case: Internal communication tool that humanizes robotic templates")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(user_message=prompt, temperature=0.4, max_tokens=150)
        print(f"\n  Original (formal):\n  {TEST_FORMAL}")
        print(f"\n  Rewritten (casual):\n  {response.content.strip()}")
        print(f"\n  [Tokens: {response.total_tokens}, Cost: ${response.cost_usd:.6f}]")
    else:
        print_prompt_box(prompt, title="Few-Shot Style Transfer Prompt")


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS: Effect of example count on classification accuracy
# ─────────────────────────────────────────────────────────────────────────────

def analyze_example_count(client: LLMClient) -> None:
    """
    Demonstrate how adding more examples improves ambiguous classification.
    
    Task: Classify customer churn risk as HIGH, MEDIUM, or LOW.
    """

    all_examples = [
        ("Used app daily for 1 year, recently submitted 0 support tickets, renewed last month.", "LOW"),
        ("Logged in once in the last 30 days, downgraded from Pro to Free plan.", "HIGH"),
        ("Active user, opened 2 support tickets about billing this month.", "MEDIUM"),
        ("Canceled auto-renew but still active. Usage dropped 60% month-over-month.", "HIGH"),
        ("New customer (7 days), completed onboarding, invited 3 teammates.", "LOW"),
    ]

    ambiguous_case = "Customer contacted support about a missing feature, usage is steady, contract up for renewal next quarter."

    template = """Classify customer churn risk as HIGH, MEDIUM, or LOW.
{examples}
Customer behavior: "{case}"
Churn Risk:"""

    print("\n" + "═" * 72)
    print("  ANALYSIS: How Example Count Affects Ambiguous Classification")
    print("═" * 72)

    for n_examples in [0, 1, 3, 5]:
        examples_text = ""
        for behavior, label in all_examples[:n_examples]:
            examples_text += f'Customer behavior: "{behavior}"\nChurn Risk: {label}\n\n'

        prompt = template.format(examples=examples_text, case=ambiguous_case)
        tokens = count_tokens(prompt)

        print(f"\n  📊 {n_examples}-shot ({tokens} tokens):")

        if not client.dry_run and n_examples in (0, 5):  # Only API call for 0 and 5
            response = client.chat(user_message=prompt, temperature=0.0, max_tokens=20)
            print(f"     → {response.content.strip()}")
        else:
            print(f"     → [Would call API — {tokens} tokens]")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Few-Shot Prompting Examples")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 02 — Few-Shot Prompting")
    print("  Technique: Use 2–8 labeled examples to teach the model a pattern")
    print("═" * 72)

    task_financial_sentiment(client)
    task_medical_ner(client)
    task_style_transfer(client)
    analyze_example_count(client)

    print("\n✅ Few-shot examples complete.")
    print("   Next: 04_role_prompting.py — assign expert personas to the model\n")


if __name__ == "__main__":
    main()
