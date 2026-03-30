"""
04_advanced_techniques/02_meta_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   Meta-Prompting uses the LLM itself to GENERATE, CRITIQUE, or
        IMPROVE prompts, creating a self-referential feedback loop.

        Three forms:
        1. Prompt Generation: Describe a task → get an optimized prompt
        2. Prompt Critique:   Provide a prompt → get improvement suggestions
        3. Prompt Iteration:  Auto-run generate → evaluate → revise loop

WHY:    Writing good prompts is hard. Meta-prompting shortcuts the
        manual trial-and-error process by:
        - Leveraging the model's knowledge of what works
        - Getting expert-level formatting and structure suggestions
        - Creating specialized prompts for new domains quickly
        - Identifying failure modes you might not have considered

WHEN TO USE:
        ✓ You're starting a new domain-specific task (law, medicine, code)
        ✓ An existing prompt is producing inconsistent output
        ✓ You need to generate prompt variants for A/B testing
        ✓ Building a prompt library for a team
        ✗ One-off tasks where writing the prompt directly is faster
        ✗ Highly sensitive prompts where you need full manual control

RELATED TECHNIQUES:
        - APE (Automatic Prompt Engineer):  Generate + evaluate many prompts
        - DSPy:                              Optimize prompts via gradient descent
        - PromptBreeder:                     Evolutionary prompt optimization
        (see 06_automatic_prompt_optimization.py for APE implementation)
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, print_cost_estimate


# ─────────────────────────────────────────────────────────────────────────────
# 1. Prompt Generator from Task Description
# ─────────────────────────────────────────────────────────────────────────────

META_GENERATOR_SYSTEM = """You are an expert prompt engineer with deep knowledge of 
large language model behavior. Your specialty is writing production-quality prompts 
that are clear, specific, and produce reliable, well-formatted outputs.

When given a task description, you generate an optimized prompt that:
- Specifies the exact role/persona the model should adopt
- Defines the task with precise requirements
- Specifies the output format explicitly
- Includes handling for edge cases
- Has a clear termination condition (what "done" looks like)

You output ONLY the prompt itself — no explanation, no metadata."""


def generate_prompt_for_task(
    client: LLMClient,
    task_description: str,
    target_audience: str = "general",
    output_format: str = "not specified",
) -> str:
    """Use meta-prompting to generate an optimized prompt for a given task."""

    meta_request = f"""Create a production-ready prompt for the following task.

TASK DESCRIPTION: {task_description}
TARGET AUDIENCE FOR OUTPUTS: {target_audience}
DESIRED OUTPUT FORMAT: {output_format}

Requirements for the prompt you generate:
- Include a clear persona/role definition
- Use XML tags to separate prompt sections
- Be specific about what success looks like
- Handle ambiguous inputs gracefully
- Specify failure modes to avoid

Output ONLY the prompt text (no explanation, no markdown headers):"""

    response = client.chat(
        messages=[
            {"role": "system", "content": META_GENERATOR_SYSTEM},
            {"role": "user", "content": meta_request},
        ],
        temperature=0.3,
        max_tokens=600,
    )

    if client.dry_run:
        return "[DRY RUN — generated prompt would appear here]"

    return response.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 2. Prompt Critique
# ─────────────────────────────────────────────────────────────────────────────

CRITIQUE_SYSTEM = """You are a senior prompt engineer conducting a thorough review 
of prompts. You analyze prompts for clarity, specificity, potential failure modes, 
injection vulnerabilities, and output quality issues. You provide actionable, 
prioritized improvements."""


def critique_prompt(
    client: LLMClient,
    prompt_to_review: str,
    task_context: str = "",
) -> dict:
    """
    Critique a prompt and return structured improvement suggestions.
    Returns dict with: score, issues, improved_prompt.
    """

    critique_request = f"""Review the following prompt and provide structured analysis.
{f'Task context: {task_context}' if task_context else ''}

<prompt_to_review>
{prompt_to_review}
</prompt_to_review>

Analyze for:
1. Clarity issues (ambiguous instructions)
2. Missing specificity (vague requirements)
3. Output format problems (unclear structure requested)
4. Potential failure modes (what could go wrong)
5. Security issues (injection vulnerabilities)
6. Token efficiency (unnecessarily verbose)

Output a JSON object:
{{
  "overall_score": <1-10>,
  "grade": "<A/B/C/D/F>",
  "top_issues": [
    {{"priority": "high", "issue": "...", "fix": "..."}},
    {{"priority": "medium", "issue": "...", "fix": "..."}}
  ],
  "improved_prompt": "...",
  "estimated_improvement_pct": <10-50>
}}"""

    response = client.chat(
        messages=[
            {"role": "system", "content": CRITIQUE_SYSTEM},
            {"role": "user", "content": critique_request},
        ],
        temperature=0.2,
        max_tokens=800,
    )

    if client.dry_run:
        return {"overall_score": 7, "grade": "B", "top_issues": [], 
                "improved_prompt": "[DRY RUN]", "estimated_improvement_pct": 15}

    try:
        return json.loads(response.content.strip())
    except json.JSONDecodeError:
        return {"raw_critique": response.content, "overall_score": None}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Iterative Improvement Loop
# ─────────────────────────────────────────────────────────────────────────────

def iterative_prompt_improvement(
    client: LLMClient,
    initial_prompt: str,
    test_input: str,
    expected_output_description: str,
    iterations: int = 3,
    verbose: bool = True,
) -> tuple[str, list[dict]]:
    """
    Run an iterative improve → test → grade loop on a prompt.

    Returns: (best_prompt, iteration_history)

    Each iteration:
    1. Run the current prompt on test_input
    2. Grade the output against expected_output_description
    3. Use critique to get an improved version
    4. Repeat
    """

    current_prompt = initial_prompt
    history = []
    best_prompt = initial_prompt
    best_score = 0.0

    for i in range(iterations):
        if verbose:
            print(f"\n  ── Iteration {i+1}/{iterations} ───────────────────────────────────")

        # Step A: Run current prompt
        run_response = client.chat(
            messages=[
                {"role": "user", "content": f"{current_prompt}\n\nInput: {test_input}"}
            ],
            temperature=0.2,
            max_tokens=300,
        )

        if client.dry_run:
            print(f"  [DRY RUN iteration {i+1}]")
            history.append({"iteration": i+1, "score": 0.0, "prompt": current_prompt})
            continue

        output = run_response.content.strip()
        if verbose:
            print(f"  Output preview: {output[:120]}...")

        # Step B: Grade the output
        grade_prompt = f"""Grade this LLM output on a scale 0.0–1.0.

Expected: {expected_output_description}

Actual output:
{output}

Return ONLY a JSON: {{"score": <0.0-1.0>, "issues": ["issue 1", "issue 2"]}}"""

        grade_response = client.chat(
            messages=[{"role": "user", "content": grade_prompt}],
            temperature=0.0,
            max_tokens=150,
        )

        try:
            grade = json.loads(grade_response.content.strip())
            score = float(grade.get("score", 0.5))
            issues = grade.get("issues", [])
        except (json.JSONDecodeError, ValueError):
            score = 0.5
            issues = ["parsing failed"]

        if verbose:
            print(f"  Score: {score:.2f}")
            for issue in issues[:2]:
                print(f"  ⚠️  {issue}")

        history.append({
            "iteration": i + 1,
            "score": score,
            "prompt": current_prompt,
            "output_preview": output[:100],
        })

        if score > best_score:
            best_score = score
            best_prompt = current_prompt

        if score >= 0.9:
            if verbose:
                print("  ✅ Score ≥ 0.9 — stopping early")
            break

        # Step C: Critique and improve prompt based on issues
        if i < iterations - 1:
            improve_prompt = f"""Improve this prompt to fix the following issues:

Current prompt:
<prompt>
{current_prompt}
</prompt>

Issues found in the output:
{chr(10).join(f'- {issue}' for issue in issues)}

Expected output should be: {expected_output_description}

Output ONLY the improved prompt (no commentary):"""

            improve_response = client.chat(
                messages=[{"role": "user", "content": improve_prompt}],
                temperature=0.3,
                max_tokens=500,
            )
            current_prompt = improve_response.content.strip()

    if verbose and history:
        _sep = ' → '
        _scores = [f"{h['score']:.2f}" for h in history]
        print(f"\n  📈 Score progression: {_sep.join(_scores)}")
        print(f"  Best score achieved: {best_score:.2f}")

    return best_prompt, history


# ─────────────────────────────────────────────────────────────────────────────
# DEMO TASKS
# ─────────────────────────────────────────────────────────────────────────────

BAD_PROMPT = "Help me analyze this customer review and tell me useful things."

TASK_DESCRIPTIONS = [
    {
        "name": "Customer Review Analyzer",
        "description": "Extract structured insights from e-commerce customer reviews",
        "audience": "product managers and operations teams",
        "format": "JSON with: sentiment, rating_implied (1-5), mentioned_features (list), complaint (string or null), praise (string or null)",
    },
    {
        "name": "Code Security Auditor",
        "description": "Audit Python code snippets for OWASP Top 10 security vulnerabilities",
        "audience": "backend engineers doing code review",
        "format": "Markdown with sections: Summary, Vulnerabilities Found (table), Recommendations, Severity Score (1-10)",
    },
]

TEST_REVIEW = """
Received the wireless headphones yesterday. Sound quality is outstanding for the price—
deep bass and clear highs. However, the ear cushions are clearly low quality foam and after
3 hours my ears were sore. Also the Bluetooth kept dropping every 30 mins. Customer service
was fast when I emailed them, they're sending replacement ear cushions for free. I'd give 
the sound 5 stars, but overall the build quality lets it down.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Meta-Prompting Techniques")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--example", type=str, default="all",
                        choices=["generate", "critique", "iterate", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 04 — Meta-Prompting")
    print("  Let the model improve its own prompts")
    print("═" * 72)

    # ── Example 1: Generate prompts ────────────────────────────────────────
    if args.example in ("generate", "all"):
        print("\n" + "═" * 68)
        print("  EXAMPLE 1: Meta-Generate — Create Prompts from Descriptions")
        print("═" * 68)

        for task in TASK_DESCRIPTIONS:
            print(f"\n  Task: {task['name']}")
            generated = generate_prompt_for_task(
                client=client,
                task_description=task["description"],
                target_audience=task["audience"],
                output_format=task["format"],
            )
            print("\n  Generated Prompt:")
            for line in generated[:600].split("\n"):
                print(f"    {line}")
            if len(generated) > 600:
                print("    ... [truncated]")

    # ── Example 2: Critique existing prompt ───────────────────────────────
    if args.example in ("critique", "all"):
        print("\n" + "═" * 68)
        print("  EXAMPLE 2: Meta-Critique — Analyze a Weak Prompt")
        print(f"  Prompt: '{BAD_PROMPT}'")
        print("═" * 68)

        critique = critique_prompt(
            client=client,
            prompt_to_review=BAD_PROMPT,
            task_context="Product management team wants to analyze customer reviews at scale",
        )

        if not client.dry_run:
            print(f"\n  Score: {critique.get('overall_score')}/10  Grade: {critique.get('grade')}")
            print(f"  Estimated improvement if fixed: {critique.get('estimated_improvement_pct')}%")
            print("\n  Top Issues:")
            for issue in critique.get("top_issues", [])[:3]:
                print(f"    [{issue.get('priority','?').upper()}] {issue.get('issue','')}")
                print(f"    → Fix: {issue.get('fix','')[:80]}")
            print("\n  Improved Prompt (first 300 chars):")
            print(f"    {critique.get('improved_prompt','')[:300]}...")
        else:
            print("  [DRY RUN]")

    # ── Example 3: Iterative improvement ──────────────────────────────────
    if args.example in ("iterate", "all"):
        print("\n" + "═" * 68)
        print("  EXAMPLE 3: Iterative Improvement Loop")
        print("  Starting from the bad prompt, improve it 3 times")
        print("═" * 68)

        best, history = iterative_prompt_improvement(
            client=client,
            initial_prompt=BAD_PROMPT,
            test_input=TEST_REVIEW,
            expected_output_description=(
                "JSON with: sentiment (positive/negative/mixed), rating_implied (1-5 int), "
                "mentioned_features (list of strings), main_complaint (string or null), "
                "main_praise (string or null)"
            ),
            iterations=3,
            verbose=True,
        )

        if not client.dry_run:
            print(f"\n  Best prompt after iteration:")
            print(f"  {best[:300]}...")

    print("\n✅ Meta-Prompting examples complete.")
    print("   Next: 03_recursive_prompting.py — divide complex tasks recursively\n")


if __name__ == "__main__":
    main()
