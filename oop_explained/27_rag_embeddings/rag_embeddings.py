"""
=============================================================
GENERATIVE AI FOUNDATIONS
Topic 27: RAG — Retrieval-Augmented Generation & Embeddings
=============================================================

Fully runnable with numpy only (no API key, no vector DB).

COVERED:
  1. What are embeddings and why they matter
  2. TF-IDF style sparse embeddings (from scratch)
  3. Dense (neural) embedding concept — mock version
  4. Cosine similarity implementation
  5. Text chunking strategies
  6. VectorStore class (numpy-based)
  7. Full RAG pipeline: Retrieve → Augment → Generate
  8. Evaluation: Recall@k and MRR
  9. Overview of real vector databases
  10. Hybrid search (dense + sparse)
"""

import math
import re
import textwrap
from collections import Counter, defaultdict
from typing import List, Tuple, Dict, Optional

import numpy as np

rng = np.random.default_rng(seed=42)


# ─────────────────────────────────────────────
# 1. WHAT ARE EMBEDDINGS?
# ─────────────────────────────────────────────

print("=" * 58)
print("1. EMBEDDINGS — Dense Vector Representations")
print("=" * 58)
print("""
  Text                         Embedding (illustrative 4-dim)
  ─────────────────────────────────────────────────────────
  "Python is great for AI"  →  [0.85,  0.12, -0.34,  0.71]
  "I love coding in Python"  →  [0.82,  0.19, -0.29,  0.68]   ← similar!
  "The weather is sunny"    →  [-0.21, 0.88,  0.12, -0.43]   ← different

  KEY INSIGHT:
    Similar meaning  → vectors point in similar directions
    Dissimilar meaning → vectors point in different directions

  DIMENSIONALITY:
    Word2Vec/GloVe  → 100-300 dims
    OpenAI small    → 1,536 dims
    OpenAI large    → 3,072 dims
    Cohere Embed    → 1,024 dims
""")


# ─────────────────────────────────────────────
# 2. TF-IDF EMBEDDINGS (Sparse, from scratch)
# ─────────────────────────────────────────────

print("=" * 58)
print("2. TF-IDF SPARSE EMBEDDINGS")
print("=" * 58)

class TFIDFVectorizer:
    """
    Simple TF-IDF from scratch.
    TF  (term frequency)   = how often term appears in doc
    IDF (inverse doc freq) = log( N / df ) — penalises common words
    """

    def __init__(self):
        self.vocab: Dict[str, int] = {}
        self.idf: np.ndarray       = np.array([])
        self._df: Counter          = Counter()
        self._n_docs: int          = 0

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"\b[a-z]+\b", text.lower())

    def fit(self, corpus: List[str]) -> "TFIDFVectorizer":
        all_tokens: set = set()
        doc_tokens_list = [self._tokenize(d) for d in corpus]
        self._n_docs = len(corpus)

        for tokens in doc_tokens_list:
            unique = set(tokens)
            all_tokens |= unique
            for t in unique:
                self._df[t] += 1

        self.vocab = {t: i for i, t in enumerate(sorted(all_tokens))}
        self.idf   = np.zeros(len(self.vocab))
        for term, idx in self.vocab.items():
            self.idf[idx] = math.log(self._n_docs / (self._df.get(term, 0) + 1)) + 1
        return self

    def transform(self, texts: List[str]) -> np.ndarray:
        out = np.zeros((len(texts), len(self.vocab)), dtype=np.float32)
        for i, text in enumerate(texts):
            tokens = self._tokenize(text)
            tf_count = Counter(tokens)
            total = max(len(tokens), 1)
            for term, cnt in tf_count.items():
                if term in self.vocab:
                    j = self.vocab[term]
                    out[i, j] = (cnt / total) * self.idf[j]
            # L2-normalise
            norm = np.linalg.norm(out[i])
            if norm > 0:
                out[i] /= norm
        return out

    def fit_transform(self, texts: List[str]) -> np.ndarray:
        return self.fit(texts).transform(texts)


corpus = [
    "Python is a popular programming language for data science.",
    "Machine learning models require large amounts of training data.",
    "Deep learning uses neural networks with many layers.",
    "Natural language processing helps computers understand text.",
    "Python libraries like NumPy and pandas simplify data analysis.",
    "Transformers revolutionised natural language processing tasks.",
    "GPT models generate human-like text using deep learning.",
    "Vector databases store embeddings for fast similarity search.",
]

tfidf = TFIDFVectorizer()
sparse_vecs = tfidf.fit_transform(corpus)

print(f"Corpus: {len(corpus)} documents")
print(f"Vocabulary size: {len(tfidf.vocab)}")
print(f"Embedding shape: {sparse_vecs.shape}  (docs × vocab)")

# Similarity between docs 0 and 4 (both about Python)
sim_04 = float(sparse_vecs[0] @ sparse_vecs[4])
sim_01 = float(sparse_vecs[0] @ sparse_vecs[1])
print(f"\nDoc 0: '{corpus[0][:45]}...'")
print(f"Doc 4: '{corpus[4][:45]}...'")
print(f"Doc 1: '{corpus[1][:45]}...'")
print(f"  TF-IDF similarity(0,4) = {sim_04:.3f}  ← both about Python")
print(f"  TF-IDF similarity(0,1) = {sim_01:.3f}  ← less related")


# ─────────────────────────────────────────────
# 3. DENSE EMBEDDING MOCK (Neural Net Concept)
# ─────────────────────────────────────────────

print("\n" + "=" * 58)
print("3. DENSE EMBEDDINGS (Mock Neural Embeddings)")
print("=" * 58)

def mock_encode(text: str, dim: int = 64) -> np.ndarray:
    """
    Deterministic mock embedding.
    In production: openai client.embeddings.create() or
                   sentence-transformers SentenceTransformer.encode()
    """
    seed = sum(ord(c) * (i + 1) for i, c in enumerate(text[:128]))
    local_rng = np.random.default_rng(seed % (2**31))
    vec = local_rng.standard_normal(dim).astype(np.float32)
    # Inject TF-IDF signal so similar texts cluster slightly
    keywords = re.findall(r"\b[a-z]+\b", text.lower())
    for kw in keywords:
        kw_seed = sum(ord(c) for c in kw)
        kw_rng  = np.random.default_rng(kw_seed % (2**31))
        vec    += 0.5 * kw_rng.standard_normal(dim).astype(np.float32)
    norm = np.linalg.norm(vec)
    return vec / (norm + 1e-10)

dense_vecs = np.array([mock_encode(doc) for doc in corpus])
print(f"Dense embedding shape: {dense_vecs.shape}  (docs × dim)")
print("""
  REAL OPTIONS (no API key needed):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")  # free, runs locally
    vecs  = model.encode(sentences)                  # returns numpy array

    Models by size:
      all-MiniLM-L6-v2       → 22M params, 384 dims,  fast
      all-mpnet-base-v2      → 110M params, 768 dims,  better quality
      text-embedding-3-small → OpenAI API, 1536 dims,  excellent
""")


# ─────────────────────────────────────────────
# 4. COSINE SIMILARITY
# ─────────────────────────────────────────────

print("=" * 58)
print("4. COSINE SIMILARITY")
print("=" * 58)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity for unit-norm vectors = dot product."""
    return float(np.dot(a, b))

def top_k_similar(query_vec: np.ndarray,
                   doc_vecs: np.ndarray,
                   k: int = 3) -> List[Tuple[int, float]]:
    """Return (index, score) pairs for top-k similar docs."""
    scores = doc_vecs @ query_vec           # dot product with all docs at once
    top_k  = np.argsort(scores)[::-1][:k]  # sort descending
    return [(int(i), float(scores[i])) for i in top_k]


query_text   = "Python programming for machine learning"
query_vec    = mock_encode(query_text)
top_results  = top_k_similar(query_vec, dense_vecs, k=3)

print(f"Query: '{query_text}'")
print("Top-3 similar documents:")
for rank, (idx, score) in enumerate(top_results, 1):
    text_preview = corpus[idx][:60]
    print(f"  #{rank}  score={score:.4f}  '{text_preview}...'")


# ─────────────────────────────────────────────
# 5. TEXT CHUNKING STRATEGIES
# ─────────────────────────────────────────────

print("\n" + "=" * 58)
print("5. TEXT CHUNKING STRATEGIES")
print("=" * 58)

long_doc = (
    "Artificial intelligence encompasses machine learning, deep learning, "
    "and natural language processing. Machine learning enables systems to "
    "learn from data without explicit programming. Deep learning uses multi-"
    "layer neural networks for complex pattern recognition. NLP allows "
    "machines to understand and generate human language. Modern AI systems "
    "combine these approaches. Transformers use attention mechanisms to "
    "process sequences in parallel. Large language models like GPT-4 are "
    "trained on vast text corpora. They can generate coherent text, answer "
    "questions, and perform reasoning tasks. Fine-tuning adapts pretrained "
    "models to specific domains. RAG combines retrieval with generation."
)

# Strategy 1: Fixed-size chunking
def fixed_chunks(text: str, chunk_size: int = 100, overlap: int = 20) -> List[str]:
    words  = text.split()
    chunks = []
    start  = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

# Strategy 2: Sentence-based chunking
def sentence_chunks(text: str, max_sentences: int = 3) -> List[str]:
    sents  = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    for i in range(0, len(sents), max_sentences):
        chunks.append(" ".join(sents[i:i + max_sentences]))
    return chunks

# Strategy 3: Paragraph-based
def paragraph_chunks(text: str) -> List[str]:
    return [p.strip() for p in text.split("\n\n") if p.strip()]

fixed = fixed_chunks(long_doc, chunk_size=30, overlap=5)
sents = sentence_chunks(long_doc, max_sentences=2)
paras = paragraph_chunks(long_doc)  # single para here, so 1 chunk

print(f"Original doc: {len(long_doc.split())} words")
print(f"\nStrategy         Chunks  Avg words/chunk")
print(f"Fixed (30w, 5ov) {len(fixed):>6}  {sum(len(c.split()) for c in fixed)/len(fixed):.0f}")
print(f"Sentence (2-sent){len(sents):>6}  {sum(len(c.split()) for c in sents)/len(sents):.0f}")
print(f"Paragraph        {len(paras):>6}  {len(long_doc.split()):.0f}")

print(f"\nChunk 1 (fixed)  : {fixed[0]}")
print(f"Chunk 1 (sentence): {sents[0]}")
print("""
  CHOOSING CHUNK SIZE:
    Small (100-200 words) → high precision, can break context
    Large (500-1000 words) → more context, but lower precision
    Overlap (10-15%)       → preserves context across boundaries

  ADVANCED STRATEGIES:
    Hierarchical: chunk at paragraph level, sub-chunk for dense retrieval
    Semantic:     split on topic shifts (requires an LLM or classifier)
    Markdown-aware: split on headers (#, ##) to preserve document structure
""")


# ─────────────────────────────────────────────
# 6. VECTOR STORE (NumPy-based)
# ─────────────────────────────────────────────

print("=" * 58)
print("6. VECTOR STORE")
print("=" * 58)

class VectorStore:
    """
    Simple in-memory vector store with cosine similarity search.
    Production alternatives: FAISS, ChromaDB, Pinecone, Qdrant, Weaviate.
    """

    def __init__(self, dim: int = 64):
        self.dim      = dim
        self.texts:   List[str]       = []
        self.metas:   List[dict]      = []
        self.vectors: Optional[np.ndarray] = None

    def add(self, texts: List[str], metas: Optional[List[dict]] = None) -> None:
        """Embed and store texts."""
        metas     = metas or [{} for _ in texts]
        new_vecs  = np.array([mock_encode(t, self.dim) for t in texts],
                              dtype=np.float32)
        self.texts.extend(texts)
        self.metas.extend(metas)
        if self.vectors is None:
            self.vectors = new_vecs
        else:
            self.vectors = np.vstack([self.vectors, new_vecs])

    def search(self, query: str, k: int = 3,
               filter_meta: Optional[dict] = None) -> List[dict]:
        """Return top-k results as list of dicts."""
        if self.vectors is None or len(self.texts) == 0:
            return []
        q_vec  = mock_encode(query, self.dim)
        scores = self.vectors @ q_vec

        # Apply metadata filter
        valid_indices = list(range(len(self.texts)))
        if filter_meta:
            valid_indices = [i for i in valid_indices
                             if all(self.metas[i].get(k) == v
                                    for k, v in filter_meta.items())]

        # Sort valid indices by score
        valid_indices.sort(key=lambda i: scores[i], reverse=True)
        top = valid_indices[:k]

        return [{
            "text":  self.texts[i],
            "score": float(scores[i]),
            "meta":  self.metas[i],
        } for i in top]

    def __len__(self):
        return len(self.texts)


# Populate the store
store = VectorStore(dim=64)
store.add(corpus,
          metas=[{"category": "python"}   if "python" in d.lower()
                 else {"category": "ai"}
                 for d in corpus])

print(f"VectorStore size: {len(store)} documents")
results = store.search("natural language processing", k=3)
print("Search: 'natural language processing'")
for r in results:
    print(f"  [{r['score']:.4f}] [{r['meta']['category']:>6}] {r['text'][:60]}...")


# ─────────────────────────────────────────────
# 7. FULL RAG PIPELINE
# ─────────────────────────────────────────────

print("\n" + "=" * 58)
print("7. FULL RAG PIPELINE: Retrieve → Augment → Generate")
print("=" * 58)

class MockLLM:
    """Simulates an LLM for the generation step."""
    def generate(self, prompt: str) -> str:
        # Extract answer hint from context
        lines = prompt.split("\n")
        ctx_lines = [l for l in lines if l.startswith("Context:") or
                     l.startswith("  -")]
        keywords = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", prompt)
        if keywords:
            return (f"Based on the retrieved context, {keywords[0]} "
                    f"is discussed in the knowledge base. "
                    f"(Mock answer — plug in a real LLM for accurate output.)")
        return "Based on the provided context, I can provide a relevant answer."


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.

    Steps:
      1. RETRIEVE: find relevant chunks from knowledge base
      2. AUGMENT:  build a prompt that includes retrieved context
      3. GENERATE: call LLM with augmented prompt
    """

    PROMPT_TEMPLATE = """You are a helpful assistant. Answer the question based
ONLY on the provided context. If the context doesn't contain enough information,
say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""

    def __init__(self, vector_store: VectorStore, llm, top_k: int = 3):
        self.store = vector_store
        self.llm   = llm
        self.top_k = top_k

    def retrieve(self, query: str) -> List[dict]:
        return self.store.search(query, k=self.top_k)

    def augment(self, query: str, docs: List[dict]) -> str:
        context = "\n".join(f"  - {d['text']}" for d in docs)
        return self.PROMPT_TEMPLATE.format(context=context, question=query)

    def generate(self, prompt: str) -> str:
        return self.llm.generate(prompt)

    def run(self, query: str) -> dict:
        # Step 1: Retrieve
        docs   = self.retrieve(query)
        # Step 2: Augment
        prompt = self.augment(query, docs)
        # Step 3: Generate
        answer = self.generate(prompt)
        return {
            "query":          query,
            "retrieved_docs": docs,
            "prompt":         prompt,
            "answer":         answer,
        }


rag = RAGPipeline(vector_store=store, llm=MockLLM(), top_k=3)

queries = [
    "How do neural networks work?",
    "What Python libraries are used for data science?",
    "What is retrieval-augmented generation?",
]

for q in queries:
    result = rag.run(q)
    print(f"Q: {q}")
    print(f"A: {result['answer']}")
    print(f"   Sources ({len(result['retrieved_docs'])} docs):")
    for doc in result["retrieved_docs"]:
        print(f"     [{doc['score']:.3f}] {doc['text'][:55]}...")
    print()


# ─────────────────────────────────────────────
# 8. EVALUATION: Recall@k and MRR
# ─────────────────────────────────────────────

print("=" * 58)
print("8. RAG EVALUATION METRICS")
print("=" * 58)

# Gold-standard labelled dataset  (query → relevant doc indices)
eval_dataset = [
    {"query": "Python data science libraries",    "relevant": {0, 4}},
    {"query": "deep learning neural networks",    "relevant": {1, 2, 6}},
    {"query": "natural language processing text", "relevant": {3, 5}},
    {"query": "vector databases embeddings",      "relevant": {7}},
]

def recall_at_k(retrieved_indices: List[int], relevant: set, k: int) -> float:
    """Fraction of relevant docs found in top-k retrieved."""
    hits = len(set(retrieved_indices[:k]) & relevant)
    return hits / len(relevant) if relevant else 0.0

def mean_reciprocal_rank(retrieved_indices: List[int], relevant: set) -> float:
    """1 / rank of first relevant doc (0 if none found)."""
    for rank, idx in enumerate(retrieved_indices, start=1):
        if idx in relevant:
            return 1.0 / rank
    return 0.0

k = 3
recall_scores = []
mrr_scores    = []

for sample in eval_dataset:
    q    = sample["query"]
    gold = sample["relevant"]
    docs = store.search(q, k=k)
    retrieved_indices = [corpus.index(d["text"]) for d in docs if d["text"] in corpus]
    recall_scores.append(recall_at_k(retrieved_indices, gold, k))
    mrr_scores.append(mean_reciprocal_rank(retrieved_indices, gold))

print(f"Evaluation over {len(eval_dataset)} queries:")
print(f"  Recall@{k}  = {sum(recall_scores)/len(recall_scores):.3f}")
print(f"  MRR        = {sum(mrr_scores)/len(mrr_scores):.3f}")
print(f"""
  METRICS EXPLAINED:
    Recall@k     : what fraction of gold relevant docs appear in top-k
    Precision@k  : what fraction of top-k results are relevant
    MRR          : reciprocal rank of first relevant hit (higher is better)
    NDCG@k       : normalised discounted cumulative gain (accounts for rank)

  TARGET VALUES (rough):
    Recall@5 > 0.7   is good for most RAG use cases
    MRR > 0.6        means relevant doc usually appears near the top
""")


# ─────────────────────────────────────────────
# 9. HYBRID SEARCH (Dense + Sparse)
# ─────────────────────────────────────────────

print("=" * 58)
print("9. HYBRID SEARCH (Dense + Sparse)")
print("=" * 58)

def hybrid_search(query: str, corpus: List[str],
                  dense_vecs: np.ndarray,
                  sparse_vectorizer: TFIDFVectorizer,
                  alpha: float = 0.6,
                  k: int = 3) -> List[Tuple[int, float]]:
    """
    Reciprocal Rank Fusion of dense and sparse retrieval.
    alpha: weight for dense scores (1-alpha for sparse)
    """
    # Dense scores
    q_dense  = mock_encode(query)
    d_scores = dense_vecs @ q_dense

    # Sparse scores
    q_sparse = sparse_vectorizer.transform([query])[0]
    s_scores = sparse_vecs @ q_sparse

    # Normalise both to [0,1]
    def norm01(arr):
        mn, mx = arr.min(), arr.max()
        return (arr - mn) / (mx - mn + 1e-10)

    hybrid = alpha * norm01(d_scores) + (1 - alpha) * norm01(s_scores)
    top_k  = np.argsort(hybrid)[::-1][:k]
    return [(int(i), float(hybrid[i])) for i in top_k]


q_hybrid = "Python machine learning libraries data"
results  = hybrid_search(q_hybrid, corpus, dense_vecs, tfidf, alpha=0.6)
print(f"Hybrid search: '{q_hybrid}'  (alpha=0.6 dense, 0.4 sparse)")
for rank, (idx, score) in enumerate(results, 1):
    print(f"  #{rank}  score={score:.4f}  '{corpus[idx][:60]}...'")


# ─────────────────────────────────────────────
# 10. REAL VECTOR DATABASE OVERVIEW
# ─────────────────────────────────────────────

print("\n" + "=" * 58)
print("10. REAL VECTOR DATABASES")
print("=" * 58)
print("""
  ┌──────────────┬──────────┬───────────┬──────────────────────────┐
  │ DB           │ Type     │ Scale     │ Notes                    │
  ├──────────────┼──────────┼───────────┼──────────────────────────┤
  │ FAISS        │ Library  │ Millions  │ Facebook, in-memory,     │
  │              │          │           │ very fast, no persistence │
  │ ChromaDB     │ Embedded │ Thousands │ pip install chromadb,    │
  │              │          │           │ easy to start, local      │
  │ Pinecone     │ Cloud    │ Billions  │ Managed SaaS, low-latency │
  │ Weaviate     │ OSS/Cloud│ Billions  │ Built-in BM25 + vector    │
  │ Qdrant       │ OSS/Cloud│ Billions  │ Rust-based, very fast     │
  │ Milvus       │ OSS      │ Billions  │ Distributed, production   │
  │ pgvector     │ Postgres │ Millions  │ Extension for Postgres    │
  └──────────────┴──────────┴───────────┴──────────────────────────┘

  QUICKSTART with ChromaDB:
    import chromadb
    client = chromadb.Client()
    col    = client.create_collection("my_docs")
    col.add(documents=corpus, ids=[str(i) for i in range(len(corpus))])
    results = col.query(query_texts=["neural networks"], n_results=3)

  QUICKSTART with FAISS:
    import faiss, numpy as np
    dim  = 1536
    idx  = faiss.IndexFlatIP(dim)   # Inner Product (cosine for unit vecs)
    vecs = np.array(embeddings, dtype=np.float32)
    faiss.normalize_L2(vecs)
    idx.add(vecs)
    D, I = idx.search(query_vec.reshape(1,-1), k=5)  # D=scores, I=indices
""")

print("=" * 58)
print("SUMMARY — RAG Architecture")
print("=" * 58)
print("""
  DOCUMENT INGESTION (offline):
    Raw docs → Chunking → Embedding → VectorStore

  QUERY PIPELINE (online):
    User query → Embed query → Search VectorStore (top-k)
             → Build prompt (question + context)
             → LLM generates answer

  RAG IMPROVEMENTS:
    HyDE         → Generate hypothetical answer, then retrieve
    Re-ranking   → Use a cross-encoder to re-rank top-k results
    Query rewrite→ LLM rephrases query for better retrieval
    Multi-query  → Generate multiple query variants, merge results
    Parent chunk → Retrieve small chunk, return parent for context
    Metadata filter → Filter by date, category before similarity search

  WHEN TO USE RAG vs FINE-TUNING:
    RAG          → knowledge changes frequently, need citations
    Fine-tuning  → stable domain, need specific tone/format/style
    Both         → best of both worlds (expensive but powerful)
""")
