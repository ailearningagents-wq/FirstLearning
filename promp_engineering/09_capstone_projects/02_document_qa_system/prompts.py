"""
09_capstone_projects/02_document_qa_system/prompts.py
═══════════════════════════════════════════════════════════════════

All prompts for the Document Q&A system.
"""

import sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PromptVersion:
    prompt_id: str
    version: str
    template: str
    system_template: str = ""
    description: str = ""
    active: bool = False
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    tags: list[str] = field(default_factory=list)

    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)

    def render_system(self, **kwargs) -> str:
        return self.system_template.format(**kwargs) if self.system_template else ""


class PromptRegistry:
    def __init__(self):
        self._store: dict[str, dict[str, PromptVersion]] = {}

    def register(self, pv: PromptVersion) -> None:
        if pv.prompt_id not in self._store:
            self._store[pv.prompt_id] = {}
        self._store[pv.prompt_id][pv.version] = pv

    def get_active(self, prompt_id: str) -> Optional[PromptVersion]:
        versions = self._store.get(prompt_id, {})
        for pv in versions.values():
            if pv.active: return pv
        return sorted(versions.values(), key=lambda x: x.created_at)[-1] if versions else None


def build_registry() -> PromptRegistry:
    reg = PromptRegistry()

    reg.register(PromptVersion(
        prompt_id="qa_synthesize",
        version="1.0",
        system_template=(
            "You are a precise document analyst.\n"
            "Answer questions using ONLY the provided context chunks.\n"
            "If the answer is not in the context, respond exactly: NOT_IN_CONTEXT\n"
            "Always cite the source document ID(s) in square brackets at the end, e.g. [doc-001]."
        ),
        template=(
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer (with citations):"
        ),
        description="RAG synthesis with mandatory citations and NOT_IN_CONTEXT fallback",
        tags=["rag", "qa", "citations"],
        active=True,
    ))

    reg.register(PromptVersion(
        prompt_id="hallucination_check",
        version="1.0",
        template=(
            "Does this answer contain information NOT found in the context below?\n"
            "Output ONLY: YES or NO\n\n"
            "Context:\n{context}\n\n"
            "Answer to check:\n{answer}"
        ),
        description="Hallucination detector — checks if answer goes beyond context",
        tags=["safety", "hallucination", "validation"],
        active=True,
    ))

    return reg
