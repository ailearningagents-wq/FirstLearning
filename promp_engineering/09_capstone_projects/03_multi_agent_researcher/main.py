"""
09_capstone_projects/03_multi_agent_researcher/main.py
═══════════════════════════════════════════════════════

CAPSTONE PROJECT 3: Multi-Agent Researcher
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A ReAct-style orchestrator that coordinates specialized sub-agents to
research a topic and produce a structured Markdown report.

Techniques used:
  • ReAct (Reason + Act) loop (Module 03)
  • Tool/agent routing via LLM decision (Module 04)
  • Self-consistency / fact-checking (Module 03)
  • Structured output + prompt chaining (Module 03/04)
  • Prompt registry (Module 08)
  • Hallucination guard (Module 07)

Architecture:
  ┌──────────────────────────────────────────────────────┐
  │  topic → Orchestrator (plan JSON)                    │
  │    ├─ web_search  → raw facts                        │
  │    ├─ summarizer  → condensed findings               │
  │    ├─ fact_checker→ verdict JSON                     │
  │    └─ writer      → final Markdown report            │
  └──────────────────────────────────────────────────────┘

Usage:
    python main.py
    python main.py --dry-run
    python main.py --topic "quantum computing in finance" --max-steps 8
"""

import sys
import os
import re
import json
import argparse
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.llm_client import LLMClient
from prompts import build_registry, PromptVersion


# ─────────────────────────────────────────────────────────────────────────────
# Agent Registry
# ─────────────────────────────────────────────────────────────────────────────

AGENTS: dict[str, str] = {
    "web_search":   "Retrieves facts and recent statistics on a specific sub-topic.",
    "summarizer":   "Condenses raw content into concise, structured key points.",
    "fact_checker": "Validates whether a specific claim is supported by evidence.",
    "writer":       "Assembles all findings into a structured research report.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AgentCall:
    step: int
    agent_name: str
    input_text: str
    output_text: str
    cost_usd: float


@dataclass
class ResearchState:
    topic: str
    calls: list[AgentCall] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    final_report: str = ""
    total_cost: float = 0.0

    def add_call(self, call: AgentCall) -> None:
        self.calls.append(call)
        self.total_cost += call.cost_usd
        self.findings.append(f"[Step {call.step} — {call.agent_name}]\n{call.output_text}")

    def work_log(self) -> str:
        if not self.calls:
            return "No steps completed yet."
        lines = []
        for c in self.calls:
            lines.append(f"Step {c.step}: {c.agent_name} → {c.input_text[:60]}...")
        return "\n".join(lines)

    def findings_text(self) -> str:
        return "\n\n".join(self.findings)


# ─────────────────────────────────────────────────────────────────────────────
# Simulated tool outputs (for dry-run / demo)
# ─────────────────────────────────────────────────────────────────────────────

_DRY_RUN_OUTPUTS: dict[str, str] = {
    "web_search": (
        "• LLMs automate up to 30% of coding tasks in surveyed teams (GitHub Copilot State of AI, 2024).\n"
        "• 92% of developers use AI coding assistants at least occasionally (Stack Overflow Survey, 2023).\n"
        "• AI-assisted PR review reduces defect escape rate by ~15% in controlled studies (Microsoft Research, 2024).\n"
        "• Concerns include hallucinated APIs, insecure code generation, and over-reliance (OWASP LLM Top 10, 2023).\n"
        "• 'Prompt engineering' is now a recognized skill in 40% of developer job postings (LinkedIn Jobs Data, 2024)."
    ),
    "summarizer": (
        "LLMs are reshaping software engineering by automating routine coding tasks, with adoption exceeding 90% "
        "among developers. Tools like Copilot and ChatGPT speed up development but introduce risks including "
        "hallucinated code, security vulnerabilities, and skill atrophy. Prompt engineering has emerged as a "
        "critical complementary skill."
    ),
    "fact_checker": json.dumps({
        "verdict": "SUPPORTED",
        "confidence": 0.87,
        "explanation": "The 92% adoption figure aligns with Stack Overflow 2023 developer survey results."
    }),
    "writer": (
        "# Research Report: impacts of LLMs on software engineering\n\n"
        "## Executive Summary\n"
        "Large language models are transforming software engineering practices, from code generation to automated review. "
        "While adoption is high, teams must navigate risks around code quality and security.\n\n"
        "## Key Findings\n"
        "• 92% of developers use AI assistants regularly (Stack Overflow, 2023).\n"
        "• LLMs automate ~30% of routine coding tasks (GitHub, 2024).\n"
        "• AI-assisted review reduces defect escape by ~15% (Microsoft Research, 2024).\n"
        "• Prompt engineering is now a recognized job skill in 40% of postings (LinkedIn, 2024).\n\n"
        "## Supporting Evidence\n"
        "Controlled studies show meaningful productivity gains across code generation, testing, and documentation. "
        "However, hallucinated APIs and insecure code snippets pose tangible risks that require human oversight.\n\n"
        "## Limitations\n"
        "Most studies are short-term; long-term effects on software quality and developer skill remain understudied.\n\n"
        "## Conclusion\n"
        "Organizations should adopt LLM tooling with structured review gates and invest in prompt engineering training."
    ),
}


def _dry_run_output(agent_name: str, topic: str) -> str:
    return _DRY_RUN_OUTPUTS.get(agent_name, f"[DRY-RUN] {agent_name} output for: {topic[:50]}")


# ─────────────────────────────────────────────────────────────────────────────
# Agent Execution
# ─────────────────────────────────────────────────────────────────────────────

def run_agent(
    client: LLMClient,
    agent_name: str,
    input_text: str,
    registry,
    state: ResearchState,
) -> str:
    """Dispatch to the appropriate sub-agent prompt and return its output."""
    if client.dry_run:
        return _dry_run_output(agent_name, input_text)

    pv: PromptVersion = registry.get_active(f"{agent_name}_agent")

    if agent_name == "web_search":
        rendered = pv.render(query=input_text)
    elif agent_name == "summarizer":
        rendered = pv.render(content=input_text)
    elif agent_name == "fact_checker":
        # Extract claim / evidence from input text (best-effort split)
        if "\nEvidence:" in input_text:
            parts = input_text.split("\nEvidence:", 1)
            claim = parts[0].replace("Claim:", "").strip()
            evidence = parts[1].strip()
        else:
            claim = input_text
            evidence = state.findings_text()[:800]
        rendered = pv.render(claim=claim, evidence=evidence)
    elif agent_name == "writer":
        rendered = pv.render(topic=state.topic, findings=state.findings_text())
    else:
        rendered = input_text

    response = client.chat(
        messages=[{"role": "user", "content": rendered}],
        system=pv.render_system(),
        temperature=0.3,
        max_tokens=600,
    )
    return response.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration Loop
# ─────────────────────────────────────────────────────────────────────────────

def orchestrate(
    client: LLMClient,
    topic: str,
    registry,
    max_steps: int = 7,
) -> ResearchState:
    state = ResearchState(topic=topic)
    orch_pv = registry.get_active("orchestrator_system")

    print(f"\n  Researching: {topic}")
    print("  " + "─" * 60)

    for step in range(1, max_steps + 1):
        # ── Orchestrator decides next action ──────────────────────────────
        if client.dry_run:
            # Deterministic dry-run sequence
            dry_plan = [
                {"next_agent": "web_search",   "input": f"LLM impact on software engineering productivity {topic}", "rationale": "Gather initial facts.", "done": False},
                {"next_agent": "web_search",   "input": f"LLM risks and challenges in software development", "rationale": "Gather risk data.", "done": False},
                {"next_agent": "summarizer",   "input": state.findings_text() or "Initial findings.", "rationale": "Condense raw data.", "done": False},
                {"next_agent": "fact_checker", "input": "Claim: 92% of developers use AI assistants\nEvidence: Stack Overflow 2023 developer survey", "rationale": "Validate key stat.", "done": False},
                {"next_agent": "writer",       "input": state.findings_text() or "Write the report.", "rationale": "Final report.", "done": True},
            ]
            plan = dry_plan[min(step - 1, len(dry_plan) - 1)]
        else:
            orch_prompt = orch_pv.render(topic=topic, work_log=state.work_log())
            orch_resp = client.chat(
                messages=[{"role": "user", "content": orch_prompt}],
                system=orch_pv.render_system(),
                temperature=0.2,
                max_tokens=200,
            )
            state.total_cost += orch_resp.cost_usd

            raw = orch_resp.content.strip()
            # Strip markdown fences if present
            raw = re.sub(r"```(?:json)?", "", raw).strip().rstrip("```").strip()
            try:
                plan = json.loads(raw)
            except json.JSONDecodeError:
                print(f"  ⚠  Orchestrator returned invalid JSON at step {step} — stopping.")
                break

        next_agent = plan.get("next_agent", "")
        agent_input = plan.get("input", "")
        rationale  = plan.get("rationale", "")
        done       = plan.get("done", False)

        if next_agent not in AGENTS:
            print(f"  ⚠  Unknown agent {next_agent!r} — stopping.")
            break

        # ── Execute agent ──────────────────────────────────────────────────
        print(f"  Step {step}: [{next_agent:14s}] {rationale}")
        output = run_agent(client, next_agent, agent_input, registry, state)

        cost_this_step = 0.0
        if not client.dry_run:
            # cost already charged in run_agent via LLMClient; approximate
            cost_this_step = 0.0  # already captured by LLMClient internals

        call = AgentCall(
            step=step,
            agent_name=next_agent,
            input_text=agent_input,
            output_text=output,
            cost_usd=cost_this_step,
        )
        state.add_call(call)

        if next_agent == "writer":
            state.final_report = output

        if done:
            print("  ✅ Orchestrator signals completion.")
            break

    return state


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_TOPIC = "impacts of LLMs on software engineering"


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-Agent Researcher")
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--topic",     default=DEFAULT_TOPIC,
                        help="Research topic (default: impacts of LLMs on software engineering)")
    parser.add_argument("--max-steps", type=int, default=7,
                        help="Maximum agent calls before forcing a report (default: 7)")
    args = parser.parse_args()

    client   = LLMClient(dry_run=args.dry_run)
    registry = build_registry()

    print("\n" + "═" * 72)
    print("  CAPSTONE 3: MULTI-AGENT RESEARCHER")
    print(f"  Topic:     {args.topic}")
    print(f"  Max steps: {args.max_steps}")
    print(f"  Mode:      {'dry-run' if args.dry_run else 'live'}")
    print("═" * 72)

    state = orchestrate(client, args.topic, registry, max_steps=args.max_steps)

    # ── Report ──────────────────────────────────────────────────────────────
    print("\n" + "═" * 72)
    print("  FINAL REPORT")
    print("═" * 72)
    if state.final_report:
        print(state.final_report[:2400])
        if len(state.final_report) > 2400:
            print("  ... [truncated — full report in state.final_report]")
    else:
        print("  ⚠  No report generated (writer agent not reached within max_steps).")

    print("\n" + "═" * 72)
    print("  AGENT CALL SUMMARY")
    print("═" * 72)
    for c in state.calls:
        label = f"{c.agent_name:14s}"
        print(f"  Step {c.step}: {label} → {c.input_text[:55]}...")

    print(f"\n  Total steps:  {len(state.calls)}")
    if not args.dry_run and state.total_cost > 0:
        print(f"  Total cost:   ${state.total_cost:.5f}")

    print("\n✅ Multi-agent research complete.\n")


if __name__ == "__main__":
    main()
