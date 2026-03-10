"""
=============================================================
GENERATIVE AI FOUNDATIONS
Topic 24: Transformers & NLP — From Tokens to LLMs
=============================================================

Install (optional): pip install transformers tokenizers

WHY TRANSFORMERS?
------------------
"Attention Is All You Need" (Vaswani et al., 2017) introduced the
Transformer architecture, which replaced RNNs/LSTMs for nearly all
NLP tasks and is now the foundation of:
  • BERT, RoBERTa, DeBERTa — text understanding & embeddings
  • GPT-2, GPT-4, Claude, Gemini — text generation
  • Whisper — speech recognition
  • DALL-E, Stable Diffusion (vision Transformer)
  • AlphaFold 2 — protein structure prediction

COVERED:
  1. Text preprocessing & tokenization
  2. Word embeddings concept (Word2Vec-like with NumPy)
  3. Attention mechanism — the math
  4. Transformer architecture concepts
  5. BERT vs GPT — understanding vs generation
  6. HuggingFace pipeline API
  7. Essential vocabulary for GenAI
"""

import numpy as np


# ─────────────────────────────────────────────
# 1. TEXT PREPROCESSING & TOKENIZATION
# ─────────────────────────────────────────────

print("=" * 55)
print("1. TEXT PREPROCESSING & TOKENIZATION")
print("=" * 55)

# Raw text processing: split, lower, remove punctuation
import re

def naive_tokenize(text: str) -> list:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return text.split()

text = "Hello! Transformers are amazing, aren't they?"
tokens = naive_tokenize(text)
print(f"Input  : {text}")
print(f"Tokens : {tokens}")

# Build a vocabulary
corpus = [
    "the cat sat on the mat",
    "the dog sat on the rug",
    "cats and dogs are pets",
    "the mat and the rug looked similar",
]
all_words = set()
for sentence in corpus:
    all_words.update(naive_tokenize(sentence))

vocab      = sorted(all_words)
word2idx   = {w: i for i, w in enumerate(vocab)}
idx2word   = {i: w for w, i in word2idx.items()}
vocab_size = len(vocab)

print(f"\nVocabulary ({vocab_size} words): {vocab}")
print(f"'cat' → index {word2idx['cat']}")
print(f"index {word2idx['mat']} → '{idx2word[word2idx['mat']]}'")

# Subword tokenization (BPE concept — used by GPT)
print("""
  SUBWORD TOKENIZATION (used in real LLMs):
    "playing" → ["play", "##ing"]      (WordPiece — BERT)
    "playing" → ["play", "ing"]        (BPE — GPT)
    "unforeseen" → ["un", "fore", "seen"]

  WHY SUBWORD?
    • Fixed vocab of ~50,000 tokens covers any language
    • "unknown" tokens rare — even new words can be broken down
    • "chatGPT" → ["chat", "G", "PT"]

  TOKEN COUNTS (rough):
    1 token ≈ 4 characters ≈ ¾ of an English word
    1000 tokens ≈ 750 words ≈ 1-2 pages of text
""")

# Demonstrate using HuggingFace tokenizer if available
try:
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained("bert-base-uncased")
    sample = "The Transformer architecture changed NLP forever!"
    encoded = tok(sample)
    decoded_tokens = tok.convert_ids_to_tokens(encoded["input_ids"])
    print(f"  BERT tokens: {decoded_tokens}")
    print(f"  Token IDs  : {encoded['input_ids']}")
    print(f"  Attn mask  : {encoded['attention_mask']}")
except Exception:
    print("  (transformers not installed — showing example output)")
    print("  BERT tokens: ['[CLS]', 'the', 'transformer', 'architecture',")
    print("                'changed', 'nl', '##p', 'forever', '!', '[SEP]']")
    print("  Token IDs  : [101, 1996, 19081, 4645, 2904, 17953, 2361, ...]")


# ─────────────────────────────────────────────
# 2. WORD EMBEDDINGS (Dense Representations)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. WORD EMBEDDINGS")
print("=" * 55)

# An embedding is a dense vector representation of a word.
# Similar words have similar vectors → geometry encodes meaning.
# king - man + woman ≈ queen  (the famous Word2Vec analogy)

EMBEDDING_DIM = 4
rng = np.random.default_rng(42)

# Simulate learned embeddings (in reality, trained via Word2Vec/BERT)
embeddings = rng.standard_normal((vocab_size, EMBEDDING_DIM)).astype(np.float32)
# Normalise for cosine similarity comparison
norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
embeddings = embeddings / (norms + 1e-8)

def cosine_sim(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

cat_vec = embeddings[word2idx["cat"]]
dog_vec = embeddings[word2idx["dog"]]
mat_vec = embeddings[word2idx["mat"]]

print(f"'cat' embedding  : {cat_vec.round(3)}")
print(f"\nCosine similarity:")
print(f"  sim(cat, dog) = {cosine_sim(cat_vec, dog_vec):.3f}  (should be high — similar context)")
print(f"  sim(cat, mat) = {cosine_sim(cat_vec, mat_vec):.3f}  (should be lower   ← toy demo)")

# Embedding lookup table
class EmbeddingLayer:
    """Maps integer token IDs to dense vectors."""
    def __init__(self, vocab_size: int, dim: int, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.W = rng.standard_normal((vocab_size, dim)).astype(np.float32) * 0.01

    def forward(self, token_ids):
        return self.W[token_ids]   # row-index lookup — O(1) per token

emb_layer = EmbeddingLayer(vocab_size, EMBEDDING_DIM)
sentence_idx = [word2idx[w] for w in naive_tokenize("the cat sat on the mat")]
embedded = emb_layer.forward(np.array(sentence_idx))
print(f"\nSentence tokens : {sentence_idx}")
print(f"Embedded shape  : {embedded.shape}  (seq_len × embedding_dim)")


# ─────────────────────────────────────────────
# 3. SELF-ATTENTION — THE CORE MECHANISM
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. SELF-ATTENTION MECHANISM")
print("=" * 55)

# Self-attention lets each token "look at" all other tokens in the sequence.
# The result is a context-aware representation of each token.
#
# STEPS:
#   1. Project each token embedding into Q (query), K (key), V (value)
#   2. score = Q @ K.T / sqrt(d_k)   ← how relevant is each token to this one?
#   3. weights = softmax(score)       ← normalise to probabilities
#   4. output = weights @ V           ← weighted sum of values

def softmax2d(x, axis=-1):
    e = np.exp(x - x.max(axis=axis, keepdims=True))
    return e / e.sum(axis=axis, keepdims=True)

def scaled_dot_product_attention(Q, K, V, mask=None):
    """
    Q: (seq, d_k)
    K: (seq, d_k)
    V: (seq, d_v)
    Returns: (seq, d_v)
    """
    d_k = Q.shape[-1]
    scores = Q @ K.T / np.sqrt(d_k)      # (seq, seq)
    if mask is not None:
        scores = scores + mask            # -inf for masked positions
    weights = softmax2d(scores, axis=-1)  # (seq, seq) — attention weights
    return weights @ V, weights           # (seq, d_v), (seq, seq)

# Toy example: 4 tokens, d_model=8
np.random.seed(42)
seq_len, d_model, d_k = 4, 8, 4

X_seq = np.random.randn(seq_len, d_model).astype(np.float32)

# Learned projection matrices
W_Q = np.random.randn(d_model, d_k).astype(np.float32) * 0.1
W_K = np.random.randn(d_model, d_k).astype(np.float32) * 0.1
W_V = np.random.randn(d_model, d_k).astype(np.float32) * 0.1

Q = X_seq @ W_Q    # (4, 4)
K = X_seq @ W_K    # (4, 4)
V = X_seq @ W_V    # (4, 4)

output, attn_weights = scaled_dot_product_attention(Q, K, V)
print(f"Input  shape : {X_seq.shape}   (seq_len, d_model)")
print(f"Q/K/V  shape : {Q.shape}       (seq_len, d_k)")
print(f"Output shape : {output.shape}  (seq_len, d_k)")
print(f"\nAttention weights (row = query token, col = key token):")
print(attn_weights.round(3))
print("Each row sums to 1.0:", attn_weights.sum(axis=1).round(3))

# Causal mask — used in GPT to prevent attending to future tokens
causal_mask = np.triu(np.full((seq_len, seq_len), -1e9), k=1)
print(f"\nCausal mask (decoder/GPT):\n{causal_mask}")
_, causal_weights = scaled_dot_product_attention(Q, K, V, mask=causal_mask)
print(f"Causal attention weights:\n{causal_weights.round(3)}")
print("Upper triangle is 0 → future tokens invisible ✓")


# ─────────────────────────────────────────────
# 4. TRANSFORMER ARCHITECTURE CONCEPTS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. TRANSFORMER ARCHITECTURE")
print("=" * 55)

print("""
  ENCODER (BERT-style):
    Input tokens → Token Embedding + Positional Encoding
    → [Multi-Head Self-Attention → Add&Norm
       → Feed-Forward → Add&Norm] × N layers
    → Contextual token representations

  DECODER (GPT-style):
    Input tokens → Embedding + Positional Encoding
    → [Masked Self-Attention → Add&Norm
       → Feed-Forward → Add&Norm] × N layers
    → Logits over vocabulary → sample next token

  KEY COMPONENTS:
  ┌──────────────────────┬────────────────────────────────────────┐
  │ Component            │ Purpose                                │
  ├──────────────────────┼────────────────────────────────────────┤
  │ Token Embedding      │ integer → dense vector                 │
  │ Positional Encoding  │ inject sequence order info             │
  │ Multi-Head Attention │ H parallel attention → richer context  │
  │ Add & LayerNorm      │ residual connection + normalisation     │
  │ Feed-Forward (MLP)   │ per-position non-linear transformation  │
  │ Softmax + sampling   │ logits → probabilities → next token     │
  └──────────────────────┴────────────────────────────────────────┘

  POSITIONAL ENCODING (sinusoidal):
    PE(pos, 2i)   = sin(pos / 10000^(2i/d))
    PE(pos, 2i+1) = cos(pos / 10000^(2i/d))
    Allows the model to distinguish token at position 5 vs 50.
""")

# Positional encoding
def positional_encoding(seq_len: int, d_model: int) -> np.ndarray:
    PE = np.zeros((seq_len, d_model))
    pos = np.arange(seq_len)[:, np.newaxis]
    div = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
    PE[:, 0::2] = np.sin(pos * div)
    PE[:, 1::2] = np.cos(pos * div)
    return PE.astype(np.float32)

PE = positional_encoding(seq_len=5, d_model=8)
print(f"Positional encoding (5 tokens, d=8):\n{PE.round(3)}")


# ─────────────────────────────────────────────
# 5. BERT vs GPT — Understanding vs Generation
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. BERT vs GPT")
print("=" * 55)

print("""
             │ BERT                        │ GPT
  ───────────┼─────────────────────────────┼──────────────────────────────
  Direction  │ Bidirectional               │ Autoregressive (left→right)
  Attention  │ Full (sees all tokens)      │ Causal (only past tokens)
  Pretraining│ Masked LM + Next Sentence   │ Next token prediction
  Strength   │ Understanding, embeddings   │ Generation, open-ended text
  Fine-tune  │ classification, NER, QA     │ chat, summarization, code
  Examples   │ BERT, RoBERTa, DeBERTa      │ GPT-2/3/4, Claude, Gemini

  USE BERT/ENCODER WHEN YOU NEED:
    • sentence embeddings (semantic search, RAG)
    • text classification (sentiment, topic)
    • named entity recognition
    • question answering (extractive)

  USE GPT/DECODER WHEN YOU NEED:
    • open-ended generation (chat, story)
    • summarization
    • translation
    • code generation
    • instruction following
""")


# ─────────────────────────────────────────────
# 6. HUGGINGFACE PIPELINE API
# ─────────────────────────────────────────────

print("=" * 55)
print("6. HUGGINGFACE PIPELINE API")
print("=" * 55)

try:
    from transformers import pipeline

    # Sentiment analysis
    classifier = pipeline("sentiment-analysis",
                          model="distilbert-base-uncased-finetuned-sst-2-english")
    texts = ["I love this product!", "This is terrible.", "It's okay I guess."]
    results = classifier(texts)
    print("Sentiment analysis:")
    for t, r in zip(texts, results):
        print(f"  '{t}' → {r['label']} ({r['score']:.2f})")

    # Text generation (small model)
    from transformers import pipeline as hf_pipeline
    gen = hf_pipeline("text-generation", model="distilgpt2", max_new_tokens=30)
    out = gen("Transformers changed the world of AI by", do_sample=True, temperature=0.8)
    print(f"\nText generation:\n  {out[0]['generated_text']}")

except Exception as e:
    print(f"HuggingFace transformers not installed or no internet.")
    print(f"pip install transformers\n")
    print("  PIPELINE USAGE (pseudocode):")
    print("""
  from transformers import pipeline

  # 1-line inference for any task
  clf  = pipeline("sentiment-analysis")
  gen  = pipeline("text-generation",     model="gpt2")
  summ = pipeline("summarization",       model="facebook/bart-large-cnn")
  qa   = pipeline("question-answering",  model="deepset/roberta-base-squad2")
  emb  = pipeline("feature-extraction",  model="sentence-transformers/all-MiniLM-L6-v2")

  clf("I love this!")                              → [{'label': 'POSITIVE', ...}]
  gen("Once upon a time", max_new_tokens=50)       → [{'generated_text': ...}]
  summ("Long article text", max_length=130)        → [{'summary_text': ...}]
  qa(question="What is AI?", context="AI is ...")  → {'answer': 'AI', ...}
""")


# ─────────────────────────────────────────────
# 7. ESSENTIAL GENAI VOCABULARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. ESSENTIAL GENAI VOCABULARY")
print("=" * 55)

print("""
  TERM                │ MEANING
  ────────────────────┼──────────────────────────────────────────────────
  Token               │ smallest unit of text (~4 chars / ¾ word)
  Context window      │ max tokens model can "see" at once (e.g. 128k)
  Temperature (0-2)   │ 0=deterministic, 1=normal, 2=very random
  Top-p (nucleus)     │ sample from smallest set covering p of probability
  Top-k               │ sample from top-k most likely next tokens
  Embedding           │ dense vector representation of text/image/audio
  Latent space        │ high-dim space where embeddings live
  Fine-tuning         │ further training a pretrained model on new data
  LoRA / QLoRA        │ efficient fine-tuning (low-rank adapters)
  RLHF                │ Reinforcement Learning from Human Feedback
  Hallucination       │ model generates confident but false information
  Grounding           │ connecting model output to verified external facts
  RAG                 │ Retrieval Augmented Generation
  Prompt engineering  │ crafting inputs to get desired model outputs
  Few-shot            │ examples in the prompt to guide behaviour
  Chain-of-thought    │ "Let's think step by step" → better reasoning
  System prompt       │ persistent instructions given to the model
  Inference           │ running a model to get predictions (not training)
  Quantization        │ reduce model precision (float32→int8) for speed
  Context length      │ GPT-4: 128k, Claude: 200k, Gemini: 1M+ tokens
""")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("=" * 55)
print("SUMMARY")
print("=" * 55)
print("""
  TOKENIZATION:
    text → token IDs → embeddings → transformer layers

  SELF-ATTENTION (core):
    Q, K, V = X @ W_Q, X @ W_K, X @ W_V
    scores  = Q @ K.T / sqrt(d_k)
    weights = softmax(scores)          ← how much each token attends
    output  = weights @ V              ← context-aware representations

  BERT (encoder): sees all tokens → good for understanding/embeddings
  GPT  (decoder): causal mask   → good for text generation

  HUGGINGFACE:
    from transformers import pipeline
    pipe = pipeline("sentiment-analysis")
    pipe("text")  → result

  KEY NUMBERS (GPT-4 class models):
    ~1 trillion parameters, trained on ~13T tokens, 128K context window
    ~$0.01 per 1K tokens (API), inference: ~50 tok/s on A100 GPU
""")
