"""
08_frameworks_and_tools/02_llamaindex_basics.py
═══════════════════════════════════════════════════════════════════

WHAT: Core LlamaIndex patterns:
      1. Load documents into a VectorStoreIndex
      2. Query with a natural language query engine
      3. Metadata filtering
      4. Custom prompt templates for the synthesizer
      5. Comparison with raw retrieval from Module 05

WHY:  LlamaIndex handles the full RAG pipeline (chunking, embedding,
      indexing, retrieval, synthesis) with far less boilerplate than
      implementing it from scratch.

WHEN: Use LlamaIndex when you need production-grade RAG with:
      - Multiple document types (PDF, HTML, CSV, Notion, etc.)
      - Persistent vector stores (ChromaDB, Pinecone, Weaviate)
      - Advanced retrieval (hybrid search, re-ranking)

PITFALLS:
  - LlamaIndex's abstractions hide chunking/embedding details —
    understand the underlying mechanics (Module 05) before relying on them.
  - Default chunk_size is 1024 tokens; tune for your documents.
  - The synthesis step is a second LLM call — double your costs.
  - Always check .source_nodes to audit what the model was shown.

Install: pip install llama-index llama-index-embeddings-openai

Usage:
    python 02_llamaindex_basics.py
    python 02_llamaindex_basics.py --dry-run
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient

try:
    from llama_index.core import (
        VectorStoreIndex, Document, Settings, PromptTemplate,
        SimpleDirectoryReader,
    )
    from llama_index.core.node_parser import SentenceSplitter
    from llama_index.llms.openai import OpenAI as LlamaOpenAI
    from llama_index.embeddings.openai import OpenAIEmbedding
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Sample Knowledge Base (same content as Module 05 for comparison)
# ─────────────────────────────────────────────────────────────────────────────

DOCUMENTS_RAW = [
    {
        "text": "CloudSync Pro offers three plans. Free plan: 10GB storage, community support. "
                "Pro plan: $29/month, 100GB storage, 48-hour SLA support. "
                "Enterprise: custom pricing, unlimited storage, 4-hour SLA, dedicated CSM, 99.9% uptime guarantee. "
                "Annual plans receive a 20% discount.",
        "metadata": {"source": "kb-plans", "topic": "pricing"},
    },
    {
        "text": "To configure SAML 2.0 SSO: Download SP metadata from Settings > Security > SSO. "
                "Upload to your IdP (Okta, Azure AD, Google Workspace). "
                "Map attributes: email (required), displayName, groups. "
                "Upload IdP metadata back. Test with non-admin account. Enable. "
                "Changes take effect after 1-5 minutes.",
        "metadata": {"source": "kb-sso-saml", "topic": "authentication"},
    },
    {
        "text": "CloudSync API uses Bearer token authentication. Generate tokens in Settings > API Keys. "
                "Tokens expire after 90 days. Include header: Authorization: Bearer <token>. "
                "Base URL: https://api.cloudsync.example.com/v4. "
                "Rate limit: 1000 requests/hour per key.",
        "metadata": {"source": "kb-api", "topic": "api"},
    },
    {
        "text": "Sync conflict (SYNC_CONFLICT_001) occurs when two users edit the same file. "
                "CloudSync creates a conflict copy: originalname_CONFLICT_YYYY-MM-DD_username.ext. "
                "To resolve: download both versions, merge manually, delete the conflict copy. "
                "Enterprise plan users can enable real-time collaboration to prevent conflicts.",
        "metadata": {"source": "kb-sync", "topic": "sync"},
    },
    {
        "text": "CloudSync Pro uses AES-256 encryption at rest and TLS 1.3 in transit. "
                "SOC 2 Type II certified. HIPAA-eligible with BAA on Enterprise plan. "
                "GDPR compliant with data residency options in US, EU, APAC. "
                "Audit logs retained 7 years on Enterprise (90 days Free/Pro).",
        "metadata": {"source": "kb-security", "topic": "security"},
    },
]

QUERIES = [
    "What plans are available and how much do they cost?",
    "How do I set up SSO with Okta?",
    "Is CloudSync HIPAA compliant?",
    "What happens when two people edit the same file?",
]


# ─────────────────────────────────────────────────────────────────────────────
# Fallback demo (no LlamaIndex)
# ─────────────────────────────────────────────────────────────────────────────

def demo_without_llamaindex(client: LLMClient) -> None:
    print("\n  [LlamaIndex not installed — showing conceptual walkthrough]\n")

    print("  LlamaIndex RAG pipeline:")
    print("  ┌─────────────────────────────────────────────────┐")
    print("  │  1. Load documents (PDF, HTML, text, Notion…)   │")
    print("  │  2. SentenceSplitter → nodes (chunks)           │")
    print("  │  3. Embed each node with OpenAIEmbedding        │")
    print("  │  4. Store in VectorStoreIndex (in-memory/FAISS) │")
    print("  │  5. query_engine.query(question)                │")
    print("  │     a. Embed question                           │")
    print("  │     b. Retrieve top-k nodes (similarity search) │")
    print("  │     c. Synthesize answer with LLM + context     │")
    print("  └─────────────────────────────────────────────────┘")

    # Simulate query response with our own LLMClient
    print("\n  Simulating query with raw LLMClient:")
    context = "\n\n".join(d["text"][:200] for d in DOCUMENTS_RAW[:2])
    for q in QUERIES[:2]:
        response = client.chat(
            messages=[{"role": "user", "content": f"Context:\n{context}\n\nQ: {q}"}],
            temperature=0.1, max_tokens=100
        )
        text = response.content.strip() if not client.dry_run else "[DRY-RUN]"
        print(f"\n  Q: {q}")
        print(f"  A: {text[:120]}")


# ─────────────────────────────────────────────────────────────────────────────
# LlamaIndex Demo
# ─────────────────────────────────────────────────────────────────────────────

def demo_with_llamaindex(dry_run: bool) -> None:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Configure LlamaIndex global settings
    Settings.llm = LlamaOpenAI(model=model_name, temperature=0.1)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    Settings.chunk_size  = 256
    Settings.chunk_overlap = 32

    # ── Step 1: Create Documents ────────────────────────────────────────────
    print("\n  ── Step 1: Loading documents")
    documents = [
        Document(text=d["text"], metadata=d["metadata"])
        for d in DOCUMENTS_RAW
    ]
    print(f"  Loaded {len(documents)} documents")

    if dry_run:
        print("  [DRY-RUN: skipping embedding and indexing]")
        print("\n  Conceptual query results:")
        for q in QUERIES:
            print(f"  Q: {q[:60]}")
            print(f"  A: [DRY-RUN] Answer synthesized from relevant nodes")
        return

    # ── Step 2: Build VectorStoreIndex ──────────────────────────────────────
    print("  ── Step 2: Building VectorStoreIndex (embedding documents)...")
    index = VectorStoreIndex.from_documents(
        documents,
        transformations=[SentenceSplitter(chunk_size=256, chunk_overlap=32)],
        show_progress=False,
    )
    print(f"  Index built.")

    # ── Step 3: Custom QA Prompt ─────────────────────────────────────────────
    print("  ── Step 3: Configuring custom QA prompt")
    custom_qa_prompt = PromptTemplate(
        "You are a CloudSync Pro support assistant.\n"
        "Answer using ONLY the context below. If the answer isn't in the context, say so.\n\n"
        "Context:\n{context_str}\n\n"
        "Question: {query_str}\n\n"
        "Answer:"
    )

    query_engine = index.as_query_engine(
        similarity_top_k=2,
        text_qa_template=custom_qa_prompt,
    )

    # ── Step 4: Query ─────────────────────────────────────────────────────────
    print("  ── Step 4: Querying")
    for q in QUERIES:
        response = query_engine.query(q)
        print(f"\n  Q: {q}")
        print(f"  A: {str(response)[:200]}")
        if hasattr(response, "source_nodes") and response.source_nodes:
            sources = [n.metadata.get("source", "?") for n in response.source_nodes]
            print(f"  Sources: {sources}")

    # ── Step 5: Metadata Filtering ────────────────────────────────────────────
    print("\n  ── Step 5: Metadata Filtering (only 'security' topic)")
    from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
    filters = MetadataFilters(filters=[MetadataFilter(key="topic", value="security")])
    filtered_engine = index.as_query_engine(similarity_top_k=2, filters=filters)
    r = filtered_engine.query("What encryption does CloudSync use?")
    print(f"  Q: What encryption does CloudSync use?")
    print(f"  A: {str(r)[:200]}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="LlamaIndex Basics")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 08 — Frameworks: LlamaIndex Basics")
    print(f"  LlamaIndex available: {LLAMAINDEX_AVAILABLE}")
    print("══════════════════════════════════════════════════════════════════════")

    if LLAMAINDEX_AVAILABLE:
        demo_with_llamaindex(dry_run=args.dry_run)
    else:
        demo_without_llamaindex(client)
        print("\n  Install LlamaIndex to run the full demos:")
        print("    pip install llama-index llama-index-embeddings-openai")

    print("\n  KEY CONCEPTS")
    print("  Document          — text + metadata unit")
    print("  VectorStoreIndex  — embedding-based searchable index")
    print("  SentenceSplitter  — chunk documents into nodes")
    print("  query_engine      — retrieve + synthesize interface")
    print("  source_nodes      — inspect which chunks were used")
    print("  MetadataFilters   — restrict retrieval by doc metadata")

    print("\n✅ LlamaIndex basics complete.\n")


if __name__ == "__main__":
    main()
