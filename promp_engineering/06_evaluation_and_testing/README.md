# Module 06 — Evaluation and Testing

> "You can't improve what you don't measure." — testing your prompts rigorously is what separates amateur prompt engineers from professionals.

## Learning Objectives

After completing this module you will be able to:

- Define quantitative metrics (ROUGE, semantic similarity, exact-match) to score prompt outputs
- Design and run A/B tests to compare competing prompts on a labelled dataset
- Build adversarial test suites that probe robustness and edge-case failure modes
- Maintain a "golden set" for regression testing across prompt versions
- Instrument prompts with structured logging and an observability dashboard

---

## Why Evaluation Matters

| Pain Point | Without Evaluation | With Evaluation |
|---|---|---|
| "Is this prompt better?" | Vibes / gut feeling | Measurable win rate |
| "Did my change break anything?" | Hope it's fine | Automated regression suite |
| "Why is this costing so much?" | Surprise invoice | Per-prompt cost dashboard |
| "The LLM contradicts itself" | Hard to catch | Consistency score |
| "Which model should I use?" | Benchmarks from papers | Your own task-specific score |

---

## Files in This Module

| File | Topic | Cost (gpt-4o-mini) |
|---|---|---|
| `01_prompt_evaluation_metrics.py` | ROUGE, exact-match, semantic similarity scoring | ~$0.003 |
| `02_ab_testing_prompts.py` | Statistical A/B test of two prompt variants | ~$0.01 |
| `03_adversarial_testing.py` | Jailbreak attempts, edge cases, robustness probes | ~$0.005 |
| `04_regression_testing.py` | Golden dataset, version comparison, diff reports | ~$0.006 |
| `05_logging_and_observability.py` | PromptRecord logging, cost dashboard, export | < $0.001 |

---

## Key Concepts

### ROUGE Metrics
- **ROUGE-1**: Overlap of unigrams (single words) between reference and generated text
- **ROUGE-2**: Overlap of bigrams (word pairs)
- **ROUGE-L**: Longest Common Subsequence — respects word order

### Semantic Similarity
- **Cosine similarity** of sentence embeddings captures *meaning* better than ROUGE
- Useful when paraphrase answers are acceptable ("great" vs "excellent" should score well)

### A/B Testing
- Use the same fixed test set for both variants to remove confounding variables
- Report mean ± std, a *t*-test *p*-value, and minimum detectable effect size
- Run at least 30–50 examples for statistical significance

### Adversarial Testing
Systematically probe failure modes:
1. **Prompt injection** — user tries to override system instructions
2. **Jail-breaking** — "pretend you are DAN…" style bypasses
3. **Edge inputs** — empty string, Unicode, extreme length
4. **Hallucination triggers** — questions where the model tends to confabulate

### Regression Testing
- Use a *golden set*: (input, expected_output, expected_properties) tuples frozen once
- Run before and after every prompt change
- Fail if: score drops > threshold on any metric

---

## Quick Start

```bash
# Run all evaluations in dry-run (no API cost) to inspect the framework
python 01_prompt_evaluation_metrics.py  --dry-run
python 02_ab_testing_prompts.py         --dry-run
python 03_adversarial_testing.py        --dry-run
python 04_regression_testing.py         --dry-run
python 05_logging_and_observability.py  --dry-run
```

---

## Tips

- **Prefer automatic evaluation on large sets** over manual on small sets
- **Always version your prompts** before changing them (even as a comment)
- Treat a **failing regression test** like a failing unit test — do not merge until fixed
- **Semantic similarity ≠ factual accuracy** — combine with factual probes for high-stakes domains
