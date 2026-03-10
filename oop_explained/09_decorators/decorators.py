"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 9: Decorators
=============================================================

WHAT IS A DECORATOR?
---------------------
A decorator is a function that takes another function (or class) as input,
WRAPS it with extra behavior, and returns the enhanced version.

    @decorator
    def my_function(): ...

    is exactly equivalent to:

    def my_function(): ...
    my_function = decorator(my_function)

WHY USE DECORATORS?
  - Add cross-cutting concerns (logging, timing, caching, auth) without
    modifying the original function
  - Keep code DRY (Don't Repeat Yourself)
  - Separate concerns cleanly

TYPES COVERED:
  1. Simple function decorator
  2. Decorator with arguments
  3. Decorator factory
  4. Class-based decorator
  5. Stacking decorators
  6. functools.wraps (preserving metadata)
  7. Real-world decorators (timer, retry, memoize, validate)
"""

import time
import functools


# ─────────────────────────────────────────────
# 1. SIMPLEST DECORATOR
# ─────────────────────────────────────────────

def shout(func):
    """
    Wraps func to print its return value in UPPERCASE.
    Steps: 1) inner() calls the original func, 2) modifies result, 3) returns.
    """
    @functools.wraps(func)           # preserves __name__, __doc__ of original func
    def inner(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return inner


@shout
def greet(name: str) -> str:
    """Returns a greeting."""
    return f"hello, {name}!"


print("=" * 55)
print("SIMPLE DECORATOR")
print("=" * 55)
print(greet("Alice"))                    # HELLO, ALICE!
print(f"Function name: {greet.__name__}")  # greet (thanks to @functools.wraps)
print(f"Docstring    : {greet.__doc__}")


# ─────────────────────────────────────────────
# 2. DECORATOR WITH *ARGS AND **KWARGS
# ─────────────────────────────────────────────

def logger(func):
    """Logs every call: what was called, with what arguments, and what it returned."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        arg_str = ", ".join(
            [repr(a) for a in args] +
            [f"{k}={v!r}" for k, v in kwargs.items()]
        )
        print(f"  → Calling {func.__name__}({arg_str})")
        result = func(*args, **kwargs)
        print(f"  ← {func.__name__} returned {result!r}")
        return result
    return wrapper


@logger
def add(a, b):
    return a + b

@logger
def multiply(x, y, z=1):
    return x * y * z


print("\n" + "=" * 55)
print("LOGGER DECORATOR")
print("=" * 55)
add(3, 4)
multiply(2, 5, z=3)


# ─────────────────────────────────────────────
# 3. TIMER DECORATOR
# ─────────────────────────────────────────────

def timer(func):
    """Measures and prints execution time of any function."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start  = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"  ⏱ {func.__name__} took {elapsed:.6f}s")
        return result
    return wrapper


@timer
def slow_sum(n: int) -> int:
    return sum(range(n))


print("\n" + "=" * 55)
print("TIMER DECORATOR")
print("=" * 55)
result = slow_sum(1_000_000)
print(f"  Result: {result}")


# ─────────────────────────────────────────────
# 4. DECORATOR FACTORY (Decorator with Arguments)
# ─────────────────────────────────────────────
# To pass arguments to a decorator, add ONE more layer of nesting.
# The outer function accepts the args; the middle function accepts the function.

def repeat(times: int):
    """
    Decorator FACTORY — returns a decorator that runs func `times` times.
    Usage: @repeat(3)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = None
            for i in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 0.0, exceptions=(Exception,)):
    """
    Retry decorator: re-runs the function up to max_attempts times on failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    print(f"  Attempt {attempt}/{max_attempts} failed: {e}")
                    if attempt < max_attempts and delay > 0:
                        time.sleep(delay)
            raise last_error
        return wrapper
    return decorator


print("\n" + "=" * 55)
print("DECORATOR FACTORY")
print("=" * 55)

@repeat(3)
def say_hi():
    print("  Hi!")

say_hi()

_fail_count = 0

@retry(max_attempts=3)
def flaky_function():
    global _fail_count
    _fail_count += 1
    if _fail_count < 3:
        raise ConnectionError(f"Timeout (attempt {_fail_count})")
    return "Success on attempt 3!"

print()
outcome = flaky_function()
print(f"  Final result: {outcome}")


# ─────────────────────────────────────────────
# 5. MEMOIZE / CACHE DECORATOR
# ─────────────────────────────────────────────

def memoize(func):
    """Caches results keyed by arguments — avoids redundant computation."""
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    wrapper.cache = cache          # expose cache for inspection
    wrapper.cache_clear = cache.clear
    return wrapper


@memoize
def fib(n: int) -> int:
    """Fibonacci — exponential without caching, linear with it."""
    if n <= 1: return n
    return fib(n - 1) + fib(n - 2)


# Python stdlib equivalent:
from functools import lru_cache

@lru_cache(maxsize=128)
def factorial(n: int) -> int:
    return 1 if n <= 1 else n * factorial(n - 1)


print("\n" + "=" * 55)
print("MEMOIZE / lru_cache DECORATOR")
print("=" * 55)
print(f"fib(10)  = {fib(10)}")
print(f"fib(30)  = {fib(30)}")
print(f"Cache size: {len(fib.cache)} entries")

print(f"\nfactorial(10) = {factorial(10)}")
print(f"factorial(20) = {factorial(20)}")
print(f"Cache info: {factorial.cache_info()}")


# ─────────────────────────────────────────────
# 6. VALIDATION DECORATOR
# ─────────────────────────────────────────────

def validate_positive(*param_names):
    """
    Decorator factory that raises ValueError if specified
    positional arguments are not positive numbers.
    """
    def decorator(func):
        import inspect
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
            for name in param_names:
                val = bound.arguments.get(name)
                if val is not None and val <= 0:
                    raise ValueError(f"Parameter '{name}' must be positive, got {val}.")
            return func(*args, **kwargs)
        return wrapper
    return decorator


@validate_positive("width", "height")
def make_rectangle(width: float, height: float) -> dict:
    return {"width": width, "height": height, "area": width * height}


print("\n" + "=" * 55)
print("VALIDATION DECORATOR")
print("=" * 55)
print(make_rectangle(4, 5))

try:
    make_rectangle(-1, 5)
except ValueError as e:
    print(f"ValueError: {e}")


# ─────────────────────────────────────────────
# 7. CLASS-BASED DECORATOR
# ─────────────────────────────────────────────
# Use a class when the decorator needs to maintain STATE.

class CallCounter:
    """A class-based decorator that counts how many times a function is called."""

    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"  [{self.func.__name__} called {self.count} time(s)]")
        return self.func(*args, **kwargs)

    def reset(self):
        self.count = 0


@CallCounter
def fetch_data(url: str) -> str:
    return f"<data from {url}>"


print("\n" + "=" * 55)
print("CLASS-BASED DECORATOR")
print("=" * 55)
fetch_data("https://api.example.com/users")
fetch_data("https://api.example.com/posts")
fetch_data("https://api.example.com/comments")
print(f"Total calls: {fetch_data.count}")


# ─────────────────────────────────────────────
# 8. STACKING DECORATORS
# ─────────────────────────────────────────────
# Applied BOTTOM-UP: @timer first wraps, then @logger wraps that result.

@logger
@timer
def compute(n: int) -> int:
    """Compute sum of squares."""
    return sum(i * i for i in range(n))


print("\n" + "=" * 55)
print("STACKED DECORATORS (@logger on top of @timer)")
print("=" * 55)
compute(100_000)


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  PATTERN                   EXAMPLE
  ─────────────────────────────────────────────────
  Simple decorator          @my_decorator
  With arguments            @my_decorator_factory(arg)
  Stacked                   @dec_a  ← applied second
                            @dec_b  ← applied first

  Always use @functools.wraps(func) inside wrapper to preserve:
    func.__name__, func.__doc__, func.__module__, etc.

  STDLIB DECORATORS:
    @functools.lru_cache(maxsize=N)    → memoize with LRU eviction
    @functools.cached_property         → compute once, cache on instance
    @staticmethod / @classmethod       → OOP (see Topic 7)
    @property                          → OOP (see Topic 8)
    @dataclasses.dataclass             → (see Topic 14)
"""
print(summary)
