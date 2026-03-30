"""
06_evaluation_and_testing/01_prompt_evaluation_metrics.py
═══════════════════════════════════════════════════════════════════

WHAT: Compute ROUGE-1/2/L, exact-match, length ratio, and semantic
      similarity scores to measure prompt output quality.

WHY:  Gut-feel comparisons don't scale. Automated metrics let you
      evaluate hundreds of examples cheaply and run comparisons
      programmatically before deploying prompt changes.

WHEN: After writing or modifying a prompt, measure it against a
      reference data set (human-written "gold" answers).

PITFALLS:
  - ROUGE measures lexical overlap, NOT factual correctness.
  - Paraphrase answers score low on ROUGE even when correct.
  - Combine ≥ 2 metrics (lexical + semantic) for a fuller picture.
  - Semantic similarity requires sentence-transformers install.

Usage:
    python 01_prompt_evaluation_metrics.py
    python 01_prompt_evaluation_metrics.py --dry-run
"""

import sys
import os
import re
import math
import argparse
from dataclasses import dataclass, field
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response

try:
    from sentence_transformers import SentenceTransformer, util as st_util
    SEM_AVAILABLE = True
except ImportError:
    SEM_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# ROUGE implementation (no external dependencies)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    return re.findall(r'\w+', text.lower())


def _ngrams(tokens: list[str], n: int) -> Counter:
    return Counter(tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1))


def rouge_n(reference: str, hypothesis: str, n: int = 1) -> dict[str, float]:
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    ref_ng = _ngrams(ref_tokens, n)
    hyp_ng = _ngrams(hyp_tokens, n)

    match = sum((ref_ng & hyp_ng).values())
    recall    = match / sum(ref_ng.values()) if ref_ng else 0.0
    precision = match / sum(hyp_ng.values()) if hyp_ng else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def _lcs_length(a: list, b: list) -> int:
    m, n = len(a), len(b)
    prev = [0] * (n + 1)
    for _ in range(m):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            curr[j] = prev[j - 1] + 1 if a[_ ] == b[j - 1] else max(curr[j - 1], prev[j])
        prev = curr
    return prev[n]


def rouge_l(reference: str, hypothesis: str) -> dict[str, float]:
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    lcs = _lcs_length(ref_tokens, hyp_tokens)
    recall    = lcs / len(ref_tokens) if ref_tokens else 0.0
    precision = lcs / len(hyp_tokens) if hyp_tokens else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {"precision": precision, "recall": recall, "f1": f1}


def exact_match(reference: str, hypothesis: str) -> bool:
    return reference.strip().lower() == hypothesis.strip().lower()


def length_ratio(reference: str, hypothesis: str) -> float:
    ref_len = len(_tokenize(reference))
    hyp_len = len(_tokenize(hypothesis))
    return hyp_len / ref_len if ref_len else 0.0


def semantic_similarity(reference: str, hypothesis: str) -> float:
    """Cosine similarity of sentence embeddings (requires sentence-transformers)."""
    if not SEM_AVAILABLE:
        return -1.0
    model = SentenceTransformer("all-MiniLM-L6-v2")
    emb = model.encode([reference, hypothesis], normalize_embeddings=True)
    return float(emb[0] @ emb[1])


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class EvalResult:
    item_id: str
    question: str
    reference: str
    hypothesis: str
    rouge1_f1: float = 0.0
    rouge2_f1: float = 0.0
    rougel_f1: float = 0.0
    exact_match: bool = False
    length_ratio: float = 0.0
    semantic_sim: float = -1.0
    cost_usd: float = 0.0


def evaluate(item_id: str, question: str, reference: str, hypothesis: str,
             cost: float = 0.0) -> EvalResult:
    r = EvalResult(
        item_id=item_id,
        question=question,
        reference=reference,
        hypothesis=hypothesis,
        cost_usd=cost,
    )
    r.rouge1_f1  = rouge_n(reference, hypothesis, 1)["f1"]
    r.rouge2_f1  = rouge_n(reference, hypothesis, 2)["f1"]
    r.rougel_f1  = rouge_l(reference, hypothesis)["f1"]
    r.exact_match = exact_match(reference, hypothesis)
    r.length_ratio = length_ratio(reference, hypothesis)
    r.semantic_sim = semantic_similarity(reference, hypothesis)
    return r


# ─────────────────────────────────────────────────────────────────────────────
# Evaluation dataset (question, reference answer, prompt template)
# ─────────────────────────────────────────────────────────────────────────────

EVAL_DATASET = [
    {
        "id": "eval-001",
        "question": "What is the capital of France?",
        "reference": "Paris",
        "prompt": "Answer this geography question in one word: What is the capital of France?",
    },
    {
        "id": "eval-002",
        "question": "Name the three primary colors.",
        "reference": "The three primary colors are red, yellow, and blue.",
        "prompt": "Answer concisely: Name the three primary colors.",
    },
    {
        "id": "eval-003",
        "question": "What does HTTP stand for?",
        "reference": "HTTP stands for HyperText Transfer Protocol.",
        "prompt": "Answer in one sentence: What does HTTP stand for?",
    },
    {
        "id": "eval-004",
        "question": "Who wrote Romeo and Juliet?",
        "reference": "Romeo and Juliet was written by William Shakespeare.",
        "prompt": "Answer in one sentence: Who wrote Romeo and Juliet?",
    },
    {
        "id": "eval-005",
        "question": "What is the boiling point of water in Celsius?",
        "reference": "The boiling point of water is 100 degrees Celsius.",
        "prompt": "Answer in one sentence: What is the boiling point of water in Celsius?",
    },
]


def run_evaluation(client: LLMClient) -> list[EvalResult]:
    results = []
    for item in EVAL_DATASET:
        response = client.chat(
            messages=[{"role": "user", "content": item["prompt"]}],
            temperature=0.0,
            max_tokens=60,
        )
        hypothesis = response.content.strip() if not client.dry_run else item["reference"] + " (dry-run)"
        result = evaluate(
            item_id=item["id"],
            question=item["question"],
            reference=item["reference"],
            hypothesis=hypothesis,
            cost=response.cost_usd,
        )
        results.append(result)
    return results


def print_report(results: list[EvalResult]) -> None:
    total = len(results)
    avg_r1 = sum(r.rouge1_f1 for r in results) / total
    avg_r2 = sum(r.rouge2_f1 for r in results) / total
    avg_rl = sum(r.rougel_f1 for r in results) / total
    avg_lr = sum(r.length_ratio for r in results) / total
    exact  = sum(r.exact_match for r in results)
    avg_ss = (sum(r.semantic_sim for r in results if r.semantic_sim >= 0) /
              max(1, sum(1 for r in results if r.semantic_sim >= 0)))
    total_cost = sum(r.cost_usd for r in results)

    print("\n" + "─" * 72)
    print("  EVALUATION REPORT")
    print("─" * 72)
    header = f"  {'ID':<12} {'R-1':>6} {'R-2':>6} {'R-L':>6} {'Len':>5} {'Sem':>6} {'EM':>4}"
    print(header)
    print("  " + "─" * 68)
    for r in results:
        ss = f"{r.semantic_sim:.3f}" if r.semantic_sim >= 0 else "  n/a"
        print(
            f"  {r.item_id:<12} "
            f"{r.rouge1_f1:>6.3f} "
            f"{r.rouge2_f1:>6.3f} "
            f"{r.rougel_f1:>6.3f} "
            f"{r.length_ratio:>5.2f} "
            f"{ss:>6} "
            f"{'Y' if r.exact_match else 'N':>4}"
        )
    print("  " + "─" * 68)
    ss_str = f"{avg_ss:.3f}" if avg_ss >= 0 else "  n/a"
    print(f"  {'AVERAGE':<12} {avg_r1:>6.3f} {avg_r2:>6.3f} {avg_rl:>6.3f}"
          f" {avg_lr:>5.2f} {ss_str:>6} {exact}/{total:>2}")
    print("─" * 72)
    print(f"  Exact match: {exact}/{total} ({100*exact/total:.0f}%)")
    print(f"  ROUGE-1 F1 avg: {avg_r1:.3f}")
    print(f"  ROUGE-2 F1 avg: {avg_r2:.3f}")
    if avg_ss >= 0:
        print(f"  Semantic sim avg: {avg_ss:.3f}")
        print(f"  (sentence-transformers installed: {SEM_AVAILABLE})")
    else:
        print("  Semantic similarity: not available — pip install sentence-transformers")
    if total_cost > 0:
        print(f"  Total evaluation cost: ${total_cost:.5f}")
    print("─" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Evaluation Metrics")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 06 — Evaluation: ROUGE / Semantic Similarity Metrics")
    print("══════════════════════════════════════════════════════════════════════")
    print(f"  Dataset: {len(EVAL_DATASET)} examples")
    print(f"  Semantic similarity backend: {'sentence-transformers' if SEM_AVAILABLE else 'not available'}")

    results = run_evaluation(client)
    print_report(results)

    # Show an example output for illustration
    print("\n  EXAMPLE OUTPUT DETAIL")
    r = results[1]
    print(f"  Question:   {r.question}")
    print(f"  Reference:  {r.reference}")
    print(f"  Hypothesis: {r.hypothesis}")
    print(f"  ROUGE-1 F1: {r.rouge1_f1:.3f}  ROUGE-L F1: {r.rougel_f1:.3f}")

    print("\n✅ Evaluation metrics complete.\n")


if __name__ == "__main__":
    main()
