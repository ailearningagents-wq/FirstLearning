"""
08_frameworks_and_tools/04_guardrails_ai.py
═══════════════════════════════════════════════════════════════════

WHAT: Guardrails AI patterns for validating and repairing LLM outputs:
      1. Structural validation (JSON schema conformance)
      2. Value validators (length, content, format)
      3. Retry-on-fail with error message injection
      4. Custom validators (Python functions)

WHY:  LLMs sometimes ignore format instructions. Guardrails AI wraps
      each LLM call with automatic retries and structured parsing
      so your downstream code always receives valid data.

WHEN: Production systems that need reliable structured output —
      data extraction pipelines, form processing, entity recognition.

PITFALLS:
  - Each retry is an extra LLM call — set max_reasks carefully.
  - Guardrails can increase latency significantly on bad prompts.
  - For simple JSON extraction, Pydantic retry (Module 04) is often
    sufficient and lighter-weight.
  - Guardrails Hub validators require an account.

Install: pip install guardrails-ai

Usage:
    python 04_guardrails_ai.py
    python 04_guardrails_ai.py --dry-run
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient

try:
    import guardrails as gd
    from guardrails.validators import ValidLength, ValidChoices, PassthroughFail
    GUARDRAILS_AVAILABLE = True
    GUARDRAILS_VERSION = gd.__version__
except ImportError:
    GUARDRAILS_AVAILABLE = False
    GUARDRAILS_VERSION = "not installed"

try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic-based validation with retry (works without Guardrails AI)
# ─────────────────────────────────────────────────────────────────────────────

if PYDANTIC_AVAILABLE:
    class ProductReview(BaseModel):
        product_name: str = Field(..., min_length=2, max_length=100)
        sentiment: str = Field(..., description="Must be: positive, negative, or neutral")
        rating: int = Field(..., ge=1, le=5)
        summary: str = Field(..., min_length=10, max_length=200)
        pros: list[str] = Field(default_factory=list, max_length=5)
        cons: list[str] = Field(default_factory=list, max_length=5)

        @field_validator("sentiment")
        @classmethod
        def validate_sentiment(cls, v: str) -> str:
            allowed = {"positive", "negative", "neutral"}
            if v.lower() not in allowed:
                raise ValueError(f"sentiment must be one of {allowed}, got '{v}'")
            return v.lower()

        @field_validator("rating")
        @classmethod
        def validate_rating(cls, v: int) -> int:
            if not 1 <= v <= 5:
                raise ValueError(f"rating must be 1-5, got {v}")
            return v


def _extract_json(text: str) -> dict:
    """Extract JSON from response that may include markdown code fences."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON found in: {text[:200]}")


def extract_with_pydantic_retry(
    client: LLMClient,
    review_text: str,
    max_retries: int = 3,
) -> tuple[dict | None, int, float]:
    """
    Extract structured review data, retrying with error messages on failure.
    Returns: (result_dict, attempts_used, total_cost)
    """
    if not PYDANTIC_AVAILABLE:
        return None, 0, 0.0

    schema_str = json.dumps({
        "product_name": "string (2-100 chars)",
        "sentiment": "positive | negative | neutral",
        "rating": "integer 1-5",
        "summary": "string (10-200 chars)",
        "pros": ["list of up to 5 strings"],
        "cons": ["list of up to 5 strings"],
    }, indent=2)

    prompt = (
        f"Extract product review information. Return ONLY valid JSON matching this schema:\n"
        f"{schema_str}\n\n"
        f"Review: {review_text}"
    )
    total_cost = 0.0
    error_context = ""

    for attempt in range(1, max_retries + 1):
        full_prompt = prompt
        if error_context:
            full_prompt += f"\n\nPrevious attempt failed with: {error_context}\nPlease fix and return valid JSON."

        response = client.chat(
            messages=[{"role": "user", "content": full_prompt}],
            temperature=0.0,
            max_tokens=300,
        )
        total_cost += response.cost_usd

        if client.dry_run:
            return {
                "product_name": "DRY-RUN Product",
                "sentiment": "positive",
                "rating": 4,
                "summary": "Dry run summary of the product review.",
                "pros": ["pro1"],
                "cons": ["con1"],
            }, 1, 0.0

        try:
            raw = _extract_json(response.content)
            validated = ProductReview(**raw)
            return validated.model_dump(), attempt, total_cost
        except Exception as e:
            error_context = str(e)[:200]

    return None, max_retries, total_cost


# ─────────────────────────────────────────────────────────────────────────────
# Guardrails AI demo (when installed)
# ─────────────────────────────────────────────────────────────────────────────

GUARDRAILS_RAIL = """
<rail version="0.1">
  <output>
    <string name="product_name" description="Product name" validators="length: 2 100" on-fail-length="fix"/>
    <string name="sentiment" description="Sentiment: positive, negative, or neutral"
            validators="valid-choices: {['positive','negative','neutral']}" on-fail-valid-choices="reask"/>
    <integer name="rating" description="Rating from 1 to 5"
             validators="valid-range: 1 5" on-fail-valid-range="reask"/>
    <string name="summary" description="Short summary (10-200 chars)"
            validators="length: 10 200" on-fail-length="reask"/>
  </output>
</rail>
"""


def demo_guardrails(client: LLMClient, review_text: str) -> dict | None:
    """Demonstrate Guardrails AI validation (requires installation)."""
    if not GUARDRAILS_AVAILABLE:
        return None

    try:
        guard = gd.Guard.from_rail_string(GUARDRAILS_RAIL)
        result = guard(
            llm_api=client.chat,
            prompt=(
                "Extract: product_name, sentiment (positive/negative/neutral), "
                f"rating (1-5 int), summary from:\n\n{review_text}"
            ),
            max_reasks=2,
        )
        return result.validated_output
    except Exception as e:
        print(f"  Guardrails error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Test reviews
# ─────────────────────────────────────────────────────────────────────────────

TEST_REVIEWS = [
    {
        "text": "The CloudSync Pro desktop app is outstanding! It syncs instantly, the UI is clean, "
                "and it's never lost a file. My only complaint is the mobile app is slightly sluggish. "
                "Overall 5 stars.",
        "expected_sentiment": "positive",
    },
    {
        "text": "Terrible experience. The app crashed three times during my first week, "
                "deleted an important folder, and support took 5 days to respond with a useless reply. "
                "1 star. Never again.",
        "expected_sentiment": "negative",
    },
    {
        "text": "It does what it says on the tin. Sync is reliable, pricing is a bit steep "
                "compared to competitors, but the enterprise features are solid. 3 stars.",
        "expected_sentiment": "neutral",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Guardrails AI Patterns")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 08 — Frameworks: Guardrails AI")
    print(f"  Guardrails AI: {GUARDRAILS_VERSION}")
    print(f"  Pydantic available: {PYDANTIC_AVAILABLE}")
    print("══════════════════════════════════════════════════════════════════════")

    # ── Pattern 1: Pydantic retry (primary — no extra install) ──────────────
    print("\n  ── Pattern 1: Pydantic Validation with Retry (no extra install)")
    total_cost = 0.0
    for i, review in enumerate(TEST_REVIEWS, 1):
        result, attempts, cost = extract_with_pydantic_retry(client, review["text"])
        total_cost += cost
        if result:
            print(f"\n  Review {i}: {review['text'][:60]}...")
            print(f"  Attempts: {attempts}")
            print(f"  sentiment: {result.get('sentiment')} (expected: {review['expected_sentiment']})")
            print(f"  rating:    {result.get('rating')}")
            print(f"  summary:   {result.get('summary', '')[:80]}...")
            ok = result.get("sentiment") == review["expected_sentiment"]
            print(f"  {'✅' if ok else '⚠️ '} Sentiment match")
        else:
            print(f"  ❌ Review {i}: Extraction failed after max retries")

    # ── Pattern 2: Guardrails AI (optional) ─────────────────────────────────
    print("\n  ── Pattern 2: Guardrails AI Rail Spec")
    if GUARDRAILS_AVAILABLE:
        for review in TEST_REVIEWS[:1]:
            result = demo_guardrails(client, review["text"])
            if result:
                print(f"  Guardrails output: {result}")
    else:
        print("  Guardrails AI not installed — showing RAIL spec concept only")
        print("  Install: pip install guardrails-ai")
        print()
        print("  RAIL spec example (XML-based validation rules):")
        for line in GUARDRAILS_RAIL.strip().split("\n")[:10]:
            print(f"  {line}")

    if total_cost > 0:
        print(f"\n  Total cost: ${total_cost:.5f}")

    print("\n  KEY PATTERNS")
    print("  Pydantic + retry  — validate structured JSON, inject errors, retry")
    print("  RAIL spec         — XML schema with validators + on-fail actions")
    print("  on-fail-reask     — re-prompt the LLM with the validation error")
    print("  on-fail-fix       — auto-fix the value without re-prompting")
    print("  on-fail-filter    — remove the field if validation fails")
    print("  Custom validators — register Python functions as gd validators")

    print("\n✅ Guardrails AI complete.\n")


if __name__ == "__main__":
    main()
