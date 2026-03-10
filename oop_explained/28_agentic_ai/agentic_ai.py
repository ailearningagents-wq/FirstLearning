"""
=============================================================
GENERATIVE AI FOUNDATIONS
Topic 28: Agentic AI — ReAct, Tool Use & Multi-Agent Systems
=============================================================

Fully runnable — uses a MockLLM so no API key is needed.
Swap MockLLM for a real OpenAI/Anthropic client to go live.

COVERED:
  1. What is an AI Agent? (Perceive → Think → Act)
  2. Tool definition and ToolRegistry
  3. ReAct pattern (Reason + Act loop)
  4. AgentExecutor with safety limits
  5. Memory types (in-context, episodic, external)
  6. Planning: hierarchical task decomposition
  7. Multi-agent: Orchestrator + Specialist Workers
  8. Common agent frameworks overview
  9. Safety & limitations
"""

import json
import re
import time
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

# ─────────────────────────────────────────────
# 1. WHAT IS AN AI AGENT?
# ─────────────────────────────────────────────

print("=" * 60)
print("1. AGENT FUNDAMENTALS")
print("=" * 60)
print("""
  AGENT = Perceive → Think → Act → Observe → Loop

  ┌─────────────────────────────────────────────┐
  │                                             │
  │   Environment                               │
  │       │                                     │
  │    PERCEIVE (input: user query, sensor)     │
  │       │                                     │
  │     THINK  (LLM reasons, plans next step)  │
  │       │                                     │
  │      ACT   (call a tool / function)         │
  │       │                                     │
  │    OBSERVE (tool returns result)            │
  │       │                                     │
  │   Loop until goal reached or max turns      │
  │                                             │
  └─────────────────────────────────────────────┘

  AGENT vs PIPELINE:
    Pipeline  → fixed sequence of steps, no decisions
    Agent     → dynamically decides WHICH steps to take based on context

  AGENT vs CHATBOT:
    Chatbot   → responds to messages
    Agent     → takes actions in the world (searches, runs code, etc.)
""")


# ─────────────────────────────────────────────
# 2. TOOL DEFINITION & REGISTRY
# ─────────────────────────────────────────────

print("=" * 60)
print("2. TOOL DEFINITION & REGISTRY")
print("=" * 60)

@dataclass
class ToolSpec:
    """Describes a callable tool the agent can use."""
    name:        str
    description: str
    parameters:  Dict[str, str]          # param_name → description
    fn:          Callable[..., Any]


class ToolRegistry:
    """Manages all tools available to an agent."""

    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def call(self, name: str, **kwargs) -> Any:
        spec = self.get(name)
        if spec is None:
            return f"ERROR: Unknown tool '{name}'"
        try:
            return spec.fn(**kwargs)
        except Exception as e:
            return f"ERROR calling {name}: {e}"

    def format_for_prompt(self) -> str:
        """Return tool descriptions for injection into the system prompt."""
        lines = ["Available tools:"]
        for spec in self._tools.values():
            params = ", ".join(f"{k}: {v}" for k, v in spec.parameters.items())
            lines.append(f"  {spec.name}({params}) → {spec.description}")
        return "\n".join(lines)

    @property
    def names(self) -> List[str]:
        return list(self._tools.keys())


# ─── Define real tools ───────────────────────────────────────

def search_web(query: str) -> str:
    """Simulates a web search — replace with SerpAPI / Tavily / Bing."""
    results = {
        "python":        "Python is a high-level programming language created by Guido van Rossum in 1989.",
        "ai":            "Artificial Intelligence enables machines to mimic human cognition.",
        "transformer":   "Transformers use self-attention mechanisms, introduced in 'Attention is All You Need' (2017).",
        "rag":           "RAG (Retrieval-Augmented Generation) combines retrieval systems with generative LLMs.",
        "langchain":     "LangChain is a framework for building LLM-powered applications with chains and agents.",
    }
    for key, result in results.items():
        if key in query.lower():
            return result
    return f"Search results for '{query}': Found 3 relevant articles about {query}."


def calculate(expression: str) -> str:
    """Evaluate a safe arithmetic expression."""
    import ast
    try:
        tree = ast.parse(expression, mode='eval')
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                   ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                   ast.USub, ast.UAdd, ast.FloorDiv)
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError(f"Unsafe expression: {type(node).__name__}")
        result = eval(compile(tree, '<string>', 'eval'))  # noqa: S307
        return str(result)
    except Exception as e:
        return f"ERROR: {e}"


def get_current_date() -> str:
    """Returns today's date."""
    from datetime import date
    return str(date.today())


def store_memory(key: str, value: str) -> str:
    """Persist a key-value fact to memory."""
    AGENT_MEMORY[key] = value
    return f"Stored: {key} = {value}"


def recall_memory(key: str) -> str:
    """Retrieve a stored fact from memory."""
    return AGENT_MEMORY.get(key, f"No memory found for key '{key}'")


AGENT_MEMORY: Dict[str, str] = {}   # shared in-process memory


# Register tools
registry = ToolRegistry()

registry.register(ToolSpec(
    name        = "search_web",
    description = "Search the internet for up-to-date information.",
    parameters  = {"query": "search query string"},
    fn          = search_web,
))
registry.register(ToolSpec(
    name        = "calculate",
    description = "Evaluate a mathematical expression safely.",
    parameters  = {"expression": "arithmetic expression, e.g. '2**10 + 3*5'"},
    fn          = calculate,
))
registry.register(ToolSpec(
    name        = "get_current_date",
    description = "Return today's date in YYYY-MM-DD format.",
    parameters  = {},
    fn          = get_current_date,
))
registry.register(ToolSpec(
    name        = "store_memory",
    description = "Store a key-value fact for later retrieval.",
    parameters  = {"key": "memory key", "value": "value to store"},
    fn          = store_memory,
))
registry.register(ToolSpec(
    name        = "recall_memory",
    description = "Retrieve a previously stored fact by key.",
    parameters  = {"key": "memory key to look up"},
    fn          = recall_memory,
))

print("Registered tools:")
print(registry.format_for_prompt())


# ─────────────────────────────────────────────
# 3. MOCK LLM (ReAct-capable)
# ─────────────────────────────────────────────

class ReActLLM:
    """
    Mock LLM that produces ReAct-style output.

    ReAct format:
        Thought: <reasoning>
        Action: <tool_name>
        Action Input: <json arguments>
        Observation: <tool result>   ← filled by agent executor
        ... (repeat until)
        Thought: I now know the final answer.
        Final Answer: <answer>
    """

    def __init__(self, tool_names: List[str]):
        self.tool_names = tool_names
        self._scenarios = self._build_scenarios()

    def _build_scenarios(self) -> List[dict]:
        return [
            {
                "trigger":    "date",
                "steps": [
                    ("I need to find today's date.",
                     "get_current_date", {}),
                    (None, None, None),   # final answer
                ],
                "final": "Today's date is {get_current_date}.",
            },
            {
                "trigger":    "calculate|math|compute|result",
                "steps": [
                    ("I need to compute the mathematical expression.",
                     "calculate", {"expression": "2**10"}),
                    (None, None, None),
                ],
                "final": "The result of 2^10 is {calculate} which equals 1024.",
            },
            {
                "trigger":    "transformer|attention|llm|gpt|bert",
                "steps": [
                    ("Let me search for information about transformers.",
                     "search_web", {"query": "transformer attention mechanism"}),
                    (None, None, None),
                ],
                "final": "Based on search results: {search_web}",
            },
            {
                "trigger":    "rag|retrieval",
                "steps": [
                    ("Let me search for RAG information.",
                     "search_web", {"query": "rag retrieval augmented generation"}),
                    (None, None, None),
                ],
                "final": "About RAG: {search_web}",
            },
            {
                "trigger":    "remember|store|save",
                "steps": [
                    ("I need to store this information in memory.",
                     "store_memory", {"key": "user_fact", "value": "Python is awesome"}),
                    ("Now let me confirm it was stored.",
                     "recall_memory", {"key": "user_fact"}),
                    (None, None, None),
                ],
                "final": "I've stored and confirmed the fact: {recall_memory}",
            },
        ]

    def plan_next_step(self, goal: str, history: List[dict]) -> Tuple[str, Optional[str], Optional[dict]]:
        """
        Returns:
          (thought, tool_name|None, tool_args|None)
          When tool_name is None → Final Answer
        """
        goal_lower = goal.lower()

        for scenario in self._scenarios:
            if re.search(scenario["trigger"], goal_lower):
                step_idx = sum(1 for h in history if h.get("type") == "action")
                steps    = scenario["steps"]

                if step_idx < len(steps):
                    thought, tool, args = steps[step_idx]
                    if thought is None:   # final answer step
                        # Fill placeholders with observations
                        obs_map = {h["tool"]: h["result"]
                                   for h in history if h.get("type") == "action"}
                        final = scenario["final"]
                        for k, v in obs_map.items():
                            final = final.replace(f"{{{k}}}", str(v)[:120])
                        return ("I now have enough information to answer.", None, {"final": final})
                    return (thought, tool, args)

        # Default: no tool needed
        return ("I can answer this directly from my knowledge.",
                None,
                {"final": f"I know about '{goal}'. (MockLLM direct answer)"})


# ─────────────────────────────────────────────
# 4. AGENT EXECUTOR (ReAct Loop)
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("3 & 4. ReAct AGENT EXECUTOR")
print("=" * 60)

class AgentExecutor:
    """
    Runs the Reason + Act (ReAct) loop.

    Reference: "ReAct: Synergizing Reasoning and Acting in Language Models"
               Yao et al., 2022  https://arxiv.org/abs/2210.03629
    """

    def __init__(self, llm: ReActLLM, registry: ToolRegistry,
                 max_steps: int = 6, verbose: bool = True):
        self.llm       = llm
        self.registry  = registry
        self.max_steps = max_steps
        self.verbose   = verbose

    def run(self, goal: str) -> dict:
        history  = []
        steps    = 0

        if self.verbose:
            print(f"\n{'─'*60}")
            print(f"GOAL: {goal}")
            print(f"{'─'*60}")

        while steps < self.max_steps:
            # ── THINK ───────────────────────────────────────────────
            thought, tool_name, tool_args = self.llm.plan_next_step(goal, history)

            if self.verbose:
                print(f"[Step {steps+1}] Thought: {thought}")

            if tool_name is None:
                # Final answer reached
                final_answer = (tool_args or {}).get("final", "Done.")
                if self.verbose:
                    print(f"[Step {steps+1}] Final Answer: {final_answer}")
                return {
                    "goal":       goal,
                    "answer":     final_answer,
                    "steps":      steps + 1,
                    "history":    history,
                }

            # ── ACT ─────────────────────────────────────────────────
            if self.verbose:
                print(f"[Step {steps+1}] Action: {tool_name}({tool_args})")

            observation = self.registry.call(tool_name, **(tool_args or {}))

            if self.verbose:
                print(f"[Step {steps+1}] Observation: {str(observation)[:100]}")

            history.append({
                "type":   "action",
                "tool":   tool_name,
                "args":   tool_args,
                "result": observation,
            })

            steps += 1

        return {
            "goal":    goal,
            "answer":  "Reached max steps without a final answer.",
            "steps":   steps,
            "history": history,
        }


# Demo
llm      = ReActLLM(tool_names=registry.names)
executor = AgentExecutor(llm=llm, registry=registry, max_steps=6, verbose=True)

for user_goal in [
    "What is today's date?",
    "What are transformers in AI?",
    "Tell me about RAG",
]:
    result = executor.run(user_goal)
    print(f"→ Completed in {result['steps']} step(s)\n")


# ─────────────────────────────────────────────
# 5. MEMORY TYPES
# ─────────────────────────────────────────────

print("=" * 60)
print("5. AGENT MEMORY TYPES")
print("=" * 60)


class ConversationMemory:
    """Short-term / in-context memory (the conversation history)."""
    def __init__(self, max_messages: int = 20):
        self.messages:    List[dict] = []
        self.max_messages = max_messages

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]  # sliding window

    def as_context(self) -> str:
        return "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self.messages)

    def __len__(self):
        return len(self.messages)


class EpisodicMemory:
    """Long-term memory: past interactions stored and searchable."""
    def __init__(self):
        self.episodes: List[dict] = []

    def store(self, goal: str, outcome: str, steps: int) -> None:
        self.episodes.append({
            "goal":    goal,
            "outcome": outcome,
            "steps":   steps,
            "ts":      time.time(),
        })

    def recall(self, query: str, top_k: int = 3) -> List[dict]:
        """Simple keyword recall (use embeddings in production)."""
        scored = [(ep, sum(w in ep["goal"].lower() for w in query.lower().split()))
                  for ep in self.episodes]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [ep for ep, _ in scored[:top_k]]


class SemanticMemory:
    """Structured facts the agent learns and stores."""
    def __init__(self):
        self._facts: Dict[str, str] = {}

    def store(self, key: str, value: str) -> None:
        self._facts[key] = value

    def recall(self, key: str) -> Optional[str]:
        return self._facts.get(key)

    def list_keys(self) -> List[str]:
        return list(self._facts.keys())


conv  = ConversationMemory(max_messages=10)
epis  = EpisodicMemory()
seman = SemanticMemory()

# Simulate a session
conv.add("user", "What is today's date?")
conv.add("assistant", "Today is 2025-07-01.")
conv.add("user", "And what are transformers?")
conv.add("assistant", "Transformers use self-attention mechanisms.")

epis.store("What is today's date?",          "Answered using get_current_date tool.", 1)
epis.store("What are transformers in AI?",   "Answered with web search.",             2)

seman.store("user_name",       "Alex")
seman.store("preferred_lang",  "Python")
seman.store("last_topic",      "Transformers")

print(f"ConversationMemory  : {len(conv)} messages in context")
print(f"EpisodicMemory      : {len(epis.episodes)} past episodes")
print(f"SemanticMemory keys : {seman.list_keys()}")

# Retrieve relevant episodes
relevant = epis.recall("transformer attention model")
print(f"\nRecalled episode for 'transformer': {relevant[0]['goal'] if relevant else 'none'}")

print("""
  MEMORY TYPE COMPARISON:
  ┌──────────────────┬──────────────────────────┬─────────────────────────┐
  │ Type             │ Content                  │ Lifespan                │
  ├──────────────────┼──────────────────────────┼─────────────────────────┤
  │ In-context       │ Current conversation     │ One session             │
  │ (ConversationMem)│ messages                 │                         │
  │ Episodic         │ Past interactions,       │ Persistent (DB)         │
  │ (EpisodicMem)    │ outcomes, lessons        │                         │
  │ Semantic         │ Long-term facts,         │ Persistent (DB/KV)      │
  │ (SemanticMem)    │ user preferences         │                         │
  │ Working          │ Current task scratch-pad │ Cleared after task      │
  │ (AgentScratchpad)│ (ReAct history)          │                         │
  └──────────────────┴──────────────────────────┴─────────────────────────┘
""")


# ─────────────────────────────────────────────
# 6. PLANNING: TASK DECOMPOSITION
# ─────────────────────────────────────────────

print("=" * 60)
print("6. PLANNING — HIERARCHICAL TASK DECOMPOSITION")
print("=" * 60)

@dataclass
class Task:
    id:          str
    description: str
    depends_on:  List[str] = field(default_factory=list)
    status:      str = "pending"   # pending | running | done | failed
    result:      Any = None


class Planner:
    """
    Decomposes a high-level goal into a DAG of subtasks.
    In production: use an LLM to generate the plan.
    """

    PLANS: Dict[str, List[dict]] = {
        "research_and_summarise": [
            {"id": "T1", "desc": "Search for information about the topic",    "deps": []},
            {"id": "T2", "desc": "Extract key facts from search results",      "deps": ["T1"]},
            {"id": "T3", "desc": "Summarise facts into bullet points",         "deps": ["T2"]},
            {"id": "T4", "desc": "Format summary as a structured report",      "deps": ["T3"]},
        ],
        "date_and_calculate": [
            {"id": "T1", "desc": "Get today's date",             "deps": []},
            {"id": "T2", "desc": "Compute the required formula", "deps": []},
            {"id": "T3", "desc": "Combine date and result",      "deps": ["T1", "T2"]},
        ],
    }

    def create_plan(self, goal: str) -> List[Task]:
        plan_key = "research_and_summarise"
        for key in self.PLANS:
            if key.replace("_", " ") in goal.lower():
                plan_key = key
                break
        return [
            Task(id=t["id"], description=t["desc"], depends_on=t["deps"])
            for t in self.PLANS[plan_key]
        ]

    def execute(self, tasks: List[Task]) -> List[Task]:
        """Execute tasks respecting dependency order (topological sort)."""
        done: set = set()
        for iteration in range(len(tasks) * 2):   # safety loop limit
            ready = [t for t in tasks
                     if t.status == "pending" and all(d in done for d in t.depends_on)]
            if not ready:
                break
            for task in ready:
                task.status = "running"
                # Simulate execution
                task.result = f"Result of: {task.description}"
                task.status = "done"
                done.add(task.id)
        return tasks


planner = Planner()
plan    = planner.create_plan("research and summarise transformers")
plan    = planner.execute(plan)

print("Plan for 'research and summarise transformers':")
for task in plan:
    deps = f"← depends on {task.depends_on}" if task.depends_on else ""
    print(f"  [{task.status.upper():<7}] {task.id}: {task.description} {deps}")


# ─────────────────────────────────────────────
# 7. MULTI-AGENT SYSTEMS
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("7. MULTI-AGENT SYSTEMS")
print("=" * 60)

class SpecialistAgent:
    """A specialised agent with a narrow focus."""
    def __init__(self, name: str, specialty: str, registry: ToolRegistry):
        self.name      = name
        self.specialty = specialty
        self.registry  = registry
        self.llm       = ReActLLM(tool_names=registry.names)

    def handle(self, task: str) -> str:
        """Handle a task within this agent's specialty."""
        if self.specialty == "search":
            result = self.registry.call("search_web", query=task)
            return f"[{self.name}] Searched '{task}': {str(result)[:100]}"
        elif self.specialty == "math":
            # Extract first math-looking token
            expr = re.search(r"[\d\+\-\*\/\^\.]+[\d]", task)
            if expr:
                result = self.registry.call("calculate", expression=expr.group())
                return f"[{self.name}] Calculated '{expr.group()}' = {result}"
            return f"[{self.name}] No expression found in: {task}"
        elif self.specialty == "memory":
            parts  = task.split("=", 1)
            if len(parts) == 2:
                key, val = parts[0].strip(), parts[1].strip()
                self.registry.call("store_memory", key=key, value=val)
                return f"[{self.name}] Stored memory: {key}"
            return f"[{self.name}] Invalid memory task: {task}"
        return f"[{self.name}] Task handled: {task[:60]}"


class OrchestratorAgent:
    """
    Routes high-level goals to specialist agents.
    Pattern: Supervisor / Orchestrator-Workers
    """
    def __init__(self, specialists: List[SpecialistAgent]):
        self.specialists = {s.specialty: s for s in specialists}

    def _classify_task(self, task: str) -> str:
        task_lower = task.lower()
        if any(w in task_lower for w in ["search", "find", "look up", "what is", "who is"]):
            return "search"
        if any(w in task_lower for w in ["calculate", "compute", "+", "*", "-", "/"]):
            return "math"
        if "=" in task and len(task.split("=")) == 2:
            return "memory"
        return "search"   # default

    def run(self, goal: str) -> List[str]:
        """Decompose goal into subtasks and route to specialists."""
        # Simple decomposition: split by semicolon or 'and then'
        subtasks = [s.strip() for s in re.split(r";|and then|, then", goal)
                    if s.strip()]
        results = []
        print(f"  Orchestrator received: '{goal}'")
        print(f"  Decomposed into {len(subtasks)} subtask(s):")
        for subtask in subtasks:
            specialty = self._classify_task(subtask)
            agent     = self.specialists.get(specialty)
            if agent:
                output = agent.handle(subtask)
                results.append(output)
                print(f"    → {output}")
            else:
                results.append(f"No specialist for: {subtask}")
        return results


# Build the multi-agent system
searcher  = SpecialistAgent("search_bot",  "search", registry)
calculator= SpecialistAgent("math_bot",    "math",   registry)
memorizer = SpecialistAgent("memory_bot",  "memory", registry)
orchestra = OrchestratorAgent([searcher, calculator, memorizer])

print("Demo — Multi-agent orchestration:")
orchestra.run("Search for Python language; calculate 256*256; user_name=Alice")


# ─────────────────────────────────────────────
# 8. AGENT FRAMEWORKS OVERVIEW
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("8. AGENT FRAMEWORKS")
print("=" * 60)

print("""
  ┌──────────────────┬─────────────────────────────────────────────────┐
  │ Framework        │ Description / Best For                          │
  ├──────────────────┼─────────────────────────────────────────────────┤
  │ LangChain        │ Most popular; chains, memory, tools, agents.    │
  │                  │ Best for: rapid prototyping, many integrations. │
  │ LangGraph        │ LangChain extension for stateful graph agents.  │
  │                  │ Best for: complex multi-step, cyclic agents.    │
  │ LlamaIndex       │ Focused on RAG + data ingestion pipelines.      │
  │                  │ Best for: document Q&A, knowledge graphs.       │
  │ CrewAI           │ Role-based multi-agent teams with tasks/tools.  │
  │                  │ Best for: collaborative AI crews.               │
  │ AutoGen          │ Microsoft research; multi-agent conversations.  │
  │                  │ Best for: code generation, research agents.     │
  │ Swarm (OpenAI)   │ Lightweight agent handoff patterns.             │
  │                  │ Best for: simple routing, customer service.     │
  │ Pydantic-AI      │ Type-safe agents with Pydantic validation.      │
  │                  │ Best for: production-grade, typed outputs.      │
  └──────────────────┴─────────────────────────────────────────────────┘

  QUICK START (LangChain AgentExecutor):
    from langchain_openai import ChatOpenAI
    from langchain.agents import create_react_agent, AgentExecutor
    from langchain_community.tools import DuckDuckGoSearchRun
    from langchain import hub

    llm    = ChatOpenAI(model="gpt-4o-mini")
    tools  = [DuckDuckGoSearchRun()]
    prompt = hub.pull("hwchase17/react")
    agent  = create_react_agent(llm, tools, prompt)
    exec_  = AgentExecutor(agent=agent, tools=tools, verbose=True)
    exec_.invoke({"input": "What is today's weather in Tokyo?"})

  QUICK START (LangGraph stateful agent):
    from langgraph.prebuilt import create_react_agent
    from langchain_openai import ChatOpenAI
    graph = create_react_agent(ChatOpenAI(), tools)
    result = graph.invoke({"messages": [("user", "Tell me about AI")]})
""")


# ─────────────────────────────────────────────
# 9. SAFETY & LIMITATIONS
# ─────────────────────────────────────────────

print("=" * 60)
print("9. SAFETY & LIMITATIONS")
print("=" * 60)

print("""
  RISKS OF AGENTIC AI:
    Prompt Injection  → malicious data tricks agent into unsafe actions
    Tool Misuse       → agent calls delete/send/post with wrong params
    Infinite Loops    → agent loops forever (always set max_steps)
    Hallucination     → agent invents tool calls that don't exist
    Data Leakage      → agent sends private data to external APIs
    Over-permission   → agent has broader access than needed

  MITIGATIONS:
    ✓ max_steps limit              → always cap the action loop
    ✓ Tool allow-listing           → only expose tools actually needed
    ✓ Human-in-the-loop           → require approval for irreversible actions
    ✓ Input sanitisation           → strip injected instructions from tool outputs
    ✓ Sandboxed code execution     → run generated code in Docker/E2B sandbox
    ✓ Least-privilege tool access  → read-only tools where possible
    ✓ Logging & auditability       → record every tool call for review
    ✓ Confidence thresholds        → abort if LLM uncertainty is high

  HUMAN-IN-THE-LOOP PATTERN:
    def confirm(action: str, args: dict) -> bool:
        print(f"Agent wants to: {action}({args})")
        return input("Allow? [y/N] ").strip().lower() == "y"

    # In agent loop:
    if is_irreversible(tool_name) and not confirm(tool_name, tool_args):
        return "Action cancelled by user."
""")


print("=" * 60)
print("SUMMARY — Agentic AI Patterns")
print("=" * 60)
print("""
  CORE LOOP (ReAct):
    while not done and steps < max_steps:
        thought, tool, args = llm.plan_next_step(goal, history)
        if tool is None: return final_answer
        observation = tool_registry.call(tool, **args)
        history.append(observation)
        steps += 1

  KEY PATTERNS:
    ReAct          → Reason + Act, interleaved thinking and tool use
    CoT            → Chain-of-Thought reasoning before each action
    Plan & Execute → Generate full plan upfront, then execute
    Reflexion      → Agent reflects on failures and retries
    RLHF/RLAIF     → Fine-tune agent with human or AI feedback
    Self-Consistency → Sample multiple plans, vote on best answer

  TOOL TYPES:
    READ-ONLY  → search, read file, query DB, get weather
    WRITE      → store memory, update DB, send email, create file
    CODE       → python exec (sandbox!), bash, API call
    SUBAGENT   → delegate to a specialist LLM agent

  MULTI-AGENT TOPOLOGY:
    Sequential     → A → B → C (pipeline)
    Parallel       → A, B, C all run → aggregator
    Hierarchical   → Orchestrator → spawns workers → collects results
    Peer-to-peer   → agents converse until consensus (AutoGen style)

  PRODUCTION CHECKLIST:
    □ Structured output (Pydantic) for tool calls
    □ Retry with backoff on API errors
    □ Async tool calls for speed
    □ Streaming for user-perceived performance
    □ Persistent memory (Redis/Postgres)
    □ Observability: LangSmith / Phoenix / Langfuse
    □ Cost tracking (token usage per run)
""")
