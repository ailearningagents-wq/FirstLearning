"""
02_basic_techniques/04_role_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   Role prompting assigns a specific persona, expertise level, or
        professional identity to the model via the system message.
        "You are a [role] who [specific description]..."

WHY:    Roles influence:
        1. VOCABULARY: A doctor uses medical terms; an ELI5 tutor avoids them
        2. DEPTH: A senior engineer goes deeper than a junior one
        3. TONE: A lawyer is formal; a startup founder is informal
        4. ASSUMPTIONS: What the model takes as given vs. needing explanation
        5. PRIORITY: What the model considers important to mention first

WHEN TO USE:
        ✓ Tone and expertise level matter for your use case
        ✓ You want the model to behave like a domain expert
        ✓ Building user-facing products (chatbots, assistants)
        ✓ When the same content needs multiple audience adaptations
        ✗ Pure data extraction — role has minimal effect on structured output

ROLE DESIGN PRINCIPLES:
        1. Be specific: "senior Python engineer with 10 years of production experience"
           beats "programmer"
        2. Include constraints: "You never guess; if you're unsure, say so"
        3. Specify the audience: "You are explaining this to a Fortune 500 CEO"
        4. Add behavioral rules: "Always cite your reasoning" / "Be concise"

COMMON PITFALLS:
        - Generic roles like "helpful assistant" (model default, add nothing)
        - Roles that contradict each other ("strict but also creative")
        - Forgetting that roles affect output length (experts write more)
        - Using fictional roles for safety-sensitive tasks
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response


# ─────────────────────────────────────────────────────────────────────────────
# DEMONSTRATION — Same question, 5 different expert roles
# ─────────────────────────────────────────────────────────────────────────────

SAME_QUESTION = """
Our startup is considering building an AI-powered HR tool that automatically
screens resumes and ranks candidates. What are the key risks we should consider?
"""

ROLES = {
    "No role (baseline)": None,

    "Startup Advisor": (
        "You are a seasoned startup advisor who has helped 50+ B2B SaaS companies "
        "reach Series A. You think in first principles, challenge assumptions, and "
        "give direct, opinionated advice. Be concise — bullet points preferred."
    ),

    "Employment Lawyer": (
        "You are a senior employment attorney specializing in HR technology and "
        "algorithmic hiring bias litigation. You've handled EEOC cases and GDPR "
        "compliance for Fortune 100 companies. Be precise, cite relevant legal "
        "frameworks (EEOC, GDPR, NY Local Law 144), and flag the highest-risk items first."
    ),

    "ML Engineer": (
        "You are a principal machine learning engineer with 12 years of experience "
        "building production ML systems. You've shipped recommender systems for "
        "Amazon and search ranking for LinkedIn. Focus on technical risks, model "
        "failure modes, data quality issues, and system reliability."
    ),

    "Head of HR (Enterprise)": (
        "You are the Head of HR at a 10,000-employee multinational corporation. "
        "Your priorities are: candidate experience, hiring manager adoption, "
        "compliance, and reducing time-to-fill. You're skeptical of AI tools that "
        "promise more than they deliver. Be practical and grounded."
    ),
}


def demo_same_question_different_roles(client: LLMClient) -> None:
    """Run the same HR question through 5 different expert roles and compare."""

    print("\n" + "═" * 72)
    print("  DEMO: Same Question → 5 Expert Roles")
    print("  Question: Risks of AI-powered resume screening tool")
    print("═" * 72)

    for role_name, system_prompt in ROLES.items():
        print(f"\n  {'─' * 68}")
        print(f"  🎭 Role: {role_name}")
        if system_prompt:
            # Show a preview of the role description
            print(f"  Persona: {system_prompt[:100]}...")

        if not client.dry_run:
            response = client.chat(
                user_message=SAME_QUESTION,
                system_message=system_prompt,
                temperature=0.5,
                max_tokens=300,
            )
            print(f"\n  Response [{response.total_tokens} tokens, ${response.cost_usd:.5f}]:")
            # Indent the response for readability
            for line in response.content.strip().split("\n"):
                print(f"  {line}")
        else:
            print("  [DRY RUN — would call API with this system prompt]")


# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED — Multi-role interaction (simulated panel discussion)
# ─────────────────────────────────────────────────────────────────────────────

def demo_panel_discussion(client: LLMClient) -> None:
    """
    Simulate a panel of 3 experts debating a product decision.
    
    Technique: Multiple role prompts in sequence, each aware of previous answers.
    """

    decision = "Should we implement a 2-week free trial or require a credit card upfront?"

    panelists = [
        {
            "name": "CRO (Chief Revenue Officer)",
            "system": (
                "You are the CRO of a B2B SaaS company with $5M ARR, "
                "growing 80% YoY. Your primary concern is conversion rate, "
                "MRR growth, and reducing churn. You have strong opinions. "
                "Give your recommendation in 3 bullet points maximum."
            ),
            "question": f"The team is debating: {decision.strip()}\n\nWhat's your recommendation and why?",
        },
        {
            "name": "VP of Product",
            "system": (
                "You are the VP of Product. You care about user activation, "
                "time-to-value, and long-term retention over short-term revenue. "
                "You've read all the research on free trials vs. freemium. "
                "Respond to the CRO's point and give your own recommendation."
            ),
            "question": None,  # Will be populated with CRO's response in a real chain
        },
    ]

    print("\n" + "═" * 72)
    print("  DEMO: Multi-Role Panel Discussion")
    print(f"  Question: {decision}")
    print("═" * 72)

    conversation_history = []
    for p in panelists[:1]:  # Show first panelist in this demo
        print(f"\n  🎙  Panelist: {p['name']}")

        if not client.dry_run:
            response = client.chat(
                user_message=p["question"],
                system_message=p["system"],
                temperature=0.6,
                max_tokens=250,
            )
            for line in response.content.strip().split("\n"):
                print(f"  {line}")
            conversation_history.append({
                "role": p["name"],
                "content": response.content.strip(),
            })
        else:
            print(f"  System: {p['system'][:100]}...")
            print(f"  Question: {p['question']}")


# ─────────────────────────────────────────────────────────────────────────────
# ROLE DESIGN WORKSHOP — Show bad vs good role prompts
# ─────────────────────────────────────────────────────────────────────────────

def demo_role_quality(client: LLMClient) -> None:
    """Compare weak vs strong role definitions on the same task."""

    task = (
        "Review the following SQL query and identify performance issues:\n\n"
        "```sql\n"
        "SELECT c.name, o.total, p.product_name\n"
        "FROM customers c, orders o, products p\n"
        "WHERE c.id = o.customer_id AND o.product_id = p.id\n"
        "AND o.created_at > '2023-01-01'\n"
        "ORDER BY o.total DESC;\n"
        "```"
    )

    comparisons = [
        {
            "quality": "❌ Weak",
            "role": "You are a database expert.",
            "issue": "Too vague — 'expert' in what DBMS? What level of detail?",
        },
        {
            "quality": "✅ Strong",
            "role": (
                "You are a PostgreSQL performance engineer with 8+ years of experience "
                "optimizing slow queries in OLTP systems handling 10M+ records. "
                "You always: (1) identify the specific performance anti-pattern, "
                "(2) estimate the impact, (3) provide the rewritten query. "
                "You never give generic advice — be specific to the actual query."
            ),
            "issue": None,
        },
    ]

    print("\n" + "═" * 72)
    print("  DEMO: Role Quality Comparison — SQL Performance Review")
    print("═" * 72)

    for comp in comparisons:
        print(f"\n  {comp['quality']} Role: {comp['role'][:80]}...")
        if comp["issue"]:
            print(f"  ⚠️  Problem: {comp['issue']}")

        if not client.dry_run:
            response = client.chat(
                user_message=task,
                system_message=comp["role"],
                temperature=0.2,
                max_tokens=300,
            )
            print("\n  Response:")
            for line in response.content.strip().split("\n")[:8]:  # Show first 8 lines
                print(f"  {line}")
            print(f"  ... [{response.completion_tokens} output tokens]\n")


# ─────────────────────────────────────────────────────────────────────────────
# Role Templates Library
# ─────────────────────────────────────────────────────────────────────────────

ROLE_TEMPLATES = {
    "Code Reviewer": (
        "You are a senior software engineer performing a code review. "
        "You prioritize: security vulnerabilities, performance bottlenecks, "
        "test coverage, and readability. You give specific, actionable feedback "
        "with line numbers. You never just say 'looks good.'"
    ),
    "Legal Contract Analyst": (
        "You are a contract attorney specializing in SaaS agreements. "
        "You identify clauses that create excessive liability, restrict "
        "business operations, or create compliance risks. Flag each issue "
        "with severity: CRITICAL, HIGH, MEDIUM, or LOW."
    ),
    "Data Science Tutor": (
        "You are a patient data science tutor teaching intermediate Python "
        "developers. You use real-world analogies, avoid unnecessary jargon, "
        "and always show code examples. Check for understanding at the end "
        "of each explanation."
    ),
    "Executive Communicator": (
        "You are a business writer who specializes in communicating complex "
        "technical and data topics to C-suite executives. You write concisely, "
        "lead with the business impact, and use simple language. Maximum 3 "
        "bullet points unless asked for more."
    ),
    "Adversarial Red Teamer": (
        "You are a security researcher stress-testing AI systems. "
        "You think like an attacker: what are the worst-case failure modes? "
        "What can go wrong? What are the edge cases that break this? "
        "Be creative, thorough, and specific."
    ),
}


def print_role_library() -> None:
    """Print the reusable role template library."""
    print("\n" + "═" * 72)
    print("  REUSABLE ROLE TEMPLATE LIBRARY")
    print("  Copy these into your system prompts")
    print("═" * 72)

    for name, template in ROLE_TEMPLATES.items():
        print(f"\n  📌 {name}")
        # Wrap and indent
        import textwrap
        wrapped = textwrap.fill(template, width=68, initial_indent="     ",
                                subsequent_indent="     ")
        print(wrapped)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Role Prompting Examples")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 02 — Role Prompting")
    print("  Technique: Assign expert personas via the system message")
    print("═" * 72)

    demo_same_question_different_roles(client)
    demo_role_quality(client)
    demo_panel_discussion(client)
    print_role_library()

    print("\n✅ Role prompting examples complete.")
    print("   Next: 05_instruction_tuning.py — writing precise, unambiguous instructions\n")


if __name__ == "__main__":
    main()
