# Module 02 — Basic Prompting Techniques

## Learning Objectives

By the end of this module you will be able to:

1. Apply zero-shot, one-shot, and few-shot prompting strategies
2. Assign explicit roles to models using system and user messages
3. Write clear, specific instructions that avoid common failure modes
4. Reliably control output format (JSON, CSV, Markdown, XML)

---

## Key Concepts

| Concept | Definition |
|---|---|
| **Zero-Shot** | Asking the model to perform a task with no examples |
| **One-Shot** | Providing exactly one example to guide the model |
| **Few-Shot** | Providing 2–10 examples to demonstrate the task pattern |
| **Role Prompting** | Assigning a persona ("You are a...") to set tone & expertise |
| **Instruction Tuning** | Crafting precise, unambiguous directives |
| **Output Format Control** | Explicitly specifying the shape of the response |
| **In-Context Learning** | The model's ability to learn from examples in the prompt |

---

## When to Use Which Technique

```
Task is clear and model knows it well?     → Zero-Shot
Model makes consistent format errors?      → One-Shot (show one correct example)
Complex pattern or domain-specific format? → Few-Shot (2-8 examples)
Tone/expertise/persona matters?            → Role Prompting
Output must be parsed programmatically?    → Output Format Control
```

---

## Module Files

| File | Description |
|---|---|
| `01_zero_shot_prompting.py` | Classification, QA, summarization with no examples |
| `02_one_shot_prompting.py` | Single example to correct model behavior |
| `03_few_shot_prompting.py` | Multi-example learning for NER, sentiment, translation |
| `04_role_prompting.py` | System/user/assistant roles and persona design |
| `05_instruction_tuning.py` | Do's and don'ts for clear, specific instructions |
| `06_output_formatting.py` | JSON, CSV, Markdown, XML output control |

---

## Try It Yourself

1. **Zero → Few**: Take a zero-shot classification prompt. Add examples until accuracy improves. How many examples did it take?
2. **Role swap**: Run the same legal analysis prompt with "You are a paralegal" vs "You are a senior partner." Compare tone and depth.
3. **Format battles**: Extract the same data as JSON, then as CSV, then as YAML. Which is most token-efficient?
4. **Instruction audit**: Take a vague instruction ("Analyze this email") and rewrite it using every tip from `05_instruction_tuning.py`.
