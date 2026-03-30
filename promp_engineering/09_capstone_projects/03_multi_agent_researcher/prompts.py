"""
09_capstone_projects/03_multi_agent_researcher/prompts.py
══════════════════════════════════════════════════════════

Prompt registry for the Multi-Agent Researcher system.

Agents:
    orchestrator   — plans next step as a JSON action
    web_search     — simulates web retrieval, returns bullet facts
    summarizer     — condenses long passages into key points
    fact_checker   — validates a claim against evidence
    writer         — assembles a structured research report

Usage:
    from prompts import build_registry
    registry = build_registry()
    orchestrator_pv = registry.get_active("orchestrator_system")
"""

from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Minimal PromptRegistry (self-contained for the capstone)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromptVersion:
    name: str
    version: str
    system_template: str
    user_template: str
    model: str = "gpt-4o-mini"
    metadata: dict = field(default_factory=dict)

    @property
    def hash(self) -> str:
        raw = self.system_template + self.user_template
        return hashlib.md5(raw.encode()).hexdigest()[:8]

    def render(self, **kwargs: Any) -> str:
        return self.user_template.format(**kwargs)

    def render_system(self, **kwargs: Any) -> str:
        return self.system_template.format(**kwargs) if kwargs else self.system_template


class PromptRegistry:
    def __init__(self) -> None:
        self._store: dict[str, list[PromptVersion]] = {}
        self._active: dict[str, str] = {}

    def register(self, pv: PromptVersion) -> None:
        self._store.setdefault(pv.name, []).append(pv)
        self._active[pv.name] = pv.version

    def activate(self, name: str, version: str) -> None:
        if name not in self._store:
            raise KeyError(name)
        versions = [p.version for p in self._store[name]]
        if version not in versions:
            raise ValueError(f"Version {version!r} not found for {name!r}. Available: {versions}")
        self._active[name] = version

    def get_active(self, name: str) -> PromptVersion:
        version = self._active.get(name)
        if not version:
            raise KeyError(name)
        for pv in self._store[name]:
            if pv.version == version:
                return pv
        raise RuntimeError(f"Internal error: active version {version!r} not found for {name!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Definitions
# ─────────────────────────────────────────────────────────────────────────────

PROMPTS: list[dict] = [
    # ── Orchestrator ──────────────────────────────────────────────────────────
    {
        "name": "orchestrator_system",
        "version": "1.0",
        "system_template": (
            "You are a research orchestrator. Your job is to decompose a research topic "
            "into a sequence of atomic tasks and assign each task to the most suitable agent.\n\n"
            "Available agents:\n"
            "  - web_search   : Retrieves facts and recent data on a specific sub-topic.\n"
            "  - summarizer   : Condenses a passage into concise key points.\n"
            "  - fact_checker : Validates whether a specific claim is supported by evidence.\n"
            "  - writer       : Assembles accumulated findings into a structured report.\n\n"
            "Rules:\n"
            "1. Use web_search to gather information before summarizing.\n"
            "2. Use fact_checker to validate any critical numerical claim.\n"
            "3. Call writer only when sufficient findings are accumulated.\n"
            "4. Return ONLY valid JSON — no prose, no markdown fences.\n"
            "5. Set done:true ONLY when writer has produced a final report."
        ),
        "user_template": (
            "Research topic: {topic}\n\n"
            "Work completed so far:\n{work_log}\n\n"
            "Respond with a JSON object:\n"
            "{{\n"
            '  "next_agent": "<agent_name>",\n'
            '  "input": "<specific instruction for that agent>",\n'
            '  "rationale": "<one sentence why this step next>",\n'
            '  "done": false\n'
            "}}\n"
            "Or, if all key aspects are covered, set done:true to finalize."
        ),
        "metadata": {"tags": ["orchestration", "planning", "multi-agent"], "use_case": "ReAct loop"},
    },
    # ── Web Search Agent ─────────────────────────────────────────────────────
    {
        "name": "web_search_agent",
        "version": "1.0",
        "system_template": (
            "You are a web research specialist. Given a specific search query, you retrieve "
            "relevant facts, statistics, and references from credible sources.\n\n"
            "Output format:\n"
            "• Return 4-6 bullet points of concrete, citable facts.\n"
            "• Each bullet should include a notional source in parentheses, e.g. (GitHub, 2024) "
            "or (Stack Overflow Developer Survey, 2023).\n"
            "• Prefer quantitative data, named tools, and specific examples.\n"
            "• Do NOT summarize — provide raw facts that other agents can summarize or verify."
        ),
        "user_template": (
            "Search query: {query}\n\n"
            "Return bullet-point facts relevant to this query."
        ),
        "metadata": {"tags": ["retrieval", "web-search"], "use_case": "Information gathering"},
    },
    # ── Summarizer Agent ─────────────────────────────────────────────────────
    {
        "name": "summarizer_agent",
        "version": "1.0",
        "system_template": (
            "You are a research summarizer. You receive raw, unstructured content and "
            "produce a tight, accurate summary that preserves all key insights.\n\n"
            "Rules:\n"
            "1. Keep the summary to 80-120 words.\n"
            "2. Highlight the most significant finding in the first sentence.\n"
            "3. Preserve numerical facts exactly — do not paraphrase statistics.\n"
            "4. Do not introduce information not present in the input."
        ),
        "user_template": (
            "Content to summarize:\n{content}\n\n"
            "Produce a concise research summary."
        ),
        "metadata": {"tags": ["summarization", "compression"], "use_case": "Condense findings"},
    },
    # ── Fact-Checker Agent ───────────────────────────────────────────────────
    {
        "name": "fact_checker_agent",
        "version": "1.0",
        "system_template": (
            "You are a rigorous fact-checker. Given a claim and supporting evidence, "
            "you assess whether the evidence supports, contradicts, or is insufficient "
            "to verify the claim.\n\n"
            "Output format (JSON object):\n"
            "{{\n"
            '  "verdict": "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "explanation": "<one or two sentences>"\n'
            "}}\n"
            "Return ONLY the JSON object."
        ),
        "user_template": (
            "Claim: {claim}\n\n"
            "Evidence:\n{evidence}\n\n"
            "Return your fact-check verdict as JSON."
        ),
        "metadata": {"tags": ["verification", "fact-checking"], "use_case": "Validate claims"},
    },
    # ── Writer Agent ─────────────────────────────────────────────────────────
    {
        "name": "writer_agent",
        "version": "1.0",
        "system_template": (
            "You are a professional research writer. You receive a collection of findings "
            "and produce a well-structured, readable research report in Markdown.\n\n"
            "Report structure (required sections):\n"
            "# Research Report: <topic>\n\n"
            "## Executive Summary\n"
            "(2-3 sentence overview)\n\n"
            "## Key Findings\n"
            "(4-6 bullet points, each with a supporting data point)\n\n"
            "## Supporting Evidence\n"
            "(2-3 paragraphs of detailed analysis)\n\n"
            "## Limitations\n"
            "(1-2 paragraphs on gaps, caveats, or areas needing further research)\n\n"
            "## Conclusion\n"
            "(1 paragraph with actionable takeaways)\n\n"
            "Style guidelines:\n"
            "• Use Markdown headings, bold for key terms, and bullet lists.\n"
            "• No hallucinated data — use only the findings provided.\n"
            "• Cite sources inline as (Source, Year) where available."
        ),
        "user_template": (
            "Research topic: {topic}\n\n"
            "Accumulated findings:\n{findings}\n\n"
            "Write the complete research report in Markdown."
        ),
        "metadata": {"tags": ["writing", "reporting", "markdown"], "use_case": "Final report generation"},
    },
]


def build_registry() -> PromptRegistry:
    registry = PromptRegistry()
    for p in PROMPTS:
        registry.register(PromptVersion(
            name=p["name"],
            version=p["version"],
            system_template=p["system_template"],
            user_template=p["user_template"],
            metadata=p.get("metadata", {}),
        ))
    return registry


if __name__ == "__main__":
    reg = build_registry()
    for name in ["orchestrator_system", "web_search_agent", "summarizer_agent",
                 "fact_checker_agent", "writer_agent"]:
        pv = reg.get_active(name)
        print(f"  {pv.name:30s} v{pv.version}  hash={pv.hash}")
    print("\n✅ Multi-agent researcher prompt registry loaded.\n")
