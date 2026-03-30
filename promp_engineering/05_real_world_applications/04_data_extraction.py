"""
05_real_world_applications/04_data_extraction.py
═══════════════════════════════════════════════════════════════════

Structured data extraction from unstructured documents using:
- Constrained generation with Pydantic schemas
- Retry logic on validation failure
- Multiple document types: invoices, contracts, meeting notes, emails
- Batch processing with cost tracking
"""

import sys
import os
import json
import argparse
from typing import Optional
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, estimate_cost

try:
    from pydantic import BaseModel, Field, field_validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

if PYDANTIC_AVAILABLE:
    class LineItem(BaseModel):
        description: str
        quantity: float
        unit_price: float
        total: float

    class Invoice(BaseModel):
        invoice_number: str
        vendor_name: str
        vendor_email: Optional[str] = None
        bill_to_company: str
        issue_date: str
        due_date: str
        line_items: list[LineItem]
        subtotal: float
        tax_rate_percent: Optional[float] = None
        tax_amount: Optional[float] = None
        total_amount: float
        payment_terms: str
        currency: str = "USD"

    class MeetingNotes(BaseModel):
        meeting_title: str
        date: str
        attendees: list[str]
        decisions: list[str]
        action_items: list[dict]  # [{"owner": str, "task": str, "due": str}]
        next_meeting: Optional[str] = None
        key_metrics_mentioned: list[str]


# ─────────────────────────────────────────────────────────────────────────────
# Sample Documents
# ─────────────────────────────────────────────────────────────────────────────

INVOICE_TEXT = """
INVOICE

TechServices Plus LLC
123 Cloud Street, Austin TX 78701
billing@techservicesplus.example.com

Bill To:
Acme Corporation
Jane Smith, Finance Director
456 Main Ave, New York NY 10001

Invoice #: INV-2024-0847
Invoice Date: December 15, 2024
Due Date: January 14, 2025
Payment Terms: Net 30

SERVICES RENDERED:
---------------------------------------------------------------------
API Integration Consulting     8 hours @ $185.00/hr      $1,480.00
Platform Migration Support     12 hours @ $185.00/hr     $2,220.00
Custom Webhook Development     1 unit @ $950.00           $950.00
Monthly Maintenance (Dec)      1 month @ $400.00          $400.00
---------------------------------------------------------------------
                                           Subtotal:    $5,050.00
                                           Tax (8.5%):  $429.25
                                           TOTAL DUE:   $5,479.25

Please remit payment via ACH to routing 021000089 / account 4451289023
or via check payable to TechServices Plus LLC.

Questions? contact billing@techservicesplus.example.com
"""

MEETING_NOTES_TEXT = """
Product Roadmap Review — Q1 2025 Planning Session
Date: January 8, 2025
Location: Conference Room B + Zoom

Attendees: Sarah Chen (Head of Product), Raj Patel (Engineering Lead), 
Dana Okafor (Design Lead), Marcus Webb (VP Sales), Lisa Zhang (Data Science)

---

DISCUSSION POINTS:

1. API v3 Launch Status
   - 87% of endpoints migrated. Raj confirmed Jan 31 as final cutover date.
   - DECISION: API v2 sunset moved to March 31 (was Feb 28) due to customer requests.
   - ACTION: Raj to send migration guide to all API customers by Jan 15.

2. Mobile App Redesign
   - Dana presented Figma mockups for new onboarding flow.
   - NPS impact expected: +8 to +12 points based on similar redesigns in industry.
   - DECISION: Approved for Q1 development start. 
   - Budget allocated: $145,000 for design + development.
   - ACTION: Dana to finalize spec doc by Jan 12.
   - ACTION: Sarah to schedule user testing sessions (target: 15 participants).

3. AI Features Roadmap
   - Lisa presented ML model accuracy: 94.2% on internal test set.
   - Early access program: 23 enterprise customers signed up.
   - DECISION: General availability target moved to February 28 (was March 15).
   - ACTION: Lisa to prepare accuracy report for Feb 1 go/no-go decision.

4. Sales Feedback Integration
   - Marcus shared top 5 feature requests from Q4 sales calls.
   - #1 request: Bulk export (CSV/Excel) — affects 34% of enterprise deals.
   - DECISION: Add bulk export to Q1 sprint backlog as P1.
   - ACTION: Raj to estimate bulk export development effort by Jan 10.

KEY METRICS DISCUSSED:
- Current NPS: 52
- API adoption: 78% of enterprise customers using API
- Mobile app DAU: 12,400 (up 18% MoM)
- AI feature trial activation: 67% of enterprise tier

Next meeting: January 22, 2025 — Q1 Sprint Review
"""


# ─────────────────────────────────────────────────────────────────────────────
# Extraction Engine
# ─────────────────────────────────────────────────────────────────────────────

def extract_with_retry(
    client: LLMClient,
    document: str,
    schema_class: type,
    doc_type: str,
    max_retries: int = 3,
    verbose: bool = True,
) -> Optional[object]:
    """Extract structured data with retry on validation failure."""
    if not PYDANTIC_AVAILABLE:
        print("  Pydantic not available — skipping validation")
        return None

    schema_json = json.dumps(schema_class.model_json_schema(), indent=2)
    prompt = f"""Extract all information from the following {doc_type} into a JSON object.

SCHEMA (follow exactly):
{schema_json}

DOCUMENT:
{document}

Output ONLY a valid JSON object that conforms to the schema.
Use null for missing optional fields. Do not add extra keys."""

    for attempt in range(1, max_retries + 1):
        if verbose and attempt > 1:
            print(f"  Retry attempt {attempt}...")

        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1000,
        )

        if client.dry_run:
            print(f"  [DRY RUN — would extract {doc_type}]")
            return None

        raw = response.content.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.split("\n")[1:])
        raw = raw.rstrip("`").strip()

        try:
            data = json.loads(raw)
            obj = schema_class(**data)
            if verbose:
                print(f"  ✅ Extracted successfully (attempt {attempt})")
            return obj
        except json.JSONDecodeError as e:
            err = f"JSON error: {e.msg}"
            prompt += f"\n\nERROR in previous attempt: {err}. Fix JSON syntax."
        except Exception as e:
            err = str(e)[:100]
            prompt += f"\n\nVALIDATION ERROR: {err}. Fix the field value."

    if verbose:
        print(f"  ❌ Failed after {max_retries} attempts")
    return None


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Data Extraction Pipeline")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--doc", default="all",
                        choices=["invoice", "meeting", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 05 — Real World: Structured Data Extraction")
    print("  Constrained generation + Pydantic validation")
    print("═" * 72)

    total_cost = 0.0

    if args.doc in ("invoice", "all"):
        print("\n  ── Invoice Extraction ───────────────────────────────────────")
        print(f"  Document: {len(INVOICE_TEXT.splitlines())} lines")

        if PYDANTIC_AVAILABLE:
            invoice = extract_with_retry(
                client, INVOICE_TEXT, Invoice, "invoice", verbose=True
            )
            if invoice and not client.dry_run:
                print(f"\n  Extracted Invoice:")
                print(f"    Invoice #:    {invoice.invoice_number}")
                print(f"    Vendor:       {invoice.vendor_name}")
                print(f"    Bill To:      {invoice.bill_to_company}")
                print(f"    Due Date:     {invoice.due_date}")
                print(f"    Line Items:   {len(invoice.line_items)}")
                for item in invoice.line_items:
                    print(f"      • {item.description[:40]:<40} ${item.total:.2f}")
                print(f"    Total:        ${invoice.total_amount:.2f} {invoice.currency}")
                print(f"    Terms:        {invoice.payment_terms}")
        else:
            print("  Pydantic not installed — showing raw extraction")
            response = client.chat(
                messages=[{"role": "user", "content": f"Extract: invoice number, vendor, total due, line items from:\n\n{INVOICE_TEXT}"}],
                temperature=0.0, max_tokens=300,
            )
            if not client.dry_run:
                print(f"  Result: {response.content[:300]}")

    if args.doc in ("meeting", "all"):
        print("\n  ── Meeting Notes Extraction ─────────────────────────────────")
        print(f"  Document: {len(MEETING_NOTES_TEXT.splitlines())} lines")

        if PYDANTIC_AVAILABLE:
            notes = extract_with_retry(
                client, MEETING_NOTES_TEXT, MeetingNotes, "meeting notes", verbose=True
            )
            if notes and not client.dry_run:
                print(f"\n  Extracted Meeting Notes:")
                print(f"    Title:        {notes.meeting_title}")
                print(f"    Date:         {notes.date}")
                print(f"    Attendees:    {', '.join(notes.attendees[:4])}")
                print(f"    Decisions:    {len(notes.decisions)}")
                for d in notes.decisions[:3]:
                    print(f"      • {d[:70]}")
                print(f"    Action Items: {len(notes.action_items)}")
                for ai in notes.action_items[:3]:
                    owner = ai.get("owner", "?")
                    task  = ai.get("task", "?")[:50]
                    due   = ai.get("due", "?")
                    print(f"      • [{owner}] {task} (by {due})")
                print(f"    Metrics:      {', '.join(notes.key_metrics_mentioned[:3])}")
        else:
            response = client.chat(
                messages=[{"role": "user", "content": f"List all action items and decisions from:\n\n{MEETING_NOTES_TEXT}"}],
                temperature=0.0, max_tokens=400,
            )
            if not client.dry_run:
                print(f"  Result: {response.content[:400]}")

    print("\n✅ Data Extraction pipeline complete.\n")


if __name__ == "__main__":
    main()
