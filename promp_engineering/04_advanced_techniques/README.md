# Module 04 — Advanced Techniques

Advanced prompting strategies that go beyond standard CoT and few-shot patterns.

## Learning Objectives

After completing this module, you will be able to:

1. Implement Tree of Thoughts for problems requiring exploration of multiple paths
2. Use Meta-Prompting to have the model write better prompts for itself
3. Break complex tasks into recursive sub-problems with recursive prompting
4. Apply constrained generation to enforce strict output contracts
5. Compress long prompts without losing critical information
6. Use automated prompt optimization (APE / DSPy-style) to iteratively improve prompts

## Module Files

| File | Technique | Best For |
|------|-----------|----------|
| `01_tree_of_thought.py` | Branch-explore-prune on reasoning tree | Math, planning, strategic decisions |
| `02_meta_prompting.py` | Model writes & improves its own prompts | Prompt creation, systematic refinement |
| `03_recursive_prompting.py` | Decompose → Solve sub-problems → Merge | Long-form content, complex analysis |
| `04_constrained_generation.py` | Enforce format contracts (JSON, grammar) | APIs, structured pipelines |
| `05_prompt_compression.py` | Reduce token count while preserving quality | Cost optimization, long contexts |
| `06_automatic_prompt_optimization.py` | Iterative eval-and-improve loop | Production prompt tuning |

## Key Concepts

### Tree of Thoughts (ToT)
```
              Question
                 │
        ┌────────┼────────┐
     Branch A  Branch B  Branch C
        │         │         │
     [eval]    [eval]    [eval]
        │         ✓         │
     Prune    Continue   Prune
              │
           Answer
```

### Meta-Prompting
```
User request → [Meta-prompter] → Optimized prompt → [LLM] → Better answer
                    ▲                       │
                    └───── iterate ─────────┘
```

### Prompt Compression Techniques
- **Summarization**: Compress context → lose some detail
- **Extraction**: Keep only sentences that match key topics
- **Indexing**: Store full content externally, inject only relevant chunks
- **Abbreviation**: Use shorthand for repeated concepts

## Cost Expectations

| Technique | Relative Cost | Latency | Accuracy Gain |
|-----------|---------------|---------|---------------|
| Standard | 1× | 1× | baseline |
| Tree of Thoughts | 3–10× | 3–10× | +15–30% on math/logic |
| Meta-Prompting | 2–3× | 2–3× | +10–20% on complex tasks |
| Recursive | 2–5× | 2–5× | +20% on long-form content |
| Constrained Gen | 0.9× | 1× | → 100% valid format |
| Compression | 0.3–0.6× | 0.8× | −3–10% quality |
| Auto-Optimization | 10–50× up front | slow | +20–40% after tuning |

## Prerequisites

- Completed Modules 01–03
- Understand Chain-of-Thought and Prompt Chaining
