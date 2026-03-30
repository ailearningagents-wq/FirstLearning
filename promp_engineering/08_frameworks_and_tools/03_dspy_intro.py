"""
08_frameworks_and_tools/03_dspy_intro.py
═══════════════════════════════════════════════════════════════════

WHAT: Introduction to DSPy (Declarative Self-improving Python):
      1. Define typed Signatures (input/output fields with descriptions)
      2. Compose Modules (Predict, ChainOfThought, Retrieve)
      3. Compile with a Teleprompter optimizer (COPRO / Bootstrap)
      4. Compare compiled vs. uncompiled performance on a task

WHY:  DSPy replaces hand-written prompts with a programming model.
      The optimizer finds better prompts automatically — the same way
      a compiler optimizes code, without you writing assembly.

WHEN: Use DSPy when:
      - You have a labelled training set (even 10-50 examples)
      - You want automatic few-shot selection
      - You need reproducible, version-controlled prompt programs

PITFALLS:
  - DSPy compilation calls the LLM many times. Use a cheap model
    or evaluate offline.
  - Signatures need clear, specific descriptions to compile well.
  - DSPy is research-grade software; APIs change frequently.

Install: pip install dspy-ai

Usage:
    python 03_dspy_intro.py
    python 03_dspy_intro.py --dry-run
    python 03_dspy_intro.py --compile  # runs compilation (expensive)
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Training data for compilation
# ─────────────────────────────────────────────────────────────────────────────

TRAIN_DATA = [
    {"review": "Absolutely love this product! Fast shipping and great quality.", "sentiment": "positive"},
    {"review": "Terrible customer service. Waited 3 weeks and got the wrong item.", "sentiment": "negative"},
    {"review": "It's okay, nothing special. Works as described.", "sentiment": "neutral"},
    {"review": "Blown away by the quality! Will definitely buy again.", "sentiment": "positive"},
    {"review": "Product broke after one week. Very disappointed.", "sentiment": "negative"},
    {"review": "Average product, does what it says. Nothing to complain about.", "sentiment": "neutral"},
    {"review": "Best purchase I've made this year! Highly recommend.", "sentiment": "positive"},
    {"review": "Don't buy this. Total waste of money.", "sentiment": "negative"},
]

TEST_DATA = [
    {"review": "Works perfectly, very happy with my purchase!", "answer": "positive"},
    {"review": "Arrived broken and support won't help.", "answer": "negative"},
    {"review": "Pretty decent, meets my basic needs.", "answer": "neutral"},
    {"review": "Life-changing product, exceeded expectations!", "answer": "positive"},
]


# ─────────────────────────────────────────────────────────────────────────────
# DSPy Demo
# ─────────────────────────────────────────────────────────────────────────────

def demo_with_dspy(dry_run: bool, compile_flag: bool) -> None:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Configure DSPy LM
    lm = dspy.OpenAI(model=model_name, max_tokens=50, temperature=0.0)
    dspy.settings.configure(lm=lm)

    # ── 1. Define Signatures ─────────────────────────────────────────────────
    print("\n  ── 1. DSPy Signatures (typed I/O contracts)")

    class SentimentSignature(dspy.Signature):
        """Classify the sentiment of a product review."""
        review    = dspy.InputField(desc="The customer product review text")
        sentiment = dspy.OutputField(desc="Sentiment: exactly one of 'positive', 'negative', 'neutral'")

    class ExtractSignature(dspy.Signature):
        """Extract key information from a support ticket."""
        ticket  = dspy.InputField(desc="Customer support ticket text")
        issue   = dspy.OutputField(desc="The core issue in ≤ 10 words")
        urgency = dspy.OutputField(desc="Urgency level: low / medium / high")

    print("  SentimentSignature: review → sentiment")
    print("  ExtractSignature:   ticket → issue + urgency")

    # ── 2. Define Modules ────────────────────────────────────────────────────
    print("\n  ── 2. DSPy Modules (Predict + ChainOfThought)")

    class SimpleSentiment(dspy.Module):
        """One-step Predict module."""
        def __init__(self):
            super().__init__()
            self.predict = dspy.Predict(SentimentSignature)

        def forward(self, review: str) -> dspy.Prediction:
            return self.predict(review=review)

    class CoTSentiment(dspy.Module):
        """Chain-of-Thought module — generates reasoning before answer."""
        def __init__(self):
            super().__init__()
            self.cot = dspy.ChainOfThought(SentimentSignature)

        def forward(self, review: str) -> dspy.Prediction:
            return self.cot(review=review)

    class TicketExtractor(dspy.Module):
        def __init__(self):
            super().__init__()
            self.extract = dspy.Predict(ExtractSignature)

        def forward(self, ticket: str) -> dspy.Prediction:
            return self.extract(ticket=ticket)

    simple = SimpleSentiment()
    cot    = CoTSentiment()
    extractor = TicketExtractor()

    # ── 3. Run uncompiled modules ────────────────────────────────────────────
    print("\n  ── 3. Uncompiled Module Inference")
    if dry_run:
        print("  [DRY-RUN: showing module structure]")
        for d in TEST_DATA:
            print(f"  Review: {d['review'][:50]}... → [DRY-RUN: {d['answer']}]")
    else:
        correct = 0
        for d in TEST_DATA:
            pred = simple(review=d["review"])
            sentiment = pred.sentiment.lower().strip()
            ok = d["answer"] in sentiment
            if ok: correct += 1
            print(f"  {'✅' if ok else '❌'} {d['review'][:40]}... → {sentiment} (expected: {d['answer']})")
        print(f"  Accuracy: {correct}/{len(TEST_DATA)}")

    # ── 4. DSPy Evaluation metric ────────────────────────────────────────────
    print("\n  ── 4. Evaluation Metric for Compilation")

    def sentiment_metric(example, prediction, trace=None) -> bool:
        return example.answer.lower() in prediction.sentiment.lower()

    print("  Metric: exact match of expected sentiment in prediction")

    # ── 5. Compilation (optional — expensive) ────────────────────────────────
    if compile_flag and not dry_run:
        print("\n  ── 5. Compiling with BootstrapFewShot")
        print("  ⚠️  This calls the LLM many times to find optimal few-shot examples.")

        train_examples = [
            dspy.Example(review=d["review"], answer=d["sentiment"]).with_inputs("review")
            for d in TRAIN_DATA
        ]
        test_examples = [
            dspy.Example(review=d["review"], answer=d["answer"]).with_inputs("review")
            for d in TEST_DATA
        ]

        teleprompter = dspy.BootstrapFewShot(metric=sentiment_metric, max_bootstrapped_demos=3)
        compiled = teleprompter.compile(SimpleSentiment(), trainset=train_examples)

        print("  Evaluating compiled module:")
        correct_compiled = 0
        for ex in test_examples:
            pred = compiled(review=ex.review)
            ok = ex.answer.lower() in pred.sentiment.lower()
            if ok: correct_compiled += 1
            print(f"  {'✅' if ok else '❌'} {ex.review[:40]}... → {pred.sentiment}")
        print(f"  Compiled accuracy: {correct_compiled}/{len(test_examples)}")
    else:
        print("\n  ── 5. Compilation (skipped)")
        if not compile_flag:
            print("  Run with --compile to enable Bootstrap compilation (costly)")
        if dry_run:
            print("  Run without --dry-run to use real API calls")

    # ── 6. Multi-output extraction demo ─────────────────────────────────────
    print("\n  ── 6. Multi-output Extraction (TicketExtractor)")
    sample_ticket = ("My entire team can't access files since this morning. "
                     "We have a client demo in 2 hours. This is critical!")
    if dry_run:
        print(f"  Ticket: {sample_ticket[:60]}...")
        print("  [DRY-RUN: issue='team cannot access files', urgency='high']")
    else:
        pred = extractor(ticket=sample_ticket)
        print(f"  Ticket: {sample_ticket[:60]}...")
        print(f"  Issue:   {pred.issue}")
        print(f"  Urgency: {pred.urgency}")


# ─────────────────────────────────────────────────────────────────────────────
# Fallback demo
# ─────────────────────────────────────────────────────────────────────────────

def demo_without_dspy(client: LLMClient) -> None:
    print("\n  [DSPy not installed — showing concept walkthrough]\n")

    print("  DSPy vs Manual Prompting comparison:")
    print()
    print("  Manual:                              DSPy equivalent:")
    print("  ─────────────────────────────────    ────────────────────────────────────")
    print("  Write prompt string manually         class SentimentSig(dspy.Signature):")
    print("  Include examples by hand             dspy.InputField(desc=...)")
    print("  Static — breaks on model update      dspy.OutputField(desc=...)")
    print("  No automatic optimization            Teleprompter auto-selects examples")
    print()
    print("  Key insight: DSPy's compiler finds better prompts than hand-writing.")
    print()

    # Show the concept with our LLMClient
    print("  Simulating DSPy-style inference with LLMClient:")
    for item in TEST_DATA[:2]:
        r = client.chat(
            messages=[{"role": "user", "content": f"Classify sentiment (positive/negative/neutral): {item['review']}"}],
            temperature=0.0, max_tokens=10,
        )
        result = r.content.strip() if not client.dry_run else item["answer"]
        print(f"  Review: {item['review'][:50]}... → {result}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="DSPy Introduction")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--compile", action="store_true",
                        help="Run BootstrapFewShot compilation (calls LLM many times)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 08 — Frameworks: DSPy Introduction")
    print(f"  DSPy available: {DSPY_AVAILABLE}")
    print("══════════════════════════════════════════════════════════════════════")

    if DSPY_AVAILABLE:
        demo_with_dspy(dry_run=args.dry_run, compile_flag=args.compile)
    else:
        demo_without_dspy(client)
        print("\n  Install DSPy to run the full demos:")
        print("    pip install dspy-ai")

    print("\n  KEY CONCEPTS")
    print("  Signature    — typed I/O contract for a prompt step")
    print("  Predict      — simple one-step module")
    print("  ChainOfThought — adds reasoning field before answer")
    print("  Module       — composable program unit (like a nn.Module)")
    print("  Teleprompter — compiler that optimizes few-shot examples")
    print("  Metric       — function(example, prediction) → bool for training")

    print("\n✅ DSPy introduction complete.\n")


if __name__ == "__main__":
    main()
