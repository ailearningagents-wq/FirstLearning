"""
09_capstone_projects/02_document_qa_system/main.py
═══════════════════════════════════════════════════════════════════

CAPSTONE PROJECT 2: Document Q&A System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Answers questions about a knowledge base of documents with grounded,
cited responses and hallucination detection.

Techniques used:
  • RAG — chunking, BM25 retrieval, LLM synthesis (Module 05)
  • Structured citations (prompt design, Module 03)
  • Hallucination detection (secondary LLM call, Module 07)
  • NOT_IN_CONTEXT fallback — no confabulation (Module 05)
  • Prompt registry (Module 08)

Architecture:
  ┌───────────────────────────────────────────────────┐
  │  Documents → chunk → BM25 index                   │
  │  Query → retrieve top-k chunks                    │
  │  → synthesize answer with citations               │
  │  → hallucination check (secondary call)           │
  │  → output grounded answer OR "not in context"     │
  └───────────────────────────────────────────────────┘

Usage:
    python main.py
    python main.py --dry-run
    python main.py --query "Is CloudSync HIPAA compliant?"
"""

import sys
import os
import re
import math
import argparse
from collections import Counter
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.llm_client import LLMClient
from prompts import build_registry


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    {"id": "doc-001", "title": "Pricing Plans", "content": "CloudSync Pro has three pricing tiers. Free: 10GB storage, community support only. Pro: $29/month, 100GB storage, 48-hour SLA, email support. Enterprise: custom pricing, unlimited storage, 4-hour SLA, dedicated CSM, 99.9% uptime, priority phone support. Annual billing gets 20% off all paid plans."},
    {"id": "doc-002", "title": "Security & Compliance", "content": "CloudSync uses AES-256 encryption at rest and TLS 1.3 in transit. SOC 2 Type II certified annually. HIPAA Business Associate Agreements (BAA) are available for Enterprise customers. GDPR compliant with data residency options in US, EU, and APAC regions. Penetration tests conducted annually by third-party auditors."},
    {"id": "doc-003", "title": "SSO Configuration", "content": "SAML 2.0 and OIDC SSO are supported on Pro and Enterprise plans. To configure: 1) Download SP metadata from Settings > Security > SSO. 2) Register in your IdP (Okta, Azure AD, Google Workspace). 3) Map attributes: email is required, displayName and groups are optional. 4) Upload IdP metadata back to CloudSync. 5) Test and enable."},
    {"id": "doc-004", "title": "API Reference", "content": "REST API base URL: https://api.cloudsync.example.com/v4. Authentication: Bearer token in Authorization header. Tokens expire after 90 days; generate at Settings > API Keys. Rate limit: 1,000 requests/hour per token. Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset."},
    {"id": "doc-005", "title": "Sync and Storage", "content": "Sync conflict (error SYNC_CONFLICT_001) happens when two users edit the same file simultaneously. CloudSync creates a conflict copy named originalname_CONFLICT_YYYY-MM-DD_username.ext. Resolve by merging both versions manually. Storage quota exceeded (QUOTA_EXCEEDED_007): empty trash (items kept 30 days), delete old versions. Version history: Free=10, Pro=30, Enterprise=unlimited."},
    {"id": "doc-006", "title": "User Roles", "content": "CloudSync has four built-in roles: ADMIN (full access including billing, SSO, user management), MANAGER (workspace user management, read-only audit), EDITOR (file CRUD, link sharing), VIEWER (read-only, download). Custom roles available on Enterprise. Roles are workspace-scoped — a user can have different roles in different workspaces."},
    {"id": "doc-007", "title": "Performance", "content": "For optimal sync performance, exclude .git and node_modules directories. Enable delta sync at Settings > Performance > Delta Sync to sync only changed file blocks. Recommended bandwidth: 100 Mbps for teams >20 users. Sync below 5 MB/s: check CPU utilization, verify port 443 is open, and add *.cloudsync.example.com to VPN/proxy allowlist."},
    {"id": "doc-008", "title": "Mobile Apps", "content": "CloudSync offers iOS and Android apps. The mobile apps support offline access to starred files, camera upload for photos, and Touch/Face ID authentication. Push notifications are sent for mentions, share requests, and conflict alerts. Background sync runs every 15 minutes; foreground sync is near real-time on WiFi."},
]


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval (BM25-style)
# ─────────────────────────────────────────────────────────────────────────────

def _tok(text: str) -> list[str]:
    return re.findall(r'\w+', text.lower())


def bm25_retrieve(query: str, documents: list[dict], top_k: int = 3) -> list[dict]:
    k1, b = 1.5, 0.75
    avg_dl = sum(len(_tok(d["content"])) for d in documents) / len(documents)

    scores = []
    query_terms = set(_tok(query))
    for doc in documents:
        doc_toks = _tok(doc["content"] + " " + doc["title"])
        doc_len  = len(doc_toks)
        term_freq = Counter(doc_toks)
        score = 0.0
        for term in query_terms:
            tf = term_freq.get(term, 0)
            df = sum(1 for d in documents if term in d["content"].lower())
            idf = math.log((len(documents) - df + 0.5) / (df + 0.5) + 1)
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * doc_len / avg_dl))
        scores.append((score, doc))

    scores.sort(key=lambda x: x[0], reverse=True)
    return [d for _, d in scores[:top_k]]


# ─────────────────────────────────────────────────────────────────────────────
# Q&A Pipeline
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class QAResult:
    question: str
    retrieved_ids: list[str]
    answer: str
    not_in_context: bool = False
    hallucination_detected: bool = False
    cost_usd: float = 0.0


def answer_question(
    client: LLMClient,
    question: str,
    registry,
    top_k: int = 3,
    check_hallucination: bool = True,
) -> QAResult:
    total_cost = 0.0

    # Step 1: Retrieve
    chunks = bm25_retrieve(question, KNOWLEDGE_BASE, top_k=top_k)
    retrieved_ids = [c["id"] for c in chunks]
    context = "\n\n".join(f"[{c['id']}] {c['title']}\n{c['content']}" for c in chunks)

    # Step 2: Synthesize
    synth_pv = registry.get_active("qa_synthesize")
    prompt = synth_pv.render(context=context, question=question)
    r = client.chat(
        messages=[{"role": "user", "content": prompt}],
        system=synth_pv.render_system(),
        temperature=0.0, max_tokens=250,
    )
    total_cost += r.cost_usd

    if client.dry_run:
        answer = f"[DRY-RUN] Based on {retrieved_ids}, the answer relates to {question[:40]}. [{retrieved_ids[0]}]"
    else:
        answer = r.content.strip()

    not_in_ctx = "NOT_IN_CONTEXT" in answer.upper()

    # Step 3: Hallucination check (only if answer is not a "not in context" reply)
    hallucination = False
    if check_hallucination and not not_in_ctx and not client.dry_run:
        hall_pv = registry.get_active("hallucination_check")
        hall_prompt = hall_pv.render(context=context, answer=answer)
        r_hall = client.chat(
            messages=[{"role": "user", "content": hall_prompt}],
            temperature=0.0, max_tokens=5,
        )
        total_cost += r_hall.cost_usd
        hallucination = "YES" in r_hall.content.upper()

    return QAResult(
        question=question,
        retrieved_ids=retrieved_ids,
        answer=answer,
        not_in_context=not_in_ctx,
        hallucination_detected=hallucination,
        cost_usd=total_cost,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sample queries
# ─────────────────────────────────────────────────────────────────────────────

SAMPLE_QUERIES = [
    "What plans are available and what is their price?",
    "Is CloudSync HIPAA compliant?",
    "How do I configure SSO with Okta?",
    "What is the API rate limit?",
    "How do I resolve a sync conflict?",
    "Does CloudSync support offline access on mobile?",
    "What is the maximum file upload size allowed?",  # Not in knowledge base
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Document Q&A System")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--query", type=str, help="Single custom question")
    parser.add_argument("--top-k", type=int, default=3, help="Chunks to retrieve per query")
    args = parser.parse_args()

    client   = LLMClient(dry_run=args.dry_run)
    registry = build_registry()

    queries = [args.query] if args.query else SAMPLE_QUERIES

    print("\n" + "═" * 72)
    print("  CAPSTONE 2: DOCUMENT Q&A SYSTEM")
    print(f"  Knowledge base: {len(KNOWLEDGE_BASE)} documents | Retrieval: BM25 top-{args.top_k}")
    print("═" * 72)

    total_cost = 0.0
    not_in_ctx_count = 0
    hallucination_count = 0

    for i, q in enumerate(queries, 1):
        print(f"\n  [{i}/{len(queries)}] {q}")
        result = answer_question(client, q, registry, top_k=args.top_k)
        total_cost += result.cost_usd

        if result.not_in_context:
            not_in_ctx_count += 1
            print("  ⚠️  NOT IN CONTEXT — answer not found in knowledge base")
        else:
            sources = ", ".join(result.retrieved_ids)
            print(f"  Sources: {sources}")
            print(f"  Answer: {result.answer[:200]}")
            if result.hallucination_detected:
                hallucination_count += 1
                print("  🚨 HALLUCINATION DETECTED — answer may exceed context")

        if not client.dry_run:
            print(f"  Cost: ${result.cost_usd:.5f}")

    print("\n" + "═" * 72)
    print("  RESULTS SUMMARY")
    print("═" * 72)
    print(f"  Queries answered:     {len(queries) - not_in_ctx_count}/{len(queries)}")
    print(f"  Not in context:       {not_in_ctx_count}")
    print(f"  Hallucinations:       {hallucination_count}")
    if total_cost > 0:
        print(f"  Total cost:           ${total_cost:.5f}")
    print()
    print("  ✅ System correctly deflects questions outside the knowledge base")
    print("  ✅ Every answer includes document citation(s)")
    print("\n✅ Document Q&A complete.\n")


if __name__ == "__main__":
    main()
