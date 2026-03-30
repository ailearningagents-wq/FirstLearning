"""
08_frameworks_and_tools/05_prompt_management.py
═══════════════════════════════════════════════════════════════════

WHAT: A lightweight in-process prompt registry that provides:
      1. Prompt versioning (store multiple versions of the same prompt)
      2. Metadata tracking (author, date, tags, notes)
      3. A/B version comparison on demand
      4. Rendering with variable substitution
      5. Export/import to JSONL for persistence

WHY:  Prompts are code. They should be version-controlled, documented,
      and retrievable — not scattered in f-strings across your codebase.

WHEN: Any project with more than 5 distinct prompts used in production.

PITFALLS:
  - Don't over-engineer this. Use this file as a template; a real
    system would use a database per environment.
  - Avoid storing full conversation history in the registry — only
    the *template* (with variables).
  - Version IDs should be immutable once published; create a new version
    instead of editing an existing one.

Usage:
    python 05_prompt_management.py
    python 05_prompt_management.py --dry-run
    python 05_prompt_management.py --export prompts.jsonl
    python 05_prompt_management.py --load  prompts.jsonl
"""

import sys
import os
import json
import argparse
import hashlib
import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Registry
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromptVersion:
    prompt_id: str               # e.g., "ticket_summary"
    version: str                 # semver-like e.g., "1.0", "1.1", "2.0"
    template: str                # prompt text with {variable} placeholders
    system_template: str = ""    # optional system prompt
    description: str = ""        # human-readable explanation
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    active: bool = False         # only one version per prompt_id should be active

    @property
    def hash(self) -> str:
        return hashlib.sha256((self.template + self.system_template).encode()).hexdigest()[:12]

    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)

    def render_system(self, **kwargs) -> str:
        return self.system_template.format(**kwargs) if self.system_template else ""


class PromptRegistry:
    """In-memory prompt registry with file export/import."""

    def __init__(self):
        self._store: dict[str, dict[str, PromptVersion]] = {}  # {prompt_id: {version: PromptVersion}}

    def register(self, pv: PromptVersion) -> None:
        if pv.prompt_id not in self._store:
            self._store[pv.prompt_id] = {}
        self._store[pv.prompt_id][pv.version] = pv

    def activate(self, prompt_id: str, version: str) -> None:
        """Set a version as the active/production version."""
        versions = self._store.get(prompt_id, {})
        for v in versions.values():
            v.active = False
        if version in versions:
            versions[version].active = True

    def get_active(self, prompt_id: str) -> Optional[PromptVersion]:
        versions = self._store.get(prompt_id, {})
        for pv in versions.values():
            if pv.active:
                return pv
        # Fallback: latest version
        if versions:
            return sorted(versions.values(), key=lambda x: x.created_at)[-1]
        return None

    def get_version(self, prompt_id: str, version: str) -> Optional[PromptVersion]:
        return self._store.get(prompt_id, {}).get(version)

    def list_prompts(self) -> list[tuple[str, list[str]]]:
        return [(pid, sorted(vs.keys())) for pid, vs in self._store.items()]

    def prompt_ids(self) -> list[str]:
        return list(self._store.keys())

    def export_jsonl(self, path: str) -> None:
        with open(path, "w") as f:
            for versions in self._store.values():
                for pv in versions.values():
                    f.write(json.dumps(asdict(pv)) + "\n")
        print(f"  Exported {sum(len(vs) for vs in self._store.values())} prompt versions → {path}")

    def load_jsonl(self, path: str) -> int:
        count = 0
        with open(path) as f:
            for line in f:
                data = json.loads(line.strip())
                # Remove computed property from stored data if present
                data.pop("hash", None)
                self.register(PromptVersion(**data))
                count += 1
        return count

    def diff(self, prompt_id: str, version_a: str, version_b: str) -> list[str]:
        """Simple line diff between two versions."""
        pv_a = self.get_version(prompt_id, version_a)
        pv_b = self.get_version(prompt_id, version_b)
        if not pv_a or not pv_b:
            return ["One or both versions not found"]
        lines_a = pv_a.template.splitlines()
        lines_b = pv_b.template.splitlines()
        diffs = []
        for i, (a, b) in enumerate(zip(lines_a, lines_b)):
            if a != b:
                diffs.append(f"  Line {i+1}: - {a}")
                diffs.append(f"  Line {i+1}: + {b}")
        if len(lines_a) != len(lines_b):
            diffs.append(f"  Line count: {len(lines_a)} → {len(lines_b)}")
        return diffs or ["  (no differences)"]


# ─────────────────────────────────────────────────────────────────────────────
# Pre-built prompt library
# ─────────────────────────────────────────────────────────────────────────────

def build_registry() -> PromptRegistry:
    reg = PromptRegistry()

    # ticket_summary v1.0
    reg.register(PromptVersion(
        prompt_id="ticket_summary",
        version="1.0",
        template="Summarize this support ticket in one sentence:\n\n{ticket}",
        description="Basic ticket summarizer",
        author="alice",
        tags=["support", "summarization"],
    ))

    # ticket_summary v1.1 — adds role context
    reg.register(PromptVersion(
        prompt_id="ticket_summary",
        version="1.1",
        template="You are a CloudSync support analyst.\nSummarize this ticket in one concise sentence, noting the customer's core issue and urgency:\n\n{ticket}",
        description="Added role context and urgency signal",
        author="alice",
        tags=["support", "summarization"],
        notes="A/B tested vs 1.0 — 12% ROUGE improvement. Deploying as active.",
        active=True,
    ))

    # sentiment v1.0
    reg.register(PromptVersion(
        prompt_id="sentiment_classify",
        version="1.0",
        template="Classify the sentiment of this text as positive, negative, or neutral.\nOutput ONLY the label.\n\nText: {text}",
        description="Simple sentiment classifier",
        author="bob",
        tags=["classification", "sentiment"],
        active=True,
    ))

    # rag_answer v1.0
    reg.register(PromptVersion(
        prompt_id="rag_answer",
        version="1.0",
        system_template="You are a helpful assistant for {product_name}. Answer using ONLY the context provided.",
        template="Context:\n{context}\n\nQuestion: {question}\n\nAnswer:",
        description="RAG answer synthesizer with grounding instruction",
        author="carol",
        tags=["rag", "qa", "support"],
        active=True,
    ))

    # code_review v1.0
    reg.register(PromptVersion(
        prompt_id="code_review",
        version="1.0",
        template=(
            "Review this code for:\n"
            "1. Bugs and logic errors\n"
            "2. Security vulnerabilities (OWASP)\n"
            "3. Performance issues\n"
            "4. Style and readability\n\n"
            "Code:\n```{language}\n{code}\n```\n\n"
            "Provide findings as a structured list with severity (critical/high/medium/low)."
        ),
        system_template="You are a senior software engineer doing a security-focused code review.",
        description="Code review with OWASP security focus",
        author="dave",
        tags=["code", "security", "review"],
        active=True,
    ))

    return reg


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Registry and Versioning")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--export", metavar="FILE", help="Export registry to JSONL")
    parser.add_argument("--load",   metavar="FILE", help="Load registry from JSONL")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 08 — Frameworks: Prompt Management")
    print("══════════════════════════════════════════════════════════════════════")

    # Build registry
    reg = build_registry()

    if args.load:
        count = reg.load_jsonl(args.load)
        print(f"  Loaded {count} prompt versions from {args.load}")

    # ── Section 1: Registry overview ────────────────────────────────────────
    print("\n  ── 1. Registered Prompts")
    for pid, versions in reg.list_prompts():
        active_pv = reg.get_active(pid)
        active_v  = next((v for v, pv in reg._store[pid].items() if pv.active), "none")
        print(f"  {pid:<24} versions: {', '.join(versions):<12} active: {active_v}")
        if active_pv:
            print(f"    hash: {active_pv.hash}  tags: {active_pv.tags}")

    # ── Section 2: Render and use a prompt ─────────────────────────────────
    print("\n  ── 2. Render + Use Active Prompt")
    pv = reg.get_active("ticket_summary")
    if pv:
        ticket = "I can't log in after the password reset, my whole team is blocked for 2 hours."
        rendered_prompt = pv.render(ticket=ticket)
        print(f"  Prompt ID: {pv.prompt_id} v{pv.version}")
        print(f"  Hash: {pv.hash}")
        print(f"  Rendered: {rendered_prompt[:100]}...")

        response = client.chat(
            messages=[{"role": "user", "content": rendered_prompt}],
            temperature=0.1, max_tokens=60,
        )
        result = response.content.strip() if not client.dry_run else "[DRY-RUN]"
        print(f"  Response: {result}")

    # ── Section 3: Version diff ─────────────────────────────────────────────
    print("\n  ── 3. Version Diff (ticket_summary v1.0 → v1.1)")
    diffs = reg.diff("ticket_summary", "1.0", "1.1")
    for d in diffs:
        print(f"  {d}")

    # ── Section 4: A/B test via registry ────────────────────────────────────
    print("\n  ── 4. Run Both Versions Side-by-Side")
    for version in ["1.0", "1.1"]:
        pv = reg.get_version("ticket_summary", version)
        if pv:
            rendered = pv.render(ticket=ticket)
            response = client.chat(
                messages=[{"role": "user", "content": rendered}],
                temperature=0.1, max_tokens=60,
            )
            result = response.content.strip() if not client.dry_run else f"[DRY-RUN v{version}]"
            print(f"  v{version}: {result[:80]}")

    # ── Section 5: Export ────────────────────────────────────────────────────
    if args.export:
        reg.export_jsonl(args.export)

    # ── Section 6: Governance checklist ─────────────────────────────────────
    print("\n  ── 5. Prompt Governance Checklist")
    checks = [
        ("Prompts stored in registry (not f-strings)",   True),
        ("Each prompt has author + description",         True),
        ("Active version explicitly set",                True),
        ("Versions tagged for easy filtering",           True),
        ("Diff between versions documented",             True),
        ("A/B test results recorded in notes field",     True),
        ("Registry exported to persistent storage",      bool(args.export)),
    ]
    for desc, done in checks:
        print(f"  {'✅' if done else '⬜'} {desc}")

    print("\n✅ Prompt management complete.\n")


if __name__ == "__main__":
    main()
