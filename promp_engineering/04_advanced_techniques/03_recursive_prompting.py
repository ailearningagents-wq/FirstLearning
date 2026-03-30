"""
04_advanced_techniques/03_recursive_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   Recursive Prompting decomposes a large, complex task into smaller
        subtasks — potentially through multiple levels — solves each, then
        assembles the pieces into a final result.

        Unlike a fixed Prompt Chain, the decomposition can be:
        - Determined DYNAMICALLY by the model (it chooses how to split)
        - RECURSIVE (subtasks can themselves be decomposed)
        - Used with a MERGE step that synthesizes sub-results

PATTERNS:
        1. Divide-and-Conquer
           task → [LLM: split into N subtasks] → [solve each] → [merge]

        2. Hierarchical Analysis (Fixed Depth)
           document → [section summaries] → [chapter summaries] → [book summary]

        3. Recursive Tree (Dynamic Depth)
           problem → [LLM: is this atomic?]
             - YES → solve directly
             - NO  → decompose → recurse on each → merge

WHEN TO USE:
        ✓ Long-form content generation (reports, analyses, books)
        ✓ Complex analytical tasks with natural sub-components
        ✓ Code generation for large modules (function by function)
        ✓ Any task where the correct decomposition isn't obvious
        ✗ Simple single-step tasks
        ✗ Tasks with no clear sub-structure

COMPARED TO PROMPT CHAINING:
        Chains: fixed sequence, steps defined by programmer
        Recursion: dynamic splitting decided by the model; handles arbitrary depth
"""

import sys
import os
import json
import argparse
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 1: Dynamic Decomposition (Model decides how to split)
# ─────────────────────────────────────────────────────────────────────────────

def decompose_task(client: LLMClient, task: str, context: str = "") -> list[str]:
    """Ask the model to break a task into independently-solvable subtasks."""
    prompt = f"""You are a task decomposition expert.

Break the following task into 3-5 independent subtasks that can each be 
completed separately and then combined into a complete solution.

Task: {task}
{f"Context: {context}" if context else ""}

Requirements:
- Each subtask must be self-contained and independently completable
- Subtasks should NOT overlap in scope
- Together they must cover the entire original task
- Order them in the sequence they should be completed

Output ONLY a JSON array of subtask strings:
["subtask 1 description", "subtask 2 description", ...]"""

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=300,
    )

    if client.dry_run:
        return [
            f"[DRY RUN] Subtask 1 of '{task[:40]}...'",
            f"[DRY RUN] Subtask 2 of '{task[:40]}...'",
            f"[DRY RUN] Subtask 3 of '{task[:40]}...'",
        ]

    try:
        return json.loads(response.content.strip())
    except json.JSONDecodeError:
        lines = [l.strip("- ") for l in response.content.split("\n") if l.strip()]
        return lines[:5]


def solve_subtask(client: LLMClient, subtask: str, parent_task: str, context: str = "") -> str:
    """Solve a single atomic subtask."""
    prompt = f"""You are completing one part of a larger task.

LARGER TASK: {parent_task}
YOUR SUBTASK: {subtask}
{f"CONTEXT: {context}" if context else ""}

Focus ONLY on your subtask. Be thorough and specific.
Your output will be combined with outputs from other subtasks."""

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=500,
    )

    if client.dry_run:
        return f"[DRY RUN solution for: {subtask[:50]}]"

    return response.content.strip()


def merge_results(
    client: LLMClient,
    original_task: str,
    subtask_results: list[dict],
) -> str:
    """Merge subtask outputs into a coherent final result."""
    results_text = "\n\n".join(
        f"### Subtask {i+1}: {item['subtask']}\n{item['result']}"
        for i, item in enumerate(subtask_results)
    )

    prompt = f"""You are synthesizing multiple partial results into a complete solution.

ORIGINAL TASK: {original_task}

SUBTASK RESULTS:
{results_text}

Synthesize these into a coherent, complete response that:
- Flows naturally (not a list of disconnected parts)
- Eliminates redundancy
- Preserves all unique insights from each subtask
- Has a logical structure appropriate for the task type"""

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800,
    )

    if client.dry_run:
        return "[DRY RUN — merged result would appear here]"

    return response.content.strip()


def recursive_solve(
    client: LLMClient,
    task: str,
    depth: int = 0,
    max_depth: int = 2,
    verbose: bool = True,
    indent: str = "",
) -> str:
    """
    Recursively decompose and solve a task.
    - Depth 0: Full task
    - Depth 1: Subtasks
    - Depth 2: Sub-subtasks (if still complex)
    """
    prefix = indent + "  "

    if verbose:
        print(f"\n{indent}🔍 Task (depth={depth}): {task[:80]}{'...' if len(task) > 80 else ''}")

    if depth >= max_depth:
        if verbose:
            print(f"{indent}  → Max depth reached. Solving directly.")
        return solve_subtask(client, task, task)

    subtasks = decompose_task(client, task)
    if verbose:
        print(f"{indent}  📋 Decomposed into {len(subtasks)} subtasks:")
        for i, st in enumerate(subtasks, 1):
            print(f"{indent}    {i}. {st[:70]}")

    subtask_results = []
    for subtask in subtasks:
        result = recursive_solve(
            client=client,
            task=subtask,
            depth=depth + 1,
            max_depth=max_depth,
            verbose=verbose,
            indent=prefix,
        )
        subtask_results.append({"subtask": subtask, "result": result})

    if verbose:
        print(f"\n{indent}🔗 Merging {len(subtask_results)} subtask results...")

    return merge_results(client, task, subtask_results)


# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 2: Hierarchical Document Analysis (Fixed Levels)
# ─────────────────────────────────────────────────────────────────────────────

TECHNICAL_SPEC = {
    "title": "API Gateway Design Specification v2.0",
    "sections": {
        "Authentication": """
            The gateway will support three authentication methods:
            1. API Keys (simple header-based, for server-to-server)
            2. OAuth 2.0 / OIDC (for user-facing applications)
            3. mTLS (for high-security internal services)
            
            Token validation will be handled by a dedicated Auth Service.
            JWT tokens expire after 1 hour; refresh tokens after 30 days.
            Rate limiting: 1000 req/min per API key by default.
        """,
        "Rate Limiting": """
            Token bucket algorithm per client (API key or OAuth client_id).
            Tiers: Free (100 req/min), Pro (1000 req/min), Enterprise (custom).
            Headers returned: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset.
            429 responses include Retry-After header.
            Redis cluster used for distributed rate limit state.
        """,
        "Routing & Load Balancing": """
            Routes configured via YAML; hot-reload without restart.
            Strategies: round-robin (default), least-connections, IP hash.
            Health checks every 10 seconds; unhealthy backends removed in 30s.
            Circuit breaker: opens after 5 failures in 60s, closes after 1 success.
            Canary releases supported via weighted routing (e.g., 95% stable, 5% canary).
        """,
        "Observability": """
            Structured JSON logs to stdout (12-factor app).
            Metrics: Prometheus scrape endpoint at /metrics.
            Tracing: OpenTelemetry with Jaeger backend.
            SLO targets: 99.9% uptime, p99 latency < 200ms.
            Alerting: PagerDuty integration for P0/P1 incidents.
        """,
    }
}


def hierarchical_analysis(client: LLMClient, spec: dict) -> None:
    """Demonstrate hierarchical recursive summarization of a technical spec."""

    print("\n" + "═" * 68)
    print("  EXAMPLE 2: Hierarchical Analysis — API Spec Review")
    print(f"  Document: {spec['title']}")
    print("═" * 68)

    # Level 1: Summarize each section
    section_summaries = {}
    total_cost = 0.0

    print("\n  ── Level 1: Section Summaries ──────────────────────────────────")
    for section_name, section_content in spec["sections"].items():
        print(f"\n  Summarizing: {section_name}")
        response = client.chat(
            messages=[{"role": "user", "content": (
                f"Summarize the following technical specification section in exactly 2-3 bullet points.\n"
                f"Each bullet should capture a key technical decision or constraint.\n\n"
                f"Section: {section_name}\n{section_content}"
            )}],
            temperature=0.1,
            max_tokens=150,
        )

        if client.dry_run:
            section_summaries[section_name] = "[DRY RUN]"
            print("    [DRY RUN]")
            continue

        section_summaries[section_name] = response.content.strip()
        total_cost += response.cost_usd
        for line in response.content.strip().split("\n")[:3]:
            print(f"    {line}")

    if client.dry_run:
        return

    # Level 2: Synthesize all section summaries
    print("\n  ── Level 2: Document-Level Synthesis ───────────────────────────")
    all_summaries = "\n\n".join(
        f"**{name}:**\n{summary}" for name, summary in section_summaries.items()
    )

    synthesis_response = client.chat(
        messages=[{"role": "user", "content": (
            f"You are a senior architect reviewing a gateway specification.\n\n"
            f"Section summaries:\n{all_summaries}\n\n"
            f"Provide a 150-word executive summary covering:\n"
            f"1. What is being built (1 sentence)\n"
            f"2. Key architectural decisions (3 bullet points)\n"
            f"3. Main risks or open questions (2 bullet points)"
        )}],
        temperature=0.2,
        max_tokens=300,
    )
    total_cost += synthesis_response.cost_usd

    print(format_response(synthesis_response, title="Architecture Summary", show_stats=True))
    print(f"\n  💰 Hierarchical analysis total: ${total_cost:.6f}")


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE 3: Recursive Code Generation
# ─────────────────────────────────────────────────────────────────────────────

CODE_TASK = (
    "Write a Python module for a simple in-memory key-value store with: "
    "get, set, delete, TTL (time-to-live) expiry per key, and an LRU eviction policy. "
    "Include docstrings, type hints, and unit tests."
)

def example_recursive_code(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  EXAMPLE 3: Recursive Code Generation")
    print(f"  Task: {CODE_TASK[:80]}...")
    print("═" * 68)

    result = recursive_solve(
        client=client,
        task=CODE_TASK,
        depth=0,
        max_depth=1,  # One level of decomposition
        verbose=True,
    )

    if not client.dry_run:
        print("\n  ── Final Assembled Code (truncated) ────────────────────────")
        print(f"  {result[:600]}...")
        print(f"\n  Total lines: ~{result.count(chr(10))} lines of Python")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Recursive Prompting")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--example", type=str, default="hierarchical",
                        choices=["recursive", "hierarchical", "code", "all"],
                        help="'hierarchical' is cheapest; 'recursive' and 'code' make more API calls")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 04 — Recursive Prompting")
    print("  Patterns: Divide-and-Conquer | Hierarchical | Recursive Tree")
    print("═" * 72)

    if args.example in ("recursive", "all"):
        print("\n" + "═" * 68)
        print("  EXAMPLE 1: Recursive Decomposition — Market Analysis Report")
        print("═" * 68)
        result = recursive_solve(
            client=client,
            task="Write a comprehensive competitive analysis of the B2B SaaS CRM market for a startup entering the mid-market segment",
            depth=0,
            max_depth=1,
            verbose=True,
        )
        if not client.dry_run:
            print(f"\n  Result preview: {result[:300]}...")

    if args.example in ("hierarchical", "all"):
        hierarchical_analysis(client, TECHNICAL_SPEC)

    if args.example in ("code", "all"):
        example_recursive_code(client)

    print("\n✅ Recursive Prompting examples complete.")
    print("   Next: 04_constrained_generation.py — enforce strict output contracts\n")


if __name__ == "__main__":
    main()
