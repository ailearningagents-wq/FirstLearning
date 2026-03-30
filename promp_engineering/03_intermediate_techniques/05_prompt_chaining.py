"""
03_intermediate_techniques/05_prompt_chaining.py
═══════════════════════════════════════════════════════════════════

WHAT:   Prompt Chaining decomposes a complex task into a PIPELINE of
        smaller prompts where the OUTPUT of each step becomes the
        INPUT of the next step.

        task → [Prompt 1] → intermediate → [Prompt 2] → intermediate
              → [Prompt 3] → ... → final output

WHY:    A single large prompt that tries to do everything suffers from:
        - Attention dilution (model forgets early parts)
        - Mixing concerns (worse formatting, worse reasoning)
        - Debugging nightmares (which part went wrong?)
        - No branching logic

        Chaining gives you:
        ✓ Fine-grained control at each step
        ✓ The ability to validate/correct between steps
        ✓ Parallelism (some steps can run concurrently)
        ✓ Cheaper intermediate steps (smaller prompts = fewer tokens)

WHEN TO USE:
        ✓ Content generation pipelines (outline → draft → edit → format)
        ✓ Data pipelines (extract → transform → validate → load)
        ✓ Conditional workflows (classify → route → specialized handler)
        ✓ Long documents that need multiple transformation passes

CHAIN PATTERNS:
        - Sequential:   A → B → C
        - Conditional:  A → if X then B else C
        - Map-Reduce:   Chunk → [B, B, B] → Aggregate
        - Fan-Out:      A → [B1, B2, B3] → C

PITFALLS:
        - Error propagation: bad step 2 corrupts step 3
        - Latency accumulation: N serial LLM calls = N× latency
        - Over-engineering: 10 steps for a 2-step job
"""

import sys
import os
import json
import argparse
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_cost_estimate


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 1: Blog Post Factory Pipeline
# Classify → Outline → Draft section headers → Write intro → Edit
# ─────────────────────────────────────────────────────────────────────────────

BLOG_TOPIC = "Why every Python developer should understand async/await"
BLOG_AUDIENCE = "intermediate Python developers who know functions/classes"
BLOG_WORD_COUNT = 800

def example_blog_pipeline(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 1: Blog Post Factory — 4-Step Chain")
    print(f"  Topic: {BLOG_TOPIC}")
    print("═" * 68)

    # ── Step 1: Audience & Angle Analysis ─────────────────────────────────────
    print("\n  ── Step 1/4: Audience & Angle Analysis ───────────────────────")
    step1_prompt = f"""You are a content strategist.

Analyze this blog topic and audience:
- Topic: {BLOG_TOPIC}
- Audience: {BLOG_AUDIENCE}
- Target word count: {BLOG_WORD_COUNT}

Provide a JSON object with these keys:
{{
  "hook_angle": "The most compelling angle for this audience",
  "key_pain_point": "The #1 problem this article solves for them",
  "what_to_avoid": "Concepts the audience finds confusing or irrelevant",
  "seo_focus_keyword": "Best SEO keyword phrase to target",
  "estimated_read_minutes": <number>
}}

Output ONLY the JSON, nothing else."""

    step1_response = client.chat(
        messages=[{"role": "user", "content": step1_prompt}],
        temperature=0.3,
        max_tokens=250,
    )

    if client.dry_run:
        print("  [DRY RUN — pipeline would execute here]")
        return

    print(format_response(step1_response, title="Audience Analysis", show_stats=True))

    try:
        analysis = json.loads(step1_response.content.strip())
    except json.JSONDecodeError:
        analysis = {"hook_angle": step1_response.content, "key_pain_point": "", 
                    "what_to_avoid": "", "seo_focus_keyword": "", "estimated_read_minutes": 5}

    # ── Step 2: Structured Outline ──────────────────────────────────────────
    print("\n  ── Step 2/4: Creating Structured Outline ────────────────────")
    step2_prompt = f"""You are a technical blog editor.

Create a detailed outline for this blog post. Use the audience analysis below.

Topic: {BLOG_TOPIC}
Angle: {analysis.get('hook_angle', '')}
Key pain point to solve: {analysis.get('key_pain_point', '')}
Avoid: {analysis.get('what_to_avoid', '')}
SEO keyword: {analysis.get('seo_focus_keyword', '')}
Target: {BLOG_WORD_COUNT} words

Output a markdown outline with:
- H1 title (include the SEO keyword naturally)
- H2 sections (5-6 of them)
- Under each H2: 2-3 bullet points describing what content goes there
- Estimated word count per section

Keep the outline concise — this is a planning document, not the article."""

    step2_response = client.chat(
        messages=[{"role": "user", "content": step2_prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    print(format_response(step2_response, title="Blog Outline", show_stats=True))
    outline = step2_response.content.strip()

    # ── Step 3: Write Introduction ─────────────────────────────────────────
    print("\n  ── Step 3/4: Writing the Introduction ───────────────────────")
    step3_prompt = f"""You are a technical writer writing for {BLOG_AUDIENCE}.

Using the outline below, write ONLY the introduction section (150–200 words).

The introduction must:
- Open with the hook angle: {analysis.get('hook_angle', '')}
- State the core problem: {analysis.get('key_pain_point', '')}
- Tell readers exactly what they'll learn
- End with a transition sentence to the first section
- Use plain, conversational English — no jargon without explanation

OUTLINE:
{outline}

Write the introduction now (H1 title + intro paragraph only):"""

    step3_response = client.chat(
        messages=[{"role": "user", "content": step3_prompt}],
        temperature=0.4,
        max_tokens=300,
    )
    print(format_response(step3_response, title="Blog Introduction", show_stats=True))
    intro = step3_response.content.strip()

    # ── Step 4: Editorial Review & Improvements ────────────────────────────
    print("\n  ── Step 4/4: Editorial Review ────────────────────────────────")
    step4_prompt = f"""You are a senior editor at a technical publication.

Review this blog introduction and provide:
1. Quality score (1-10) for clarity, engagement, and SEO
2. Three specific improvement suggestions
3. A rewritten version incorporating those improvements

Target audience: {BLOG_AUDIENCE}
SEO keyword to include: {analysis.get('seo_focus_keyword', '')}

ORIGINAL INTRODUCTION:
{intro}

Output as JSON:
{{
  "quality_score": <1-10>,
  "improvements": ["improvement 1", "improvement 2", "improvement 3"],
  "revised_introduction": "..."
}}"""

    step4_response = client.chat(
        messages=[{"role": "user", "content": step4_prompt}],
        temperature=0.3,
        max_tokens=500,
    )
    print(format_response(step4_response, title="Editorial Review", show_stats=True))

    total_cost = (step1_response.cost_usd + step2_response.cost_usd +
                  step3_response.cost_usd + step4_response.cost_usd)
    total_tokens = (step1_response.total_tokens + step2_response.total_tokens +
                    step3_response.total_tokens + step4_response.total_tokens)

    print(f"\n  💰 4-step chain total: ${total_cost:.6f} ({total_tokens} tokens)")
    print("  📝 In a full pipeline this would continue with all H2 sections...")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 2: Conditional Chain — Customer Support Triage
# Classify → Route to handler → Generate response → QA check
# ─────────────────────────────────────────────────────────────────────────────

CUSTOMER_EMAILS = [
    {
        "id": "EML-001",
        "subject": "URGENT: Production database is down",
        "body": "Our entire app is down. Users cannot log in. Started 10 mins ago. "
                "Error: 'Connection refused to primary DB'. We're on the Enterprise plan.",
    },
    {
        "id": "EML-002",
        "subject": "Question about pricing for additional seats",
        "body": "Hi, we currently have 25 seats on the Pro plan. We're growing and "
                "need about 40 more seats. What would the pricing be? Any discounts?",
    },
]

RESPONSE_HANDLERS = {
    "P0_OUTAGE": "infrastructure_on_call_team",
    "BILLING_INQUIRY": "sales_team",
    "FEATURE_REQUEST": "product_team",
    "BUG_REPORT": "engineering_team",
    "GENERAL_QUESTION": "support_team",
}

def example_conditional_chain(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 2: Conditional Chain — Customer Support Triage")
    print("  Pattern: Classify → Route → Respond → QA")
    print("═" * 68)

    for email in CUSTOMER_EMAILS:
        print(f"\n  ── Processing {email['id']}: '{email['subject']}' ──")

        # Step 1: Classify
        classify_prompt = f"""Classify this customer email into exactly one category.

EMAIL:
Subject: {email['subject']}
Body: {email['body']}

Choose from: P0_OUTAGE, BILLING_INQUIRY, FEATURE_REQUEST, BUG_REPORT, GENERAL_QUESTION

Output a JSON object:
{{
  "category": "<CATEGORY>",
  "urgency": "<critical|high|medium|low>",
  "sentiment": "<frustrated|neutral|positive>",
  "reasoning": "<one sentence>"
}}

Output ONLY the JSON."""

        classify_response = client.chat(
            messages=[{"role": "user", "content": classify_prompt}],
            temperature=0.1,
            max_tokens=150,
        )

        if client.dry_run:
            print("  [DRY RUN]")
            continue

        print(f"\n  Step 1 — Classification:")
        try:
            classification = json.loads(classify_response.content.strip())
            print(f"    Category: {classification.get('category')}")
            print(f"    Urgency:  {classification.get('urgency')}")
            print(f"    Why:      {classification.get('reasoning')}")
        except Exception:
            classification = {"category": "GENERAL_QUESTION", "urgency": "medium"}
            print(f"    (parse fallback) {classify_response.content[:80]}")

        # Step 2: Route
        category = classification.get("category", "GENERAL_QUESTION")
        handler  = RESPONSE_HANDLERS.get(category, "support_team")
        print(f"\n  Step 2 — Routing: → {handler}")

        # Step 3: Generate response for that handler
        tone_map = {
            "P0_OUTAGE": "urgent, empathetic, action-focused",
            "BILLING_INQUIRY": "friendly, consultative, highlighting value",
            "GENERAL_QUESTION": "helpful, concise, professional",
        }
        tone = tone_map.get(category, "professional and helpful")

        generate_prompt = f"""You are a {handler} responding to a customer email.
Tone: {tone}

ORIGINAL EMAIL:
Subject: {email['subject']}
{email['body']}

Classification context: {category}, urgency={classification.get('urgency')}

Write a {tone} email response (3-5 sentences). Include:
- Acknowledge their message specifically
- State what immediate action you're taking
- Set clear expectations for next steps
- Sign off appropriately for a {handler}"""

        generate_response = client.chat(
            messages=[{"role": "user", "content": generate_prompt}],
            temperature=0.3,
            max_tokens=250,
        )

        print(f"\n  Step 3 — Generated Response:")
        prefix = "    "
        for line in generate_response.content.strip().split("\n"):
            print(f"{prefix}{line}")

        step_cost = classify_response.cost_usd + generate_response.cost_usd
        print(f"\n  💰 This email: ${step_cost:.6f}")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Map-Reduce Chain — Summarize a long document
# ─────────────────────────────────────────────────────────────────────────────

LONG_DOCUMENT = """
BOARD MEETING MINUTES — Q4 2024
EcoTech Ventures Inc. | November 15, 2024

ATTENDEES: Sarah Chen (CEO), Marcus Webb (CFO), Dr. Priya Nair (CTO),
Jordan Lee (VP Sales), Board Members: Frank Dunsworth, Linh Tran, Ahmed Hassan

1. FINANCIAL PERFORMANCE
Revenue for Q4 2024 reached $12.4M, up 34% YoY. Gross margin improved to 68%
from 61% last year due to infrastructure optimization. Operating cash flow turned
positive for the first time at $1.2M. CFO Webb reported the company has 18 months
of runway at current burn rate. ARR stands at $48M. Net Revenue Retention is 118%.

2. PRODUCT UPDATES
CTO Nair presented v4.0 launch metrics: 2,300 new enterprise customers in Q4,
97.8% uptime achieved, API response times reduced by 40%. New ML prediction module
drove 23% feature adoption among Enterprise tier. Mobile app reached 4.1 stars.

3. SALES & MARKET EXPANSION
VP Lee reported pipeline grew to $38M. Closed 3 contracts over $500K each.
Expansion into APAC started: offices in Singapore and Sydney operational.
Channel partner program launched with 12 certified partners generating 15% of new ARR.

4. RISKS & CONCERNS
Board member Dunsworth raised concerns about rising CAC (+18% QoQ). Legal team
flagged pending EU AI Act compliance requirements due Q2 2025. CTO noted key
engineer attrition risk — 3 senior engineers accepted offers from Big Tech.

5. 2025 ROADMAP APPROVAL
Board approved $18M operating budget for 2025. Priority investments: AI R&D ($5M),
APAC expansion ($4M), Security & Compliance ($3M), Marketing ($3M), Headcount ($3M).
Target: $72M ARR by end of 2025 (50% growth).

ACTION ITEMS:
- CFO to model 3 CAC improvement scenarios by Dec 1
- CTO to present retention plan for engineering team by Nov 30
- Legal to publish EU AI Act compliance roadmap
- CEO to finalize Series C term sheets (2 active offers)

Meeting adjourned 4:47 PM.
""".strip()

def example_map_reduce(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 3: Map-Reduce Chain — Long Document Summarization")
    print("  Pattern: Chunk → [Summarize each] → Aggregate")
    print("═" * 68)

    # Chunk the document into sections (simulating chunked pages)
    sections = [
        ("Financial Performance", LONG_DOCUMENT[LONG_DOCUMENT.find("1. FINANCIAL"):LONG_DOCUMENT.find("2. PRODUCT")]),
        ("Product Updates",       LONG_DOCUMENT[LONG_DOCUMENT.find("2. PRODUCT"):LONG_DOCUMENT.find("3. SALES")]),
        ("Sales & Expansion",     LONG_DOCUMENT[LONG_DOCUMENT.find("3. SALES"):LONG_DOCUMENT.find("4. RISKS")]),
        ("Risks & Action Items",  LONG_DOCUMENT[LONG_DOCUMENT.find("4. RISKS"):]),
    ]

    print(f"\n  Document split into {len(sections)} chunks (simulating pages)")
    chunk_summaries = []
    chunk_total_cost = 0.0

    # MAP phase
    for i, (section_name, section_text) in enumerate(sections, 1):
        print(f"\n  ── Map Step {i}/{len(sections)}: Summarizing '{section_name}' ─")

        map_prompt = f"""Summarize this section of a board meeting document.
Focus on: key metrics, decisions made, action items, and risks.
Keep to 3-5 bullet points. Be specific — include numbers.

SECTION: {section_name}
{section_text}

Output as bullet points:"""

        map_response = client.chat(
            messages=[{"role": "user", "content": map_prompt}],
            temperature=0.1,
            max_tokens=200,
        )

        if client.dry_run:
            print("  [DRY RUN]")
            return

        chunk_summaries.append(f"### {section_name}\n{map_response.content.strip()}")
        chunk_total_cost += map_response.cost_usd
        print(f"  Cost: ${map_response.cost_usd:.6f}")
        for line in map_response.content.strip().split("\n")[:3]:
            print(f"    {line}")
        print("    ...")

    # REDUCE phase
    print(f"\n  ── Reduce Step: Aggregating {len(sections)} summaries ──────────")
    all_summaries = "\n\n".join(chunk_summaries)

    reduce_prompt = f"""You are a board-level executive assistant.

Below are summaries of each section of a Q4 board meeting.
Synthesize these into a single executive summary (150-200 words) that:
1. Opens with overall company health (1 sentence)
2. Highlights the 3 most important business facts with numbers
3. Lists the 3 highest-priority risks or action items
4. Closes with strategic outlook

SECTION SUMMARIES:
{all_summaries}

EXECUTIVE SUMMARY:"""

    reduce_response = client.chat(
        messages=[{"role": "user", "content": reduce_prompt}],
        temperature=0.2,
        max_tokens=300,
    )

    print(format_response(reduce_response, title="Executive Summary", show_stats=True))
    total = chunk_total_cost + reduce_response.cost_usd
    print(f"\n  💰 Map-Reduce total: ${total:.6f}")
    print(f"  📊 Compressed {len(LONG_DOCUMENT)} chars to ~300-word summary")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Chaining Patterns")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--example", type=str, default="all",
                        choices=["blog", "support", "mapreduce", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 03 — Prompt Chaining")
    print("  Patterns: Sequential | Conditional | Map-Reduce")
    print("═" * 72)

    if args.example in ("blog", "all"):
        example_blog_pipeline(client)

    if args.example in ("support", "all"):
        example_conditional_chain(client)

    if args.example in ("mapreduce", "all"):
        example_map_reduce(client)

    print("\n✅ Prompt Chaining examples complete.")
    print("   Next: 06_delimiters_and_structure.py — control structure techniques\n")


if __name__ == "__main__":
    main()
