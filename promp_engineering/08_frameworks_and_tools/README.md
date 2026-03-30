# Module 08 — Frameworks and Tools

> Raw API calls scale, but real applications need abstractions: chains, pipelines, prompt templates, and evaluation harnesses. This module introduces the most important Python libraries in the LLM ecosystem.

## Learning Objectives

After completing this module you will be able to:

- Build chains and agents with **LangChain** using prompt templates and output parsers
- Index and query documents with **LlamaIndex**
- Compile and optimize prompts programmatically with **DSPy**
- Validate structured outputs and enforce guardrails with **Guardrails AI**
- Version, store, and retrieve prompts from a **Prompt Registry**

---

## Library Overview

| Library | Purpose | Stars (approx.) | Best For |
|---|---|---|---|
| LangChain | Chains, agents, retrieval | 85k+ | Rapid prototyping, agents |
| LlamaIndex | Document indexing, RAG | 30k+ | Knowledge-base Q&A |
| DSPy | Programmatic prompt optimization | 15k+ | Research, high-accuracy pipelines |
| Guardrails AI | Output validation, rail specs | 3k+ | Production safety |
| (custom) | Prompt registry / versioning | — | All production systems |

---

## Files in This Module

| File | Topic | Cost (gpt-4o-mini) |
|---|---|---|
| `01_langchain_basics.py` | Chains, PromptTemplate, OutputParser | ~$0.004 |
| `02_llamaindex_basics.py` | VectorStore index, query engine | ~$0.003 |
| `03_dspy_intro.py` | Signatures, modules, compilation | ~$0.005 |
| `04_guardrails_ai.py` | Rail specs, validators, retry | ~$0.003 |
| `05_prompt_management.py` | Registry, versioning, A/B tracking | < $0.001 |

---

## Installation

```bash
# Core (required for all files in this module)
pip install langchain langchain-openai langchain-community

# LlamaIndex
pip install llama-index llama-index-vector-stores-faiss

# DSPy
pip install dspy-ai

# Guardrails AI
pip install guardrails-ai

# All at once
pip install langchain langchain-openai langchain-community \
            llama-index llama-index-vector-stores-faiss \
            dspy-ai guardrails-ai
```

Each file gracefully degrades if its optional dependency is not installed — showing the pattern with mock outputs so you can learn the API without needing every package.

---

## Quick Start

```bash
python 01_langchain_basics.py  --dry-run
python 02_llamaindex_basics.py --dry-run
python 03_dspy_intro.py        --dry-run
python 04_guardrails_ai.py     --dry-run
python 05_prompt_management.py --dry-run
```
