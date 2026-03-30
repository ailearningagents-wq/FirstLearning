"""
05_real_world_applications/06_rag_basic.py
═══════════════════════════════════════════════════════════════════

Basic Retrieval-Augmented Generation (RAG) implementation:
1. Chunk and index a knowledge base
2. Embed user query (or use keyword search as fallback)
3. Retrieve top-k relevant chunks
4. Augment the prompt with retrieved context
5. Generate a grounded answer

This file uses FAISS + sentence-transformers for vector search,
with a BM25-style keyword fallback if sentence-transformers is unavailable.

Install extras: pip install sentence-transformers faiss-cpu
"""

import sys
import os
import re
import math
import argparse
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens, format_response

# Optional: vector search
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Base: CloudSync Pro documentation
# ─────────────────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    {
        "id": "kb-001",
        "title": "Plans Overview",
        "content": "CloudSync Pro offers three plans: Free (10GB, community support), Pro ($29/month, 100GB, 48-hour support), and Enterprise (custom pricing, unlimited storage, 4-hour SLA, 99.9% uptime guarantee, dedicated CSM). Annual plans receive a 20% discount. Plans can be upgraded at any time and downgraded at end of billing period.",
    },
    {
        "id": "kb-002",
        "title": "SSO Setup - SAML",
        "content": "To configure SAML 2.0 SSO: 1) Download SP metadata from Settings > Security > SSO > Download Metadata. 2) Upload to your IdP (Okta, Azure AD, Google Workspace). 3) Map attributes: email (required), displayName, groups (optional). 4) Upload IdP metadata back to Settings > Security > SSO > Upload IdP Metadata. 5) Test with non-admin account. 6) Enable. Changes take effect after browser cache clear (1-5 minutes).",
    },
    {
        "id": "kb-003",
        "title": "SSO Setup - OIDC",
        "content": "To configure OIDC SSO: 1) Register CloudSync as OIDC client in your IdP. 2) Go to Settings > Security > SSO > OIDC Configuration. 3) Enter Client ID, Client Secret, and Discovery URL. 4) Set redirect URI to https://your-domain/auth/oidc/callback. 5) Test authentication flow. OIDC is recommended for modern IdPs; SAML for legacy enterprise systems.",
    },
    {
        "id": "kb-004",
        "title": "API Authentication",
        "content": "CloudSync API uses Bearer token authentication. Generate tokens at Settings > API Keys. Tokens expire after 90 days. Include in requests: Authorization: Bearer <token>. Base URL: https://api.cloudsync.example.com/v4. Rate limit: 1000 requests/hour per key. Headers returned: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset. 429 responses include Retry-After header.",
    },
    {
        "id": "kb-005",
        "title": "Sync Conflicts",
        "content": "Sync conflict (error SYNC_CONFLICT_001) occurs when two users edit the same file concurrently. CloudSync creates a conflict copy named: originalname_CONFLICT_YYYY-MM-DD_username.ext. To resolve: download both versions, manually merge changes, then delete the conflict copy. Enable real-time collaboration mode (Enterprise only) to prevent conflicts.",
    },
    {
        "id": "kb-006",
        "title": "Storage Quota",
        "content": "Storage quota (error QUOTA_EXCEEDED_007) is enforced per workspace. Free: 10GB, Pro: 100GB, Enterprise: unlimited. To free space: empty workspace trash (keeps items 30 days by default), delete old versions (version history: Free keeps 10 versions, Pro keeps 30, Enterprise unlimited). Upgrade at Settings > Billing > Change Plan.",
    },
    {
        "id": "kb-007",
        "title": "Security and Compliance",
        "content": "CloudSync Pro uses AES-256 encryption at rest and TLS 1.3 in transit. SOC 2 Type II certified (report available on request). HIPAA-eligible with BAA on Enterprise plan. GDPR compliant — data residency options in US, EU, APAC. Audit logs retained 7 years on Enterprise (90 days on Free/Pro). Annual penetration testing by third party.",
    },
    {
        "id": "kb-008",
        "title": "Data Migration from S3",
        "content": "Migrate from AWS S3 using the Import Wizard (Settings > Data > Import). Provide temporary read credentials via AWS IAM role or access keys. Migration speed: ~500GB/hour. Files maintain original timestamps and folder structure. Verify migration at Settings > Data > Migration History. Note: S3 data transfer costs may apply from AWS side.",
    },
    {
        "id": "kb-009",
        "title": "User Roles and Permissions",
        "content": "Four roles: ADMIN (full access including billing, SSO, user management), MANAGER (workspace-level user management, read-only audit logs), EDITOR (create/edit/delete files, link sharing), VIEWER (read-only, can download). Custom roles available on Enterprise. Roles are assigned per-workspace, so a user can be Editor in Project A and Viewer in Project B.",
    },
    {
        "id": "kb-010",
        "title": "Performance and Troubleshooting",
        "content": "If sync speed is below 5 MB/s: check server CPU <60%, exclude .git and node_modules directories, enable delta sync at Settings > Performance > Delta Sync. Network timeout (NETWORK_TIMEOUT_003): verify port 443 is open, add *.cloudsync.example.com to VPN/proxy exceptions. Recommended: 100 Mbps for teams >20 users.",
    },
]

QUESTIONS = [
    "How do I set up SSO with Okta?",
    "What is the storage limit on the Pro plan?",
    "How do I handle a sync conflict error?",
    "Is CloudSync HIPAA compliant?",
    "How do I generate an API key?",
    "My sync speed is slow, what should I check?",
]


# ─────────────────────────────────────────────────────────────────────────────
# Retrieval Methods
# ─────────────────────────────────────────────────────────────────────────────

def bm25_score(query: str, document: str) -> float:
    """Simple BM25-inspired keyword relevance score (no external dependencies)."""
    k1 = 1.5
    b  = 0.75
    avg_doc_len = 150  # approximate

    query_terms = set(re.findall(r'\w+', query.lower()))
    doc_words   = re.findall(r'\w+', document.lower())
    doc_len     = len(doc_words)
    word_counts = Counter(doc_words)

    score = 0.0
    for term in query_terms:
        tf = word_counts.get(term, 0)
        idf = math.log(len(KNOWLEDGE_BASE) / (sum(1 for c in KNOWLEDGE_BASE if term in c["content"].lower()) + 1)) + 1
        numerator   = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
        score += idf * (numerator / denominator)

    return score


def retrieve_by_keyword(query: str, top_k: int = 3) -> list[dict]:
    """Retrieve top-k chunks using BM25 keyword scoring."""
    scored = [
        (bm25_score(query, chunk["content"] + " " + chunk["title"]), chunk)
        for chunk in KNOWLEDGE_BASE
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def retrieve_by_embedding(query: str, top_k: int = 3) -> list[dict]:
    """Retrieve top-k chunks using semantic embedding similarity."""
    if not (EMBEDDING_AVAILABLE and FAISS_AVAILABLE):
        return retrieve_by_keyword(query, top_k)

    model = SentenceTransformer("all-MiniLM-L6-v2")
    docs  = [f"{c['title']} {c['content']}" for c in KNOWLEDGE_BASE]

    doc_embeddings = model.encode(docs, normalize_embeddings=True).astype("float32")
    query_emb = model.encode([query], normalize_embeddings=True).astype("float32")

    dim   = doc_embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(doc_embeddings)

    _, indices = index.search(query_emb, top_k)
    return [KNOWLEDGE_BASE[i] for i in indices[0]]


# ─────────────────────────────────────────────────────────────────────────────
# RAG Answer Generation
# ─────────────────────────────────────────────────────────────────────────────

def rag_answer(
    client: LLMClient,
    question: str,
    top_k: int = 3,
    use_embedding: bool = False,
) -> tuple[str, list[dict], float]:
    """
    Retrieve relevant chunks, then generate a grounded answer.
    Returns: (answer, retrieved_chunks, estimated_cost)
    """
    # Retrieve
    if use_embedding and EMBEDDING_AVAILABLE:
        chunks = retrieve_by_embedding(question, top_k)
        retrieval_method = "embedding"
    else:
        chunks = retrieve_by_keyword(question, top_k)
        retrieval_method = "keyword (BM25)"

    # Build context
    context = "\n\n".join(
        f"[{chunk['id']}] {chunk['title']}\n{chunk['content']}"
        for chunk in chunks
    )

    # Estimate cost
    prompt = f"""You are a helpful customer support assistant for CloudSync Pro.

Answer the user's question using ONLY the information in the provided context.
If the answer isn't in the context, say "I don't have that information — please contact support@cloudsync.example.com".
Keep the answer concise and actionable.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""

    cost = 0.0
    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=250,
    )

    if client.dry_run:
        return f"[DRY RUN answer — retrieved using {retrieval_method}]", chunks, 0.0

    cost = response.cost_usd
    return response.content.strip(), chunks, cost


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Basic RAG System")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--embedding", action="store_true",
                        help="Use sentence-transformers for semantic search (requires install)")
    parser.add_argument("--question", type=str,
                        help="Custom question to ask (default: run all sample questions)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 05 — Real World: Basic RAG (Retrieval-Augmented Generation)")
    print(f"  Knowledge base: {len(KNOWLEDGE_BASE)} chunks")
    retrieval_type = "semantic embedding" if (args.embedding and EMBEDDING_AVAILABLE) else "keyword BM25"
    print(f"  Retrieval: {retrieval_type}")
    print("═" * 72)

    questions = [args.question] if args.question else QUESTIONS[:4]  # Limit default run to save cost

    total_cost = 0.0
    for i, question in enumerate(questions, 1):
        print(f"\n  ── Q{i}: {question}")

        answer, chunks, cost = rag_answer(
            client, question, top_k=2, use_embedding=args.embedding
        )
        total_cost += cost

        print(f"  Retrieved sources: {', '.join(c['id'] for c in chunks)}")
        for chunk in chunks:
            print(f"    [{chunk['id']}] {chunk['title']}")

        print(f"\n  Answer: {answer}")
        if not client.dry_run:
            print(f"  Cost: ${cost:.6f}")

    if not client.dry_run:
        print(f"\n  Total cost for {len(questions)} questions: ${total_cost:.6f}")

    print("\n✅ Basic RAG complete.")
    print("   Module 05 complete! Next: 06_evaluation_and_testing/\n")


if __name__ == "__main__":
    main()
