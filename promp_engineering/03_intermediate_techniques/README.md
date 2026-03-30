# Module 03 — Intermediate Prompting Techniques

## Learning Objectives

1. Apply Chain-of-Thought (CoT) to complex reasoning tasks
2. Use Self-Consistency to improve reliability on ambiguous problems
3. Implement the ReAct pattern for tool-using agents
4. Use Generated Knowledge Prompting for better factual accuracy
5. Build multi-step prompt chains where outputs feed inputs
6. Use delimiters and XML tags to create robust, unambiguous prompts

---

## Key Concepts

| Concept | Definition |
|---|---|
| **Chain-of-Thought (CoT)** | Prompt the model to reason step-by-step before answering |
| **Self-Consistency** | Run CoT multiple times, take majority vote |
| **ReAct** | Interleave Reasoning (Thought) with Actions (tool calls) and Observations |
| **Generated Knowledge** | Ask the model to surface its knowledge before answering |
| **Prompt Chaining** | Output of one prompt becomes input to the next |
| **Delimiters** | Special markers (```, ###, XML tags) to segment prompt parts |
| **Zero-Shot CoT** | "Let's think step by step" added to a simple prompt |

---

## Module Files

| File | Description |
|---|---|
| `01_chain_of_thought.py` | CoT for math word problems, logic puzzles, multi-step reasoning |
| `02_self_consistency.py` | Majority voting across multiple CoT traces |
| `03_react_prompting.py` | Reason + Act pattern for simulated tool-using agents |
| `04_generated_knowledge.py` | Ask model to generate facts first, then answer |
| `05_prompt_chaining.py` | Pipeline: classify → extract → generate → validate |
| `06_delimiters_and_structure.py` | Markdown, XML, and custom delimiter strategies |

---

## Try It Yourself

1. **CoT vs. Direct**: Take a logic puzzle and compare direct answer vs. CoT. Which is more often correct?
2. **Self-Consistency**: Run the same difficult question 5 times at temperature=0.7. How often do all 5 agree?
3. **Chain it**: Build a 3-step chain: (1) extract key facts from an article, (2) identify contradictions, (3) generate follow-up questions.
4. **Delimiter experiment**: Remove all delimiters from a complex prompt. Does the model still follow all instructions?
