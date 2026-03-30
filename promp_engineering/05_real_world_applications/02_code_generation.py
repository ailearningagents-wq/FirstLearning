"""
05_real_world_applications/02_code_generation.py
═══════════════════════════════════════════════════════════════════

AI-powered code generation assistant with:
- Role-specific prompting (expert developer persona)
- Structured output (code + explanation + tests)
- Basic syntax validation
- Before/after improvement patterns
- Multiple language support
"""

import sys
import os
import re
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.llm_client import LLMClient
from utils.helpers import format_response, count_tokens


CODE_TASKS = {
    "async-rate-limiter": {
        "language": "Python",
        "description": (
            "Implement an async rate limiter class using token bucket algorithm. "
            "Requirements: asyncio-compatible, configurable rate (calls/second) and burst size, "
            "context manager support, thread-safe. Include type hints and docstrings."
        ),
    },
    "sql-query-builder": {
        "language": "Python",
        "description": (
            "Implement a safe SQL query builder class that prevents SQL injection. "
            "Support SELECT with WHERE, JOIN, ORDER BY, LIMIT. "
            "Use parameterized queries. Include type hints, docstrings, and 3 usage examples."
        ),
    },
    "react-search-hook": {
        "language": "TypeScript",
        "description": (
            "Create a custom React hook `useDebounceSearch` that: debounces user input (300ms), "
            "cancels in-flight requests when new input arrives (AbortController), "
            "returns { results, isLoading, error }, handles errors gracefully."
        ),
    },
}

CODE_REVIEW_SUBJECT = """
def process_user_data(user_id, db_conn):
    query = "SELECT * FROM users WHERE id = " + str(user_id)
    result = db_conn.execute(query)
    data = result.fetchall()
    
    output = []
    for row in data:
        user = {}
        for i in range(len(row)):
            user[result.description[i][0]] = row[i]
        output.append(user)
    
    password = output[0]['password']
    print("User password: " + password)
    return output
"""


def build_code_gen_prompt(language: str, description: str) -> str:
    return f"""You are a senior {language} engineer with 10+ years of experience.
You write clean, idiomatic, production-ready code.

TASK: {description}

Requirements for your response:
1. Write complete, runnable code (no placeholders or TODO comments)
2. Include comprehensive docstrings and type hints
3. Handle edge cases and errors properly
4. Follow {language} best practices and idioms
5. After the code, add a brief "How it works" explanation (3-5 sentences)
6. Add 2-3 unit test examples (as commented test calls or pytest functions)

FORMAT:
```{language.lower()}
[your complete implementation]
```

**How it works:**
[explanation]

**Usage examples / Tests:**
```{language.lower()}
[test code]
```"""


def build_code_review_prompt(code: str) -> str:
    return f"""You are a senior security-focused code reviewer.

Review the following code for: security vulnerabilities, bugs, performance issues,
and code quality problems.

```python
{code.strip()}
```

Provide:
1. **Security Issues** (highest priority): List each OWASP-relevant vulnerability
2. **Bugs**: Logic errors or incorrect behavior
3. **Code Quality**: Style, readability, maintainability issues
4. **Refactored Code**: A corrected, secure version

Format your security issues as:
| Severity | Vulnerability | Line(s) | Fix |
|----------|--------------|---------|-----|"""


def extract_code_block(response_text: str, language: str = "python") -> str:
    """Extract the first code block from a markdown response."""
    pattern = rf"```{language}?\s*(.*?)```"
    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return response_text.strip()


def basic_syntax_check(code: str) -> tuple[bool, str]:
    """Basic Python syntax check using compile()."""
    try:
        compile(code, "<string>", "exec")
        return True, "OK"
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Code Generation Assistant")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--task", default="async-rate-limiter",
                        choices=list(CODE_TASKS.keys()) + ["review"])
    args = parser.parse_args()

    client = LLMClient(dry_run=args.dry_run)

    print("\n" + "═" * 72)
    print("  MODULE 05 — Real World: AI Code Generation")
    print("═" * 72)

    if args.task == "review":
        print("\n  ── Code Security Review ──────────────────────────────────────")
        print(f"  Reviewing: {len(CODE_REVIEW_SUBJECT.strip().splitlines())} lines of Python")
        print(f"\n  Input code:")
        for line in CODE_REVIEW_SUBJECT.strip().split("\n"):
            print(f"    {line}")

        prompt = build_code_review_prompt(CODE_REVIEW_SUBJECT)
        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
        )

        if not client.dry_run:
            print(format_response(response, title="Security Review", show_stats=True))
        else:
            print("\n  [DRY RUN — would show security vulnerabilities and refactored code]")

    else:
        task = CODE_TASKS[args.task]
        print(f"\n  ── Generating: {args.task} ({task['language']}) ─────────────")
        print(f"  Description: {task['description'][:100]}...")

        prompt = build_code_gen_prompt(task["language"], task["description"])
        prompt_tokens = count_tokens(prompt, "gpt-4o-mini")
        print(f"  Prompt tokens: {prompt_tokens}")

        response = client.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.15,
            max_tokens=1500,
        )

        if not client.dry_run:
            print(format_response(response, title=f"{task['language']} Implementation", show_stats=True))

            # Validate Python code
            if task["language"] == "Python":
                code = extract_code_block(response.content, "python")
                if code:
                    valid, msg = basic_syntax_check(code)
                    status = "✅ Syntax OK" if valid else f"❌ {msg}"
                    print(f"\n  Syntax check: {status}")
                    print(f"  Code length: {len(code.splitlines())} lines")
        else:
            print("\n  [DRY RUN — would generate complete implementation with tests]")

    print("\n✅ Code generation complete.\n")


if __name__ == "__main__":
    main()
