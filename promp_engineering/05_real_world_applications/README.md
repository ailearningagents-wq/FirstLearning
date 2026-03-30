# Module 05 — Real World Applications

End-to-end implementations using the prompt techniques from Modules 01–04 to
solve practical business and engineering problems.

## Learning Objectives

After completing this module, you will be able to:

1. Build a production-quality document summarization pipeline
2. Set up an AI-powered code generation assistant with validation
3. Create a stateful chatbot with multi-turn memory
4. Extract structured data from unstructured documents at scale
5. Implement a content moderation pipeline
6. Build a simple Retrieval-Augmented Generation (RAG) system

## Module Files

| File | Application | Techniques Used |
|------|-------------|-----------------|
| `01_text_summarization.py` | Multi-document summarizer | Map-Reduce, prompt chaining |
| `02_code_generation.py` | AI coding assistant | Role prompting, output formatting, validation |
| `03_chatbot_with_memory.py` | Stateful conversation agent | Context compression, system prompts |
| `04_data_extraction.py` | Invoice / document parser | Constrained generation, Pydantic |
| `05_content_moderation.py` | Multi-stage safety pipeline | Classification, CoT, few-shot |
| `06_rag_basic.py` | Document Q&A with retrieval | Chunking, embedding, RAG pattern |

## Business Context

Each application in this module targets a real-world use case with:
- Realistic input data (not toy examples)
- Cost tracking per operation
- Error handling for production reliability
- Extensible design patterns

## Prerequisites

- Completed Modules 01–04
- `pip install tiktoken sentence-transformers faiss-cpu` for RAG example
