"""
08_frameworks_and_tools/01_langchain_basics.py
═══════════════════════════════════════════════════════════════════

WHAT: Core LangChain patterns:
      1. PromptTemplate + ChatPromptTemplate
      2. Simple LLMChain (prompt | model | parser)
      3. StrOutputParser and PydanticOutputParser
      4. Sequential chain (pipe multiple steps)
      5. RunnablePassthrough (pass-through input in a chain)

WHY:  LangChain provides reusable abstractions that make prompts
      composable, testable, and serializable. The LCEL (LangChain
      Expression Language) pipe (|) syntax is now the standard.

WHEN: Use LangChain when you need: structured output parsing,
      chaining multiple LLM calls, or building agents with tools.

PITFALLS:
  - LangChain evolves fast — pin the version in requirements.txt.
  - Abstraction cost: simple tasks can be over-engineered with chains.
  - LCEL is more efficient than legacy LLMChain; prefer it for new code.
  - Use with your own LLMClient only when needed; LangChain has its own
    cost tracking via callbacks.

Install: pip install langchain langchain-openai

Usage:
    python 01_langchain_basics.py
    python 01_langchain_basics.py --dry-run
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
    from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from pydantic import BaseModel, Field
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# Fallback: when LangChain is not installed, demo the concepts with our client
# ─────────────────────────────────────────────────────────────────────────────

def demo_without_langchain(client: LLMClient) -> None:
    """Show the same patterns using raw LLMClient calls."""
    print("\n  [LangChain not installed — showing equivalent raw pattern]\n")

    # Pattern 1: PromptTemplate equivalent
    def make_prompt(template: str, **kwargs) -> str:
        return template.format(**kwargs)

    # Pattern 2: Chain equivalent
    def chain(template: str, **inputs) -> str:
        prompt = make_prompt(template, **inputs)
        r = client.chat(messages=[{"role": "user", "content": prompt}],
                        temperature=0.2, max_tokens=100)
        return r.content.strip() if not client.dry_run else "[DRY-RUN output]"

    # Example 1: Simple chain
    topic = "asynchronous programming in Python"
    result = chain("Generate a one-sentence summary about {topic}.", topic=topic)
    print(f"  Simple chain output: {result}")

    # Example 2: Sequential chain (step 1 output → step 2 input)
    outline = chain("Write a 3-point outline for a blog post about {topic}.", topic=topic)
    print(f"\n  Outline (step 1): {outline[:120]}...")
    intro   = chain("Write an introductory paragraph based on this outline:\n{outline}", outline=outline)
    print(f"  Introduction (step 2): {intro[:120]}...")


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Demos
# ─────────────────────────────────────────────────────────────────────────────

def demo_with_langchain(dry_run: bool) -> None:
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Build LLM (LangChain wraps OpenAI)
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.2,
    )
    if dry_run:
        print("  [DRY-RUN: showing chain structure without API calls]")

    # ── Pattern 1: Simple PromptTemplate + StrOutputParser ──────────────────
    print("\n  ── Pattern 1: Simple Chain (LCEL pipe syntax)")
    simple_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a concise technical writer."),
        ("human",  "Summarize {topic} in one sentence."),
    ])
    simple_chain = simple_prompt | llm | StrOutputParser()
    print(f"  Chain: ChatPromptTemplate | ChatOpenAI | StrOutputParser")

    if not dry_run:
        result = simple_chain.invoke({"topic": "async/await in Python"})
        print(f"  Output: {result}")
    else:
        print("  Output: [DRY-RUN — would call ChatOpenAI]")

    # ── Pattern 2: Structured output with JSON parser ────────────────────────
    print("\n  ── Pattern 2: JSON Output Parser")

    class TopicAnalysis(BaseModel):
        summary: str = Field(description="One sentence summary")
        difficulty: str = Field(description="beginner/intermediate/advanced")
        key_concepts: list[str] = Field(description="Top 3 concepts")

    json_parser = JsonOutputParser(pydantic_object=TopicAnalysis)

    structured_prompt = ChatPromptTemplate.from_messages([
        ("system", "Analyze the given programming topic. Return valid JSON matching this schema: {format_instructions}"),
        ("human",  "Topic: {topic}"),
    ]).partial(format_instructions=json_parser.get_format_instructions())

    structured_chain = structured_prompt | llm | json_parser
    print("  Chain: ChatPromptTemplate (with format instructions) | LLM | JsonOutputParser")

    if not dry_run:
        result = structured_chain.invoke({"topic": "Python decorators"})
        print(f"  Output: {result}")
    else:
        print("  Output: [DRY-RUN — would return {'summary': ..., 'difficulty': ..., 'key_concepts': [...]}]")

    # ── Pattern 3: Sequential chain with RunnablePassthrough ────────────────
    print("\n  ── Pattern 3: Sequential Chain (outline → draft)")

    outline_prompt = ChatPromptTemplate.from_template(
        "Write a 3-bullet outline for a blog post about: {topic}"
    )
    draft_prompt = ChatPromptTemplate.from_template(
        "Expand this outline into an introductory paragraph:\n{outline}"
    )

    sequential_chain = (
        {"outline": outline_prompt | llm | StrOutputParser(),
         "topic":   RunnablePassthrough()}
        | draft_prompt
        | llm
        | StrOutputParser()
    )
    print("  Chain: outline_prompt | llm | (passthrough) → draft_prompt | llm")

    if not dry_run:
        result = sequential_chain.invoke({"topic": "Python type hints"})
        print(f"  Output: {result[:200]}...")
    else:
        print("  Output: [DRY-RUN — would produce a draft paragraph]")

    # ── Pattern 4: Using .batch() for multiple inputs ───────────────────────
    print("\n  ── Pattern 4: Batch Processing")
    topics = ["decorators", "generators", "dataclasses"]
    simple_chain_batch = simple_prompt | llm | StrOutputParser()
    print(f"  Batch of {len(topics)} topics with simple_chain.batch()")
    if not dry_run:
        results = simple_chain_batch.batch([{"topic": t} for t in topics])
        for t, r in zip(topics, results):
            print(f"  {t}: {r[:60]}...")
    else:
        print("  Output: [DRY-RUN — would call .batch() in parallel]")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="LangChain Basics")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 08 — Frameworks: LangChain Basics")
    print(f"  LangChain available: {LANGCHAIN_AVAILABLE}")
    print("══════════════════════════════════════════════════════════════════════")

    if LANGCHAIN_AVAILABLE:
        demo_with_langchain(dry_run=args.dry_run)
    else:
        demo_without_langchain(client)
        print("\n  Install LangChain to run the full demos:")
        print("    pip install langchain langchain-openai")

    print("\n  KEY CONCEPTS SUMMARY")
    print("  PromptTemplate     — reusable prompt with named variables")
    print("  ChatPromptTemplate — multi-message (system + human + etc.) template")
    print("  LCEL pipe (|)      — compose steps: prompt | model | parser")
    print("  StrOutputParser    — extract text from LLM response")
    print("  JsonOutputParser   — parse JSON with optional Pydantic schema")
    print("  RunnablePassthrough— include original input downstream in chain")
    print("  .batch()           — run chain on multiple inputs in parallel")

    print("\n✅ LangChain basics complete.\n")


if __name__ == "__main__":
    main()
