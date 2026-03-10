"""
=============================================================
GENERATIVE AI FOUNDATIONS
Topic 26: LLM APIs — OpenAI, Anthropic & Patterns
=============================================================

Install (optional): pip install openai anthropic

This module shows ALL patterns with a MockLLM so everything
runs without an API key.  Real API usage is shown alongside.

COVERED:
  1. MockLLM — simulate API for offline learning
  2. OpenAI Chat Completions API
  3. Anthropic Claude Messages API
  4. Streaming responses
  5. Embeddings API
  6. Function / Tool calling
  7. Structured output (JSON mode)
  8. Error handling & retries
  9. Best practices (cost, safety, rate limits)
"""

import json
import time
import random
import textwrap
from typing import Optional

# ─────────────────────────────────────────────
# 1. MOCK LLM — Simulate API responses locally
# ─────────────────────────────────────────────

print("=" * 55)
print("1. MOCK LLM (offline simulation)")
print("=" * 55)

class MockLLMResponse:
    """Mimics the object structure of the OpenAI response."""
    def __init__(self, content: str, model: str = "mock-gpt-4",
                 prompt_tokens: int = 0, completion_tokens: int = 0):
        self.id      = f"chatcmpl-mock-{random.randint(1000,9999)}"
        self.model   = model
        self.choices = [type("Choice", (), {
            "message": type("Msg", (), {
                "role":    "assistant",
                "content": content,
            })(),
            "finish_reason": "stop",
        })()]
        self.usage = type("Usage", (), {
            "prompt_tokens":     prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens":      prompt_tokens + completion_tokens,
        })()


class MockLLM:
    """
    Simulates an LLM API client.
    Replace with openai.OpenAI() or anthropic.Anthropic() in production.
    """
    def __init__(self, model: str = "mock-gpt-4", latency: float = 0.1):
        self.model   = model
        self.latency = latency
        self._responses = {
            "hello":       "Hello! How can I assist you today?",
            "python":      "Python is a high-level, interpreted programming language.",
            "sentiment":   '{"sentiment": "POSITIVE", "confidence": 0.95}',
            "summarize":   "This text describes key concepts in AI and LLMs.",
            "weather":     '{"temperature": 22, "condition": "sunny", "humidity": 45}',
            "default":     "I understand your question. Here is a helpful response.",
        }

    def _pick_response(self, messages: list) -> str:
        last_content = messages[-1]["content"].lower()
        for key, resp in self._responses.items():
            if key in last_content:
                return resp
        return self._responses["default"]

    def chat_completions_create(self, messages: list, temperature: float = 0.7,
                                 max_tokens: int = 512, **kwargs) -> MockLLMResponse:
        time.sleep(self.latency)   # simulate network latency
        content = self._pick_response(messages)
        # Rough token estimation
        prompt_tokens = sum(len(m["content"]) // 4 for m in messages)
        comp_tokens   = len(content) // 4
        return MockLLMResponse(content, self.model, prompt_tokens, comp_tokens)

    def embeddings_create(self, input_text, model: str = "text-embedding-3-small"):
        """Return a 1536-dim mock embedding."""
        time.sleep(self.latency / 2)
        import numpy as np
        rng = np.random.default_rng(hash(input_text) & 0xFFFFFFFF)
        vec = rng.standard_normal(1536).astype(np.float32)
        vec /= (np.linalg.norm(vec) + 1e-8)
        return type("EmbResponse", (), {
            "data": [type("Datum", (), {"embedding": vec.tolist()})()],
            "usage": type("U", (), {"total_tokens": len(input_text) // 4})(),
        })()


client = MockLLM()
print(f"MockLLM client: model={client.model}")


# ─────────────────────────────────────────────
# 2. CHAT COMPLETIONS — Core API Pattern
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. CHAT COMPLETIONS API")
print("=" * 55)

# ── REAL OPENAI CODE (commented out, needs API key) ──────────
# from openai import OpenAI
# client = OpenAI(api_key="sk-...")        # or env var OPENAI_API_KEY
# response = client.chat.completions.create(
#     model       = "gpt-4o-mini",
#     messages    = messages,
#     temperature = 0.7,
#     max_tokens  = 512,
# )
# ─────────────────────────────────────────────────────────────

def chat(system: str, user: str, temperature: float = 0.7) -> str:
    """Send a single-turn message and return the response text."""
    messages = [
        {"role": "system",  "content": system},
        {"role": "user",    "content": user},
    ]
    response = client.chat_completions_create(
        messages    = messages,
        temperature = temperature,
        max_tokens  = 512,
    )
    return response.choices[0].message.content


# Basic call
answer = chat(
    system = "You are a helpful assistant.",
    user   = "Say hello!"
)
print(f"Answer: {answer}")

# Show response object
response = client.chat_completions_create(
    messages    = [{"role":"user","content":"Tell me about Python"}],
    temperature = 0,
    max_tokens  = 256,
)
print(f"\nresponse.id     : {response.id}")
print(f"response.model  : {response.model}")
print(f"response.usage  : prompt={response.usage.prompt_tokens} "
      f"completion={response.usage.completion_tokens} "
      f"total={response.usage.total_tokens}")
print(f"response text   : {response.choices[0].message.content[:70]}")


# ─────────────────────────────────────────────
# 3. MULTI-TURN CONVERSATION (Stateful Chat)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. MULTI-TURN CONVERSATION")
print("=" * 55)

class ChatSession:
    """Manages conversation history for multi-turn chat."""
    def __init__(self, system_prompt: str, llm=None):
        self.messages = [{"role": "system", "content": system_prompt}]
        self.llm      = llm or MockLLM()

    def send(self, user_message: str, **kwargs) -> str:
        self.messages.append({"role": "user", "content": user_message})
        resp = self.llm.chat_completions_create(self.messages, **kwargs)
        assistant_text = resp.choices[0].message.content
        self.messages.append({"role": "assistant", "content": assistant_text})
        return assistant_text

    def reset(self, keep_system: bool = True):
        self.messages = self.messages[:1] if keep_system else []

    @property
    def turn_count(self):
        return sum(1 for m in self.messages if m["role"] == "user")


session = ChatSession("You are a Python tutor. Be concise.")
print("Conversation:")
for user_msg in ["Where do I start with Python?",
                 "How do I handle errors in Python?",
                 "Can you give me a quick example?"]:
    reply = session.send(user_msg)
    print(f"  User      : {user_msg}")
    print(f"  Assistant : {reply[:80]}")
    print()

print(f"Total turns in history: {session.turn_count}")
print(f"Context size (messages): {len(session.messages)}")


# ─────────────────────────────────────────────
# 4. STREAMING RESPONSES
# ─────────────────────────────────────────────

print("=" * 55)
print("4. STREAMING RESPONSES")
print("=" * 55)

# ── REAL OPENAI STREAMING (commented out) ─────────────────────
# from openai import OpenAI
# client = OpenAI()
# stream = client.chat.completions.create(
#     model    = "gpt-4o-mini",
#     messages = [{"role":"user","content":"Count to 10 slowly."}],
#     stream   = True,
# )
# full_text = ""
# for chunk in stream:
#     delta = chunk.choices[0].delta.content or ""
#     print(delta, end="", flush=True)
#     full_text += delta
# ─────────────────────────────────────────────────────────────

def simulate_streaming(text: str, delay: float = 0.03):
    """Simulate token-by-token streaming."""
    words = text.split()
    full = ""
    print("  Streaming: ", end="")
    for word in words:
        print(word, end=" ", flush=True)
        full += word + " "
        time.sleep(delay)
    print()  # newline
    return full.strip()

streamed = simulate_streaming("Python is a powerful language for AI and data science.")
print(f"  Full text: {streamed}")
print("""
  WHY STREAMING?
    • Better perceived performance — user sees output immediately
    • Allows early stopping if the answer is already sufficient
    • Required for long outputs (avoid timeout)
    • Use SSE (Server-Sent Events) or WebSocket to push to browser
""")


# ─────────────────────────────────────────────
# 5. EMBEDDINGS API
# ─────────────────────────────────────────────

print("=" * 55)
print("5. EMBEDDINGS API")
print("=" * 55)

import numpy as np

# ── REAL OPENAI EMBEDDINGS (commented out) ────────────────────
# from openai import OpenAI
# client = OpenAI()
# resp = client.embeddings.create(
#     input = "Python is great for AI",
#     model = "text-embedding-3-small",   # 1536 dims
# )
# vec = resp.data[0].embedding
# ─────────────────────────────────────────────────────────────

def get_embedding(text: str) -> np.ndarray:
    resp = client.embeddings_create(text)
    return np.array(resp.data[0].embedding, dtype=np.float32)

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

sentences = [
    "Python is great for machine learning.",
    "I love programming in Python.",
    "The Eiffel Tower is in Paris.",
    "Machine learning requires lots of data.",
]

vecs = [(s, get_embedding(s)) for s in sentences]
print("Pairwise cosine similarities:")
for i, (s1, v1) in enumerate(vecs):
    for j, (s2, v2) in enumerate(vecs):
        if i < j:
            sim = cosine_sim(v1, v2)
            mark = "← related" if sim > 0.5 else ""
            print(f"  ({i}↔{j}) {sim:.3f}  '{s1[:30]}' vs '{s2[:30]}' {mark}")

print(f"\nEmbedding dimensions: {vecs[0][1].shape[0]}")
print("""
  USE CASES:
    Semantic search        → find most similar documents
    Clustering             → group similar texts
    Classification         → train a small classifier on top of embeddings
    RAG retrieval          → find relevant context for LLM
    Duplicate detection    → high similarity → likely duplicate
""")


# ─────────────────────────────────────────────
# 6. FUNCTION / TOOL CALLING
# ─────────────────────────────────────────────

print("=" * 55)
print("6. FUNCTION / TOOL CALLING")
print("=" * 55)

# Tool calling lets the LLM request structured function calls.
# The app executes the function and returns results to the LLM.
#
# Flow:
#   1. Define tools with JSON schema
#   2. LLM sees tools + user message
#   3. LLM outputs: {"tool_call": "get_weather", "args": {"city": "Paris"}}
#   4. App executes get_weather("Paris")
#   5. App sends result back → LLM gives final answer

# Define tools (JSON Schema for OpenAI)
weather_tool = {
    "type": "function",
    "function": {
        "name":        "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type":        "string",
                    "description": "The name of the city."
                },
                "unit": {
                    "type":    "string",
                    "enum":    ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["city"]
        }
    }
}

calc_tool = {
    "type": "function",
    "function": {
        "name":        "calculate",
        "description": "Perform arithmetic calculations safely.",
        "parameters": {
            "type":       "object",
            "properties": {
                "expression": {"type":"string", "description": "Math expression to evaluate."}
            },
            "required":   ["expression"]
        }
    }
}

# Tool implementations
def get_weather(city: str, unit: str = "celsius") -> dict:
    # In production: call a real weather API
    fake_data = {"Paris": 18, "Tokyo": 24, "New York": 12}
    temp = fake_data.get(city, random.randint(10, 35))
    if unit == "fahrenheit":
        temp = temp * 9/5 + 32
    return {"city": city, "temperature": temp, "unit": unit, "condition": "sunny"}

def calculate(expression: str) -> dict:
    # ⚠ NEVER use eval() on untrusted input — use ast.literal_eval or a safe parser
    import ast
    try:
        tree = ast.parse(expression, mode='eval')
        # Only allow safe nodes
        allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
                   ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
                   ast.USub, ast.UAdd)
        for node in ast.walk(tree):
            if not isinstance(node, allowed):
                raise ValueError(f"Unsafe expression: {expression}")
        result = eval(compile(tree, '<string>', 'eval'))  # noqa: S307
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e)}

TOOLS = {
    "get_weather": get_weather,
    "calculate":   calculate,
}

# Simulate the tool-calling flow
class ToolCallingLLM(MockLLM):
    """MockLLM that can simulate tool calls."""
    def detect_tool_call(self, user_message: str) -> Optional[dict]:
        msg = user_message.lower()
        if "weather" in msg:
            # Extract city (simplified)
            words = user_message.split()
            city  = next((w for w in words if w[0].isupper() and w not in {"What","Tell","Is","The","How"}), "Paris")
            return {"name": "get_weather", "arguments": {"city": city}}
        if any(op in msg for op in ["+","-","*","/","**","calculate","compute"]):
            # Extract expression (simplified)
            expr = next((w for w in user_message.split() if any(c.isdigit() for c in w)), "2+2")
            return {"name": "calculate", "arguments": {"expression": expr}}
        return None


tool_client = ToolCallingLLM()

def agent_turn(user_message: str) -> str:
    """One turn: detect tool need → execute → return final answer."""
    tool_call = tool_client.detect_tool_call(user_message)

    if tool_call:
        fn_name = tool_call["name"]
        fn_args = tool_call["arguments"]
        print(f"  → LLM requests tool: {fn_name}({fn_args})")
        tool_result = TOOLS[fn_name](**fn_args)
        print(f"  ← Tool result: {tool_result}")
        # Feed result back to LLM
        follow_up = [
            {"role": "user",      "content": user_message},
            {"role": "function",  "content": json.dumps(tool_result), "name": fn_name},
        ]
        final = tool_client.chat_completions_create(follow_up)
        return f"Based on the data: {json.dumps(tool_result)}"
    else:
        resp = tool_client.chat_completions_create([{"role":"user","content":user_message}])
        return resp.choices[0].message.content


print("Tool calling demo:")
for query in ["What's the weather in Tokyo?",
              "Calculate 15 * 4 + 22",
              "Tell me about neural networks"]:
    print(f"\n  User: {query}")
    answer = agent_turn(query)
    print(f"  Bot : {answer}")


# ─────────────────────────────────────────────
# 7. ERROR HANDLING & RETRIES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. ERROR HANDLING & RETRIES")
print("=" * 55)

import time
import functools

def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for exponential backoff on API calls."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 0.5)
                    print(f"  Attempt {attempt+1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        return wrapper
    return decorator


@retry_with_backoff(max_retries=2, base_delay=0.1)
def call_api_with_retry(messages: list) -> str:
    return client.chat_completions_create(messages).choices[0].message.content


result = call_api_with_retry([{"role": "user", "content": "Hello!"}])
print(f"API call result: {result}")

# Common error types
print("""
  COMMON API ERRORS:
    openai.RateLimitError      → 429 — too many requests → backoff & retry
    openai.APIConnectionError  → network issue → retry
    openai.AuthenticationError → bad API key → check key, do NOT retry
    openai.BadRequestError     → 400 — context too long, bad format → fix input
    openai.InternalServerError → 500 — server issue → retry after delay

  BEST PRACTICES:
    • Never hardcode API keys — use os.environ["OPENAI_API_KEY"]
    • Set max_tokens to avoid runaway costs
    • Log all API calls (timestamp, tokens, cost) for billing audits
    • Cache deterministic responses (temperature=0) to save costs
    • Use streaming for long outputs in user-facing apps
""")


# ─────────────────────────────────────────────
# 8. ANTHROPIC CLAUDE API PATTERN
# ─────────────────────────────────────────────

print("=" * 55)
print("8. ANTHROPIC CLAUDE API")
print("=" * 55)

# ── REAL ANTHROPIC CODE (commented out) ───────────────────────
# import anthropic
# client = anthropic.Anthropic(api_key="sk-ant-...")
# message = client.messages.create(
#     model      = "claude-opus-4-5",
#     max_tokens = 1024,
#     system     = "You are a helpful assistant.",
#     messages   = [{"role": "user", "content": "Hello!"}],
# )
# print(message.content[0].text)
# ─────────────────────────────────────────────────────────────

print("""
  OPENAI vs ANTHROPIC — API differences:
  ┌─────────────────────┬───────────────────────┬───────────────────────┐
  │ Feature             │ OpenAI                │ Anthropic             │
  ├─────────────────────┼───────────────────────┼───────────────────────┤
  │ Client init         │ OpenAI(api_key=...)   │ Anthropic(api_key=...)│
  │ Endpoint            │ chat.completions.     │ messages.create()     │
  │                     │ create()              │                       │
  │ System prompt       │ messages[0] "system"  │ system= kwarg         │
  │ Response text       │ .choices[0].message   │ .content[0].text      │
  │                     │ .content              │                       │
  │ Models              │ gpt-4o, gpt-4o-mini   │ claude-opus-4-5,      │
  │                     │ o1, o3                │ claude-sonnet-4-5     │
  │ Context window      │ 128K (gpt-4o)         │ 200K (claude-3+)      │
  └─────────────────────┴───────────────────────┴───────────────────────┘
""")


# ─────────────────────────────────────────────
# 9. COST & BEST PRACTICES
# ─────────────────────────────────────────────

print("=" * 55)
print("9. COST ESTIMATION & BEST PRACTICES")
print("=" * 55)

# Approximate pricing (March 2025, may change)
LLM_PRICING = {
    "gpt-4o":            {"input": 2.50, "output": 10.00},  # per 1M tokens
    "gpt-4o-mini":       {"input": 0.15, "output":  0.60},
    "claude-opus-4-5":   {"input":15.00, "output": 75.00},
    "claude-sonnet-4-5": {"input": 3.00, "output": 15.00},
    "claude-haiku":      {"input": 0.25, "output":  1.25},
}

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in LLM_PRICING:
        return 0.0
    p = LLM_PRICING[model]
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000

print("Cost estimate for 1000 requests (500 in + 500 out tokens each):")
for model, _ in LLM_PRICING.items():
    cost = estimate_cost(model, 500_000, 500_000)
    print(f"  {model:<22}: ${cost:.2f}")

print("""
  BEST PRACTICES:
    ✓ Cache responses for identical inputs (save cost, improve latency)
    ✓ Use gpt-4o-mini / claude-haiku for simple tasks
    ✓ Prompt compression: remove filler text before sending
    ✓ Set max_tokens to cap output length
    ✓ Batch requests where API supports it
    ✓ Store env vars securely (never in code):
        import os
        api_key = os.environ.get("OPENAI_API_KEY")
    ✓ Monitor usage with SDK usage tracking
    ✓ Use tiktoken to count tokens before sending:
        import tiktoken
        enc   = tiktoken.encoding_for_model("gpt-4o")
        n_tok = len(enc.encode(text))
""")

print("=" * 55)
print("SUMMARY")
print("=" * 55)
print("""
  CORE PATTERN (OpenAI):
    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model    = "gpt-4o-mini",
        messages = [{"role":"system","content":"..."},
                    {"role":"user",  "content":"..."}],
        max_tokens  = 512,
        temperature = 0.7,
    )
    text = resp.choices[0].message.content

  EMBEDDINGS:
    resp = client.embeddings.create(input=text, model="text-embedding-3-small")
    vec  = resp.data[0].embedding   # list[float], 1536 dims

  TOOL CALLING:
    1. Define tools as JSON schema
    2. Pass tools= to create()
    3. Check finish_reason == "tool_calls"
    4. Execute function, pass result back as role="tool"

  STREAMING (append stream=True):
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        print(delta, end="", flush=True)

  COST RULE OF THUMB:
    gpt-4o-mini  ≈ $0.001 per 1,000 words   ← default for most tasks
    gpt-4o       ≈ $0.020 per 1,000 words   ← complex reasoning
""")
