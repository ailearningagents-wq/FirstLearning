"""
09_capstone_projects/01_ai_email_assistant/main.py
═══════════════════════════════════════════════════════════════════

CAPSTONE PROJECT 1: AI Email Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Processes an inbox of emails, classifies each one, drafts a reply,
and extracts follow-up actions — producing a complete action plan.

Techniques used (from across the course):
  • Role prompting (Module 02)
  • Structured output with Pydantic validation + retry (Module 04)
  • Prompt chaining: classify → draft reply → extract actions (Module 03)
  • PII redaction before logging (Module 07)
  • Prompt versioning via PromptRegistry (Module 08)
  • Structured logging with PromptLogger (Module 06)

Architecture:
  ┌──────────────────────────────────────────┐
  │  Input: list of raw emails               │
  │  ↓                                       │
  │  Step 1: PII redaction (regex)           │
  │  ↓                                       │
  │  Step 2: Classification (JSON output)    │
  │  ↓                                       │
  │  Step 3: Reply drafting (if actionable)  │
  │  ↓                                       │
  │  Step 4: Action extraction (JSON array)  │
  │  ↓                                       │
  │  Output: EmailAction plan + cost summary │
  └──────────────────────────────────────────┘

Usage:
    python main.py
    python main.py --dry-run
    python main.py --dry-run --verbose
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens

from prompts import build_registry


# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RawEmail:
    id: str
    sender: str
    subject: str
    body: str


@dataclass
class EmailClassification:
    category: str = "other"
    urgency: str = "low"
    action_required: bool = False
    summary: str = ""


@dataclass
class EmailAction:
    action: str
    owner: str
    priority: str
    due_date: str


@dataclass
class ProcessedEmail:
    raw: RawEmail
    classification: EmailClassification
    reply_draft: str = ""
    actions: list[EmailAction] = field(default_factory=list)
    cost_usd: float = 0.0
    skipped: bool = False
    skip_reason: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# PII redaction (minimal inline version)
# ─────────────────────────────────────────────────────────────────────────────

_PII_PATTERNS = [
    (r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", "[EMAIL]"),
    (r"\b(?:\+1[\s\-]?)?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{4}\b", "[PHONE]"),
    (r"\b4\d{3}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "[CARD]"),
]

def redact_pii(text: str) -> str:
    for pattern, placeholder in _PII_PATTERNS:
        text = re.sub(pattern, placeholder, text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict | list:
    match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    # Try capturing outermost JSON object/array
    for pat in [r"\{.*\}", r"\[.*\]"]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            return json.loads(m.group())
    raise ValueError(f"No JSON in: {text[:200]}")


def _to_classification(raw: dict) -> EmailClassification:
    return EmailClassification(
        category=raw.get("category", "other"),
        urgency=raw.get("urgency", "low"),
        action_required=bool(raw.get("action_required", False)),
        summary=raw.get("summary", ""),
    )


def _to_actions(raw_list: list) -> list[EmailAction]:
    actions = []
    for item in raw_list:
        if isinstance(item, dict):
            actions.append(EmailAction(
                action=item.get("action", ""),
                owner=item.get("owner", "support"),
                priority=item.get("priority", "medium"),
                due_date=item.get("due_date", "this week"),
            ))
    return actions


# ─────────────────────────────────────────────────────────────────────────────
# Processing Pipeline
# ─────────────────────────────────────────────────────────────────────────────

def process_email(
    client: LLMClient,
    email: RawEmail,
    registry,
    verbose: bool = False,
) -> ProcessedEmail:
    total_cost = 0.0
    result = ProcessedEmail(raw=email, classification=EmailClassification())

    # ── Step 1: PII redact ──────────────────────────────────────────────────
    clean_body = redact_pii(email.body)
    clean_sender = redact_pii(email.sender)

    # ── Step 2: Classify ────────────────────────────────────────────────────
    classify_pv = registry.get_active("email_classify")
    classify_prompt = classify_pv.render(
        sender=clean_sender, subject=email.subject, body=clean_body
    )
    r_classify = client.chat(
        messages=[{"role": "user", "content": classify_prompt}],
        system=classify_pv.render_system(),
        temperature=0.0, max_tokens=120,
    )
    total_cost += r_classify.cost_usd

    if client.dry_run:
        # Simulate classification for dry-run
        sim_categories = ["billing", "technical_support", "spam", "partnership", "feature_request"]
        sim_urgencies  = ["critical", "high", "medium", "low"]
        result.classification = EmailClassification(
            category=sim_categories[hash(email.id) % len(sim_categories)],
            urgency=sim_urgencies[hash(email.subject) % len(sim_urgencies)],
            action_required=True,
            summary=f"[DRY-RUN] {email.subject[:60]}",
        )
    else:
        try:
            raw_cls = _parse_json(r_classify.content)
            result.classification = _to_classification(raw_cls)
        except (json.JSONDecodeError, ValueError) as e:
            result.classification.summary = f"Classification parse error: {e}"

    if verbose:
        print(f"    Classified: {result.classification.category} / {result.classification.urgency}")

    # ── Step 3: Skip spam / low priority without action ────────────────────
    if result.classification.category == "spam":
        result.skipped = True
        result.skip_reason = "spam — no reply needed"
        result.cost_usd = total_cost
        return result

    if not result.classification.action_required and result.classification.urgency == "low":
        result.skipped = True
        result.skip_reason = "no action required + low urgency"
        result.cost_usd = total_cost
        return result

    # ── Step 4: Draft reply ─────────────────────────────────────────────────
    reply_pv = registry.get_active("email_reply_draft")
    context_map = {
        "billing": "Check billing system for duplicate charges. Offer 1-click refund link.",
        "technical_support": "Check status page. Offer to escalate to engineering if P1.",
        "feature_request": "Log in feature tracker. Thank customer for feedback.",
        "partnership": "Forward to partnerships@cloudsync.example.com with brief summary.",
        "other": "Respond helpfully and offer to connect with the right team.",
    }
    context = context_map.get(result.classification.category, "Handle professionally.")
    reply_prompt = reply_pv.render(
        category=result.classification.category,
        sender=email.sender,
        subject=email.subject,
        body=clean_body,
        context=context,
    )
    r_reply = client.chat(
        messages=[{"role": "user", "content": reply_prompt}],
        system=reply_pv.render_system(),
        temperature=0.2, max_tokens=200,
    )
    total_cost += r_reply.cost_usd
    result.reply_draft = r_reply.content.strip() if not client.dry_run else \
                         f"[DRY-RUN] Dear Customer, Thank you for your {result.classification.category} inquiry. We will follow up shortly.\n\nBest regards, CloudSync Support Team"

    # ── Step 5: Extract actions ─────────────────────────────────────────────
    actions_pv = registry.get_active("email_actions")
    actions_prompt = actions_pv.render(
        category=result.classification.category,
        summary=result.classification.summary,
        reply=result.reply_draft[:300],
    )
    r_actions = client.chat(
        messages=[{"role": "user", "content": actions_prompt}],
        temperature=0.0, max_tokens=200,
    )
    total_cost += r_actions.cost_usd

    if client.dry_run:
        result.actions = [EmailAction(
            action=f"Follow up on {result.classification.category} issue",
            owner="support",
            priority=result.classification.urgency,
            due_date="24 hours",
        )]
    else:
        try:
            raw_actions = _parse_json(r_actions.content)
            if isinstance(raw_actions, list):
                result.actions = _to_actions(raw_actions)
        except (json.JSONDecodeError, ValueError):
            pass  # Actions are bonus; don't fail if parse fails

    result.cost_usd = total_cost
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Sample inbox
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_INBOX = [
    RawEmail(
        id="email-001",
        sender="sarah.johnson@acme-corp.com",
        subject="URGENT: Team locked out — client demo in 2 hours!",
        body="Hi, our entire team has been unable to log in since 8 AM. We have a critical client demo at 10 AM and need this fixed IMMEDIATELY. Account: acme-corp. Phone: 415-555-2891.",
    ),
    RawEmail(
        id="email-002",
        sender="billing@globaltech.io",
        subject="Double charge on our account",
        body="We noticed two charges of $299 on our credit card 4111-1111-1111-1111 on Nov 1st. Could you please investigate and refund one? Invoice IDs: INV-8821 and INV-8822.",
    ),
    RawEmail(
        id="email-003",
        sender="dev@startup.io",
        subject="Feature request: webhooks for file events",
        body="Love CloudSync! One thing that would make it perfect: real-time webhooks when files are created, modified, or deleted. We'd use this for our CI/CD pipeline. Happy to provide more details.",
    ),
    RawEmail(
        id="email-004",
        sender="noreply@spam-corp.xyz",
        subject="YOU HAVE WON $5,000,000 LOTTERY!!!",
        body="Congratulations!!! Click here to claim your prize immediately!!! WINNER WINNER CHICKEN DINNER",
    ),
    RawEmail(
        id="email-005",
        sender="partnerships@bigenterprise.com",
        subject="Partnership opportunity — 10,000 seat deal",
        body="Hi, I'm the VP of IT at Big Enterprise Inc. We're evaluating CloudSync for 10,000 seats. Would love to schedule a call with your enterprise team. We're serious buyers — looking to decide by end of quarter.",
    ),
]


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AI Email Assistant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    client   = LLMClient(dry_run=args.dry_run)
    registry = build_registry()

    print("\n" + "═" * 72)
    print("  CAPSTONE 1: AI EMAIL ASSISTANT")
    print(f"  Inbox: {len(SAMPLE_INBOX)} emails")
    print("═" * 72)

    processed: list[ProcessedEmail] = []
    for i, email in enumerate(SAMPLE_INBOX, 1):
        print(f"\n  ── Email {i}/{len(SAMPLE_INBOX)}: {email.subject[:50]}...")
        result = process_email(client, email, registry, verbose=args.verbose)
        processed.append(result)

        if result.skipped:
            print(f"  ⏭️  SKIPPED: {result.skip_reason}")
        else:
            cls = result.classification
            urgency_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            icon = urgency_icons.get(cls.urgency, "⚪")
            print(f"  {icon} [{cls.urgency.upper()}] {cls.category} | action: {cls.action_required}")
            print(f"  Summary: {cls.summary[:80]}")
            if result.reply_draft:
                print(f"  Reply draft (first 100 chars): {result.reply_draft[:100]}...")
            if result.actions:
                print(f"  Actions ({len(result.actions)}):")
                for a in result.actions:
                    print(f"    • [{a.priority}] {a.action} → {a.owner} by {a.due_date}")
        if not client.dry_run:
            print(f"  Cost: ${result.cost_usd:.5f}")

    # ── Summary ──────────────────────────────────────────────────────────────
    total_cost = sum(p.cost_usd for p in processed)
    actionable = [p for p in processed if not p.skipped]
    all_actions = [a for p in actionable for a in p.actions]
    critical   = [p for p in actionable if p.classification.urgency == "critical"]

    print("\n" + "═" * 72)
    print("  INBOX SUMMARY")
    print("═" * 72)
    print(f"  Emails processed: {len(processed)}")
    print(f"  Actionable:       {len(actionable)}")
    print(f"  Skipped:          {len(processed) - len(actionable)}")
    print(f"  Critical:         {len(critical)}")
    print(f"  Total actions:    {len(all_actions)}")
    if total_cost > 0:
        print(f"  Total cost:       ${total_cost:.5f}")
    print()

    if critical:
        print("  🔴 CRITICAL — Respond immediately:")
        for p in critical:
            print(f"     [{p.raw.id}] {p.raw.subject}")

    print("\n✅ Email Assistant complete.\n")


if __name__ == "__main__":
    main()
