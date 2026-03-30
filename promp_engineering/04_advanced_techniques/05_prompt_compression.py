"""
04_advanced_techniques/05_prompt_compression.py
═══════════════════════════════════════════════════════════════════

WHAT:   Prompt Compression reduces the token count of prompts — especially
        long context documents — while preserving the information needed
        to produce high-quality answers.

        Compression Techniques:
        1. LLM-based Summarization  → Ask the model to condense context
        2. Extractive Filtering     → Keep only the most relevant sentences
        3. Abbreviation/Encoding    → Replace repeated phrases with shorthand
        4. Structural Pruning       → Remove boilerplate, headers, whitespace
        5. Selective Context Window → Split and only include relevant chunks
        6. LLMLingua (library)      → Token-level perplexity-based compression

WHY:    Every token costs money and latency. A 10,000-token context costs
        ~$0.0030 per call with gpt-4o-mini. If you make 1,000 calls/day,
        that's $3/day or $90/month. Compressing to 3,000 tokens saves
        $65/month with no quality loss for most tasks.

COST MATH (gpt-4o-mini at $0.15/M input tokens):
        10,000 tok × 1,000 calls/day × 30 days × $0.00000015 = $45/month
        3,000 tok  × 1,000 calls/day × 30 days × $0.00000015 = $13.50/month
        → 70% compression saves $31.50/month (from this input alone)

WHEN TO USE:
        ✓ RAG pipelines where retrieved chunks are long
        ✓ Chat with context (compressing older turns)
        ✓ Document Q&A (compress the document per question)
        ✓ Pipelines approaching context window limits
        ✗ Short prompts (<500 tokens) — overhead not worth it
        ✗ Tasks where every word of the source matters (legal review, poetry)

QUALITY TRADEOFF:
        Compression level   Quality retention   Cost reduction
        Light (80%)         99%+                ~20% savings
        Medium (50%)        95–98%              ~50% savings
        Heavy (30%)         88–94%              ~70% savings
        Extreme (<20%)      70–85%              ~80% savings
"""

import sys
import os
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens, estimate_cost, format_response


# ─────────────────────────────────────────────────────────────────────────────
# LONG CONTEXT: Simulated RAG retrieved document
# ─────────────────────────────────────────────────────────────────────────────

RETRIEVED_DOCUMENT = """
PRODUCT MANUAL — CloudSync Pro v4.2
Enterprise File Synchronization and Collaboration Platform

================================================================================
INTRODUCTION
================================================================================

CloudSync Pro is a cloud-based file synchronization and collaboration platform
designed for enterprise use. This manual covers installation, configuration,
user management, and troubleshooting for version 4.2.

================================================================================
CHAPTER 1: SYSTEM REQUIREMENTS
================================================================================

For optimal performance, CloudSync Pro v4.2 requires the following:

Operating Systems:
- Windows 10/11 (64-bit) or Windows Server 2019/2022
- macOS 11 (Big Sur) or later
- Ubuntu 20.04 LTS or later
- Red Hat Enterprise Linux 8 or later

Hardware Requirements (per user session):
- CPU: 2 GHz dual-core processor minimum
- RAM: 4 GB minimum, 8 GB recommended  
- Storage: 10 GB for installation, plus space for local sync cache
- Network: 10 Mbps minimum, 100 Mbps recommended for large file sync

Browser Support:
- Google Chrome 90+ (recommended)
- Mozilla Firefox 88+
- Microsoft Edge 90+
- Safari 14+ (macOS only)

================================================================================
CHAPTER 2: INSTALLATION
================================================================================

2.1 Server Installation
-----------------------
The CloudSync server component runs on Linux only. We recommend Ubuntu 22.04 LTS.

Prerequisites:
- Docker Engine 24.0+
- Docker Compose 2.20+
- 16 GB RAM on the server
- Port 443 (HTTPS) open inbound
- Port 5432 (PostgreSQL) open internally only

Installation steps:
1. Download the installer: curl -sSL https://installer.example.com | bash
2. Run the setup wizard: sudo cloudsync-setup
3. Configure SSL certificate (Let's Encrypt or custom)
4. Run database migrations: cloudsync-admin migrate
5. Start services: systemctl start cloudsync

2.2 Client Installation
------------------------
Download the appropriate client for your OS from the admin portal.
The client auto-updates by default. Disable in Settings > Updates > Automatic.

================================================================================
CHAPTER 3: USER MANAGEMENT
================================================================================

3.1 User Roles
---------------
CloudSync Pro supports four user roles:

ADMIN: Full access to all settings, user management, billing, and audit logs.
       Can create/delete workspaces, manage SSO configuration, and access API keys.

MANAGER: Can invite/remove users within their assigned workspaces.
         Can view (but not export) audit logs for their workspaces.
         Cannot access billing or organization-wide settings.

EDITOR: Can create, edit, and delete files/folders in assigned workspaces.
        Can share files with external users (link sharing).
        Cannot manage workspace members.

VIEWER: Read-only access. Can download files but cannot upload, edit, or share.
        Ideal for external contractors or auditors.

3.2 Single Sign-On (SSO) Configuration
----------------------------------------
CloudSync supports SAML 2.0 and OIDC-based SSO.

For SAML setup:
1. Generate SP metadata: Settings > Security > SSO > Download Metadata
2. Upload IdP metadata: Settings > Security > SSO > Upload IdP Metadata
3. Map attributes: email (required), displayName, groups (optional)
4. Test with a non-admin account before enabling for all users
5. Enable: Settings > Security > SSO > Enable SAML

For OIDC setup:
1. Register CloudSync as an OIDC client in your IdP
2. Configure: Settings > Security > SSO > OIDC
3. Enter: Client ID, Client Secret, Discovery URL
4. Set redirect URI: https://your-domain/auth/oidc/callback
5. Test authentication flow

================================================================================
CHAPTER 4: TROUBLESHOOTING
================================================================================

4.1 Sync Errors
----------------

Error: "SYNC_CONFLICT_001" — File Modified Simultaneously
This error occurs when two users edit the same file concurrently. CloudSync
creates a conflict copy with the format: filename_CONFLICT_YYYY-MM-DD_user.ext
Resolution: Download both versions, manually merge, delete the conflict copy.

Error: "NETWORK_TIMEOUT_003" — Connection to sync server failed
Common causes: VPN blocking port 443, corporate proxy misconfiguration.
Check: telnet your-domain 443 should succeed from the client machine.
Fix: Configure exceptions in VPN/proxy for *.cloudsync.example.com

Error: "QUOTA_EXCEEDED_007" — Storage quota exceeded  
Free tier: 10 GB per workspace. Pro: 100 GB. Enterprise: Unlimited.
Resolution: Delete unused files, empty trash, or upgrade plan.

4.2 Performance Issues
-----------------------
If sync is slow (< 5 MB/s on a 100 Mbps connection):
- Check CPU usage on the server (should be < 60% during sync)
- Look for large .git directories in sync scope — exclude them
- Review sync exclusion list: Settings > Sync > Exclusions
- Enable delta sync: Settings > Performance > Delta Sync (default: on)

================================================================================
APPENDIX A: API REFERENCE
================================================================================

Base URL: https://api.cloudsync.example.com/v4

Authentication: Bearer tokens (90-day expiry). Generate at: Settings > API Keys

Common Endpoints:
GET    /files/{workspace_id}           List files in a workspace
POST   /files/{workspace_id}           Upload a file (multipart/form-data)
DELETE /files/{workspace_id}/{file_id} Delete a file
GET    /users                          List organization users (admin only)
POST   /users/invite                   Send invitation email
GET    /audit-log                      Retrieve audit events (admin only)

Rate Limits: 1000 requests/hour per API key. Headers: X-RateLimit-Remaining.

================================================================================
END OF MANUAL
================================================================================
""".strip()

USER_QUESTION = "How do I set up SSO with SAML for our identity provider?"


# ─────────────────────────────────────────────────────────────────────────────
# TECHNIQUE 1: LLM-Based Targeted Summarization
# ─────────────────────────────────────────────────────────────────────────────

def compress_by_summarization(
    client: LLMClient,
    document: str,
    question: str,
    target_tokens: int = 500,
) -> str:
    """Compress a document to target_tokens by summarizing relevant content."""
    prompt = f"""Compress the following document to answer this specific question.
Keep ONLY the content directly relevant to the question.
Target: ~{target_tokens} tokens (about {target_tokens * 4} characters).

QUESTION: {question}

DOCUMENT:
{document}

Compressed version (preserve all facts relevant to the question):"""

    response = client.chat(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=target_tokens + 100,
    )

    if client.dry_run:
        return "[DRY RUN compressed content]"

    return response.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# TECHNIQUE 2: Extractive Filtering (rule-based, no API call)
# ─────────────────────────────────────────────────────────────────────────────

def compress_by_extraction(document: str, question: str, top_n_sentences: int = 15) -> str:
    """
    Keep sentences that contain keywords from the question.
    Fast, free (no LLM call), but less precise than LLM-based.
    """
    # Extract question keywords
    stopwords = {"how", "do", "i", "to", "the", "a", "an", "for", "with", "our", "of", "and", "is"}
    question_words = set(word.lower().strip("?.,!") for word in question.split()) - stopwords

    # Score each paragraph by keyword overlap
    paragraphs = [p.strip() for p in document.split("\n") if p.strip() and len(p.strip()) > 20]

    scored = []
    for para in paragraphs:
        para_lower = para.lower()
        score = sum(1 for word in question_words if word in para_lower)
        scored.append((score, para))

    # Sort by relevance, keep top_n
    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [para for _, para in scored[:top_n_sentences]]

    return "\n".join(relevant)


# ─────────────────────────────────────────────────────────────────────────────
# TECHNIQUE 3: Structural Pruning (remove boilerplate, no API call)
# ─────────────────────────────────────────────────────────────────────────────

def compress_by_pruning(document: str) -> str:
    """Remove structural noise: decorative lines, excessive whitespace, headers."""
    lines = document.split("\n")
    pruned = []
    for line in lines:
        stripped = line.strip()
        # Skip decorative lines (===, ---, ...)
        if re.match(r'^[=\-_*]{3,}$', stripped):
            continue
        # Skip empty lines (but keep single newlines as paragraph breaks)
        if not stripped:
            if pruned and pruned[-1] != "":
                pruned.append("")
            continue
        pruned.append(line)

    return "\n".join(pruned).strip()


# ─────────────────────────────────────────────────────────────────────────────
# COMPRESSION COMPARISON DEMO
# ─────────────────────────────────────────────────────────────────────────────

def demo_compression_techniques(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  DEMO: Compression Technique Comparison")
    print(f"  Document: Product manual ({len(RETRIEVED_DOCUMENT)} chars)")
    print(f"  Question: {USER_QUESTION}")
    print("═" * 68)

    model = "gpt-4o-mini"
    original_tokens = count_tokens(RETRIEVED_DOCUMENT, model)
    original_cost   = estimate_cost(RETRIEVED_DOCUMENT, model, expected_output_tokens=200)

    print(f"\n  Original document: {original_tokens} tokens, estimated cost: ${original_cost:.6f}")
    print(f"  {'─' * 60}")
    print(f"\n  {'Technique':<28} {'Tokens':<10} {'Ratio':<10} {'Cost':<12} {'Free?'}")
    print(f"  {'─' * 28} {'─' * 10} {'─' * 10} {'─' * 12} {'─' * 6}")

    results = {}

    # Pruning (free)
    pruned = compress_by_pruning(RETRIEVED_DOCUMENT)
    pruned_tokens = count_tokens(pruned, model)
    results["Structural Pruning"] = pruned
    print(f"  {'Structural Pruning':<28} {pruned_tokens:<10} "
          f"{pruned_tokens/original_tokens:.0%}      "
          f"${estimate_cost(pruned, model, 200):<11.6f} ✅ Yes")

    # Extraction (free)
    extracted = compress_by_extraction(RETRIEVED_DOCUMENT, USER_QUESTION, top_n_sentences=12)
    extracted_tokens = count_tokens(extracted, model)
    results["Extractive Filtering"] = extracted
    print(f"  {'Extractive Filtering':<28} {extracted_tokens:<10} "
          f"{extracted_tokens/original_tokens:.0%}      "
          f"${estimate_cost(extracted, model, 200):<11.6f} ✅ Yes")

    # LLM Summarization (costs tokens but more precise)
    print(f"\n  Running LLM-based summarization...")
    if not client.dry_run:
        summarized = compress_by_summarization(client, RETRIEVED_DOCUMENT, USER_QUESTION, target_tokens=300)
        summarized_tokens = count_tokens(summarized, model)
        results["LLM Summarization"] = summarized
        print(f"  {'LLM Summarization':<28} {summarized_tokens:<10} "
              f"{summarized_tokens/original_tokens:.0%}      "
              f"${estimate_cost(summarized, model, 200):<11.6f} ❌ Costs")
    else:
        print(f"  {'LLM Summarization':<28} [DRY RUN]")

    # Now answer the question with each compressed version
    print(f"\n  {'─' * 60}")
    print(f"  Testing answer quality with each compressed version:")
    print(f"  {'─' * 60}")

    for technique, compressed_doc in list(results.items())[:2]:  # Only free methods to save cost
        print(f"\n  ── {technique} ───────────────────────────────────────────")
        if client.dry_run:
            print("  [DRY RUN]")
            continue

        answer_response = client.chat(
            messages=[{
                "role": "user",
                "content": f"Based on the following documentation, answer this question:\n\n"
                           f"QUESTION: {USER_QUESTION}\n\n"
                           f"DOCUMENTATION:\n{compressed_doc}"
            }],
            temperature=0.1,
            max_tokens=300,
        )
        print(f"  Answer quality check:")
        answer = answer_response.content.strip()
        # Check for key concepts that should be in a good SAML answer
        quality_checks = ["SAML", "metadata", "IdP", "SSO", "attribute"]
        hits = sum(1 for k in quality_checks if k.lower() in answer.lower())
        print(f"  Answer mentions {hits}/{len(quality_checks)} key concepts")
        print(f"  First line: {answer.split(chr(10))[0][:100]}")


def demo_chat_history_compression(client: LLMClient) -> None:
    """Show how to compress old chat messages to reduce context size."""
    print("\n" + "═" * 68)
    print("  DEMO: Chat History Compression")
    print("  Keep recent messages verbatim, compress older ones")
    print("═" * 68)

    long_history = [
        {"role": "user", "content": "Hi, I'm looking to migrate from AWS S3 to your product"},
        {"role": "assistant", "content": "Great! CloudSync Pro supports migration from AWS S3 via our Import Wizard. The process involves generating temporary read credentials in your AWS account, then our importer transfers files in parallel batches. Typical migration speed is 500 GB/hour."},
        {"role": "user", "content": "How much does it cost for 10TB?"},
        {"role": "assistant", "content": "For 10TB on the Enterprise plan, pricing starts at $800/month. This includes unlimited users, SSO integration, 99.9% uptime SLA, and dedicated support. We also offer a 30-day free trial."},
        {"role": "user", "content": "Do you support HIPAA compliance?"},
        {"role": "assistant", "content": "Yes, CloudSync Pro is HIPAA-eligible. We offer a Business Associate Agreement (BAA) on the Enterprise plan. We use AES-256 encryption at rest and TLS 1.3 in transit. Our data centers are SOC 2 Type II certified. Audit logs are retained for 7 years."},
        {"role": "user", "content": "Now back to the SSO setup — how do I configure SAML?"},  # Recent
    ]

    # Compress first 4 messages to a summary
    old_messages = long_history[:-2]
    recent_messages = long_history[-2:]

    old_tokens_before = count_tokens(
        " ".join(m["content"] for m in old_messages), "gpt-4o-mini"
    )

    _history_text = ''.join(f"{m['role'].upper()}: {m['content']}\n" for m in old_messages)
    compress_prompt = f"""Compress this conversation history into a 50-word summary of key facts established.
Output ONLY the summary — it will replace the full history to save tokens.

CONVERSATION:
{_history_text}

SUMMARY:"""

    if not client.dry_run:
        compress_result = client.chat(
            messages=[{"role": "user", "content": compress_prompt}],
            temperature=0.1,
            max_tokens=100,
        )
        summary = compress_result.content.strip()
        old_tokens_after = count_tokens(summary, "gpt-4o-mini")

        print(f"\n  Previously: {old_tokens_before} tokens in old messages")
        print(f"  Now:        {old_tokens_after} tokens (compressed summary)")
        print(f"  Savings:    {old_tokens_before - old_tokens_after} tokens ({1 - old_tokens_after/old_tokens_before:.0%} reduction)")
        print(f"\n  Summary: {summary}")
        print(f"\n  New context = summary + {len(recent_messages)} recent messages (much cheaper!)")
    else:
        print("\n  [DRY RUN — would compress 4 old messages into a ~50-word summary]")
        print(f"  Old messages: {old_tokens_before} tokens")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Prompt Compression Techniques")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--example", type=str, default="all",
                        choices=["compare", "chat", "all"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 04 — Prompt Compression")
    print("  Reduce token cost while preserving answer quality")
    print("═" * 72)

    if args.example in ("compare", "all"):
        demo_compression_techniques(client)

    if args.example in ("chat", "all"):
        demo_chat_history_compression(client)

    print("\n✅ Prompt Compression examples complete.")
    print("   Next: 06_automatic_prompt_optimization.py — APE algorithm\n")


if __name__ == "__main__":
    main()
