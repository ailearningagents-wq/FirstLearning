# Prompt Engineering with Python — Complete Learning Curriculum

> A production-quality, self-contained course taking you from zero to advanced prompt engineering practitioner.

---

## Overview

Prompt engineering is the craft of designing inputs to large language models (LLMs) to reliably produce high-quality, accurate, and useful outputs. This curriculum covers every technique from basic zero-shot prompting to advanced tree-of-thought reasoning, real-world applications, evaluation methods, security hardening, and capstone projects.

---

## Prerequisites

| Requirement | Minimum Version |
|---|---|
| Python | 3.9+ |
| OpenAI account | API key required |
| pip | 23.0+ |

**Assumed knowledge:** Basic Python (functions, loops, dicts), familiarity with REST APIs.

---

## Quick Start

```bash
# 1. Clone / navigate to this folder
cd promp_engineering/

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API keys
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 5. Run your first example
python 01_fundamentals/03_first_api_call.py
```

---

## Curriculum Structure

| Module | Topic | Files |
|--------|-------|-------|
| `01_fundamentals/` | What is Prompt Engineering, anatomy, first API call, parameters, tokens | 5 `.py` files |
| `02_basic_techniques/` | Zero-shot, one-shot, few-shot, role prompting, instruction tuning, output formatting | 6 `.py` files |
| `03_intermediate_techniques/` | Chain-of-thought, self-consistency, ReAct, generated knowledge, chaining, delimiters | 6 `.py` files |
| `04_advanced_techniques/` | Tree-of-thought, meta-prompting, recursive prompting, constrained generation, compression, auto-optimization | 6 `.py` files |
| `05_real_world_applications/` | Summarization, code generation, chatbot, data extraction, content moderation, RAG | 6 `.py` files |
| `06_evaluation_and_testing/` | Metrics, A/B testing, adversarial testing, regression, logging | 5 `.py` files |
| `07_security_and_safety/` | Prompt injection, defenses, PII handling, ethics | 4 `.py` files |
| `08_frameworks_and_tools/` | LangChain, LlamaIndex, DSPy, Guardrails AI, prompt management | 5 `.py` files |
| `09_capstone_projects/` | Email assistant, document QA system, multi-agent researcher | 3 projects |

---

## Environment Variables

Copy `.env.example` to `.env` and populate:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...        # Optional, for Claude
OPENAI_MODEL=gpt-4o-mini     # Default model (cost-efficient)
```

---

## Cost Awareness

Every example in this course:
- Prints estimated token count and API cost before/after each call
- Supports a `--dry-run` flag to preview prompts without spending tokens
- Uses `gpt-4o-mini` by default (~$0.00015/1K input tokens) for affordability

Running ALL examples in this course will cost approximately **$1–5** depending on your model selection.

---

## Learning Path

```
01 Fundamentals  →  02 Basic Techniques  →  03 Intermediate
       ↓                                           ↓
04 Advanced  ←────────────────────────────  05 Real-World Apps
       ↓
06 Evaluation  →  07 Security  →  08 Frameworks  →  09 Capstone
```

---

## Contributing / Extending

- Each module's `README.md` contains "Try It Yourself" exercises
- The `utils/llm_client.py` wrapper makes it easy to swap LLM providers
- Add your own prompts to any module and run them with cost estimates

---

## License

MIT License — free to use, adapt, and distribute for educational purposes.
