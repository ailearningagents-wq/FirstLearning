"""
04_advanced_techniques/04_constrained_generation.py
═══════════════════════════════════════════════════════════════════

WHAT:   Constrained Generation forces LLM outputs to conform to a strict
        schema, grammar, or set of rules — enabling reliable parsing and
        downstream processing without manual cleanup.

        Key Techniques:
        1. JSON Mode (OpenAI API `response_format={"type": "json_object"}`)
        2. Structured Outputs (OpenAI API with Pydantic schemas)
        3. Grammar-constrained decoding (llama.cpp, Outlines library)
        4. Prompt-based constraints with validation + retry loop
        5. Pydantic validation with regeneration on failure

WHY:    In production pipelines, receiving unstructured text that "looks like"
        JSON but has trailing commas, markdown fences, or wrong types will
        crash your system. Constrained generation gives you:
        ✓ Zero parsing failures (with proper validation loop)
        ✓ Type-safe results from the first call
        ✓ Consistent field names and structure
        ✓ Downstream code that doesn't need defensive try/except everywhere

WHEN TO USE:
        ✓ Any integration where LLM output feeds into a database or API
        ✓ Extraction tasks (always need consistent structure)
        ✓ Classification tasks (need canonical labels)
        ✗ Creative writing (no benefit)
        ✗ Exploratory analysis (structure might restrict insight)
"""

import sys
import os
import json
import argparse
from typing import Optional, Literal
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response

try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    print("  Note: pydantic not installed — schema validation demos skipped")


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS (Output Contracts)
# ─────────────────────────────────────────────────────────────────────────────

if PYDANTIC_AVAILABLE:
    class SentimentLabel(str, Enum):
        POSITIVE = "positive"
        NEGATIVE = "negative"
        NEUTRAL  = "neutral"
        MIXED    = "mixed"

    class ReviewAnalysis(BaseModel):
        sentiment: SentimentLabel
        rating_implied: int = Field(ge=1, le=5, description="1-5 star rating inferred from text")
        main_topic: str = Field(max_length=60)
        key_positives: list[str] = Field(max_length=5)
        key_negatives: list[str] = Field(max_length=5)
        would_recommend: bool
        confidence: float = Field(ge=0.0, le=1.0)

    class JobPosting(BaseModel):
        job_title: str
        company_name: str
        location: str
        remote_policy: Literal["remote", "hybrid", "onsite", "unclear"]
        salary_min_usd: Optional[int] = None
        salary_max_usd: Optional[int] = None
        required_years_experience: Optional[int] = None
        key_skills: list[str] = Field(max_length=10)
        seniority: Literal["junior", "mid", "senior", "staff", "lead", "unclear"]

    class IncidentReport(BaseModel):
        severity: Literal["P0", "P1", "P2", "P3"]
        affected_service: str
        root_cause_summary: str = Field(max_length=200)
        timeline_start_utc: str  # ISO format string
        resolution_steps: list[str]
        recurrence_prevention: str = Field(max_length=300)
        customer_impact_score: int = Field(ge=0, le=100, description="0=none, 100=complete outage")


# ─────────────────────────────────────────────────────────────────────────────
# Validation + Retry Engine
# ─────────────────────────────────────────────────────────────────────────────

def generate_validated(
    client: LLMClient,
    prompt: str,
    schema_class: type,
    max_retries: int = 3,
    verbose: bool = True,
) -> tuple[Optional[object], int]:
    """
    Generate structured output conforming to a Pydantic schema.
    Retries on validation failure, injecting the error message into the next attempt.

    Returns: (validated_instance, attempts_used)
    """
    schema_desc = json.dumps(schema_class.model_json_schema(), indent=2)

    base_prompt = f"""{prompt}

Output a JSON object that EXACTLY matches this schema:
{schema_desc}

CRITICAL: Output ONLY the JSON object — no markdown fences, no explanation.
Every field marked as required must be present."""

    for attempt in range(1, max_retries + 1):
        if verbose:
            print(f"\n  Attempt {attempt}/{max_retries}...")

        response = client.chat(
            messages=[{"role": "user", "content": base_prompt}],
            temperature=0.1,
            max_tokens=600,
        )

        if client.dry_run:
            return None, 1

        raw = response.content.strip()
        # Strip common wrapping
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.rstrip("`").strip()

        try:
            data = json.loads(raw)
            instance = schema_class(**data)
            if verbose:
                print(f"  ✅ Valid on attempt {attempt}")
            return instance, attempt
        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {e}"
            if verbose:
                print(f"  ❌ {error_msg} — retrying...")
            base_prompt += f"\n\nPrevious attempt failed: {error_msg}. Fix the JSON syntax."
        except Exception as e:
            error_msg = str(e)
            if verbose:
                print(f"  ❌ Validation error: {error_msg[:120]} — retrying...")
            base_prompt += f"\n\nPrevious attempt failed validation: {error_msg}. Fix the values."

    return None, max_retries


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLES
# ─────────────────────────────────────────────────────────────────────────────

REVIEW_TEXT = """
Just upgraded from the Basic to Pro plan for my team of 8. The onboarding was 
surprisingly smooth — the CSV import wizard handled our messy legacy data without 
a single error. Dashboard loading is maybe 2x slower than the old tool though, 
especially the reports tab. Support chat replied in under 5 minutes on a Sunday! 
Would absolutely recommend to any operations team, but IT might want to check 
the SSO docs before rolling out company-wide.
"""

JOB_POSTING_TEXT = """
Senior Platform Engineer at DataStream Inc.

We're a Series B startup building real-time analytics infrastructure. 
Join our team in San Francisco (2 days in office required) to help scale 
our Kafka+Flink pipelines to 10M events/sec.

Comp: $180,000–$230,000 + equity + benefits
Requirements: 5+ years backend engineering, strong Python/Go, Kafka, Kubernetes, 
experience with high-throughput streaming systems. A/B testing infrastructure a plus.
"""

INCIDENT_TEXT = """
At 14:32 UTC our primary Postgres cluster (prod-db-01) hit 100% CPU due to a 
runaway analytics query introduced in deploy v2.4.1 at 14:15 UTC. Read traffic 
degraded for 18 minutes until we killed the offending query at 14:50 UTC. 
Around 15,000 users experienced slow page loads > 10s. We added query timeout 
limits (30s max) and query-level EXPLAIN logging. Going forward, analytics 
queries will be routed to the read replica, and deploys will include a 
mandatory 5-minute query performance soak test.
"""


def example_review_extraction(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 1: Review Analysis — ReviewAnalysis Schema")
    print("═" * 68)

    if not PYDANTIC_AVAILABLE:
        print("  Skipped — pydantic not installed")
        return

    result, attempts = generate_validated(
        client=client,
        prompt=f"Analyze this customer review:\n\n{REVIEW_TEXT}",
        schema_class=ReviewAnalysis,
        verbose=True,
    )

    if result and not client.dry_run:
        print(f"\n  Extracted ReviewAnalysis:")
        print(f"  Sentiment:        {result.sentiment.value}")
        print(f"  Rating implied:   {result.rating_implied}/5")
        print(f"  Would recommend:  {result.would_recommend}")
        print(f"  Confidence:       {result.confidence:.0%}")
        print(f"  Positives:        {result.key_positives}")
        print(f"  Negatives:        {result.key_negatives}")


def example_job_extraction(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 2: Job Posting Extraction — JobPosting Schema")
    print("═" * 68)

    if not PYDANTIC_AVAILABLE:
        print("  Skipped — pydantic not installed")
        return

    result, attempts = generate_validated(
        client=client,
        prompt=f"Extract structured information from this job posting:\n\n{JOB_POSTING_TEXT}",
        schema_class=JobPosting,
        verbose=True,
    )

    if result and not client.dry_run:
        print(f"\n  Extracted JobPosting:")
        print(f"  Title:       {result.job_title}")
        print(f"  Company:     {result.company_name}")
        print(f"  Location:    {result.location}")
        print(f"  Remote:      {result.remote_policy}")
        print(f"  Salary:      ${result.salary_min_usd:,}–${result.salary_max_usd:,}")
        print(f"  Experience:  {result.required_years_experience}+ years")
        print(f"  Seniority:   {result.seniority}")
        print(f"  Skills:      {', '.join(result.key_skills[:5])}")


def example_incident_extraction(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 3: Incident Report — IncidentReport Schema")
    print("═" * 68)

    if not PYDANTIC_AVAILABLE:
        print("  Skipped — pydantic not installed")
        return

    result, attempts = generate_validated(
        client=client,
        prompt=f"Convert this incident description into a structured report:\n\n{INCIDENT_TEXT}",
        schema_class=IncidentReport,
        verbose=True,
    )

    if result and not client.dry_run:
        print(f"\n  Extracted IncidentReport:")
        print(f"  Severity:         {result.severity}")
        print(f"  Service:          {result.affected_service}")
        print(f"  Customer Impact:  {result.customer_impact_score}/100")
        print(f"  Root Cause:       {result.root_cause_summary[:100]}")
        print(f"  Resolution steps: {len(result.resolution_steps)} steps")


def demo_format_comparison(client: LLMClient) -> None:
    """Compare unstructured vs structured output for a classification task."""
    print("\n" + "═" * 68)
    print("  DEMO: Unstructured vs Constrained Output Comparison")
    print("═" * 68)

    text = "I love the product but the support team never responds. Three tickets open for 2 weeks!"

    # Unstructured
    bad_prompt = f"What is the sentiment of this review? Is it positive or negative? {text}"
    # Structured
    good_prompt = f"""Classify this review. Output ONLY JSON: 
{{"sentiment": "positive|negative|neutral|mixed", "confidence": 0.0-1.0, "issue_detected": true|false}}

Review: {text}"""

    if not client.dry_run:
        bad_response = client.chat(
            messages=[{"role": "user", "content": bad_prompt}],
            temperature=0.0, max_tokens=80
        )
        good_response = client.chat(
            messages=[{"role": "user", "content": good_prompt}],
            temperature=0.0, max_tokens=60
        )
        print(f"\n  ❌ Unstructured: {bad_response.content.strip()}")
        print(f"  ✅ Constrained:  {good_response.content.strip()}")
        print(f"\n  Parser would fail on unstructured output.")
        print(f"  json.loads() works cleanly on constrained output.")
    else:
        print("\n  [DRY RUN — would compare unstructured vs constrained outputs]")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Constrained Generation with Pydantic")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--example", type=str, default="all",
                        choices=["review", "job", "incident", "compare", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 04 — Constrained Generation")
    print("  Enforce strict output schemas via Pydantic + validation loops")
    print("═" * 72)

    if args.example in ("review", "all"):
        example_review_extraction(client)
    if args.example in ("job", "all"):
        example_job_extraction(client)
    if args.example in ("incident", "all"):
        example_incident_extraction(client)
    if args.example in ("compare", "all"):
        demo_format_comparison(client)

    print("\n✅ Constrained Generation examples complete.")
    print("   Next: 05_prompt_compression.py — reduce token cost\n")


if __name__ == "__main__":
    main()
