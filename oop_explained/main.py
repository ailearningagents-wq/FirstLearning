"""
=============================================================
PYTHON CONCEPTS — MASTER RUNNER
Run ALL topics in sequence with section separators.
=============================================================

Project Structure:
  oop_explained/
  ── OOP CONCEPTS ─────────────────────────────────────────────
  ├── 01_classes_objects/         → Classes, objects, __init__, attributes
  ├── 02_encapsulation/           → Public, protected, private, @property
  ├── 03_inheritance/             → Single, multi-level, multiple, hierarchical
  ├── 04_polymorphism/            → Method overriding, duck typing, operators
  ├── 05_abstraction/             → ABC, @abstractmethod, abstract properties
  ├── 06_special_methods/         → Dunder methods (__str__, __add__, etc.)
  ├── 07_class_static_methods/    → @classmethod, @staticmethod
  ├── 08_properties/              → @property, getters, setters, deleters
  ── IMPORTANT PYTHON CONCEPTS ────────────────────────────────
  ├── 09_decorators/              → Function decorators, factories, wrappers
  ├── 10_generators/              → yield, generator expressions, itertools
  ├── 11_comprehensions/          → List/dict/set comprehensions, walrus
  ├── 12_exception_handling/      → try/except/finally, custom exceptions
  ├── 13_functional_programming/  → lambda, map, filter, reduce, closures
  ├── 14_type_hints_dataclasses/  → typing, @dataclass, generics
  ├── 15_file_io/                 → open, json, csv, pathlib, struct
  ├── 16_collections/             → dict/list/deque/Counter/heapq/bisect
  ├── 17_closures_scope/          → LEGB, nonlocal, closure factories
  ├── 18_concurrency/             → threading, multiprocessing, asyncio
  ── AI / ML / GENERATIVE AI ──────────────────────────────────
  ├── 19_numpy/                   → Arrays, broadcasting, linear algebra
  ├── 20_pandas/                  → DataFrames, groupby, ML data-prep
  ├── 21_visualization/           → Matplotlib, Seaborn, charts & plots
  ├── 22_scikit_learn/            → ML pipeline, models, evaluation
  ├── 23_neural_networks/         → NumPy NN from scratch + PyTorch intro
  ├── 24_transformers_nlp/        → Attention, BERT/GPT, HuggingFace
  ├── 25_prompt_engineering/      → Zero-shot, few-shot, CoT, templates
  ├── 26_llm_apis/                → OpenAI/Anthropic API patterns (mock)
  ├── 27_rag_embeddings/          → TF-IDF, cosine sim, VectorStore, RAG
  ├── 28_agentic_ai/              → ReAct, tool use, multi-agent patterns
  ── REAL-TIME PROJECTS ───────────────────────────────────────────────
  ├── 29_school_management_system/ → Python + MySQL CRUD, OOP, reports
  └── main.py                     ← YOU ARE HERE

Usage:
  python3 main.py                        → run all 28 topics
  python3 main.py 1 3 5                  → run topics 1, 3, 5 only
  python3 main.py 9 10 11                → run decorator/generator/comprehension
  python3 main.py 19 20 21               → run numpy/pandas/visualization
  python3 main.py 26 27 28               → run LLM APIs / RAG / Agentic AI
  python3 main.py 29                     → run School Management System
"""

import sys
import os
import importlib.util
import traceback


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

TOPICS = [
    # ── OOP Concepts ──────────────────────────────────────────────────────
    (1,  "01_classes_objects",         "classes_and_objects",    "Classes & Objects"),
    (2,  "02_encapsulation",           "encapsulation",          "Encapsulation"),
    (3,  "03_inheritance",             "inheritance",            "Inheritance"),
    (4,  "04_polymorphism",            "polymorphism",           "Polymorphism"),
    (5,  "05_abstraction",             "abstraction",            "Abstraction"),
    (6,  "06_special_methods",         "special_methods",        "Special (Dunder) Methods"),
    (7,  "07_class_static_methods",    "class_static_methods",   "Class & Static Methods"),
    (8,  "08_properties",              "properties",             "Properties (@property)"),
    # ── Important Python Concepts ──────────────────────────────────────────
    (9,  "09_decorators",              "decorators",             "Decorators"),
    (10, "10_generators",              "generators",             "Generators & Iterators"),
    (11, "11_comprehensions",          "comprehensions",         "Comprehensions"),
    (12, "12_exception_handling",      "exception_handling",     "Exception Handling"),
    (13, "13_functional_programming",  "functional_programming", "Functional Programming"),
    (14, "14_type_hints_dataclasses",  "type_hints_dataclasses", "Type Hints & Dataclasses"),
    (15, "15_file_io",                 "file_io",                "File I/O"),
    (16, "16_collections",             "collections_module",     "Collections & Data Structures"),
    (17, "17_closures_scope",          "closures_scope",         "Closures & Scope"),
    (18, "18_concurrency",             "concurrency",            "Concurrency (Threads/Processes/asyncio)"),
    # ── AI / ML / Generative AI ────────────────────────────────────────────
    (19, "19_numpy",              "numpy_basics",        "NumPy — Numerical Computing"),
    (20, "20_pandas",             "pandas_basics",       "Pandas — Data Analysis"),
    (21, "21_visualization",      "visualization",       "Visualization (Matplotlib/Seaborn)"),
    (22, "22_scikit_learn",       "scikit_learn_ml",     "Scikit-learn — Machine Learning"),
    (23, "23_neural_networks",    "neural_networks",     "Neural Networks (from scratch + PyTorch)"),
    (24, "24_transformers_nlp",   "transformers_nlp",    "Transformers & NLP"),
    (25, "25_prompt_engineering", "prompt_engineering",  "Prompt Engineering"),
    (26, "26_llm_apis",           "llm_apis",            "LLM APIs (OpenAI / Anthropic patterns)"),
    (27, "27_rag_embeddings",     "rag_embeddings",      "RAG & Vector Embeddings"),
    (28, "28_agentic_ai",         "agentic_ai",          "Agentic AI (ReAct, Tools, Multi-Agent)"),
    # ── Real-Time Projects ────────────────────────────────────────────
    (29, "29_school_management_system", "school_management",   "Project: School Management System (MySQL)"),
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          PYTHON — COMPLETE CONCEPTS GUIDE (29 Topics)        ║
║   OOP · Python · NumPy · ML · LLMs · RAG · Projects          ║
╚══════════════════════════════════════════════════════════════╝
"""

def section_banner(number: int, title: str):
    bar = "═" * 62
    print(f"\n╔{bar}╗")
    print(f"║  TOPIC {number}: {title:<53}║")
    print(f"╚{bar}╝\n")


def run_module(folder: str, module_name: str, title: str, number: int):
    """Dynamically import and execute a topic module."""
    path = os.path.join(BASE_DIR, folder, f"{module_name}.py")

    if not os.path.exists(path):
        print(f"  [SKIPPED] File not found: {path}")
        return

    section_banner(number, title)

    spec   = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules so ClassVar / type annotations resolve correctly
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception:
        print(f"\n  [ERROR] Exception in {title}:")
        traceback.print_exc()
    finally:
        sys.modules.pop(module_name, None)  # clean up after execution


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print(BANNER)

    # Parse optional topic numbers from command line: python main.py 1 3 5
    selected = set()
    for arg in sys.argv[1:]:
        try:
            selected.add(int(arg))
        except ValueError:
            print(f"[WARNING] Ignoring non-integer argument: {arg!r}")

    topics_to_run = [t for t in TOPICS if (not selected or t[0] in selected)]

    if not topics_to_run:
        print("No matching topics found. Run without arguments to run all topics.")
        print(f"Available topic numbers: {[t[0] for t in TOPICS]}")
        return

    total = len(topics_to_run)
    topic_names = [f"{t[0]}:{t[3]}" for t in topics_to_run]
    print(f"  Running {total} topic(s):")
    for name in topic_names:
        print(f"    • {name}")
    print()

    for number, folder, module_name, title in topics_to_run:
        run_module(folder, module_name, title, number)

    print("\n" + "═" * 64)
    print("  ALL TOPICS COMPLETE!")
    print("═" * 64)
    print("""
  QUICK REFERENCE — ALL 29 TOPICS:
  ─────────────────────────────────────────────────────────────
  ── OOP ──────────────────────────────────────────────────────
   1  Classes & Objects     Blueprint → instance, __init__
   2  Encapsulation         public/_protected/__private, @property
   3  Inheritance           super(), MRO, multiple inheritance
   4  Polymorphism          override, duck typing, operators
   5  Abstraction           ABC, @abstractmethod
   6  Special Methods       __str__, __add__, __enter__, __call__
   7  Class/Static Methods  @classmethod (cls), @staticmethod
   8  Properties            @property, setter, deleter, caching
  ── PYTHON CONCEPTS ──────────────────────────────────────────
   9  Decorators            @functools.wraps, factories, classes
  10  Generators            yield, yield from, send(), itertools
  11  Comprehensions        [x for x], {k:v}, {x}, (x), walrus :=
  12  Exception Handling    try/except/else/finally, raise from
  13  Functional Prog.      lambda, map, filter, reduce, partial
  14  Type Hints/Dataclass  typing, @dataclass, Generic[T]
  15  File I/O              open, json, csv, pathlib, struct
  16  Collections           dict, Counter, deque, heapq, bisect
  17  Closures & Scope      LEGB, nonlocal, closure factories
  18  Concurrency           threads, processes, asyncio
  ── AI / ML / GENERATIVE AI ──────────────────────────────────
  19  NumPy                 arrays, broadcasting, linalg, float32
  20  Pandas                DataFrame, groupby, merge, ML data-prep
  21  Visualization         Matplotlib, Seaborn, save to file
  22  Scikit-learn          Pipeline, GridSearchCV, metrics, CV
  23  Neural Networks       NN from scratch, PyTorch intro
  24  Transformers & NLP    Attention, positional enc, HuggingFace
  25  Prompt Engineering    zero/few-shot, CoT, templates, patterns
  26  LLM APIs              OpenAI/Anthropic patterns, tool calling
  27  RAG & Embeddings      TF-IDF, cosine sim, VectorStore, hybrid
  28  Agentic AI            ReAct, tools, memory, multi-agent
  ── REAL-TIME PROJECTS ───────────────────────────────────────
  29  School Mgmt System  Python + MySQL, OOP, CRUD, reports
  ─────────────────────────────────────────────────────────────

  Run individual topics:
    python3 main.py 1          → Classes & Objects only
    python3 main.py 3 4 5      → Inheritance, Polymorphism, Abstraction
    python3 main.py 9 10 11    → Decorators, Generators, Comprehensions
    python3 main.py 19 20 21   → NumPy, Pandas, Visualization
    python3 main.py 26 27 28   → LLM APIs, RAG, Agentic AI
    python3 main.py 29         → School Management System (MySQL)
    python3 main.py            → All 29 topics
""")


if __name__ == "__main__":
    main()
