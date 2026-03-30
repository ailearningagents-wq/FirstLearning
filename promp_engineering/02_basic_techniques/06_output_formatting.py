"""
02_basic_techniques/06_output_formatting.py
═══════════════════════════════════════════════════════════════════

WHAT:   Techniques to force LLMs to produce specific output formats:
        JSON, CSV, Markdown, XML, and custom schemas. Includes parsing
        and validation strategies for production use.

WHY:    Unstructured prose responses are unusable in automated pipelines.
        If your code needs to parse the LLM response, you MUST control
        the output format. Even small deviations break downstream parsers.

FORMAT SELECTION GUIDE:
        JSON  → API responses, database inserts, inter-service communication
        CSV   → Spreadsheet export, bulk data processing, tabular data
        Markdown → Documentation, reports, human-readable output
        XML   → Legacy system integration, document formats
        Custom → Domain-specific formats (SPARQL, SQL, specific DSLs)

RELIABILITY RANKING (most → least reliable):
        1. JSON with explicit schema + example
        2. Markdown tables (very reliable)
        3. JSON without schema
        4. CSV
        5. XML
        6. Custom formats

PRODUCTION TIPS:
        - Always validate parsed output — LLMs occasionally break format
        - Use Pydantic models to validate JSON responses
        - Add "Return ONLY [format] with no explanation" to block preamble
        - Test with adversarial inputs that might cause format breaks
        - Consider using function calling / tool use for guaranteed JSON
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, count_tokens


# ─────────────────────────────────────────────────────────────────────────────
# SOURCE DATA — Used across all format examples
# ─────────────────────────────────────────────────────────────────────────────

INCIDENT_REPORT = """
Production incident #INC-2847 occurred on March 14, 2024 at 14:23 UTC.
The payments microservice (v2.4.1) began returning HTTP 503 errors. 
Root cause: a Redis connection pool exhaustion triggered by an unexpected 
traffic spike (3x normal volume from the Black Friday promotional email blast).
Impact: 847 failed payment transactions, $23,400 in lost revenue, 
12% of users experienced checkout failures for 47 minutes.
Engineers Sarah Kim and Marcus Jones resolved it by increasing the Redis 
connection pool limit and enabling circuit breakers.
Timeline: Detected 14:23 UTC, mitigated 14:47 UTC, resolved 15:10 UTC.
Post-mortem: Implement auto-scaling for Redis pool, add traffic spike alerting.
"""


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT 1 — JSON (with Pydantic validation)
# ─────────────────────────────────────────────────────────────────────────────

def demo_json_output(client: LLMClient) -> None:
    """Extract structured incident data as JSON and validate with Pydantic."""

    # Explicit JSON schema in the prompt reduces format errors
    prompt = f"""Extract all key information from the incident report below.
Return ONLY valid JSON matching this exact schema. No markdown, no explanation.

Schema:
{{
  "incident_id": "string",
  "severity": "P0|P1|P2|P3",
  "service_affected": "string",
  "service_version": "string",
  "start_time_utc": "ISO8601 datetime",
  "mitigation_time_utc": "ISO8601 datetime",
  "resolution_time_utc": "ISO8601 datetime",
  "duration_minutes": integer,
  "root_cause": "string",
  "impact": {{
    "failed_transactions": integer,
    "revenue_lost_usd": number,
    "affected_user_pct": number
  }},
  "responders": ["string"],
  "action_items": ["string"]
}}

Incident Report:
```
{INCIDENT_REPORT.strip()}
```"""

    print("\n" + "═" * 72)
    print("  FORMAT 1: JSON Output with Schema Enforcement")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(
            user_message=prompt,
            temperature=0.0,  # Factual extraction = deterministic
            max_tokens=500,
        )

        print(f"\n  Raw response ({response.total_tokens} tokens):")
        print(f"  {response.content.strip()}")

        # Attempt to parse and validate
        try:
            # Strip any markdown code fences the model might have added despite instructions
            raw = response.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)

            print("\n  ✅ JSON parsed successfully!")
            print(f"     Incident ID:    {data.get('incident_id', 'N/A')}")
            print(f"     Duration:       {data.get('duration_minutes', 'N/A')} minutes")
            print(f"     Revenue lost:   ${data.get('impact', {}).get('revenue_lost_usd', 0):,.0f}")
        except json.JSONDecodeError as e:
            print(f"\n  ⚠️  JSON parse error: {e}")
            print("  → In production: add retry logic or use OpenAI function calling")
    else:
        print(f"  Prompt ({count_tokens(prompt)} tokens)")
        print(f"  Output format: JSON with explicit schema")


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT 2 — CSV for tabular data
# ─────────────────────────────────────────────────────────────────────────────

SALES_DATA_TEXT = """
Q1 2024 regional sales performance:
North America had $2.3M in revenue from 847 enterprise deals, 
with 89% quota attainment and a 23% win rate against competition.
EMEA achieved $1.8M across 524 deals, 94% quota, 31% win rate.
APAC brought in $0.9M from 312 deals, 71% quota, 18% win rate.
LATAM generated $0.4M from 198 deals, 82% quota, 22% win rate.
Global total: $5.4M, 834 enterprise deals, average deal size $64,748.
"""


def demo_csv_output(client: LLMClient) -> None:
    """Convert a natural language sales report into a CSV table."""

    prompt = f"""Convert the sales data below into a CSV table.

Requirements:
- Headers: Region,Revenue_USD,Deals,Quota_Attainment_Pct,Win_Rate_Pct
- One row per region plus a GLOBAL TOTAL row
- Numbers only (no $, M, or % signs)
- Revenue in actual USD (e.g., 2300000 not 2.3M)
- Return ONLY the CSV, no explanation, no markdown fences

Sales Report:
```
{SALES_DATA_TEXT.strip()}
```"""

    print("\n" + "═" * 72)
    print("  FORMAT 2: CSV Table Output")
    print("  Use case: Parse natural language reports into spreadsheets")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(user_message=prompt, temperature=0.0, max_tokens=200)
        csv_content = response.content.strip()
        print(f"\n  CSV Output:\n{csv_content}")

        # Parse and display as a table
        import io
        try:
            import csv
            reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(reader)
            print(f"\n  ✅ Parsed {len(rows)} rows")
            if rows:
                print(f"  Columns: {list(rows[0].keys())}")
        except Exception as e:
            print(f"  ⚠️  CSV parse note: {e}")
    else:
        print(f"  Input text → CSV table with 5 columns")


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT 3 — Markdown (structured report)
# ─────────────────────────────────────────────────────────────────────────────

CODE_REVIEW_TEXT = """
def authenticate_user(username, password):
    users = db.query(f"SELECT * FROM users WHERE username='{username}'")
    if users and users[0]['password'] == password:
        token = str(uuid.uuid4())
        session[username] = token
        return token
    return None
"""


def demo_markdown_output(client: LLMClient) -> None:
    """Generate a structured Markdown code review report."""

    prompt = f"""Perform a comprehensive code security review of the Python function below.

Output your review as a Markdown document with these sections:
# Code Review: authenticate_user()

## Summary
(2-3 sentence executive summary)

## Critical Issues
(Use: | Issue | Line | Severity | Fix |  table format)

## Security Recommendations
(Numbered list with code examples for the most critical fixes)

## Revised Implementation
(Provide a complete, secure rewrite in a Python code block)

---
Code to review:
```python
{CODE_REVIEW_TEXT.strip()}
```"""

    print("\n" + "═" * 72)
    print("  FORMAT 3: Markdown Report Output")
    print("  Use case: Structured code review / documentation reports")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(
            user_message=prompt,
            temperature=0.1,
            max_tokens=700,
        )
        format_response(response, title="Markdown Code Review Report")
    else:
        print(f"  Input: Python function with security issues")
        print(f"  Output format: Structured Markdown with table + code blocks")


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT 4 — XML (for legacy system integration)
# ─────────────────────────────────────────────────────────────────────────────

INVOICE_TEXT = """
Invoice from Acme Supplies Inc.
Date: March 15, 2024
Invoice Number: INV-20240315-4521
Bill To: TechCorp Inc., 500 Market St, San Francisco CA 94105

Items:
- AWS Cloud Credits (Annual): 48 units @ $125.00 = $6,000.00
- Support Services: 40 hours @ $150.00 = $6,000.00  
- Software License (Enterprise): 1 unit @ $12,500.00 = $12,500.00

Subtotal: $24,500.00
Tax (8.5%): $2,082.50
Total Due: $26,582.50
Payment Terms: Net 30
Due Date: April 14, 2024
"""


def demo_xml_output(client: LLMClient) -> None:
    """Convert an invoice into XML for legacy ERP system integration."""

    prompt = f"""Convert the invoice below into XML format for SAP ERP import.

Use this exact XML structure:
<?xml version="1.0" encoding="UTF-8"?>
<Invoice>
  <Header>
    <InvoiceNumber>...</InvoiceNumber>
    <InvoiceDate>YYYY-MM-DD</InvoiceDate>
    <DueDate>YYYY-MM-DD</DueDate>
    <PaymentTerms>...</PaymentTerms>
  </Header>
  <Vendor>
    <Name>...</Name>
  </Vendor>
  <BillTo>
    <Company>...</Company>
    <Address>...</Address>
    <City>...</City>
    <State>...</State>
    <ZipCode>...</ZipCode>
  </BillTo>
  <LineItems>
    <Item seq="1">
      <Description>...</Description>
      <Quantity>...</Quantity>
      <UnitPrice>...</UnitPrice>
      <Total>...</Total>
    </Item>
  </LineItems>
  <Totals>
    <Subtotal>...</Subtotal>
    <TaxRate>...</TaxRate>
    <TaxAmount>...</TaxAmount>
    <GrandTotal>...</GrandTotal>
  </Totals>
</Invoice>

Return ONLY the XML. Numbers without currency symbols.

Invoice:
```
{INVOICE_TEXT.strip()}
```"""

    print("\n" + "═" * 72)
    print("  FORMAT 4: XML Output for Legacy ERP Integration")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(user_message=prompt, temperature=0.0, max_tokens=500)
        print("\n  XML Output:")
        print(response.content.strip())

        # Validate XML
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content.strip())
            print(f"\n  ✅ Valid XML — root element: <{root.tag}>")
        except Exception as e:
            print(f"  ⚠️  XML validation note: {e}")
    else:
        print(f"  Input: Invoice text")
        print(f"  Output format: SAP-compatible XML")


# ─────────────────────────────────────────────────────────────────────────────
# FORMAT COMPARISON — Token efficiency
# ─────────────────────────────────────────────────────────────────────────────

def demo_format_comparison() -> None:
    """Compare token usage across formats for the same data."""

    # The same contact records in different formats
    data_prose = (
        "We have three contacts: Alice Smith, Software Engineer, email alice@example.com, "
        "phone 415-555-0101. Bob Jones, Product Manager, email bob@example.com, "
        "phone 212-555-0202. Carol White, Data Scientist, email carol@example.com, "
        "phone 628-555-0303."
    )

    data_json = json.dumps([
        {"name": "Alice Smith", "title": "Software Engineer",
         "email": "alice@example.com", "phone": "415-555-0101"},
        {"name": "Bob Jones", "title": "Product Manager",
         "email": "bob@example.com", "phone": "212-555-0202"},
        {"name": "Carol White", "title": "Data Scientist",
         "email": "carol@example.com", "phone": "628-555-0303"},
    ])

    data_csv = (
        "name,title,email,phone\n"
        "Alice Smith,Software Engineer,alice@example.com,415-555-0101\n"
        "Bob Jones,Product Manager,bob@example.com,212-555-0202\n"
        "Carol White,Data Scientist,carol@example.com,628-555-0303"
    )

    data_markdown = (
        "| Name | Title | Email | Phone |\n"
        "|------|-------|-------|-------|\n"
        "| Alice Smith | Software Engineer | alice@example.com | 415-555-0101 |\n"
        "| Bob Jones | Product Manager | bob@example.com | 212-555-0202 |\n"
        "| Carol White | Data Scientist | carol@example.com | 628-555-0303 |"
    )

    formats = [
        ("Prose", data_prose),
        ("JSON", data_json),
        ("CSV", data_csv),
        ("Markdown table", data_markdown),
    ]

    print("\n" + "═" * 72)
    print("  FORMAT TOKEN EFFICIENCY COMPARISON")
    print("  (Same 3 contacts in different formats)")
    print("═" * 72)
    print(f"\n  {'Format':<20} {'Tokens':>8} {'Characters':>12}")
    print("  " + "─" * 44)

    for name, data in formats:
        tokens = count_tokens(data)
        print(f"  {name:<20} {tokens:>8} {len(data):>12}")

    print("\n  💡 CSV and JSON are most token-efficient for tabular data.")
    print("     Markdown tables are ~25% less efficient but more human-readable.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Output Formatting Examples")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--format",
        choices=["json", "csv", "markdown", "xml", "all"],
        default="all",
    )
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 02 — Output Format Control")
    print("  Force LLMs to produce parseable, structured output every time")
    print("═" * 72)

    if args.format in ("json", "all"):
        demo_json_output(client)

    if args.format in ("csv", "all"):
        demo_csv_output(client)

    if args.format in ("markdown", "all"):
        demo_markdown_output(client)

    if args.format in ("xml", "all"):
        demo_xml_output(client)

    demo_format_comparison()

    print("\n✅ Output formatting examples complete.")
    print("   Module 02 complete! Next: Module 03 — Intermediate Techniques\n")


if __name__ == "__main__":
    main()
