"""
03_intermediate_techniques/03_react_prompting.py
═══════════════════════════════════════════════════════════════════

WHAT:   ReAct (Reason + Act) is a prompting framework where the model
        interleaves:
        - Thought: Reasoning about what to do next
        - Action: Calling a tool or taking a step
        - Observation: What the tool returned

        This loop continues until the model reaches a final answer.

WHY:    Pure reasoning (CoT) can hallucinate facts. Pure retrieval can't
        reason. ReAct combines both: the model REASONS about WHAT to look up,
        then ACTS to look it up, then incorporates the result into its reasoning.

ARCHITECTURE:
        while not solved:
            thought = model.think(context)
            action  = model.decide_action(thought)
            if action.type == "finish":
                return action.answer
            observation = tool_executor(action)
            context += thought + action + observation

WHEN TO USE:
        ✓ Tasks requiring real-time or private data (databases, APIs)
        ✓ Multi-step research or information gathering
        ✓ Workflows that conditionally call different tools
        ✗ Simple single-step tasks (overhead not worth it)
        ✗ Tasks with no external data needs

SIMULATED TOOLS (this file):
        We simulate tool outputs since we can't call real APIs in a lesson.
        Module 08 shows real tool integration via LangChain.

COMMON PITFALLS:
        - Infinite loops (model keeps calling tools without converging)
        - Model confuses Thought vs Action vs Observation sections
        - Observation parsing errors when tool output is unexpected
"""

import sys
import os
import json
import re
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATED TOOL SUITE
# ─────────────────────────────────────────────────────────────────────────────

# In a real system, these would call actual APIs, databases, search engines, etc.

def tool_search_web(query: str) -> str:
    """Simulated web search tool."""
    results = {
        "current bitcoin price": "Bitcoin (BTC) current price: $67,450 USD (as of March 14, 2024)",
        "OpenAI GPT-4o release date": "OpenAI GPT-4o was released on May 13, 2024",
        "python latest version": "Python 3.12.2 is the latest stable release (February 2024)",
        "S&P 500 today": "S&P 500 closed at 5,234.18 (+0.57%) on March 14, 2024",
    }
    for key, value in results.items():
        if key.lower() in query.lower():
            return value
    return f"Search results for '{query}': [3 relevant articles found — top result discusses recent developments]"


def tool_calculator(expression: str) -> str:
    """Safe mathematical calculator tool."""
    # Only allow safe mathematical operations
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: Only basic arithmetic operations allowed"
    try:
        result = eval(expression, {"__builtins__": {}})
        return f"Result: {result}"
    except Exception as e:
        return f"Calculation error: {e}"


def tool_lookup_database(query: str) -> str:
    """Simulated internal database lookup."""
    db = {
        "customer ACM-8821": json.dumps({
            "customer_id": "ACM-8821",
            "name": "Acme Corp",
            "plan": "Enterprise",
            "mrr": 4500,
            "since": "2021-03-15",
            "open_tickets": 2
        }),
        "product inventory SKU-F4X": json.dumps({
            "sku": "SKU-F4X",
            "product": "Premium LED Panel",
            "stock": 143,
            "warehouse": "Chicago",
            "reorder_point": 50
        }),
    }
    for key, value in db.items():
        if key in query.lower():
            return value
    return "No records found matching query"


def tool_send_email(to: str, subject: str, body: str) -> str:
    """Simulated email sending (dry-run only)."""
    return f"[SIMULATED] Email queued: to={to}, subject='{subject}', body_length={len(body)} chars"


TOOLS = {
    "search": {
        "fn": tool_search_web,
        "description": "Search the web for current information. Input: search query string.",
    },
    "calculator": {
        "fn": tool_calculator,
        "description": "Evaluate a mathematical expression. Input: arithmetic expression like '234 * 1.08'",
    },
    "database_lookup": {
        "fn": tool_lookup_database,
        "description": "Query internal database. Input: entity type + identifier, e.g. 'customer ACM-8821'",
    },
    "send_email": {
        "fn": lambda args: tool_send_email(**json.loads(args)),
        "description": "Send an email. Input: JSON with keys: to, subject, body",
    },
    "finish": {
        "fn": None,
        "description": "Return the final answer when you have enough information.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# ReAct System Prompt
# ─────────────────────────────────────────────────────────────────────────────

def build_react_system_prompt() -> str:
    tool_descriptions = "\n".join(
        f"  - {name}: {info['description']}"
        for name, info in TOOLS.items()
    )
    return f"""You are a helpful AI assistant that can use tools to answer questions.

AVAILABLE TOOLS:
{tool_descriptions}

RESPONSE FORMAT — You MUST use exactly this format for every response:
Thought: [your reasoning about what to do next]
Action: tool_name
Action Input: [input to the tool]

When you have the final answer:
Thought: [final reasoning]
Action: finish
Action Input: [your complete final answer]

RULES:
- Always start with a Thought before any Action
- Never skip an Observation before the next Thought
- Use the calculator for any arithmetic — don't do math in your head
- Use finish only when you have enough information to answer completely"""


# ─────────────────────────────────────────────────────────────────────────────
# ReAct Engine
# ─────────────────────────────────────────────────────────────────────────────

def react_agent(
    client: LLMClient,
    task: str,
    max_steps: int = 10,
    verbose: bool = True,
) -> str:
    """
    Run a ReAct agent loop until the task is complete or max_steps reached.

    Returns:
        The final answer string.
    """
    system = build_react_system_prompt()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"Task: {task}"},
    ]

    total_cost = 0.0

    for step in range(max_steps):
        if verbose:
            print(f"\n  {'─' * 60}")
            print(f"  Step {step + 1}")
            print(f"  {'─' * 60}")

        response = client.chat(
            messages=messages,
            temperature=0.1,
            max_tokens=400,
        )

        if client.dry_run:
            print(f"  [DRY RUN — step {step + 1}]")
            return "[DRY RUN — ReAct loop would execute here]"

        total_cost += response.cost_usd
        model_output = response.content.strip()

        if verbose:
            for line in model_output.split("\n"):
                print(f"  {line}")

        # Parse the model's response
        action_match = re.search(r"Action:\s*(.+)", model_output)
        input_match  = re.search(r"Action Input:\s*(.+)", model_output, re.DOTALL)

        if not action_match:
            if verbose:
                print("  ⚠️  No Action found — aborting loop")
            break

        action_name = action_match.group(1).strip().lower()
        action_input = input_match.group(1).strip() if input_match else ""

        # Final answer?
        if action_name == "finish":
            if verbose:
                print(f"\n  ✅ Task complete! Total cost: ${total_cost:.6f}")
            return action_input

        # Execute the tool
        if action_name not in TOOLS:
            observation = f"Error: Tool '{action_name}' not found. Available: {list(TOOLS.keys())}"
        else:
            try:
                observation = TOOLS[action_name]["fn"](action_input)
            except Exception as e:
                observation = f"Tool error: {e}"

        if verbose:
            print(f"\n  Observation: {observation}")

        # Add to conversation history
        messages.append({"role": "assistant", "content": model_output})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    return "Task did not complete within max_steps"


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE TASKS
# ─────────────────────────────────────────────────────────────────────────────

TASKS = [
    {
        "name": "Customer Health Score",
        "description": "Look up customer, calculate tenure, categorize health",
        "task": (
            "Look up customer ACM-8821 in the database. Calculate how many years "
            "they've been a customer (today is March 14, 2024). "
            "Then compose and send a health check email to account@acme.example.com "
            "summarizing their plan, MRR, and any open tickets."
        ),
    },
    {
        "name": "Market Research + Calculation",
        "description": "Search current data, then perform calculation",
        "task": (
            "Search for the current S&P 500 level. If I invested $50,000 when "
            "the S&P 500 was at 4,800, calculate my percentage return and "
            "current portfolio value."
        ),
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="ReAct Prompting with Tool Use")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--task", type=int, default=0,
                        choices=range(len(TASKS)),
                        help="Which task to run (0 or 1)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 03 — ReAct Prompting (Reason + Act)")
    print("  Pattern: Thought → Action → Observation → Thought → ...")
    print("═" * 72)

    # Show tool descriptions
    print("\n  Available Tools:")
    for name, info in TOOLS.items():
        print(f"    🔧 {name}: {info['description'][:60]}...")

    task_data = TASKS[args.task]
    print(f"\n  Task: {task_data['name']}")
    print(f"  Description: {task_data['description']}")
    print(f"  Goal: {task_data['task']}")

    answer = react_agent(
        client=client,
        task=task_data["task"],
        verbose=True,
    )

    print(f"\n  {'═' * 60}")
    print(f"  FINAL ANSWER:")
    print(f"  {answer}")
    print(f"  {'═' * 60}")

    print("\n✅ ReAct examples complete.")
    print("   Next: 04_generated_knowledge.py — generate facts before answering\n")


if __name__ == "__main__":
    main()
