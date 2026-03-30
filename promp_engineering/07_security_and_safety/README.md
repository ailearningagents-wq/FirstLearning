# Module 07 — Security and Safety

> LLMs are powerful, but they can be manipulated, coaxed into leaking data, or used to generate harmful content. This module teaches you to build defensively.

## Learning Objectives

After completing this module you will be able to:

- Demonstrate common prompt injection and jailbreak attack patterns
- Apply structural and semantic defenses against injection attacks
- Detect and redact PII from text before it enters an LLM
- Reason through ethical considerations: bias, fairness, and harm avoidance
- Build a layered defense-in-depth strategy for LLM-powered systems

---

## The Security Mindset for LLM Systems

Unlike traditional software vulnerabilities (buffer overflows, SQL injection), LLM security is partly *contextual* and *probabilistic*. A defense may work 99% of the time and still fail. This means:

1. **Defense in depth** — multiple overlapping layers
2. **Assume breach** — design for when the model outputs something unexpected
3. **Log everything** — you need forensics when incidents happen
4. **Human review** — keep humans in the loop for high-stakes decisions

---

## The OWASP LLM Top 10

| Rank | Vulnerability | Covered In |
|---|---|---|
| LLM01 | Prompt Injection | `01_prompt_injection.py` |
| LLM02 | Insecure Output Handling | `02_defense_strategies.py` |
| LLM03 | Training Data Poisoning | (out of scope for this course) |
| LLM04 | Model Denial of Service | `02_defense_strategies.py` |
| LLM05 | Supply-Chain Vulnerabilities | (depends on deployment) |
| LLM06 | Sensitive Information Disclosure | `03_pii_handling.py` |
| LLM07 | Insecure Plugin Design | `02_defense_strategies.py` |
| LLM08 | Excessive Agency | `02_defense_strategies.py` |
| LLM09 | Overreliance | `04_ethical_considerations.py` |
| LLM10 | Model Theft | (out of scope) |

---

## Files in This Module

| File | Topic | Cost (gpt-4o-mini) |
|---|---|---|
| `01_prompt_injection.py` | Attack patterns + detection | ~$0.004 |
| `02_defense_strategies.py` | Input sanitisation, allow-lists, output validation | ~$0.003 |
| `03_pii_handling.py` | PII detection + redaction (regex + optional Presidio) | ~$0.002 |
| `04_ethical_considerations.py` | Bias testing, harm avoidance, responsible deployment | ~$0.005 |

---

## Quick Start

```bash
# Security demos — always safe to run (dry-run shows the attack patterns only)
python 01_prompt_injection.py   --dry-run
python 02_defense_strategies.py --dry-run
python 03_pii_handling.py       --dry-run
python 04_ethical_considerations.py --dry-run
```

---

## Defense Checklist

- [ ] Validate and sanitize all user inputs before injecting into prompts
- [ ] Use separate system/user message roles (never concatenate into one string)
- [ ] Scan outputs for forbidden patterns before displaying to users
- [ ] Redact PII before logging or sending to third-party models
- [ ] Set `max_tokens` to prevent runaway generation costs
- [ ] Maintain an allow-list of permitted intents / actions
- [ ] Log all LLM calls with prompt hash, user ID, and response metadata
- [ ] Run adversarial tests (Module 06) before every deployment
- [ ] Add a human review step for decisions with real-world consequences
