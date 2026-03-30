"""
04_advanced_techniques/06_automatic_prompt_optimization.py
═══════════════════════════════════════════════════════════════════

WHAT:   Automatic Prompt Optimization (APE) uses an algorithmic loop to
        find better prompts without manual trial-and-error.

        Steps:
        1. Provide a task + small labeled dataset (input/expected_output pairs)
        2. Generate N candidate prompts (via meta-prompting)
        3. Score each candidate on the labeled dataset
        4. Select top performers, generate variations (mutation)
        5. Repeat until convergence or budget exhausted

        Related systems:
        - APE (Automatic Prompt Engineer) — Large et al., 2022
        - DSPy — compile-time prompt optimization via gradient-free methods
        - PromptBreeder — evolutionary mutation of prompts
        - OPRO — optimization by prompting

WHY:    Manual prompt tuning is: slow, biased, inconsistent, and doesn't
        generalize. APE finds prompts that work across a diverse dataset.
        Even with 10–20 labeled examples, it can improve accuracy by 15–40%.

WHEN TO USE:
        ✓ Production tasks where you have labeled ground truth (10+ examples)
        ✓ When accuracy matters more than the one-time optimization cost
        ✓ Before deploying a prompt at high volume
        ✗ Exploratory/new tasks with no labeled data
        ✗ Tasks where prompts change per-request (no fixed structure to optimize)

COST WARNING:
        Optimization is expensive up-front (N prompts × M eval examples × iterations).
        Example: 5 candidates × 10 eval examples × 3 iterations = 150 LLM calls.
        For gpt-4o-mini: ~150 × $0.00008 = ~$0.012 one-time cost.
        Break-even: if 1,000 prod calls/day, even 5% accuracy gain is worth it.
"""

import sys
import os
import json
import argparse
import random
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens, estimate_cost


# ─────────────────────────────────────────────────────────────────────────────
# LABELED DATASET: Sentiment Classification Ground Truth
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Example:
    input_text: str
    expected_output: str


LABELED_DATASET = [
    Example("The product exceeded my expectations! Super fast shipping too.", "positive"),
    Example("Complete waste of money. Broke after 2 days.", "negative"),
    Example("Item arrived. Works as described.", "neutral"),
    Example("Absolutely love it! Would buy again.", "positive"),
    Example("Not great, not terrible. Does the job.", "neutral"),
    Example("Very disappointed. Nothing like the photos.", "negative"),
    Example("OK product for the price. Some minor issues.", "neutral"),
    Example("Best purchase of the year! Highly recommend.", "positive"),
    Example("Defective on arrival. Seller was unresponsive.", "negative"),
    Example("Does what it says on the box.", "neutral"),
    Example("Amazing quality, fast delivery, great seller!", "positive"),
    Example("Poor build quality, loud noise. Returning.", "negative"),
]

VALID_LABELS = {"positive", "negative", "neutral"}

# ─────────────────────────────────────────────────────────────────────────────
# Scoring Function
# ─────────────────────────────────────────────────────────────────────────────

def score_prompt(
    client: LLMClient,
    prompt_template: str,
    dataset: list[Example],
    verbose: bool = False,
) -> float:
    """
    Score a prompt against a labeled dataset.
    Returns accuracy [0.0, 1.0].
    The prompt should contain {INPUT} placeholder.
    """
    correct = 0
    for example in dataset:
        prompt = prompt_template.replace("{INPUT}", example.input_text)
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )

        if client.dry_run:
            # Simulate 70% accuracy for dry run
            correct += 1 if random.random() < 0.70 else 0
            continue

        prediction = response.content.strip().lower()
        # Normalize prediction to canonical label
        for label in VALID_LABELS:
            if label in prediction:
                prediction = label
                break

        if prediction == example.expected_output:
            correct += 1
        elif verbose:
            print(f"    ✗ Expected '{example.expected_output}', got '{prediction[:20]}' for: {example.input_text[:50]}")

    return correct / len(dataset)


# ─────────────────────────────────────────────────────────────────────────────
# Candidate Prompt Generator
# ─────────────────────────────────────────────────────────────────────────────

def generate_candidate_prompts(
    client: LLMClient,
    task_description: str,
    labels: list[str],
    n_candidates: int = 5,
    seed_examples: list[Example] | None = None,
) -> list[str]:
    """
    Generate N candidate prompt templates.
    Templates must contain {INPUT} placeholder.
    """
    examples_text = ""
    if seed_examples:
        examples_text = "\n".join(
            f'  Input: "{ex.input_text}" → Label: {ex.expected_output}'
            for ex in seed_examples[:3]
        )

    meta_prompt = f"""Generate {n_candidates} different prompt templates for this task.

TASK: {task_description}
VALID LABELS: {', '.join(labels)}
{f"EXAMPLE MAPPINGS:{chr(10)}{examples_text}" if examples_text else ""}

Each prompt template must:
1. Contain {{INPUT}} as a placeholder for the actual input text
2. Instruct the model to output ONLY one of the valid labels (nothing else)
3. Use a different strategy or wording approach
4. Be under 100 words

Good strategies to try:
- Simple instruction with label list
- Role-based (you are a specialist...)
- Few-shot with 1-2 examples
- Chain-of-thought variant (compressed)
- Strict JSON format request

Output ONLY a JSON array of {n_candidates} template strings:
["template 1", "template 2", ...]

Each template must contain {{{{INPUT}}}} (escaped braces for JSON)."""

    response = client.chat(
        messages=[{"role": "user", "content": meta_prompt}],
        temperature=0.7,
        max_tokens=800,
    )

    if client.dry_run:
        return [
            "Classify sentiment as positive, negative, or neutral. Reply with one word only.\n\nText: {INPUT}\n\nSentiment:",
            "You are a sentiment analyst. Classify the following customer review.\nReturn ONLY: positive, negative, or neutral.\n\nReview: {INPUT}",
            "Is this review positive, negative, or neutral? One word answer.\n{INPUT}",
        ]

    try:
        candidates = json.loads(response.content.strip())
        # Validate they contain {INPUT}
        valid = [c for c in candidates if "{INPUT}" in c]
        return valid[:n_candidates]
    except (json.JSONDecodeError, TypeError):
        # Fallback: extract line by line
        lines = [l.strip().strip('"').strip(',') for l in response.content.split("\n") if "{INPUT}" in l]
        return lines[:n_candidates]


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Mutation (for evolution step)
# ─────────────────────────────────────────────────────────────────────────────

def mutate_prompt(client: LLMClient, prompt: str, error_analysis: str) -> str:
    """Generate a mutated variant of a prompt based on observed errors."""
    mutation_prompt = f"""Improve this prompt based on the errors observed.

CURRENT PROMPT:
{prompt}

ERRORS OBSERVED:
{error_analysis}

Generate an improved version that fixes these issues.
Keep the {{INPUT}} placeholder. Output ONLY the improved prompt:"""

    response = client.chat(
        messages=[{"role": "user", "content": mutation_prompt}],
        temperature=0.5,
        max_tokens=200,
    )

    if client.dry_run:
        return prompt + "\nBe precise — output ONLY one of the exact labels."

    improved = response.content.strip()
    return improved if "{INPUT}" in improved else prompt


# ─────────────────────────────────────────────────────────────────────────────
# APE Main Loop
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromptCandidate:
    template: str
    score: float = 0.0
    generation: int = 0
    token_count: int = 0


def automatic_prompt_engineer(
    client: LLMClient,
    task_description: str,
    labels: list[str],
    dataset: list[Example],
    n_candidates: int = 5,
    n_generations: int = 3,
    top_k: int = 2,
    eval_sample_size: int | None = None,
    verbose: bool = True,
) -> tuple[str, list[dict]]:
    """
    Run the APE (Automatic Prompt Engineer) optimization loop.

    Args:
        task_description: What the prompt should accomplish
        labels:           Valid output labels
        dataset:          Labeled examples for evaluation
        n_candidates:     Prompts to generate per generation
        n_generations:    Number of optimization rounds
        top_k:            Keep top-k prompts between generations
        eval_sample_size: Number of examples to use for scoring (None = all)

    Returns: (best_prompt, optimization_history)
    """
    eval_data = dataset
    if eval_sample_size and eval_sample_size < len(dataset):
        eval_data = random.sample(dataset, eval_sample_size)

    if verbose:
        print(f"\n  APE Config: {n_candidates} candidates × {n_generations} generations")
        print(f"  Eval size: {len(eval_data)} examples, beam width: {top_k}")
        print(f"  Estimated API calls: ~{n_candidates * len(eval_data) * n_generations}")

    history = []
    best_candidates: list[PromptCandidate] = []

    # Generation 0: Initial candidates
    if verbose:
        print(f"\n  ── Generation 0: Bootstrapping {n_candidates} candidates ─────────")

    seed = dataset[:3]
    initial_templates = generate_candidate_prompts(
        client, task_description, labels, n_candidates, seed_examples=seed
    )

    candidates = [PromptCandidate(template=t, generation=0) for t in initial_templates]

    for gen in range(n_generations):
        if verbose:
            print(f"\n  ── Generation {gen + 1}/{n_generations}: Scoring {len(candidates)} prompts ────")

        # Score candidates
        for i, candidate in enumerate(candidates):
            candidate.score = score_prompt(client, candidate.template, eval_data, verbose=False)
            candidate.token_count = count_tokens(candidate.template, "gpt-4o-mini")
            if verbose:
                print(f"    Candidate {i+1}: score={candidate.score:.2%}, "
                      f"tokens={candidate.token_count}")

        # Sort and keep top-k
        candidates.sort(key=lambda c: c.score, reverse=True)
        top_candidates = candidates[:top_k]

        history.append({
            "generation": gen + 1,
            "best_score": top_candidates[0].score,
            "best_template_preview": top_candidates[0].template[:80],
            "all_scores": [c.score for c in candidates],
        })

        if verbose:
            print(f"\n  Top candidate (gen {gen+1}): score={top_candidates[0].score:.2%}")
            print(f"    Template: {top_candidates[0].template[:100]}...")

        if gen < n_generations - 1:
            # Mutate top candidates to create next generation
            if verbose:
                print(f"\n  Generating mutations from top-{top_k} candidates...")
            next_candidates = list(top_candidates)  # Keep the best

            for base_candidate in top_candidates:
                error_desc = "Output sometimes includes explanation text instead of just the label"
                mutated = mutate_prompt(client, base_candidate.template, error_desc)
                next_candidates.append(PromptCandidate(
                    template=mutated,
                    generation=gen + 1
                ))

            candidates = next_candidates

    # Final best prompt
    best = top_candidates[0] if top_candidates else PromptCandidate("[EMPTY]")
    return best.template, history


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE: Sentiment Classifier Optimization
# ─────────────────────────────────────────────────────────────────────────────

# Intentionally bad starting prompt to demonstrate improvement
BASELINE_PROMPT = "Tell me how you feel about this review, whether it's good or bad or in-between: {INPUT}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Automatic Prompt Optimization")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate without API calls")
    parser.add_argument("--generations", type=int, default=2,
                        help="Number of optimization generations (default: 2)")
    parser.add_argument("--candidates", type=int, default=3,
                        help="Number of candidate prompts per generation (default: 3)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 04 — Automatic Prompt Optimization (APE)")
    print("  Algorithm: Generate → Evaluate → Select → Mutate → Repeat")
    print("═" * 72)

    # Show dataset overview
    print("\n  Labeled dataset overview:")
    label_counts = {}
    for ex in LABELED_DATASET:
        label_counts[ex.expected_output] = label_counts.get(ex.expected_output, 0) + 1
    for label, count in sorted(label_counts.items()):
        print(f"    {label}: {count} examples")

    print(f"\n  Total examples: {len(LABELED_DATASET)}")

    # Score baseline first
    print(f"\n  ── Baseline Prompt Evaluation ────────────────────────────────")
    print(f"  Baseline: '{BASELINE_PROMPT[:70]}...'")

    baseline_score = score_prompt(client, BASELINE_PROMPT, LABELED_DATASET[:6])
    print(f"  Baseline accuracy: {baseline_score:.2%}")

    # Run APE
    print(f"\n  ── Running APE Optimization ──────────────────────────────────")
    best_prompt, history = automatic_prompt_engineer(
        client=client,
        task_description="Classify customer product reviews as: positive, negative, or neutral. Output ONLY the label.",
        labels=["positive", "negative", "neutral"],
        dataset=LABELED_DATASET,
        n_candidates=args.candidates,
        n_generations=args.generations,
        top_k=2,
        eval_sample_size=6,
        verbose=True,
    )

    # Final comparison
    print(f"\n  ── Results Summary ───────────────────────────────────────────")
    print(f"\n  Generation progression:")
    for gen_data in history:
        bar = "█" * int(gen_data['best_score'] * 20)
        print(f"    Gen {gen_data['generation']}: {gen_data['best_score']:.2%} {bar}")

    print(f"\n  Baseline:   {baseline_score:.2%}")
    if history:
        final_score = history[-1]['best_score']
        improvement = final_score - baseline_score
        print(f"  Optimized:  {final_score:.2%}  (Δ{improvement:+.2%})")

    print(f"\n  Best prompt found:")
    for line in best_prompt.split("\n"):
        print(f"    {line}")

    print("\n✅ Automatic Prompt Optimization complete.")
    print("   Module 04 complete! Next: 05_real_world_applications/\n")


if __name__ == "__main__":
    main()
