"""
09_capstone_projects/01_ai_email_assistant/prompts.py
═══════════════════════════════════════════════════════════════════

All prompts for the AI Email Assistant, versioned in a PromptRegistry.
Import this module and call build_registry() to get the prompt registry.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dataclasses import dataclass, field
from typing import Optional
import hashlib, datetime, json


# ─────────────────────────────────────────────────────────────────────────────
# Minimal PromptRegistry (standalone copy so this project is self-contained)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromptVersion:
    prompt_id: str
    version: str
    template: str
    system_template: str = ""
    description: str = ""
    author: str = "capstone"
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    tags: list[str] = field(default_factory=list)
    active: bool = False

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
            if pv.active:
                return pv
        return sorted(versions.values(), key=lambda x: x.created_at)[-1] if versions else None


def build_registry() -> PromptRegistry:
    reg = PromptRegistry()

    # ── Email Classification ────────────────────────────────────────────────
    reg.register(PromptVersion(
        prompt_id="email_classify",
        version="1.0",
        system_template=(
            "You are an email triage assistant for a SaaS company.\n"
            "Classify emails into one of these categories and determine urgency.\n"
            "Output ONLY valid JSON with keys: category, urgency, action_required, summary.\n"
            "Categories: billing | technical_support | feature_request | partnership | spam | other\n"
            "Urgency: critical | high | medium | low\n"
            "action_required: true | false"
        ),
        template=(
            "Classify this email:\n\n"
            "From: {sender}\n"
            "Subject: {subject}\n"
            "Body:\n{body}\n\n"
            "Return JSON only."
        ),
        description="Email classifier with category + urgency + action_required",
        tags=["classification", "email", "triage"],
        active=True,
    ))

    # ── Reply Drafting ───────────────────────────────────────────────────────
    reg.register(PromptVersion(
        prompt_id="email_reply_draft",
        version="1.0",
        system_template=(
            "You are a professional customer success manager at CloudSync Pro.\n"
            "Write helpful, warm, and concise email replies.\n"
            "Guidelines:\n"
            "- Address the customer by name if available\n"
            "- Acknowledge their specific issue\n"
            "- Provide a clear next step or resolution\n"
            "- Keep replies under 150 words\n"
            "- Close with: 'Best regards, CloudSync Support Team'"
        ),
        template=(
            "Draft a reply to this {category} email.\n\n"
            "Original Email:\n"
            "From: {sender}\n"
            "Subject: {subject}\n"
            "Body: {body}\n\n"
            "Additional context: {context}\n\n"
            "Draft the reply:"
        ),
        description="Email reply drafter with role + category context",
        tags=["email", "reply", "drafting"],
        active=True,
    ))

    # ── Action Extraction ────────────────────────────────────────────────────
    reg.register(PromptVersion(
        prompt_id="email_actions",
        version="1.0",
        template=(
            "Extract a list of required follow-up actions from this email.\n"
            "Output as JSON array of objects with keys: action, owner, priority, due_date.\n\n"
            "Email category: {category}\n"
            "Email summary: {summary}\n"
            "Reply drafted: {reply}\n\n"
            "Return JSON array only. If no actions needed, return []."
        ),
        description="Extract actionable tasks from email + drafted reply",
        tags=["extraction", "actions", "email"],
        active=True,
    ))

    return reg
