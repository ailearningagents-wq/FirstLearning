"""
02_basic_techniques/01_zero_shot_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   Zero-shot prompting means asking the model to perform a task
        WITHOUT providing any examples. You rely entirely on the model's
        pre-trained knowledge and your instruction clarity.

WHY:    Zero-shot is the fastest, most token-efficient approach.
        Modern LLMs (GPT-4o, Claude 3) are excellent zero-shot learners
        for well-defined tasks like classification, summarization, and Q&A.

WHEN TO USE:
        ✓ The task is well-defined (clear instruction = clear output)
        ✓ The model has likely seen similar tasks in training
        ✓ Speed or token efficiency is a priority
        ✗ Avoid when: output format is unusual, domain is very specialized,
          or the model keeps getting the format wrong (→ use few-shot instead)

COMMON PITFALLS:
        - Giving vague instructions ("analyze this") → unpredictable output
        - Not specifying output format → model picks whatever it prefers
        - Expecting domain knowledge the model doesn't have
        - Confusing zero-shot capability with zero-shot RELIABILITY
          (a model may know how to do a task but do it inconsistently)
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_cost_estimate, print_prompt_box


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — Zero-Shot Text Classification
# ─────────────────────────────────────────────────────────────────────────────

def task_classification(client: LLMClient) -> None:
    """Classify customer product reviews into categories — no examples given."""

    reviews = [
        {
            "text": "The delivery took 3 weeks and the package was damaged when it arrived. Complete waste of money.",
            "expected": "NEGATIVE / Logistics",
        },
        {
            "text": "Setup was straightforward, and the feature set exceeds what I expected at this price point.",
            "expected": "POSITIVE / Product",
        },
        {
            "text": "Battery life is excellent but the app keeps crashing on iOS 17.",
            "expected": "MIXED / Technical",
        },
    ]

    system = "You are a product analytics specialist at an e-commerce company."

    # ❌ Bad zero-shot prompt — vague, no format
    BAD_PROMPT_TEMPLATE = "What do you think about this review?\n\n{review}"

    # ✅ Good zero-shot prompt — precise instruction, explicit output format
    GOOD_PROMPT_TEMPLATE = """Classify the following product review.

Categories: POSITIVE | NEGATIVE | NEUTRAL | MIXED
Topics: PRODUCT_QUALITY | SHIPPING | PRICING | SUPPORT | TECHNICAL | OTHER

Respond with valid JSON only:
{{
  "sentiment": "<POSITIVE|NEGATIVE|NEUTRAL|MIXED>",
  "primary_topic": "<topic>",
  "secondary_topics": ["<topic>", ...],
  "key_issues": ["<brief issue description>"],
  "would_recommend": true|false|null,
  "urgency": "HIGH|MEDIUM|LOW"
}}

Review:
```
{review}
```"""

    print("\n" + "═" * 72)
    print("  TASK 1: Zero-Shot Customer Review Classification")
    print("═" * 72)

    for i, review_data in enumerate(reviews, 1):
        review = review_data["text"]
        print(f"\n  Review {i}: {review[:60]}...")
        print(f"  Expected: {review_data['expected']}")

        # Show bad vs good on first example
        if i == 1:
            print_prompt_box(BAD_PROMPT_TEMPLATE.format(review=review), title="❌ Bad Zero-Shot Prompt")
            print_prompt_box(GOOD_PROMPT_TEMPLATE.format(review=review), title="✅ Good Zero-Shot Prompt")

        if not client.dry_run:
            prompt = GOOD_PROMPT_TEMPLATE.format(review=review)
            response = client.chat(
                user_message=prompt,
                system_message=system,
                temperature=0.1,   # Low temp for classification
                max_tokens=200,
            )
            format_response(response, title=f"Classification Result (Review {i})", show_stats=(i == 1))


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — Zero-Shot Question Answering (with context)
# ─────────────────────────────────────────────────────────────────────────────

def task_qa(client: LLMClient) -> None:
    """Answer questions about a policy document — closed-book QA."""

    policy_excerpt = """
    RETURN POLICY — Section 4.2
    
    All products purchased from GlobalShop may be returned within 30 days of 
    the delivery date, provided they are in their original, unopened condition 
    with all original packaging and accessories. Electronics have a 15-day 
    return window. Personalized items and downloadable software are 
    non-returnable. Refunds are processed within 5-7 business days to the 
    original payment method. Shipping costs for returns are the customer's 
    responsibility unless the return is due to a defective product or our error.
    """

    questions = [
        "Can I return an open laptop if I've had it for 10 days?",
        "Who pays for return shipping if my order arrived broken?",
        "How long does it take to get my money back after I return something?",
    ]

    # ✅ Structured QA prompt with grounding
    QA_PROMPT_TEMPLATE = """You are a customer service assistant. Answer the customer's 
question based ONLY on the provided policy. If the policy doesn't address 
the question, say "I don't have that information in our current policy."

Policy Document:
```
{policy}
```

Customer Question: {question}

Respond in this format:
Answer: <direct answer>
Policy Reference: <quote the relevant policy text, or "N/A">
Confidence: HIGH | MEDIUM | LOW"""

    print("\n" + "═" * 72)
    print("  TASK 2: Zero-Shot Grounded Question Answering")
    print("  (Model answers from the provided policy document — not its training data)")
    print("═" * 72)

    for q in questions:
        print(f"\n  ❓ Q: {q}")
        prompt = QA_PROMPT_TEMPLATE.format(policy=policy_excerpt.strip(), question=q)

        if not client.dry_run:
            response = client.chat(
                user_message=prompt,
                temperature=0.0,  # Factual extraction → deterministic
                max_tokens=150,
            )
            # Parse and display just the answer line
            lines = response.content.strip().split("\n")
            for line in lines:
                if line.startswith("Answer:") or line.startswith("Policy") or line.startswith("Confidence"):
                    print(f"     {line}")
        else:
            print(f"     [DRY RUN — would query policy document]")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — Zero-Shot Summarization (extractive vs. abstractive)
# ─────────────────────────────────────────────────────────────────────────────

def task_summarization(client: LLMClient) -> None:
    """
    Summarize a medical research abstract in two styles:
    1. Extractive: key sentences pulled directly from text
    2. Abstractive: rewritten for a lay audience
    """

    abstract = """
    Background: Type 2 diabetes mellitus (T2DM) affects approximately 537 million 
    adults worldwide. Lifestyle interventions remain the cornerstone of prevention, 
    however adherence rates are consistently below 40% at 12 months.
    
    Methods: We conducted a randomized controlled trial (n=1,247) comparing a 
    mobile-app-based coaching intervention (MCI) against standard care over 18 months.
    Primary endpoint: glycated hemoglobin (HbA1c) reduction. Secondary endpoints 
    included BMI change, step count adherence, and quality-of-life scores (SF-36).
    
    Results: The MCI arm showed a mean HbA1c reduction of 1.2% (95% CI: 0.9–1.5%, 
    p<0.001) versus 0.3% in the control arm. BMI decreased by 2.1 kg/m² in the MCI 
    group. App adherence was 67% at 18 months, significantly above historical benchmarks. 
    No serious adverse events were attributable to the intervention.
    
    Conclusions: Mobile-app-based coaching significantly outperforms standard care for 
    T2DM management, with clinically meaningful HbA1c reductions and high adherence. 
    Widespread adoption could reduce the global T2DM burden substantially.
    """

    # Two different zero-shot prompts for two different audiences
    EXTRACTIVE_PROMPT = f"""Extract the 3 most important sentences from the medical abstract below.
Output as a numbered list. Do not paraphrase — use exact sentences from the text.

Abstract:
```
{abstract.strip()}
```"""

    ABSTRACTIVE_PROMPT = f"""Summarize the following medical research abstract for a 
patient with no medical background. Use simple language, avoid all medical 
jargon, and aim for 3 sentences maximum.

Abstract:
```
{abstract.strip()}
```"""

    print("\n" + "═" * 72)
    print("  TASK 3: Zero-Shot Summarization — Extractive vs Abstractive")
    print("═" * 72)

    for prompt_type, prompt in [("Extractive (key sentences)", EXTRACTIVE_PROMPT),
                                  ("Abstractive (lay audience)", ABSTRACTIVE_PROMPT)]:
        print(f"\n  📄 {prompt_type}:")

        if not client.dry_run:
            response = client.chat(user_message=prompt, temperature=0.2, max_tokens=250)
            print(f"  {response.content.strip()}")
            print(f"  [Tokens: {response.total_tokens}, Cost: ${response.cost_usd:.6f}]")
        else:
            print(f"  [DRY RUN — type: {prompt_type}]")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Zero-Shot Prompting Examples")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run, temperature=0.1)

    print("\n" + "═" * 72)
    print("  MODULE 02 — Zero-Shot Prompting")
    print("  Technique: Ask the model without providing any examples")
    print("═" * 72)

    task_classification(client)
    task_qa(client)
    task_summarization(client)

    print("\n✅ Zero-shot examples complete.")
    print("   When zero-shot isn't reliable enough, add examples → see 02_one_shot_prompting.py\n")


if __name__ == "__main__":
    main()
