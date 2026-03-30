"""
06_evaluation_and_testing/05_logging_and_observability.py
═══════════════════════════════════════════════════════════════════

WHAT: Structured logging system for LLM calls — captures prompt hash,
      latency, tokens, cost, model, and output; exports to JSONL;
      prints a cost/usage dashboard.

WHY:  Observability is the difference between guessing why your AI
      app is slow/expensive and knowing exactly which prompts are
      the culprits.

WHEN: Always. Wrap every LLM call with a PromptLogger in production.

PITFALLS:
  - Log prompt TEXT sparingly — it's expensive to store and may
    contain PII. Store a hash + metadata by default.
  - Centralize your log store early; retrofitting observability is hard.
  - Use structured (JSONL/JSON) logs so they can be queried.

Usage:
    python 05_logging_and_observability.py
    python 05_logging_and_observability.py --dry-run
    python 05_logging_and_observability.py --dry-run --export logs.jsonl
"""

import sys
import os
import re
import json
import time
import hashlib
import argparse
import datetime
from dataclasses import dataclass, asdict, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient


# ─────────────────────────────────────────────────────────────────────────────
# PromptRecord dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PromptRecord:
    record_id: str
    timestamp: str
    prompt_id: str         # logical name (e.g., "summarize_ticket")
    prompt_hash: str       # SHA-256 of the rendered prompt
    model: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    cost_usd: float
    success: bool
    error: str = ""
    tags: list[str] = field(default_factory=list)
    # prompt text is NOT stored by default for privacy; set store_prompt=True to include
    prompt_text: str = ""
    response_text: str = ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _record_id() -> str:
    return f"rec-{int(time.time() * 1000) % 1_000_000:06d}"


# ─────────────────────────────────────────────────────────────────────────────
# PromptLogger
# ─────────────────────────────────────────────────────────────────────────────

class PromptLogger:
    """Wrap LLMClient calls and capture structured PromptRecords."""

    def __init__(self, client: LLMClient, store_prompts: bool = False):
        self.client = client
        self.store_prompts = store_prompts
        self.records: list[PromptRecord] = []

    def call(
        self,
        prompt_id: str,
        messages: list[dict],
        system: str = "",
        tags: list[str] | None = None,
        **kwargs,
    ) -> str:
        """Execute an LLM call and record metadata. Returns response text."""
        rendered = system + "\n".join(m["content"] for m in messages)
        prompt_hash = _sha256(rendered)

        t0 = time.monotonic()
        success = True
        error_msg = ""
        response_text = ""
        cost_usd = 0.0
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        model = self.client.model or "unknown"
        provider = getattr(self.client, "provider", "unknown")

        try:
            if system:
                response = self.client.chat(messages=messages, system=system, **kwargs)
            else:
                response = self.client.chat(messages=messages, **kwargs)
            response_text = response.content.strip()
            cost_usd = response.cost_usd
            total_tokens = response.total_tokens
            # Estimate split if not available
            prompt_tokens = int(total_tokens * 0.6)
            completion_tokens = total_tokens - prompt_tokens
        except Exception as exc:
            success = False
            error_msg = str(exc)

        latency_ms = (time.monotonic() - t0) * 1000

        record = PromptRecord(
            record_id=_record_id(),
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            prompt_id=prompt_id,
            prompt_hash=prompt_hash,
            model=model,
            provider=provider,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost_usd,
            success=success,
            error=error_msg,
            tags=tags or [],
            prompt_text=rendered[:500] if self.store_prompts else "",
            response_text=response_text[:200] if self.store_prompts else "",
        )
        self.records.append(record)
        return response_text

    def export_jsonl(self, path: str) -> None:
        with open(path, "w") as f:
            for rec in self.records:
                f.write(json.dumps(asdict(rec)) + "\n")
        print(f"  Exported {len(self.records)} records → {path}")


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def print_dashboard(records: list[PromptRecord]) -> None:
    if not records:
        print("  No records to display.")
        return

    print("\n" + "═" * 72)
    print("  OBSERVABILITY DASHBOARD")
    print("═" * 72)

    # ── Per-prompt breakdown ──────────────────────────────────────────────
    by_pid: dict[str, list[PromptRecord]] = {}
    for r in records:
        by_pid.setdefault(r.prompt_id, []).append(r)

    print(f"\n  {'Prompt ID':<28} {'Calls':>5} {'Avg ms':>7} {'Avg tok':>7} {'Total $':>9} {'Err':>4}")
    print("  " + "─" * 60)
    for pid, recs in sorted(by_pid.items()):
        calls    = len(recs)
        avg_lat  = sum(r.latency_ms for r in recs) / calls
        avg_tok  = sum(r.total_tokens for r in recs) / calls
        tot_cost = sum(r.cost_usd for r in recs)
        errors   = sum(1 for r in recs if not r.success)
        print(f"  {pid:<28} {calls:>5} {avg_lat:>7.0f} {avg_tok:>7.0f} {tot_cost:>9.6f} {errors:>4}")

    # ── Aggregate stats ───────────────────────────────────────────────────
    total_calls  = len(records)
    total_tokens = sum(r.total_tokens for r in records)
    total_cost   = sum(r.cost_usd for r in records)
    total_errors = sum(1 for r in records if not r.success)
    avg_latency  = sum(r.latency_ms for r in records) / total_calls
    p95_lat      = sorted(r.latency_ms for r in records)[int(0.95 * total_calls)]

    print("  " + "─" * 60)
    print(f"  {'TOTAL':<28} {total_calls:>5}")
    print()
    print(f"  Total cost:        ${total_cost:.6f}")
    print(f"  Total tokens:      {total_tokens:,}")
    print(f"  Avg latency:       {avg_latency:.0f} ms")
    print(f"  p95 latency:       {p95_lat:.0f} ms")
    print(f"  Error rate:        {100*total_errors/total_calls:.1f}%")

    # ── Cost by model ─────────────────────────────────────────────────────
    by_model: dict[str, float] = {}
    for r in records:
        by_model[r.model] = by_model.get(r.model, 0.0) + r.cost_usd
    if len(by_model) > 1:
        print("\n  Cost by model:")
        for m, c in sorted(by_model.items(), key=lambda x: -x[1]):
            print(f"    {m}: ${c:.6f}")

    # ── Tag summary ───────────────────────────────────────────────────────
    tag_costs: dict[str, float] = {}
    for r in records:
        for tag in r.tags:
            tag_costs[tag] = tag_costs.get(tag, 0.0) + r.cost_usd
    if tag_costs:
        print("\n  Cost by tag:")
        for tag, c in sorted(tag_costs.items(), key=lambda x: -x[1]):
            print(f"    #{tag}: ${c:.6f}")

    print("\n" + "═" * 72)


# ─────────────────────────────────────────────────────────────────────────────
# Demo calls
# ─────────────────────────────────────────────────────────────────────────────

DEMO_CALLS = [
    {
        "prompt_id": "ticket_summary",
        "messages": [{"role": "user", "content": "Summarize in one sentence: Customer can't log in after password reset."}],
        "tags": ["summarization", "support"],
        "temperature": 0.3, "max_tokens": 60,
    },
    {
        "prompt_id": "sentiment_classify",
        "messages": [{"role": "user", "content": "Classify sentiment: 'This product is amazing!'"}],
        "tags": ["classification"],
        "temperature": 0.0, "max_tokens": 10,
    },
    {
        "prompt_id": "ticket_summary",
        "messages": [{"role": "user", "content": "Summarize: User lost 3 months of files after accidental deletion."}],
        "tags": ["summarization", "support"],
        "temperature": 0.3, "max_tokens": 60,
    },
    {
        "prompt_id": "code_explain",
        "messages": [{"role": "user", "content": "Explain in one sentence: def fib(n): return n if n<2 else fib(n-1)+fib(n-2)"}],
        "tags": ["code", "explanation"],
        "temperature": 0.2, "max_tokens": 80,
    },
    {
        "prompt_id": "sentiment_classify",
        "messages": [{"role": "user", "content": "Classify sentiment: 'Worst experience ever, I want a refund.'"}],
        "tags": ["classification"],
        "temperature": 0.0, "max_tokens": 10,
    },
    {
        "prompt_id": "rag_answer",
        "messages": [{"role": "user", "content": "Based on context: [CloudSync Free plan = 10GB]. Q: How much storage do free users get?"}],
        "tags": ["rag", "support"],
        "temperature": 0.1, "max_tokens": 40,
    },
    {
        "prompt_id": "ticket_summary",
        "messages": [{"role": "user", "content": "Summarize: SSO broke after Okta tenant migration, users get 403."}],
        "tags": ["summarization", "support"],
        "temperature": 0.3, "max_tokens": 60,
    },
    {
        "prompt_id": "code_explain",
        "messages": [{"role": "user", "content": "Explain: async def fetch(url): async with aiohttp.ClientSession() as s: r = await s.get(url); return await r.json()"}],
        "tags": ["code", "explanation"],
        "temperature": 0.2, "max_tokens": 80,
    },
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Logging and Observability")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--export", metavar="FILE", help="Export JSONL log to this path")
    parser.add_argument("--store-prompts", action="store_true",
                        help="Include prompt/response text in records (privacy risk)")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)
    logger = PromptLogger(client, store_prompts=args.store_prompts)

    print("\n══════════════════════════════════════════════════════════════════════")
    print("  MODULE 06 — Evaluation: Logging + Observability")
    print("══════════════════════════════════════════════════════════════════════")
    print(f"  Simulating {len(DEMO_CALLS)} LLM calls across 4 prompt types...")

    for call_kwargs in DEMO_CALLS:
        pid = call_kwargs.pop("prompt_id")
        tags = call_kwargs.pop("tags")
        logger.call(prompt_id=pid, tags=tags, **call_kwargs)
        # restore for loop idempotency
        call_kwargs["prompt_id"] = pid
        call_kwargs["tags"] = tags

    print_dashboard(logger.records)

    if args.export:
        logger.export_jsonl(args.export)

    print("\n  SAMPLE RECORD (JSON)")
    sample = asdict(logger.records[0])
    for k, v in sample.items():
        if v or k in ("cost_usd", "total_tokens"):
            print(f"    {k}: {v!r}")

    print("\n✅ Logging and observability complete.\n")


if __name__ == "__main__":
    main()
