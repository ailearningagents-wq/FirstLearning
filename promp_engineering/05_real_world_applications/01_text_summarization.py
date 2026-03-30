"""
05_real_world_applications/01_text_summarization.py
═══════════════════════════════════════════════════════════════════

Real-world text summarization pipeline using Map-Reduce + prompt chaining.
Handles documents of any length by chunking and hierarchical summarization.

Supports:
- Single document summarization
- Multi-document comparison/synthesis  
- Summarization at multiple detail levels (executive / tactical / detailed)
- Cost tracking per document
"""

import sys
import os
import argparse
import textwrap
from typing import Literal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens, estimate_cost, format_response, truncate

CHUNK_SIZE_TOKENS = 1200
CHUNK_OVERLAP_TOKENS = 100


# ─────────────────────────────────────────────────────────────────────────────
# Sample Documents
# ─────────────────────────────────────────────────────────────────────────────

EARNINGS_CALL_Q4 = """
Good morning, everyone. Thank you for joining us for our Q4 2024 earnings call.
I'm joined today by our CFO, Jennifer Park, and our COO, Marcus Chen.

Let me start with our headline numbers: Q4 revenue came in at $847 million,
representing 31% year-over-year growth and beating consensus estimates by $23 million.
Full-year 2024 revenue was $2.9 billion, up 28% from $2.27 billion in 2023.

Our enterprise segment was the primary growth driver, growing 42% to $520 million 
in Q4 alone. We added 847 net new enterprise customers in the quarter, bringing our 
total enterprise count to 9,200. Average contract value for new enterprise deals 
was $184,000, up 15% year-over-year.

SMB continues to be a profitable business for us. While growth has moderated to 18%,
our SMB NRR remains strong at 108%, which tells us the customers we have are 
expanding. We acquired the SMB segment profitably through our self-serve model 
at a CAC payback of under 6 months.

On the product side, we launched our AI Assistant feature in October to all tiers.
By end of Q4, 67% of enterprise customers had activated at least one AI workflow.
This drove our product usage metric to an all-time high, and we're seeing AI 
features accelerate expansion revenue within accounts.

Turning to profitability: Q4 operating income was $127 million, a 15% operating 
margin, up from 9% in Q4 2023. This improvement reflects both scale benefits and 
headcount discipline — we grew revenue 31% while headcount grew just 12%.

Free cash flow for the full year was $340 million, representing a 12% FCF margin.
We ended the year with $1.8 billion in cash and no debt.

For Q1 2025 guidance: we expect revenue of $890–$905 million (29–31% growth) and 
operating income of $130–$145 million. Full-year 2025 guidance is $3.6–3.7 billion
in revenue and $580–$620 million in operating income.

Jennifer, do you want to walk through the balance sheet?

Absolutely. As mentioned, we closed Q4 with $1.8B in cash. Our DSO improved to 
48 days from 54 days a year ago — a sign of billing and collections discipline.
Deferred revenue grew 35% to $1.2 billion, providing strong forward revenue visibility.
Our Rule of 40 score (growth rate + FCF margin) is 43, demonstrating balanced growth 
and profitability. We repurchased $200M of stock in Q4 as part of our ongoing program.

Now I'll turn it over to Marcus for operational highlights.

Thanks Jennifer. On the go-to-market side, we made significant investments in our 
partner ecosystem in 2024. Channel partners now contribute 22% of new ACV, up from 
14% a year ago. We certified 380 new partners in Q4 alone and expect the channel 
to grow to 30% of new ACV by end of 2025.

Customer success has been a focus. We reduced churn in our enterprise segment from 
4.1% to 2.8% annually through proactive health scoring and executive engagement.
Our NPS improved from 42 to 58, among the top quartile of B2B SaaS companies.

International expansion: EMEA revenue grew 48% in Q4 and is now 24% of total revenue.
APAC grew 63% from a smaller base and is at 8% of revenue. We opened offices in 
Amsterdam, Singapore, and Seoul in Q4 and plan 4 more in 2025.

We're excited about the opportunities ahead and look forward to your questions.
""".strip()

COMPETITOR_PRESS_RELEASE = """
ACME CORP REPORTS RECORD Q4 RESULTS

SAN FRANCISCO, January 28, 2025 — Acme Corp (NASDAQ: ACME) today reported financial 
results for the fourth quarter ended December 31, 2024.

Q4 2024 Revenue: $634 million (up 18% year-over-year)
Q4 2024 Net Income: $87 million (14% margin)
Full Year 2024 Revenue: $2.2 billion (up 21%)

"We delivered solid execution in a competitive market," said CEO Robert Martinez.
"Our new CloudEdge platform launched in Q3 is gaining traction with 1,200 customers 
in its first quarter."

Enterprise customer count grew to 6,800, up 600 from Q3. Acme's AI features, 
launched in November, are in beta with 200 customers.

For Q1 2025, Acme guides to $660–$680 million revenue (16–17% growth).
""".strip()

ANALYST_REPORT = """
EQUITY RESEARCH NOTE: Enterprise SaaS Sector Update
Rating: OUTPERFORM
Target Price: $115 (from $98)

The enterprise SaaS sector continues to outperform our expectations as AI features
drive meaningful usage expansion within existing accounts. Key findings:

1. AI MONETIZATION IS WORKING: Companies with mature AI features (>6 months in market)
   are seeing 20-35% higher NRR versus cohorts without AI features. This is structural,
   not one-time, as AI creates stickiness and daily engagement.

2. ENTERPRISE > SMB: Large deal momentum is accelerating even as SMB faces 
   macro headwinds. Enterprise deals are getting larger (ACV up 15-20% YoY) while 
   SMB CAC is rising due to digital marketing inflation.

3. INTERNATIONAL OPPORTUNITY: EMEA and APAC represent the next growth vectors.
   Companies with established EMEA offices are growing internationally at 40-60% 
   versus 15-25% for those with less presence.

4. RISK: Competition from hyperscalers (MSFT, GOOG) is intensifying. We estimate 
   10-15% of enterprise deals now have a competitive element from platform vendors.
   Native integrations and workflow depth remain key differentiators.

Our top picks: [Company A] and [Company B]. Both trade at 12x forward revenue vs 
sector median of 10x, justified by above-average growth (30%+) and margin trajectory.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# Core Summarization Functions
# ─────────────────────────────────────────────────────────────────────────────

SummaryLevel = Literal["executive", "tactical", "detailed"]

LEVEL_CONFIG = {
    "executive": {
        "words": 75,
        "focus": "key decisions, headline metrics, strategic implications",
        "audience": "C-level executives with 30 seconds to read",
    },
    "tactical": {
        "words": 200,
        "focus": "specific metrics, action items, risks, and opportunities",
        "audience": "managers and analysts who need to act on this information",
    },
    "detailed": {
        "words": 400,
        "focus": "all significant details, quotes, numbers, and context",
        "audience": "team members who need comprehensive understanding",
    },
}


def summarize_single(
    client: LLMClient,
    text: str,
    level: SummaryLevel = "tactical",
    doc_type: str = "document",
) -> str:
    config = LEVEL_CONFIG[level]
    prompt = f"""You are a business analyst creating a {level}-level summary.

TARGET LENGTH: ~{config['words']} words
FOCUS: {config['focus']}
AUDIENCE: {config['audience']}
DOCUMENT TYPE: {doc_type}

DOCUMENT:
{text}

SUMMARY:"""

    # Check if document needs chunking
    doc_tokens = count_tokens(text, "gpt-4o-mini")
    if doc_tokens > CHUNK_SIZE_TOKENS:
        return summarize_long_document(client, text, level, doc_type)

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=config["words"] * 2,
    )

    if client.dry_run:
        return f"[DRY RUN {level} summary of {doc_tokens}-token {doc_type}]"

    return response.content.strip()


def chunk_text(text: str, chunk_size_tokens: int = CHUNK_SIZE_TOKENS) -> list[str]:
    """Split text into overlapping chunks by approximate token count."""
    words = text.split()
    words_per_chunk = chunk_size_tokens * 3 // 4  # ~0.75 tokens per word
    overlap = CHUNK_OVERLAP_TOKENS * 3 // 4

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + words_per_chunk, len(words))
        chunks.append(" ".join(words[start:end]))
        start = end - overlap
        if start >= len(words) - overlap:
            break
    return chunks


def summarize_long_document(
    client: LLMClient,
    text: str,
    level: SummaryLevel,
    doc_type: str,
) -> str:
    """Map-Reduce summarization for long documents."""
    chunks = chunk_text(text)
    config = LEVEL_CONFIG[level]

    # Map: summarize each chunk
    chunk_summaries = []
    for i, chunk in enumerate(chunks, 1):
        response = client.chat(
            messages=[{"role": "user", "content": (
                f"Extract key facts, metrics, and decisions from this passage "
                f"(chunk {i}/{len(chunks)} of a {doc_type}). "
                f"Focus on: {config['focus']}. Keep to 3-5 bullet points.\n\n{chunk}"
            )}],
            temperature=0.1,
            max_tokens=200,
        )
        if client.dry_run:
            chunk_summaries.append(f"[DRY RUN chunk {i}]")
        else:
            chunk_summaries.append(response.content.strip())

    # Reduce: synthesize chunk summaries
    all_summaries = "\n\n".join(
        f"Section {i+1}:\n{s}" for i, s in enumerate(chunk_summaries)
    )

    reduce_response = client.chat(
        messages=[{"role": "user", "content": (
            f"Synthesize these section summaries into a single {level}-level summary "
            f"(~{config['words']} words). Eliminate redundancy. Preserve all key numbers.\n\n"
            f"Audience: {config['audience']}\n\n{all_summaries}\n\nSUMMARY:"
        )}],
        temperature=0.2,
        max_tokens=config["words"] * 2,
    )

    if client.dry_run:
        return f"[DRY RUN reduced summary from {len(chunks)} chunks]"
    return reduce_response.content.strip()


def compare_documents(
    client: LLMClient,
    documents: dict[str, str],
    comparison_focus: str,
) -> str:
    """Compare multiple documents and synthesize a comparison report."""
    doc_summaries = {}
    for name, doc in documents.items():
        response = client.chat(
            messages=[{"role": "user", "content": (
                f"Extract key metrics and facts from this document related to: {comparison_focus}\n\n{doc}"
            )}],
            temperature=0.1,
            max_tokens=250,
        )
        doc_summaries[name] = response.content.strip() if not client.dry_run else f"[DRY RUN summary of {name}]"

    summaries_text = "\n\n".join(f"### {name}\n{summary}" for name, summary in doc_summaries.items())

    compare_response = client.chat(
        messages=[{"role": "user", "content": (
            f"Compare these documents and generate a competitive analysis table.\n"
            f"Focus on: {comparison_focus}\n\n{summaries_text}\n\n"
            f"Format as: 1) Key Differences table, 2) Winners/Losers on each metric, "
            f"3) Strategic implications paragraph"
        )}],
        temperature=0.2,
        max_tokens=600,
    )

    if client.dry_run:
        return "[DRY RUN comparison report]"
    return compare_response.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Text Summarization Pipeline")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--level", default="tactical", choices=["executive", "tactical", "detailed"])
    parser.add_argument("--demo", default="all",
                        choices=["single", "levels", "compare", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 05 — Real World: Text Summarization Pipeline")
    print("═" * 72)

    total_cost = 0.0

    if args.demo in ("single", "all"):
        print("\n  ── Demo 1: Single Document Summarization ───────────────────")
        tokens = count_tokens(EARNINGS_CALL_Q4, "gpt-4o-mini")
        print(f"  Document: Earnings call transcript ({tokens} tokens)")
        print(f"  Level: {args.level}")

        summary = summarize_single(client, EARNINGS_CALL_Q4, args.level, "earnings call transcript")
        print(f"\n  {args.level.upper()} SUMMARY:")
        print(textwrap.indent(summary, "    "))

    if args.demo in ("levels", "all"):
        print("\n  ── Demo 2: Same Document at Three Levels ───────────────────")
        for level in ["executive", "tactical"]:  # Skip detailed to save cost
            print(f"\n  {level.upper()} ({LEVEL_CONFIG[level]['words']} words):")
            summary = summarize_single(client, EARNINGS_CALL_Q4, level, "earnings call")
            lines = summary.split("\n")
            for line in lines[:5]:
                print(f"    {line}")
            if len(lines) > 5:
                print(f"    ... [{len(lines) - 5} more lines]")

    if args.demo in ("compare", "all"):
        print("\n  ── Demo 3: Multi-Document Competitive Comparison ───────────")
        DOCS = {
            "Target Company Q4": EARNINGS_CALL_Q4,
            "Competitor Q4":     COMPETITOR_PRESS_RELEASE,
            "Analyst View":      ANALYST_REPORT,
        }
        comparison = compare_documents(
            client=client,
            documents=DOCS,
            comparison_focus="revenue growth, profitability, AI adoption, international expansion",
        )
        print(f"\n  COMPARISON REPORT:")
        print(textwrap.indent(comparison[:600], "    "))
        if len(comparison) > 600:
            print("    ... [truncated — run without --dry-run for full output]")

    print("\n✅ Text Summarization pipeline complete.\n")


if __name__ == "__main__":
    main()
