# Module 01 — Fundamentals of Prompt Engineering

## Learning Objectives

By the end of this module you will be able to:

1. Define prompt engineering and explain its role in the modern AI stack
2. Identify the four structural parts of a well-formed prompt
3. Make your first API call to OpenAI using Python
4. Understand the effect of `temperature`, `top_p`, `max_tokens`, and `frequency_penalty`
5. Count tokens, estimate costs, and build cost-awareness into every workflow

---

## Key Concepts

| Concept | Definition |
|---|---|
| **Prompt** | The text input you send to an LLM to elicit a response |
| **Instruction** | The directive telling the model what task to perform |
| **Context** | Background information that shapes the response |
| **Input** | The data the model should operate on |
| **Output format** | The shape you want the response to take |
| **Temperature** | Controls randomness (0 = deterministic, 2 = wild) |
| **Token** | The atomic unit of text the model processes (~0.75 English words) |
| **Prompt Engineering** | The discipline of designing prompts to reliably produce high-quality outputs |

---

## Module Files

| File | Description |
|---|---|
| `01_what_is_prompt_engineering.py` | History, motivation, and mental models |
| `02_anatomy_of_a_prompt.py` | Decomposing prompts into instruction, context, input, output format |
| `03_first_api_call.py` | "Hello World" — your first real OpenAI API call |
| `04_temperature_and_parameters.py` | Live experiments with generation parameters |
| `05_tokens_and_pricing.py` | Token counting, cost estimation, and budget management |

---

## Try It Yourself

1. **Experiment**: Run `03_first_api_call.py` with three different tasks (summarize, translate, classify). Compare the outputs.
2. **Temperature**: Run `04_temperature_and_parameters.py` and set temperature to `0.0`, `0.7`, and `1.5` for the same prompt. What changes?
3. **Cost**: Take a 1,000-word Wikipedia article. Run `05_tokens_and_pricing.py` on it and calculate the cost of summarizing it with GPT-4o vs GPT-4o-mini.
4. **Anatomy**: Take any prompt you've written before and label its four parts: instruction, context, input, output format.
