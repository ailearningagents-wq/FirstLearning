"""
05_real_world_applications/03_chatbot_with_memory.py
═══════════════════════════════════════════════════════════════════

Stateful multi-turn chatbot with:
- Persistent conversation memory
- Context window management (compression of old turns)
- Specialized system persona (customer support agent)
- Conversation summary for long sessions
- User intent detection
"""

import sys
import os
import json
import argparse
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import count_tokens, format_response


MAX_CONTEXT_TOKENS = 3000
COMPRESS_THRESHOLD  = 2000


SYSTEM_PROMPT = """You are Alex, a knowledgeable and friendly customer support agent for CloudSync Pro,
an enterprise file synchronization platform.

YOUR KNOWLEDGE BASE:
- Plans: Free (10GB), Pro ($29/mo, 100GB), Enterprise (custom, unlimited)
- SSO: Supports SAML 2.0 and OIDC
- Sync conflict resolution: Conflict copies created, manual merge required  
- Rate limits: API 1000 req/hour per key
- Support SLA: Free (community), Pro (48h), Enterprise (4h response, 99.9% uptime)
- Billing: Monthly or annual (20% discount); cancellation takes effect end of billing period
- Security: AES-256 at rest, TLS 1.3 in transit, SOC 2 Type II certified

BEHAVIOR RULES:
1. Be concise and helpful — answer in 2-4 sentences unless asked for detail
2. If you don't know something, say so and offer to escalate
3. Always confirm you understood the user's question correctly if ambiguous
4. Suggest upgrading plan when the user's need exceeds their current plan
5. For billing or account changes, tell user to go to Settings > Billing or contact billing@cloudsync.example.com
6. Never make up pricing or policy details not in your knowledge base"""


@dataclass
class ConversationMemory:
    messages: list[dict] = field(default_factory=list)
    context_summary: str = ""
    turn_count: int = 0
    total_tokens_used: int = 0

    def add_turn(self, role: str, content: str) -> None:
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        self.turn_count += 1

    def get_api_messages(self) -> list[dict]:
        """Return messages in the format expected by the chat API."""
        api_messages = []
        if self.context_summary:
            api_messages.append({
                "role": "system",
                "content": f"{SYSTEM_PROMPT}\n\n[CONVERSATION CONTEXT SO FAR: {self.context_summary}]"
            })
        else:
            api_messages.append({"role": "system", "content": SYSTEM_PROMPT})

        # Include recent messages (without timestamp)
        for msg in self.messages:
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return api_messages

    def total_content_tokens(self, model: str = "gpt-4o-mini") -> int:
        all_content = SYSTEM_PROMPT + self.context_summary
        all_content += " ".join(m["content"] for m in self.messages)
        return count_tokens(all_content, model)

    def to_dict(self) -> dict:
        return {
            "turn_count": self.turn_count,
            "context_summary": self.context_summary,
            "messages": self.messages,
        }


class SupportChatbot:
    def __init__(self, client: LLMClient, verbose: bool = True):
        self.client = client
        self.memory = ConversationMemory()
        self.verbose = verbose

    def _compress_old_messages(self) -> None:
        """Summarize the oldest half of messages to free up context window."""
        if len(self.memory.messages) < 4:
            return

        half = len(self.memory.messages) // 2
        old_messages = self.memory.messages[:half]
        self.memory.messages = self.memory.messages[half:]

        old_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in old_messages
        )

        response = self.client.chat(
            messages=[{
                "role": "user",
                "content": (
                    f"Summarize this customer support conversation in 60 words. "
                    f"Include: customer's issues raised, solutions provided, account facts mentioned.\n\n"
                    f"{old_text}"
                )
            }],
            temperature=0.1,
            max_tokens=120,
        )

        if not self.client.dry_run:
            new_summary = response.content.strip()
            if self.memory.context_summary:
                self.memory.context_summary += " | " + new_summary
            else:
                self.memory.context_summary = new_summary

            if self.verbose:
                print(f"\n  [Context compressed — {half} turns summarized]")
                print(f"  Summary: {self.memory.context_summary[:100]}...")

    def chat(self, user_message: str) -> str:
        """Process a user message and return the assistant response."""
        # Check if we need to compress context
        if self.memory.total_content_tokens() > COMPRESS_THRESHOLD:
            self._compress_old_messages()

        self.memory.add_turn("user", user_message)
        messages = self.memory.get_api_messages()

        response = self.client.chat(
            messages=messages,
            temperature=0.3,
            max_tokens=300,
        )

        assistant_reply = response.content.strip() if not self.client.dry_run else f"[DRY RUN reply to: {user_message[:50]}]"
        self.memory.add_turn("assistant", assistant_reply)

        if not self.client.dry_run:
            self.memory.total_tokens_used += response.total_tokens

        return assistant_reply

    def get_conversation_summary(self) -> str:
        """Generate a final summary of the conversation."""
        if not self.memory.messages:
            return "No conversation to summarize."

        history = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in self.memory.messages[-6:]
        )

        response = self.client.chat(
            messages=[{
                "role": "user",
                "content": (
                    f"Summarize this support conversation. Include: "
                    f"customer's main issue, resolution status, any action items.\n\n{history}"
                )
            }],
            temperature=0.1,
            max_tokens=150,
        )

        if self.client.dry_run:
            return "[DRY RUN summary]"

        return response.content.strip()


# ─────────────────────────────────────────────────────────────────────────────
# Simulated Conversation Scenarios
# ─────────────────────────────────────────────────────────────────────────────

DEMO_CONVERSATION = [
    "Hi, I'm having trouble with SAML SSO setup. We use Okta as our IdP.",
    "I downloaded the SP metadata from Settings. What do I upload to Okta?",
    "Got it. What attributes does CloudSync need from Okta?",
    "How long until SSO changes take effect after I save?",
    "Also, our security team asked about your encryption standards.",
    "We're on the Pro plan. Does Pro include SSO or do we need Enterprise?",
    "What's the price difference between Pro and Enterprise?",
]


def run_demo_conversation(client: LLMClient) -> None:
    print("\n" + "═" * 68)
    print("  DEMO: Multi-Turn Customer Support Chatbot")
    print("  Scenario: Customer needs SSO setup help + pricing questions")
    print("═" * 68)

    bot = SupportChatbot(client, verbose=True)

    for i, user_msg in enumerate(DEMO_CONVERSATION, 1):
        print(f"\n  ── Turn {i}/{len(DEMO_CONVERSATION)} ──────────────────────────────────────")
        print(f"  USER: {user_msg}")

        reply = bot.chat(user_msg)
        print(f"  ALEX: {reply}")

        tokens = bot.memory.total_content_tokens()
        print(f"  [Context: {tokens} tokens | Turn {bot.memory.turn_count}]")

    print("\n  ── Conversation Summary ─────────────────────────────────────")
    summary = bot.get_conversation_summary()
    print(f"  {summary}")

    if not client.dry_run:
        print(f"\n  Total tokens used this session: {bot.memory.total_tokens_used:,}")


def run_interactive(client: LLMClient) -> None:
    """Interactive mode — type messages in the terminal."""
    print("\n" + "═" * 68)
    print("  INTERACTIVE: Chat with CloudSync Support Agent (Alex)")
    print("  Type 'quit' to exit, 'summary' for conversation summary")
    print("═" * 68)

    bot = SupportChatbot(client, verbose=False)

    while True:
        try:
            user_input = input("\n  You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Interrupted]")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "summary":
            print(f"\n  Summary: {bot.get_conversation_summary()}")
            continue

        reply = bot.chat(user_input)
        print(f"\n  Alex: {reply}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stateful Chatbot with Memory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--interactive", action="store_true",
                        help="Start interactive chat session")
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 05 — Real World: Chatbot with Memory")
    print("  Features: context compression, persona, multi-turn state")
    print("═" * 72)

    if args.interactive:
        run_interactive(client)
    else:
        run_demo_conversation(client)

    print("\n✅ Chatbot with Memory demo complete.\n")


if __name__ == "__main__":
    main()
