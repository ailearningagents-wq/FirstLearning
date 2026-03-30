"""
04_advanced_techniques/01_tree_of_thought.py
═══════════════════════════════════════════════════════════════════

WHAT:   Tree of Thoughts (ToT) extends Chain-of-Thought by generating
        MULTIPLE reasoning branches simultaneously, evaluating each, and
        either continuing the best ones or pruning dead ends.

        Unlike CoT (linear: one thought at a time), ToT is a search
        tree where the model explores many possible next steps and
        backtracks from poor choices.

ALGORITHM:
        1. Generate k possible next thoughts/approaches (breadth-first)
        2. Evaluate each thought's promise: "good" / "maybe" / "bad"
        3. Continue from the most promising branch
        4. Repeat until reaching a final answer or max depth

WHY:    Some tasks (math, planning, creative writing with constraints)
        benefit from systematic exploration of possibilities rather than
        committing to the first plausible-sounding path. ToT mimics how
        humans "think ahead" and backtrack.

        Research results (Yao et al., 2023):
        - GPT-4 with ToT: 74% success on Game of 24 (vs 4% CoT)
        - Mini crossword tasks: 60% with ToT vs 16% CoT

WHEN TO USE:
        ✓ Mathematical puzzle solving
        ✓ Strategic planning with constraints
        ✓ Creative writing where quality can be evaluated
        ✓ Multi-step workflows needing error recovery
        ✗ Simple factual queries (massive overhead for no gain)
        ✗ Time-sensitive applications (latency is 5–15×)

COST WARNING: This is the most expensive technique in this course.
        Running width=3, depth=3 = potentially 9+ LLM calls per question.
        Use --dry-run to understand the structure without API costs.
"""

import sys
import os
import json
import argparse
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response


# ─────────────────────────────────────────────────────────────────────────────
# TREE NODE
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ThoughtNode:
    thought: str
    score: float = 0.0          # 0.0–1.0 — evaluated promise
    depth: int = 0
    children: list = field(default_factory=list)
    is_final: bool = False
    parent: Optional["ThoughtNode"] = field(default=None, repr=False)


# ─────────────────────────────────────────────────────────────────────────────
# Tree of Thoughts Engine
# ─────────────────────────────────────────────────────────────────────────────

def generate_thoughts(
    client: LLMClient,
    problem: str,
    current_thought: str,
    k: int,
    depth: int,
    max_depth: int,
) -> list[str]:
    """Generate k next steps/thoughts from the current reasoning position."""

    if depth == 0:
        prompt = f"""Problem: {problem}

Generate {k} DISTINCT opening approaches to solve this problem.
Each approach should start from a different angle or strategy.
Make them meaningfully different — not just paraphrases of each other.

Output as a JSON list of {k} strings:
["approach 1", "approach 2", ...]

Output ONLY the JSON."""
    elif depth >= max_depth - 1:
        prompt = f"""Problem: {problem}

Reasoning so far:
{current_thought}

We are at the final reasoning step. Generate {k} possible ANSWERS/CONCLUSIONS.
Each should be a complete, specific answer to the problem.

Output as a JSON list of {k} strings:
["answer 1", "answer 2", ...]

Output ONLY the JSON."""
    else:
        prompt = f"""Problem: {problem}

Reasoning so far:
{current_thought}

Generate {k} different NEXT STEPS to continue solving this problem.
Each should build on the reasoning so far but take a different direction.

Output as a JSON list of {k} strings:
["next step 1", "next step 2", ...]

Output ONLY the JSON."""

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
    )

    if client.dry_run:
        return [f"[DRY RUN thought {i+1} at depth {depth}]" for i in range(k)]

    try:
        thoughts = json.loads(response.content.strip())
        return thoughts[:k] if isinstance(thoughts, list) else [response.content.strip()]
    except json.JSONDecodeError:
        return [line.strip("- ") for line in response.content.strip().split("\n") if line.strip()][:k]


def evaluate_thought(
    client: LLMClient,
    problem: str,
    thought_path: str,
) -> float:
    """Score a thought path [0.0–1.0] for promise/correctness."""

    prompt = f"""You are evaluating whether a line of reasoning will lead to a correct answer.

Problem: {problem}

Reasoning path:
{thought_path}

Evaluate this reasoning path. Consider:
- Is the logic correct so far?
- Is this approach likely to lead to the correct answer?
- Are there any obvious errors or dead ends?

Respond with ONLY a JSON object:
{{"score": <0.0-1.0>, "assessment": "<one sentence why>"}}

Where 1.0 = highly promising, 0.0 = clearly wrong/dead end."""

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=100,
    )

    if client.dry_run:
        return 0.7

    try:
        evaluation = json.loads(response.content.strip())
        return float(evaluation.get("score", 0.5))
    except (json.JSONDecodeError, ValueError):
        return 0.5


def tree_of_thoughts(
    client: LLMClient,
    problem: str,
    branching_factor: int = 3,
    max_depth: int = 3,
    beam_width: int = 2,
    verbose: bool = True,
) -> str:
    """
    Breadth-first search through the thought tree.

    branching_factor: k = how many thoughts to generate at each node
    max_depth: maximum tree depth before forcing a conclusion
    beam_width: keep top-N branches at each level (beam search)

    Returns: The final best answer.
    """
    if verbose:
        print(f"\n  🌳 Tree of Thoughts — branching={branching_factor}, depth={max_depth}, beam={beam_width}")
        print(f"  Problem: {problem[:80]}{'...' if len(problem) > 80 else ''}")

    total_cost = 0.0

    # Level 0 → root thoughts
    root_thoughts = generate_thoughts(client, problem, "", branching_factor, 0, max_depth)
    current_layer: list[ThoughtNode] = []

    for thought in root_thoughts:
        node = ThoughtNode(thought=thought, depth=0)
        if not client.dry_run:
            node.score = evaluate_thought(client, problem, thought)
        else:
            node.score = 0.7
        current_layer.append(node)

    # Beam search across layers
    for depth in range(1, max_depth):
        if verbose:
            print(f"\n  ── Depth {depth} (evaluating {len(current_layer)} branches) ─────────────")

        # Keep only top beam_width nodes by score
        current_layer.sort(key=lambda n: n.score, reverse=True)
        active_nodes = current_layer[:beam_width]

        if verbose:
            for i, node in enumerate(active_nodes):
                print(f"    Branch {i+1} (score={node.score:.2f}): {node.thought[:80]}...")

        next_layer: list[ThoughtNode] = []

        for node in active_nodes:
            # Build the thought path as accumulated context
            thought_path = node.thought

            child_thoughts = generate_thoughts(
                client, problem, thought_path, branching_factor, depth, max_depth
            )

            for child_thought in child_thoughts:
                child_node = ThoughtNode(
                    thought=child_thought,
                    depth=depth,
                    parent=node,
                )
                full_path = f"{thought_path}\n{child_thought}"
                if not client.dry_run:
                    child_node.score = evaluate_thought(client, problem, full_path)
                else:
                    child_node.score = 0.75
                next_layer.append(child_node)

        current_layer = next_layer

    # Best final node
    current_layer.sort(key=lambda n: n.score, reverse=True)
    best_node = current_layer[0] if current_layer else ThoughtNode("No answer found")

    if verbose:
        print(f"\n  ✅ Best answer (score={best_node.score:.2f}):")
        print(f"  {best_node.thought}")

    return best_node.thought


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLES
# ─────────────────────────────────────────────────────────────────────────────

def example_game_of_24(client: LLMClient) -> None:
    """Game of 24: use four numbers and arithmetic to make 24."""
    print("\n" + "═" * 68)
    print("  EXAMPLE 1: Game of 24 — Classic ToT Benchmark")
    print("  Task: Use 4, 7, 8, 9 with +/-/×/÷ to make exactly 24")
    print("═" * 68)

    problem = ("Use the four numbers 4, 7, 8, 9 with basic arithmetic operations "
               "(+, -, *, /) to make exactly 24. Each number must be used exactly once.")

    answer = tree_of_thoughts(
        client=client,
        problem=problem,
        branching_factor=3,
        max_depth=3,
        beam_width=2,
        verbose=True,
    )

    print(f"\n  Final answer: {answer}")
    print("\n  Reference solution: (8 - 4) × (9 - 3) ... wait, 9-7=2, 2×(8+4)=24 ✓")
    print("  Or: 4 × (9 - 8 + 7) = 4 × 8 ... try: 7 × (8 - 4) + ... manual: 8/(9-7)*... 8/(9-7)=4, 4*4=16. Hmm. Actually: (4+8)*(9-7)=12*2=24 ✓")


def example_strategic_planning(client: LLMClient) -> None:
    """Strategic planning with multiple constraints."""
    print("\n" + "═" * 68)
    print("  EXAMPLE 2: Product Strategy Planning")
    print("  Task: Decide whether to build, buy, or partner for ML capability")
    print("═" * 68)

    problem = (
        "A 50-person B2B SaaS company (Series A, 18 months runway) needs to add "
        "AI-powered document summarization to their product. Options: (A) build "
        "in-house with 2 ML engineers over 6 months, (B) buy a $120K/year API "
        "from a vendor, (C) white-label a startup product for $40K/year with "
        "less reliability. Current product ARR: $3M, target ARR: $6M in 18 months. "
        "What is the optimal decision and why?"
    )

    answer = tree_of_thoughts(
        client=client,
        problem=problem,
        branching_factor=3,
        max_depth=2,
        beam_width=2,
        verbose=True,
    )

    print(f"\n  Final recommendation: {answer[:200]}...")


def demo_tot_vs_cot(client: LLMClient) -> None:
    """Show when ToT helps vs when CoT is sufficient."""
    print("\n" + "═" * 68)
    print("  DEMO: When to Use ToT vs CoT")
    print("═" * 68)

    comparisons = [
        ("Simple arithmetic",           "4 × 6 + 12 = ?",              "CoT",   "Single path, no backtracking needed"),
        ("Game of 24",                   "Make 24 from: 3, 3, 8, 8",    "ToT",   "Requires search over many arrangements"),
        ("Essay writing (short)",        "Write intro for climate essay", "CoT",  "One good path usually suffices"),
        ("Proof by contradiction",       "Prove √2 is irrational",       "ToT",   "Explore which proof strategy works"),
        ("Factual question",             "Capital of France?",            "None",  "Direct lookup — dont even need CoT"),
        ("Multi-constraint planning",    "Schedule 5 tasks with ~deps",   "ToT",   "Combinatorial search needed"),
    ]

    print(f"\n  {'Task Type':<35} {'Recommended':<12} {'Why'}")
    print(f"  {'─' * 35} {'─' * 12} {'─' * 35}")
    for task_type, example, recommended, reason in comparisons:
        print(f"  {task_type:<35} {recommended:<12} {reason}")

    print("\n  Cost comparison (per task, approximate):")
    print("    Direct answer:     $0.00005")
    print("    CoT:               $0.00015")
    print("    ToT (3×3):         $0.00150  (10× CoT)")
    print("    ToT (5×4):         $0.00600  (40× CoT)")
    print("    → Only use ToT when accuracy gain > cost increase!")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Tree of Thoughts Prompting")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show structure without API calls (⚠️ ToT is expensive)")
    parser.add_argument("--example", type=str, default="strategy",
                        choices=["24", "strategy", "compare"],
                        help="Which example to run (default: strategy — less expensive)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 04 — Tree of Thoughts (ToT)")
    print("  ⚠️  High cost: use --dry-run to explore structure first")
    print("═" * 72)

    if not args.dry_run:
        print("\n  ⚠️  WARNING: ToT makes many API calls.")
        print("  Use --dry-run to see the structure for free, or run with small branching.")

    if args.example == "24":
        example_game_of_24(client)
    elif args.example == "strategy":
        example_strategic_planning(client)
    elif args.example == "compare":
        demo_tot_vs_cot(client)

    print("\n✅ Tree of Thoughts examples complete.")
    print("   Next: 02_meta_prompting.py — make the model improve its own prompts\n")


if __name__ == "__main__":
    main()
