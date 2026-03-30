# Module 09 — Capstone Projects

> It's time to build something real. Each project integrates the techniques from the entire course into a production-quality, runnable application.

## Learning Objectives

After completing this module you will be able to:

- Architect multi-component LLM applications with clear separation of concerns
- Combine retrieval, memory, structured output, and safety in a single system
- Write maintainable prompt code with versioning and logging from day one
- Deploy-ready: each project has a `--dry-run` mode and clear cost estimates

---

## Projects

### Project 1: AI Email Assistant (`01_ai_email_assistant/`)

**What it does:** Processes an incoming email inbox, classifies each email, drafts a reply using role-specific instructions, and outputs a structured action plan.

**Techniques used:** Role prompting, few-shot classification, structured output (Pydantic), prompt chaining, PII redaction

**Files:**
- `main.py` — Pipeline orchestrator (read → classify → draft → output)
- `prompts.py` — All prompts versioned in a registry

---

### Project 2: Document Q&A System (`02_document_qa_system/`)

**What it does:** Indexes a knowledge base of documents and answers questions with grounded citations, detecting when the answer is not in the knowledge base.

**Techniques used:** RAG (chunking + retrieval + synthesis), output validation, hallucination detection, structured citations

**Files:**
- `main.py` — Index + query + cite pipeline
- `prompts.py` — Prompt registry for system, synthesis, and citation prompts

---

### Project 3: Multi-Agent Researcher (`03_multi_agent_researcher/`)

**What it does:** An orchestrator spawns specialized sub-agents (web_search, summarizer, fact_checker, writer) via a ReAct-style loop to research a topic and produce a structured report.

**Techniques used:** ReAct prompting, multi-agent coordination, tool use, chain of thought, structured reporting

**Files:**
- `main.py` — Orchestrator + agent loop
- `prompts.py` — All agent system prompts and tool descriptions

---

## Quick Start

```bash
cd 09_capstone_projects

# Project 1: Email Assistant
python 01_ai_email_assistant/main.py --dry-run

# Project 2: Document Q&A
python 02_document_qa_system/main.py --dry-run

# Project 3: Multi-Agent Researcher
python 03_multi_agent_researcher/main.py --dry-run --topic "impacts of AI on software engineering"
```

---

## Cost Estimates (gpt-4o-mini)

| Project | Dry-Run | Full Run |
|---|---|---|
| Email Assistant (5 emails) | $0 | ~$0.008 |
| Document Q&A (5 queries) | $0 | ~$0.006 |
| Multi-Agent Researcher | $0 | ~$0.020 |

---

## Completion Checklist

- [ ] Project 1: Email Assistant runs end-to-end
- [ ] Project 2: Document Q&A cites sources correctly
- [ ] Project 3: Multi-agent loop completes a research task
- [ ] All three use `PromptRegistry` from Module 08
- [ ] All three log calls via `PromptLogger` from Module 06
- [ ] All three pass `--dry-run` with zero API calls
