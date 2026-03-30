"""
07_security_and_safety/03_pii_handling.py
═══════════════════════════════════════════════════════════════════

WHAT: Detect and redact Personally Identifiable Information (PII)
      from text before it is sent to an LLM, using:
        1. Regex-based detection (no dependencies — primary)
        2. Microsoft Presidio integration (optional — more accurate)

WHY:  Sending PII to third-party LLM APIs may violate GDPR, HIPAA,
      CCPA and your own privacy policy. Redact first, send the
      anonymized text, then optionally restore before responding.

WHEN: Any system where untrusted users can input free text that
      gets forwarded to an external AI API.

PITFALLS:
  - Regex recall is limited — it will miss unusual formats.
  - Presidio false positives can destroy non-PII text (e.g., "John" in
    "John Doe Building"). Tune recognizer thresholds.
  - Token restoration must use reversible maps, not hashes.
  - After redaction the LLM may produce "PERSON_1 complained…" — you
    must restore before showing to the original user.

Install Presidio (optional):
    pip install presidio-analyzer presidio-anonymizer
    python -m spacy download en_core_web_lg

Usage:
    python 03_pii_handling.py
    python 03_pii_handling.py --dry-run
"""

import sys
import os
import re
import argparse
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient

# Optional Presidio
try:
    from presidio_analyzer import AnalyzerEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# PII Type definitions
# ─────────────────────────────────────────────────────────────────────────────

PII_PATTERNS: list[tuple[str, str]] = [
    # (label, regex pattern)
    ("EMAIL",       r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
    ("PHONE_US",    r"\b(?:\+1[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b"),
    ("SSN",         r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    ("CREDIT_CARD", r"\b(?:4\d{3}|5[1-5]\d{2}|6(?:011|5\d{2})|3[47]\d{1,2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b"),
    ("IP_ADDRESS",  r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ("DATE_BIRTH",  r"\b(?:dob|date of birth|born)[:\s]+(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\w+ \d{1,2},?\s+\d{4})\b"),
    ("URL",         r"https?://[^\s<>\"]+"),
    ("ZIP_CODE",    r"\b\d{5}(?:[-\s]\d{4})?\b"),
    ("PASSPORT",    r"\b[A-Z]{1,2}\d{7,9}\b"),
    ("NAME_HINT",   r"\b(?:Mr\.|Mrs\.|Ms\.|Dr\.)\s[A-Z][a-z]+ [A-Z][a-z]+"),
]


@dataclass
class PIIEntity:
    label: str
    original: str
    start: int
    end: int
    placeholder: str = ""


@dataclass
class RedactionResult:
    original: str
    redacted: str
    entities: list[PIIEntity] = field(default_factory=list)
    restoration_map: dict[str, str] = field(default_factory=dict)


def redact_regex(text: str) -> RedactionResult:
    """Regex-based PII redaction with reversible placeholder map."""
    entities: list[PIIEntity] = []
    found_spans: list[tuple[int, int]] = []

    for label, pattern in PII_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start, end = match.start(), match.end()
            # Avoid overlapping with already-found spans
            if not any(s <= start < e or s < end <= e for s, e in found_spans):
                counter = sum(1 for e in entities if e.label == label)
                placeholder = f"[{label}_{counter + 1}]"
                entities.append(PIIEntity(label=label, original=match.group(),
                                          start=start, end=end, placeholder=placeholder))
                found_spans.append((start, end))

    # Sort by start position (descending) for safe in-place replacement
    entities.sort(key=lambda e: e.start, reverse=True)

    redacted = text
    restoration_map: dict[str, str] = {}
    for ent in entities:
        redacted = redacted[:ent.start] + ent.placeholder + redacted[ent.end:]
        restoration_map[ent.placeholder] = ent.original

    return RedactionResult(original=text, redacted=redacted,
                           entities=entities, restoration_map=restoration_map)


def restore_pii(text: str, restoration_map: dict[str, str]) -> str:
    """Replace placeholders with original values after LLM processing."""
    for placeholder, original in restoration_map.items():
        text = text.replace(placeholder, original)
    return text


def redact_presidio(text: str) -> RedactionResult:
    """Presidio-based PII redaction (more accurate, requires install)."""
    if not PRESIDIO_AVAILABLE:
        return redact_regex(text)

    analyzer  = AnalyzerEngine()
    anonymizer = AnonymizerEngine()

    results = analyzer.analyze(text=text, language="en")
    anonymized = anonymizer.anonymize(text=text, analyzer_results=results)

    entities = [
        PIIEntity(
            label=r.entity_type,
            original=text[r.start:r.end],
            start=r.start,
            end=r.end,
            placeholder=f"[{r.entity_type}_{i+1}]",
        )
        for i, r in enumerate(results)
    ]

    # Build restoration map (Presidio uses its own placeholders — we rebuild ours)
    restoration_map = {e.placeholder: e.original for e in entities}

    # Use our placeholder format in the final redacted text
    redacted = text
    for ent in sorted(entities, key=lambda e: e.start, reverse=True):
        redacted = redacted[:ent.start] + ent.placeholder + redacted[ent.end:]

    return RedactionResult(original=text, redacted=redacted,
                           entities=entities, restoration_map=restoration_map)


# ─────────────────────────────────────────────────────────────────────────────
# Anonymized LLM call pipeline
# ─────────────────────────────────────────────────────────────────────────────

def pii_safe_call(
    client: LLMClient,
    user_input: str,
    task: str = "Summarize the following support ticket in one sentence:",
    use_presidio: bool = False,
) -> tuple[str, RedactionResult, float]:
    """
    1. Redact PII from user input
    2. Call LLM with redacted text
    3. Restore PII in the response
    Returns: (final_response, redaction_result, cost_usd)
    """
    result = redact_presidio(user_input) if use_presidio else redact_regex(user_input)

    prompt = f"{task}\n\nTicket:\n{result.redacted}"
    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=100,
    )

    raw_response = response.content.strip() if not client.dry_run else \
                   f"[DRY-RUN] Summary of redacted ticket with {len(result.entities)} entities removed."

    # Restore PII in the response if it contains placeholders
    final_response = restore_pii(raw_response, result.restoration_map)

    return final_response, result, response.cost_usd


# ─────────────────────────────────────────────────────────────────────────────
# Test cases
# ─────────────────────────────────────────────────────────────────────────────

TEST_INPUTS = [
    "Hi, I'm Jane Smith (jane.smith@acme.com, 415-555-9012). My credit card 4111-1111-1111-1111 was charged twice. DOB: 03/15/1985.",
    "User IP 192.168.1.42 logged in and then export failed. My passport number is AB1234567.",
    "Please help Mr. John Williams (john@cloudcorp.io). He's getting sync errors since yesterday.",
    "Contact our engineer at https://internal.cloudsync.example.com/ticket/12345 for this issue.",
    "Normal ticket: I can't upload files larger than 500MB. Please help.",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="PII Detection and Redaction")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--presidio", action="store_true",
                        help="Use Presidio instead of regex (requires installation)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    backend = "Presidio" if (args.presidio and PRESIDIO_AVAILABLE) else "Regex"
    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 07 — Security: PII Handling")
    print(f"  Backend: {backend}")
    if args.presidio and not PRESIDIO_AVAILABLE:
        print("  ⚠️  Presidio not installed — falling back to regex")
    print("══════════════════════════════════════════════════════════════════════")

    total_cost = 0.0
    total_entities = 0

    for i, text in enumerate(TEST_INPUTS, 1):
        print(f"\n  ── Test {i}/{len(TEST_INPUTS)}")
        print(f"  Original:  {text}")

        final_response, redaction, cost = pii_safe_call(
            client, text, use_presidio=args.presidio
        )
        total_cost  += cost
        total_entities += len(redaction.entities)

        print(f"  Redacted:  {redaction.redacted}")
        if redaction.entities:
            print(f"  Entities:  {[f'{e.label}:{e.original[:20]}' for e in redaction.entities]}")
        else:
            print("  Entities:  (none detected)")
        print(f"  Response:  {final_response}")

    print("\n" + "─" * 72)
    print(f"  Total PII entities detected: {total_entities}")
    print(f"  Average per document: {total_entities / len(TEST_INPUTS):.1f}")
    if total_cost > 0:
        print(f"  Total cost: ${total_cost:.5f}")
    print("─" * 72)

    print("\n  PATTERN COVERAGE (regex backend)")
    for label, pattern in PII_PATTERNS:
        print(f"  {label:<14}  {pattern[:50]}...")

    print("\n✅ PII handling complete.\n")


if __name__ == "__main__":
    main()
