"""
01_fundamentals/02_anatomy_of_a_prompt.py
═══════════════════════════════════════════════════════════════════

WHAT:   Break down every prompt into its four structural components:
        Instruction, Context, Input, and Output Format.
        Understanding this anatomy is the foundation for all advanced
        techniques in later modules.

WHY:    Prompts that "feel" good but produce bad results almost always
        have one of these components missing or vague. Naming the parts
        lets you systematically debug and improve any prompt.

WHEN TO USE:
        Every time you write a prompt — even simple ones. Mentally check:
        "Do I have a clear instruction? Enough context? The right input?
        The output format I actually need?"

COMMON PITFALLS:
        - Omitting output format → model picks whatever format it prefers
        - Vague instructions → model makes assumptions that may be wrong
        - No context → model uses its prior training distribution (may not match your domain)
        - Too much irrelevant context → dilutes the signal, wastes tokens
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import print_prompt_box, print_cost_estimate, count_tokens


# ─────────────────────────────────────────────────────────────────────────────
# THE FOUR PARTS OF A PROMPT
# ─────────────────────────────────────────────────────────────────────────────

ANATOMY = {
    "instruction": {
        "name": "Instruction",
        "symbol": "🎯",
        "definition": "The task directive — what you want the model to DO.",
        "examples": [
            "Summarize the following article",
            "Classify the sentiment as POSITIVE, NEGATIVE, or NEUTRAL",
            "Translate the following text to French",
            "Write a Python function that...",
            "Extract all named entities from...",
        ],
        "tips": [
            "Use action verbs: summarize, classify, extract, generate, rewrite",
            "Be specific about scope: 'in 3 bullet points', 'in one sentence'",
            "Avoid ambiguous verbs: 'describe' (how?), 'write about' (what format?)",
        ],
    },
    "context": {
        "name": "Context",
        "symbol": "📚",
        "definition": "Background information that shapes HOW the model should respond.",
        "examples": [
            "You are a senior data scientist reviewing code for production readiness.",
            "This is a customer support ticket from a user who has been waiting 5 days.",
            "The audience is non-technical C-suite executives.",
            "This analysis will be used in a legal brief — precision is critical.",
        ],
        "tips": [
            "Specify the persona/role when tone/expertise matters",
            "Provide domain-specific vocabulary or constraints",
            "Include information the model can't infer from the input alone",
            "Keep context relevant — irrelevant context reduces quality",
        ],
    },
    "input": {
        "name": "Input",
        "symbol": "📥",
        "definition": "The actual data the model should operate on.",
        "examples": [
            "The customer complaint text",
            "The code snippet to review",
            "The article to summarize",
            "The product description to translate",
        ],
        "tips": [
            "Use delimiters (```, ###, <text>) to clearly separate input from instructions",
            "Signal what type of data it is: 'Here is the Python code:', 'Customer email:'",
            "For long inputs, tell the model how long it is: 'The following 500-word article'",
        ],
    },
    "output_format": {
        "name": "Output Format",
        "symbol": "📤",
        "definition": "The exact shape you want the response to take.",
        "examples": [
            "Respond in JSON with keys: sentiment, confidence, reasoning",
            "Use a numbered list",
            "Write exactly 3 sentences",
            "Format as a Markdown table with columns: Issue, Severity, Recommendation",
        ],
        "tips": [
            "Be explicit — the model will default to plain prose if you don't specify",
            "Show an example output structure when possible",
            "Specify length constraints: '< 50 words', '3-5 bullet points'",
            "For code, specify language, style guide, and type hints",
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# EXAMPLE: Building a prompt incrementally
# ─────────────────────────────────────────────────────────────────────────────

# The task: Extract action items from a customer support email

EMAIL = """
From: Sarah Chen <sarah.chen@globex.com>
Subject: Critical: Integration failing in production since yesterday

Hi team,

Our payment integration has been completely down since Tuesday 2pm EST.
We're losing approx $12,000/hour in revenue. Our CTO, David Park, has been 
escalating this internally. 

We need:
1. A hotfix deployed by EOD today
2. A post-mortem report by next Monday
3. A dedicated Slack channel for real-time updates

We've been customers for 3 years and this is unacceptable.

Regards,
Sarah Chen
VP of Engineering, Globex Corp
"""

# ── Version 1: Just an instruction (bad) ──────────────────────────────────
PROMPT_V1 = f"""Extract action items from this email.

{EMAIL}"""

# ── Version 2: Instruction + context ──────────────────────────────────────
PROMPT_V2 = f"""Extract action items from this email.
You are a technical account manager at a B2B SaaS company.

{EMAIL}"""

# ── Version 3: Instruction + context + output format (good) ───────────────
PROMPT_V3 = f"""Extract all action items from the customer email below.

You are a technical account manager at a B2B SaaS company.
Prioritize items by urgency: CRITICAL > HIGH > MEDIUM > LOW.

Format your response as JSON with this structure:
{{
  "action_items": [
    {{
      "item": "<action description>",
      "owner": "<internal team: Engineering/Support/Management>",
      "deadline": "<specific deadline or 'ASAP'>",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW"
    }}
  ],
  "customer_sentiment": "FRUSTRATED|NEUTRAL|SATISFIED",
  "escalation_needed": true|false
}}

Customer Email:
```
{EMAIL}
```"""

# ── Version 4: Full anatomy — instruction + context + input + output format ─
PROMPT_V4 = f"""You are a senior technical account manager at Acme SaaS Inc.
Your role is to triage incoming customer escalations and assign them to the 
appropriate internal teams with clear SLAs.

# Task
Extract all action items from the customer escalation email below.
Analyze urgency based on: revenue impact, time since issue started, and customer tier.

# Customer Context
- Account tier: Enterprise (3-year customer)
- Revenue impact mentioned: $12,000/hour
- Issue age: ~24 hours

# Output Format
Respond with valid JSON only. No markdown, no preamble.
{{
  "escalation_id": "<YYYY-MM-DD-XXXX format>",
  "customer": {{
    "name": "<full name>",
    "title": "<job title>",
    "company": "<company name>"
  }},
  "issue_summary": "<one sentence>",
  "revenue_impact_hourly_usd": <number or null>,
  "action_items": [
    {{
      "id": 1,
      "action": "<specific, actionable description>",
      "owner_team": "Engineering|Support|Management|Legal",
      "deadline": "<ISO datetime or 'EOD today' or 'ASAP'>",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "sla_hours": <number>
    }}
  ],
  "customer_sentiment": "CRITICAL|FRUSTRATED|NEUTRAL|SATISFIED",
  "recommended_response_tone": "<brief guidance for the responder>"
}}

# Customer Email
```
{EMAIL}
```"""


# ─────────────────────────────────────────────────────────────────────────────
# ANATOMY CHECKER — Utility to analyze any prompt
# ─────────────────────────────────────────────────────────────────────────────

def analyze_prompt_anatomy(prompt: str) -> dict:
    """
    Heuristically check which anatomical parts are present in a prompt.
    
    This is a teaching tool. Real detection would use an LLM itself.
    
    Args:
        prompt: The prompt text to analyze.
    
    Returns:
        Dict with presence scores for each anatomical component.
    """
    analysis = {}
    text_lower = prompt.lower()

    # Instruction heuristics
    action_verbs = ["summarize", "extract", "classify", "translate", "write",
                    "analyze", "generate", "list", "explain", "compare",
                    "identify", "review", "format", "convert"]
    analysis["instruction"] = {
        "present": any(v in text_lower for v in action_verbs),
        "hint": "Look for a clear action verb near the start",
    }

    # Context heuristics
    context_signals = ["you are", "you're", "as a", "acting as", "your role",
                       "context:", "background:", "audience:"]
    analysis["context"] = {
        "present": any(s in text_lower for s in context_signals),
        "hint": "Add 'You are a [role]...' to provide context",
    }

    # Input/data heuristics
    input_signals = ["```", "###", "---", "<", ">"
                     "the following", "here is", "below"]
    analysis["input"] = {
        "present": any(s in text_lower for s in input_signals) or len(prompt) > 200,
        "hint": "Delimit your input data with ``` or ### to separate it from instructions",
    }

    # Output format heuristics
    format_signals = ["json", "csv", "markdown", "bullet", "list",
                      "table", "format", "respond with", "output:", "return"]
    analysis["output_format"] = {
        "present": any(s in text_lower for s in format_signals),
        "hint": "Specify output format: 'Respond as JSON with keys...'",
    }

    return analysis


def print_anatomy_check(prompt: str, title: str = "Prompt Anatomy Check") -> None:
    """Print a formatted anatomy analysis for a prompt."""
    analysis = analyze_prompt_anatomy(prompt)
    parts = ["instruction", "context", "input", "output_format"]
    score = sum(1 for p in parts if analysis[p]["present"])

    print(f"\n{'─' * 60}")
    print(f"  🔬 {title}")
    print(f"  Score: {score}/4 components present")
    print(f"{'─' * 60}")
    for part in parts:
        icon = "✅" if analysis[part]["present"] else "❌"
        info = ANATOMY[part]
        print(f"  {icon}  {info['symbol']} {info['name']:<16} "
              f"{'(present)' if analysis[part]['present'] else analysis[part]['hint']}")
    print(f"{'─' * 60}\n")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "═" * 72)
    print("  MODULE 01 — Anatomy of a Prompt")
    print("═" * 72)

    # ── Explain each part ─────────────────────────────────────────
    print("\n📐 THE FOUR PARTS OF A PROMPT\n")
    for key, part in ANATOMY.items():
        print(f"  {part['symbol']}  {part['name']}")
        print(f"     {part['definition']}")
        print(f"     Examples:")
        for ex in part["examples"][:2]:
            print(f"       • {ex}")
        print(f"     Tips:")
        for tip in part["tips"][:2]:
            print(f"       ✓ {tip}")
        print()

    # ── Progressive prompt building ───────────────────────────────
    print("═" * 72)
    print("  CASE STUDY: Building a Prompt Incrementally")
    print("  Task: Extract action items from a customer escalation email")
    print("═" * 72)

    prompts = [
        (PROMPT_V1, "v1: Instruction only"),
        (PROMPT_V2, "v2: Instruction + Context"),
        (PROMPT_V3, "v3: Instruction + Context + Output Format"),
        (PROMPT_V4, "v4: Full Anatomy (production-ready)"),
    ]

    for prompt, label in prompts:
        print(f"\n{'─' * 72}")
        print(f"  {label}")
        print(f"  Token count: {count_tokens(prompt)}")
        print_anatomy_check(prompt, title=label)

    # ── Show the best prompt (V4) in full ─────────────────────────
    print("\n📝 FULL PRODUCTION-READY PROMPT (v4):")
    print_prompt_box(PROMPT_V4, title="✅ Full Anatomy Prompt")

    # ── Cost impact of better prompts ─────────────────────────────
    print("\n💡 TOKEN COUNT COMPARISON (input tokens only):")
    for prompt, label in prompts:
        tokens = count_tokens(prompt)
        print(f"   {label:<40} {tokens:>5} tokens")

    print("\n✅ Key Insight:")
    print("   A 4-part structured prompt uses ~3x more tokens but produces")
    print("   dramatically more reliable, structured, and useful outputs.")
    print("   The token cost is minimal; the quality gain is significant.")
    print("\n" + "═" * 72 + "\n")


if __name__ == "__main__":
    main()
