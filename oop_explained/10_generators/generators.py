"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 10: Generators & Iterators
=============================================================

WHAT IS AN ITERATOR?
---------------------
An iterator is any object that implements:
  __iter__() → returns self
  __next__() → returns the next value, raises StopIteration when done

What this means: you can use it in a `for` loop, pass to next(), etc.

WHAT IS A GENERATOR?
---------------------
A generator is a SPECIAL KIND of iterator created with:
  1. A GENERATOR FUNCTION — uses `yield` instead of `return`
  2. A GENERATOR EXPRESSION — like a list comprehension but with ()

WHY USE GENERATORS?
  - LAZY evaluation: values computed ONE AT A TIME, only when needed
  - MEMORY EFFICIENT: never holds the whole sequence in memory
  - Can represent INFINITE sequences
  - Pipelines of data transformations

KEY CONCEPTS:
  yield         → pause function, emit value, resume later
  yield from    → delegate to a sub-generator
  send()        → send a value INTO a running generator
  Generator expressions → (expr for x in iterable)
"""


# ─────────────────────────────────────────────
# 1. GENERATOR FUNCTION (yield)
# ─────────────────────────────────────────────

def countdown(n: int):
    """
    Generator that counts down from n to 1.
    Each call to next() runs the function until the next yield.
    """
    print("  [Generator started]")
    while n > 0:
        print(f"  [About to yield {n}]")
        yield n                  # ← pauses here, returns n to caller
        print(f"  [Resumed after yield {n}]")
        n -= 1
    print("  [Generator exhausted]")


print("=" * 55)
print("GENERATOR FUNCTION")
print("=" * 55)

gen = countdown(3)
print(f"Type: {type(gen)}")           # <class 'generator'>
print("Calling next() manually:")
print(f"  next() → {next(gen)}")
print(f"  next() → {next(gen)}")
print(f"  next() → {next(gen)}")

try:
    next(gen)
except StopIteration:
    print("  StopIteration raised — generator exhausted.\n")

# The for loop calls next() automatically
print("Using for loop:")
for n in countdown(3):
    print(f"  Got: {n}")


# ─────────────────────────────────────────────
# 2. INFINITE GENERATOR
# ─────────────────────────────────────────────

def integers_from(start: int = 0):
    """Infinite generator — never exhausts. Use with take() or islice()."""
    n = start
    while True:
        yield n
        n += 1


def take(n: int, iterable):
    """Take first n items from any iterable."""
    for i, item in enumerate(iterable):
        if i >= n: break
        yield item


def fibonacci():
    """Infinite Fibonacci sequence."""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


print("\n" + "=" * 55)
print("INFINITE GENERATORS")
print("=" * 55)

print("First 10 integers:", list(take(10, integers_from(0))))
print("First 12 Fibonacci:", list(take(12, fibonacci())))

# Using itertools.islice — the stdlib way
from itertools import islice
print("First 15 Fibonacci (islice):", list(islice(fibonacci(), 15)))


# ─────────────────────────────────────────────
# 3. GENERATOR EXPRESSIONS
# ─────────────────────────────────────────────
# Syntax: (expression for item in iterable [if condition])
# Returns a generator object — lazily evaluated, memory efficient.

print("\n" + "=" * 55)
print("GENERATOR EXPRESSIONS")
print("=" * 55)

# List comprehension: builds the ENTIRE list immediately
squares_list = [x * x for x in range(10)]

# Generator expression: computes one at a time, zero upfront memory
squares_gen  = (x * x for x in range(10))

print(f"List: {squares_list}")
print(f"Gen type: {type(squares_gen)}")
print(f"Gen values: {list(squares_gen)}")  # exhaust to show values

# Memory comparison — generator shines for large sequences
import sys
large_list = [x * x for x in range(100_000)]
large_gen  = (x * x for x in range(100_000))
print(f"\nMemory — list: {sys.getsizeof(large_list):,} bytes")
print(f"Memory — gen : {sys.getsizeof(large_gen):,} bytes")

# Useful with sum, max, min, any, all — they accept generators
total = sum(x * x for x in range(1_000_000))  # no list built in memory!
print(f"\nSum of squares (0..999999): {total:,}")


# ─────────────────────────────────────────────
# 4. GENERATOR PIPELINE
# ─────────────────────────────────────────────
# Chain generators to build lazy data processing pipelines.

def read_numbers(n: int):
    """Source: produce numbers 1..n."""
    for i in range(1, n + 1):
        yield i

def filter_even(numbers):
    """Filter: keep only even numbers."""
    for n in numbers:
        if n % 2 == 0:
            yield n

def square(numbers):
    """Transform: square each number."""
    for n in numbers:
        yield n * n

def limit(n, iterable):
    """Take only first n items."""
    count = 0
    for item in iterable:
        if count >= n: break
        yield item
        count += 1


print("\n" + "=" * 55)
print("GENERATOR PIPELINE")
print("=" * 55)

# Compose a lazy pipeline — NOTHING computed until we consume
pipeline = limit(5, square(filter_even(read_numbers(20))))
print("First 5 squares of even numbers (1-20):", list(pipeline))


# ─────────────────────────────────────────────
# 5. yield from (Sub-generators / Delegation)
# ─────────────────────────────────────────────

def chain(*iterables):
    """Re-implement itertools.chain using yield from."""
    for iterable in iterables:
        yield from iterable          # delegates to sub-iterator cleanly


def nested_flatten(lst):
    """Recursively flatten arbitrarily nested lists."""
    for item in lst:
        if isinstance(item, list):
            yield from nested_flatten(item)  # recurse via yield from
        else:
            yield item


print("\n" + "=" * 55)
print("yield from")
print("=" * 55)

print("chain([1,2], [3,4], [5]):", list(chain([1, 2], [3, 4], [5])))

nested = [1, [2, 3], [4, [5, [6, 7]]], 8]
print(f"flatten({nested}): {list(nested_flatten(nested))}")


# ─────────────────────────────────────────────
# 6. GENERATOR STATE — send() and close()
# ─────────────────────────────────────────────
# Generators are COROUTINES: you can SEND values into them via gen.send(value).
# send(value) resumes the generator AND provides `value` as the result of `yield`.

def running_average():
    """
    Coroutine that maintains a running average.
    Send numbers in; receive the current average back.
    """
    total, count = 0, 0
    while True:
        value = yield (total / count if count else None)
        total += value
        count += 1


print("\n" + "=" * 55)
print("GENERATOR send() — Coroutine")
print("=" * 55)

avg_gen = running_average()
next(avg_gen)                          # prime the generator (advance to first yield)

for num in [10, 20, 30, 40, 50]:
    avg = avg_gen.send(num)
    print(f"  Sent {num:2d} → running average = {avg:.2f}")

avg_gen.close()                        # close the generator
print("  Generator closed.")


# ─────────────────────────────────────────────
# 7. CUSTOM ITERATOR CLASS (without yield)
# ─────────────────────────────────────────────

class Range:
    """
    Re-implements Python's built-in range() to show iterator protocol.
    Uses __iter__ + __next__ instead of yield.
    """

    def __init__(self, start: int, stop: int, step: int = 1):
        if step == 0:
            raise ValueError("step cannot be zero")
        self.start = start
        self.stop  = stop
        self.step  = step

    def __iter__(self):
        """Returns an iterator object. self IS the iterator here."""
        self._current = self.start
        return self

    def __next__(self) -> int:
        if (self.step > 0 and self._current >= self.stop) or \
           (self.step < 0 and self._current <= self.stop):
            raise StopIteration
        value = self._current
        self._current += self.step
        return value

    def __len__(self) -> int:
        return max(0, (self.stop - self.start + self.step - 1) // self.step)

    def __repr__(self) -> str:
        return f"Range({self.start}, {self.stop}, {self.step})"


print("\n" + "=" * 55)
print("CUSTOM ITERATOR — Range")
print("=" * 55)

r = Range(0, 10, 2)
print(f"Range object: {r}")
print(f"List: {list(r)}")              # __iter__ + __next__
print(f"Len : {len(r)}")

print("Backward:", list(Range(10, 0, -2)))


# ─────────────────────────────────────────────
# 8. ITERTOOLS — The Generator Power Library
# ─────────────────────────────────────────────

from itertools import (
    count, cycle, repeat,
    chain, islice,
    combinations, permutations, product,
    groupby, accumulate,
    takewhile, dropwhile,
)
import operator

print("\n" + "=" * 55)
print("ITERTOOLS HIGHLIGHTS")
print("=" * 55)

# Infinite
print("count(5,2) first 5:", list(islice(count(5, 2), 5)))       # [5,7,9,11,13]
print("cycle('ABC') x6   :", list(islice(cycle('ABC'), 6)))       # A B C A B C
print("repeat(7, 4)      :", list(repeat(7, 4)))                  # [7,7,7,7]

# Combinatorial
print("\ncombinations([1,2,3], 2):", list(combinations([1,2,3], 2)))
print("permutations([1,2,3], 2) :", list(permutations([1,2,3], 2)))
print("product('AB', [1,2])     :", list(product('AB', [1, 2])))

# Functional
nums = [1, 2, 3, 4, 5, 6, 7]
print("\naccumulate(sum)     :", list(accumulate(nums)))
print("accumulate(product) :", list(accumulate(nums, operator.mul)))
print("takewhile(<4)       :", list(takewhile(lambda x: x < 4, nums)))
print("dropwhile(<4)       :", list(dropwhile(lambda x: x < 4, nums)))

# groupby
data = [("fruit", "apple"), ("fruit", "banana"), ("veg", "carrot"), ("veg", "potato")]
print("\ngroupby category:")
for key, group in groupby(data, key=lambda x: x[0]):
    items = [item[1] for item in group]
    print(f"  {key}: {items}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  Generator function   → def gen(): yield value
  Generator expression → (x*x for x in range(10))
  Infinite generator   → while True: yield value
  yield from           → delegate to sub-generator / recursive
  send()               → send value INTO generator (coroutine style)
  close()              → stop generator early

  ITERATOR PROTOCOL:
    __iter__() → return self
    __next__() → return next value or raise StopIteration

  KEY BENEFITS:
    ✔ Lazy — values computed on demand
    ✔ Memory efficient — no full list in RAM
    ✔ Composable — pipe generators like Unix pipes
    ✔ Infinite sequences become possible

  ITERTOOLS for power iteration:
    count, cycle, repeat, islice, chain,
    combinations, permutations, product,
    accumulate, groupby, takewhile, dropwhile
"""
print(summary)
