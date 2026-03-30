"""
01_fundamentals/01_what_is_prompt_engineering.py
═══════════════════════════════════════════════════════════════════

WHAT:   An introduction to prompt engineering — its definition, history,
        and why it has become a core skill for every software professional
        working with AI systems.

WHY:    LLMs are powerful but non-deterministic. The same model produces
        radically different outputs depending on how you phrase your request.
        Prompt engineering is the discipline of making that process reliable,
        repeatable, and cost-effective.

WHEN TO USE THIS MENTAL MODEL:
        Every time you interact with an LLM — whether via API, an app, or a
        no-code tool — you are implicitly doing prompt engineering. This file
        makes the implicit explicit.

COMMON PITFALLS:
        - Treating prompts as magic spells instead of structured programs
        - Assuming one great prompt works for all models
        - Ignoring the relationship between prompt design and model cost
"""

import sys
import os

# ── Add parent directory to path so we can import from utils/ ──────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import print_prompt_box


# ─────────────────────────────────────────────────────────────────────────────
# 1. DEFINITION
# ─────────────────────────────────────────────────────────────────────────────

DEFINITION = """
Prompt Engineering is the practice of designing, refining, and optimizing 
the inputs (prompts) to large language models in order to reliably elicit 
accurate, relevant, and high-quality outputs.

It is not magic. It is a discipline that combines:
  • Linguistics     — understanding how language conveys intent
  • UX Design       — designing interactions that are clear and unambiguous
  • Systems Thinking — treating the LLM as a component in a larger pipeline
  • Empiricism       — testing hypotheses about model behavior systematically
"""


# ─────────────────────────────────────────────────────────────────────────────
# 2. BRIEF HISTORY TIMELINE
# ─────────────────────────────────────────────────────────────────────────────

HISTORY = {
    "2017": "Transformer architecture introduced (Attention Is All You Need)",
    "2018": "GPT-1 released by OpenAI — first GPT model",
    "2019": "GPT-2 released — prompt-based text generation goes mainstream",
    "2020": "GPT-3 (175B params) — few-shot prompting discovered as a capability",
    "2021": 'Research on "prompt tuning" and "prefix tuning" published',
    "2022": "InstructGPT shows RLHF alignment; ChatGPT launches in November",
    "2023": 'Chain-of-thought, ReAct, Tree-of-Thought papers published; "prompt engineer" becomes a job title',
    "2024": "GPT-4o, Claude 3, Gemini 1.5; multimodal prompting; DSPy for programmatic optimization",
    "2025": "Agentic systems and long-context models drive new prompting paradigms",
}


# ─────────────────────────────────────────────────────────────────────────────
# 3. WHY IT MATTERS — Three concrete business cases
# ─────────────────────────────────────────────────────────────────────────────

USE_CASES = [
    {
        "industry": "Customer Support",
        "naive_approach": "Ask GPT to 'respond to this customer complaint'",
        "naive_result": "Generic, sometimes wrong, occasionally rude response",
        "engineered_approach": (
            "System: You are a Level-2 support agent for Acme Corp. "
            "You are empathetic, concise, and always offer a resolution. "
            "If you cannot resolve, escalate with a ticket number. "
            "Tone: professional but warm.\n\n"
            "Classify the urgency (HIGH/MEDIUM/LOW), then draft a response."
        ),
        "engineered_result": (
            "Urgency: HIGH\n\n"
            "Dear valued customer, I sincerely apologize for the service "
            "disruption you experienced. I've escalated your case to our "
            "technical team (Ticket #A-4821). You will receive an update "
            "within 2 hours. ..."
        ),
    },
    {
        "industry": "Legal",
        "naive_approach": "Summarize this contract",
        "naive_result": "Generic summary that misses key risk clauses",
        "engineered_approach": (
            "You are a senior contract attorney. Review the following "
            "contract and produce a structured summary with sections: "
            "1) Key Obligations, 2) Termination Conditions, "
            "3) Liability Caps, 4) Red Flags. Use bullet points."
        ),
        "engineered_result": "Structured legal summary with flagged risk clauses",
    },
    {
        "industry": "Software Development",
        "naive_approach": "Write a Python function to sort a list",
        "naive_result": "Basic bubble sort (wrong if you wanted quicksort + type hints)",
        "engineered_approach": (
            "Write a Python 3.11 function with full type hints and Google-style "
            "docstring that sorts a list of dicts by a specified key using "
            "Timsort. Include edge cases (empty list, missing key). "
            "Return type must be list[dict]. Include 3 pytest test cases."
        ),
        "engineered_result": "Production-ready, tested, documented function",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# 4. THE MENTAL MODEL — LLMs as Instruction Followers
# ─────────────────────────────────────────────────────────────────────────────

MENTAL_MODEL = """
Think of an LLM not as a search engine (which retrieves facts) but as an 
extremely well-read intern who:

  ✓ Has read most of the internet
  ✓ Can follow complex, multi-step instructions
  ✓ Adapts its communication style to context
  ✗ Has no memory between calls (unless you provide history)
  ✗ Can confidently state incorrect facts (hallucination)
  ✗ Is sensitive to the exact phrasing of your request

Your job as a prompt engineer is to give this intern:
  1. A clear ROLE (who they are)
  2. Clear INSTRUCTIONS (what to do)
  3. Enough CONTEXT (what they need to know)
  4. A specific OUTPUT FORMAT (what you want back)
"""


# ─────────────────────────────────────────────────────────────────────────────
# 5. PROMPT ENGINEERING vs FINE-TUNING vs RAG
# ─────────────────────────────────────────────────────────────────────────────

COMPARISON = """
╔══════════════════╦══════════════════╦═══════════════════╦════════════════════╗
║ Approach         ║ When to Use      ║ Cost              ║ Flexibility        ║
╠══════════════════╬══════════════════╬═══════════════════╬════════════════════╣
║ Prompt Eng.      ║ Most use cases   ║ Low (API calls)   ║ Very high          ║
║ RAG              ║ Private/live data║ Medium            ║ High               ║
║ Fine-Tuning      ║ Specific style   ║ High (GPU time)   ║ Medium (locked in) ║
║ Pre-training     ║ New domain       ║ Very high         ║ Very high          ║
╚══════════════════╩══════════════════╩═══════════════════╩════════════════════╝

START with prompt engineering. Add RAG if the model needs your data.
Fine-tune only when prompt engineering + RAG can't achieve your quality bar.
"""


# ─────────────────────────────────────────────────────────────────────────────
# Main — display all concepts
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Print a comprehensive introduction to prompt engineering."""

    print("\n" + "═" * 72)
    print("  MODULE 01 — What is Prompt Engineering?")
    print("═" * 72)

    # ── Definition ────────────────────────────────────────────────
    print("\n📖 DEFINITION")
    print("─" * 72)
    print(DEFINITION)

    # ── History ───────────────────────────────────────────────────
    print("\n🕰  BRIEF HISTORY")
    print("─" * 72)
    for year, event in HISTORY.items():
        print(f"  {year}  │  {event}")

    # ── Mental Model ──────────────────────────────────────────────
    print("\n🧠 MENTAL MODEL")
    print("─" * 72)
    print(MENTAL_MODEL)

    # ── Use Cases ─────────────────────────────────────────────────
    print("\n🏭 REAL-WORLD USE CASES — Before vs After Prompt Engineering")
    print("─" * 72)
    for uc in USE_CASES:
        print(f"\n  Industry: {uc['industry']}")
        print_prompt_box(uc["naive_approach"],     title="❌ Naive Prompt")
        print_prompt_box(uc["engineered_approach"], title="✅ Engineered Prompt")

    # ── Comparison Table ──────────────────────────────────────────
    print("\n📊 PROMPT ENG. vs FINE-TUNING vs RAG")
    print("─" * 72)
    print(COMPARISON)

    print("\n✅ Key Takeaway:")
    print("   The SAME model produces dramatically different outputs based")
    print("   solely on how you phrase your prompt. Prompt engineering is")
    print("   the multiplier on every LLM investment your organisation makes.")
    print("\n" + "═" * 72 + "\n")


if __name__ == "__main__":
    main()
