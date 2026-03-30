"""
02_basic_techniques/02_one_shot_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   One-shot prompting provides exactly ONE example of the desired
        input → output mapping before your actual task.

WHY:    A single well-chosen example can dramatically reduce format errors
        and ambiguity. It "shows" the model what you want rather than
        trying to describe it perfectly in words.

WHEN TO USE:
        ✓ Zero-shot keeps getting the output FORMAT wrong
        ✓ You have a specific schema/structure that's hard to describe
        ✓ The task has subtle nuances best shown by example
        ✓ Token budget is tight (one example costs much less than 5)
        ✗ When the task has multiple distinct pattern types → use few-shot
        ✗ When the example itself introduces bias

EXAMPLE QUALITY MATTERS:
        The example you choose shapes the model's behavior significantly.
        Bad example choices can actually make performance WORSE than zero-shot.

COMMON PITFALLS:
        - Choosing an example that doesn't cover edge cases
        - Picking an example that's too similar to your test case (not generalizable)
        - Forgetting to label the example clearly (Example: / Task:)
        - Using a real customer/user example that contains PII
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_prompt_box


# ─────────────────────────────────────────────────────────────────────────────
# TASK 1 — One-Shot Job Description Parser
# ─────────────────────────────────────────────────────────────────────────────

# The schema we want to extract from job postings
EXAMPLE_JOB_INPUT = """
Senior Machine Learning Engineer @ DataCore AI
Location: Remote (US)
Salary: $160,000 – $210,000 + equity + benefits
Experience: 5+ years of industry ML experience
Must have: Python, PyTorch/TensorFlow, MLOps (MLflow/Kubeflow), SQL
Nice to have: Rust, CUDA, distributed training (Ray/Horovod)
About: DataCore AI builds real-time fraud detection for fintech. We process
10B events/day. Small team, big impact.
Apply: careers@datacoreai.com
"""

EXAMPLE_JOB_OUTPUT = """{
  "title": "Senior Machine Learning Engineer",
  "company": "DataCore AI",
  "location": "Remote (US)",
  "salary_range": {"min": 160000, "max": 210000, "currency": "USD"},
  "experience_years_min": 5,
  "required_skills": ["Python", "PyTorch", "TensorFlow", "MLOps", "MLflow", "Kubeflow", "SQL"],
  "preferred_skills": ["Rust", "CUDA", "Ray", "Horovod"],
  "company_description": "Real-time fraud detection for fintech, 10B events/day",
  "contact_email": "careers@datacoreai.com",
  "remote": true
}"""

TARGET_JOB = """
Staff Data Engineer — Analytics Platform
Hybrid (NYC/London): 3 days in office
Compensation: $130k–$180k base + 15% bonus + RSUs
5+ years experience required

We need someone who breathes data pipelines. Core stack: Python, Spark, dbt,
Snowflake, Airflow. Bonus if you know: Kafka, Terraform, Great Expectations.
You'll own our event data platform serving 200+ internal analysts.

The Analytics Platform team at FinEdge is 12 engineers across 3 time zones.
Please send CV to platform-jobs@finedge.io — no recruiters please.
"""


def task_job_parser(client: LLMClient) -> None:
    """Parse a job description into structured JSON using one-shot learning."""

    # ❌ Zero-shot: works but often inconsistent field names / structures
    zero_shot_prompt = f"""Extract structured information from this job posting as JSON.

Job Posting:
```
{TARGET_JOB.strip()}
```"""

    # ✅ One-shot: shows the exact schema we want
    one_shot_prompt = f"""Extract structured information from a job posting into JSON.
Follow the exact schema shown in the example below.

─── EXAMPLE ───────────────────────────────────────────────────
Input:
{EXAMPLE_JOB_INPUT.strip()}

Output:
{EXAMPLE_JOB_OUTPUT}
─── END EXAMPLE ────────────────────────────────────────────────

Now extract from this job posting. Return ONLY the JSON object:

Input:
{TARGET_JOB.strip()}

Output:"""

    print("\n" + "═" * 72)
    print("  TASK 1: One-Shot Job Description Parsing")
    print("  Goal: Extract structured fields from unstructured job postings")
    print("═" * 72)

    print_prompt_box(one_shot_prompt[:600] + "...", title="✅ One-Shot Prompt (truncated for display)")

    if not client.dry_run:
        # Run zero-shot first
        print("\n  Running ❌ zero-shot version...")
        resp_zero = client.chat(user_message=zero_shot_prompt, temperature=0.1, max_tokens=400)
        format_response(resp_zero, title="Zero-Shot Parser Output")

        # Run one-shot
        print("\n  Running ✅ one-shot version...")
        resp_one = client.chat(user_message=one_shot_prompt, temperature=0.1, max_tokens=400)
        format_response(resp_one, title="One-Shot Parser Output (Note: consistent schema!)")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 2 — One-Shot Email Intent Detection with Metadata
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_EMAIL_INPUT = """
From: raj.patel@techcorp.com
Subject: Re: Q4 License Renewal — urgent

Hi,
We need to finalize the license renewal before December 31st or we'll lose 
the negotiated rate. Can you send the updated contract with the 15% volume 
discount applied? Also, please CC our legal team: legal@techcorp.com

Thanks,
Raj
"""

EXAMPLE_EMAIL_OUTPUT = """{
  "intent": "CONTRACT_RENEWAL",
  "urgency": "HIGH",
  "action_required": true,
  "actions": [
    "Send updated contract with 15% volume discount",
    "CC legal@techcorp.com on the contract email"
  ],
  "deadline": "December 31st",
  "sender_company": "TechCorp",
  "financial_impact": "Revenue retention (volume discount at risk)"
}"""

TARGET_EMAIL = """
From: michelle.wu@hospitalnetwork.org
Subject: System outage affecting 3 hospitals — need resolution NOW

Our EMR system has been unresponsive for 2 hours. This is impacting patient 
care across three facilities. Nurses are resorting to paper records. 
Your SLA guarantees 99.9% uptime. We expect full resolution within the hour 
and a detailed incident report by end of day. 
If this isn't resolved soon, we'll need to escalate to your executive team.

Michelle Wu
CTO, Regional Hospital Network
"""


def task_email_intent(client: LLMClient) -> None:
    """Detect email intent and extract required actions using one-shot."""

    prompt = f"""Analyze the intent of a business email and extract action items.
Follow the exact JSON schema shown in the example.

─── EXAMPLE ───────────────────────────────────────────────────
Input Email:
{EXAMPLE_EMAIL_INPUT.strip()}

Output:
{EXAMPLE_EMAIL_OUTPUT}
─── END EXAMPLE ────────────────────────────────────────────────

Now analyze this email. Return ONLY the JSON:

Input Email:
{TARGET_EMAIL.strip()}

Output:"""

    print("\n" + "═" * 72)
    print("  TASK 2: One-Shot Email Intent Detection")
    print("  Use case: Auto-routing and action extraction for a B2B CRM")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(user_message=prompt, temperature=0.1, max_tokens=300)
        format_response(response, title="Email Intent Analysis")
    else:
        print_prompt_box(prompt[:500] + "...", title="One-Shot Email Intent Prompt")


# ─────────────────────────────────────────────────────────────────────────────
# TASK 3 — One-Shot Code Review (specialized format)
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_CODE = """
def get_user(user_id):
    conn = psycopg2.connect("host=prod-db user=admin password=secret123")
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
"""

EXAMPLE_REVIEW = """| Issue | Severity | Line | Recommendation |
|-------|----------|------|----------------|
| Hardcoded database credentials | 🔴 CRITICAL | 2 | Use environment variables: `os.getenv('DB_PASSWORD')` |
| SQL injection vulnerability | 🔴 CRITICAL | 4 | Use parameterized queries: `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))` |
| Connection not closed (resource leak) | 🟡 HIGH | 2-5 | Use context manager: `with psycopg2.connect(...) as conn:` |
| No type hints | 🟢 LOW | 1 | Add: `def get_user(user_id: int) -> Optional[dict]:` |
| No error handling | 🟡 HIGH | All | Wrap in try/except, handle `psycopg2.OperationalError` |

**Overall Score: 1/10 — Do NOT merge. Security vulnerabilities present.**"""


def task_code_review(client: LLMClient) -> None:
    """Perform structured code review using one-shot format specification."""

    target_code = """
async def process_payment(amount, card_number, cvv):
    import requests
    url = "https://payment-api.example.com/charge"
    data = {"amount": amount, "card": card_number, "cvv": cvv, "merchant": "ACME"}
    r = requests.post(url, json=data, verify=False)
    if r.status_code == 200:
        log.info(f"Charged card {card_number} for ${amount}")
        return r.json()
    """

    prompt = f"""Review the Python code for bugs, security issues, and best practice violations.
Output your review as a Markdown table matching the exact format in the example.

─── EXAMPLE ───────────────────────────────────────────────────
Code to review:
```python
{EXAMPLE_CODE.strip()}
```

Code Review:
{EXAMPLE_REVIEW}
─── END EXAMPLE ────────────────────────────────────────────────

Now review this code. Follow the same table format:
```python
{target_code.strip()}
```

Code Review:"""

    print("\n" + "═" * 72)
    print("  TASK 3: One-Shot Code Security Review")
    print("  Format: Structured Markdown table with severity levels")
    print("═" * 72)

    if not client.dry_run:
        response = client.chat(user_message=prompt, temperature=0.1, max_tokens=600)
        format_response(response, title="Code Review")
    else:
        print_prompt_box(prompt[:600] + "...", title="One-Shot Code Review Prompt")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="One-Shot Prompting Examples")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 02 — One-Shot Prompting")
    print("  Technique: Provide one example to anchor the model's output format")
    print("═" * 72)

    task_job_parser(client)
    task_email_intent(client)
    task_code_review(client)

    print("\n✅ One-shot examples complete.")
    print("   For complex multi-pattern tasks, see 03_few_shot_prompting.py\n")


if __name__ == "__main__":
    main()
