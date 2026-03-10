"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 13: Functional Programming
=============================================================

WHAT IS FUNCTIONAL PROGRAMMING?
---------------------------------
Functional Programming (FP) treats computation as the evaluation of
MATHEMATICAL FUNCTIONS. Key ideas:
  - Pure functions: same input → same output, no side effects
  - Immutability: prefer not mutating state
  - Higher-order functions: functions that take/return functions
  - Function composition: combine small functions into bigger ones

PYTHON SUPPORTS FP WITH:
  lambda      → anonymous (inline) functions
  map()       → apply function to every item
  filter()    → keep items matching a predicate
  reduce()    → fold/accumulate items into one value
  sorted()    → sort with a key function
  zip()       → pair items from multiple iterables
  functools   → partial, reduce, wraps, lru_cache, cache
  operator    → module of operator functions (add, mul, etc.)
"""

from functools import reduce, partial
import operator
from typing import Callable, TypeVar

T = TypeVar("T")


# ─────────────────────────────────────────────
# 1. LAMBDA FUNCTIONS
# ─────────────────────────────────────────────
# lambda args: expression
# Anonymous, single-expression functions. No statements, no return keyword.

print("=" * 55)
print("LAMBDA FUNCTIONS")
print("=" * 55)

# Basic lambdas
square    = lambda x: x ** 2
add       = lambda a, b: a + b
greet     = lambda name: f"Hello, {name}!"

print(f"square(7)      = {square(7)}")
print(f"add(3, 4)      = {add(3, 4)}")
print(f"greet('Alice') = {greet('Alice')}")

# Lambdas as keys in sort/min/max
students = [("Alice", 92), ("Bob", 45), ("Carol", 78), ("Dave", 88)]
by_score = sorted(students, key=lambda s: s[1], reverse=True)
print(f"\nBy score (desc): {by_score}")

min_score = min(students, key=lambda s: s[1])
print(f"Lowest scorer : {min_score}")

# Lambda with conditional expression
classify = lambda n: "even" if n % 2 == 0 else "odd"
print(f"\n[{', '.join(classify(n) for n in range(6))}]")


# ─────────────────────────────────────────────
# 2. map() — Transform Every Element
# ─────────────────────────────────────────────
# map(function, iterable) → returns a lazy map object

print("\n" + "=" * 55)
print("map()")
print("=" * 55)

numbers = [1, 2, 3, 4, 5]

# Double every number
doubled = list(map(lambda x: x * 2, numbers))
print(f"doubled        : {doubled}")

# Convert to strings
as_str  = list(map(str, numbers))
print(f"as strings     : {as_str}")

# Multiple iterables — zip-like behavior
a = [1, 2, 3]
b = [10, 20, 30]
sums = list(map(lambda x, y: x + y, a, b))
print(f"element-wise + : {sums}")

# Named function with map
def celsius_to_fahrenheit(c):
    return c * 9/5 + 32

temps_c = [0, 20, 37, 100]
temps_f = list(map(celsius_to_fahrenheit, temps_c))
print(f"Celsius  : {temps_c}")
print(f"Fahrenheit: {temps_f}")

# Note: list comprehension is often preferred over map() in Python
# These are equivalent:
print("map vs comp:", list(map(square, numbers)), [square(x) for x in numbers])


# ─────────────────────────────────────────────
# 3. filter() — Select Elements
# ─────────────────────────────────────────────
# filter(function, iterable) → lazy iterator of items where function(item) is True

print("\n" + "=" * 55)
print("filter()")
print("=" * 55)

numbers = range(1, 21)

evens   = list(filter(lambda x: x % 2 == 0, numbers))
print(f"Evens    : {evens}")

primes  = list(filter(
    lambda n: n > 1 and all(n % i != 0 for i in range(2, int(n**0.5)+1)),
    range(2, 30)
))
print(f"Primes   : {primes}")

# Filter None/falsy values
mixed   = [0, 1, None, "hello", "", False, True, 42, [], [1, 2]]
truthy  = list(filter(None, mixed))    # filter(None, ...) removes falsy values
print(f"Truthy   : {truthy}")

# Combined map + filter: squares of odd numbers
odd_squares = list(map(lambda x: x**2, filter(lambda x: x % 2 != 0, range(10))))
print(f"Odd squares: {odd_squares}")
# Equivalent comprehension (usually clearer):
print(f"Via comp   : {[x**2 for x in range(10) if x % 2 != 0]}")


# ─────────────────────────────────────────────
# 4. reduce() — Fold to Single Value
# ─────────────────────────────────────────────
# reduce(function, iterable[, initializer])
# Repeatedly applies function to pairs, accumulating a single result.

print("\n" + "=" * 55)
print("reduce()")
print("=" * 55)

nums = [1, 2, 3, 4, 5]

# Sum using reduce
total   = reduce(lambda acc, x: acc + x, nums)
print(f"Sum     : {total}")                         # 15

# Product
product = reduce(operator.mul, nums)
print(f"Product : {product}")                        # 120

# Max
maximum = reduce(lambda a, b: a if a > b else b, nums)
print(f"Max     : {maximum}")                        # 5

# Flatten a list of lists
nested  = [[1, 2], [3, 4], [5, 6]]
flat    = reduce(lambda acc, x: acc + x, nested)
print(f"Flatten : {flat}")                           # [1,2,3,4,5,6]

# With initializer (starting accumulator value)
result  = reduce(lambda acc, x: acc + x, nums, 100)  # starts at 100
print(f"Sum+100 : {result}")                         # 115


# ─────────────────────────────────────────────
# 5. PURE FUNCTIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("PURE FUNCTIONS")
print("=" * 55)

# Impure — depends on/modifies external state
total  = 0
def impure_add(x):
    global total
    total += x        # side effect: mutates global
    return total

# Pure — same input always → same output, no side effects
def pure_add(current_total: float, x: float) -> float:
    return current_total + x    # no mutation; new value returned

print(f"impure_add(5): {impure_add(5)}, {impure_add(5)}")   # 5, 10 — different!
print(f"pure_add(0,5): {pure_add(0,5)}, {pure_add(0,5)}")   # 5, 5  — always same

# Immutable data approach
def process_scores(scores: list) -> list:
    """Returns a NEW list — never mutates the input."""
    return sorted([s for s in scores if s >= 60])

original = [45, 92, 78, 33, 65, 88]
processed = process_scores(original)
print(f"Original  : {original}")    # unchanged
print(f"Processed : {processed}")


# ─────────────────────────────────────────────
# 6. HIGHER-ORDER FUNCTIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("HIGHER-ORDER FUNCTIONS")
print("=" * 55)

# Functions that TAKE a function as argument
def apply_twice(func: Callable, value):
    """Apply func to value, then apply func to the result."""
    return func(func(value))

print(f"apply_twice(double, 3) = {apply_twice(lambda x: x*2, 3)}")  # 12
print(f"apply_twice(upper, hi) = {apply_twice(str.upper, 'hi')}")   # HI

# Functions that RETURN a function
def make_multiplier(n: float) -> Callable:
    """Returns a new function that multiplies its argument by n."""
    def multiplier(x):
        return x * n
    return multiplier

double  = make_multiplier(2)
triple  = make_multiplier(3)
half    = make_multiplier(0.5)

print(f"\ndouble(7) = {double(7)}")
print(f"triple(7) = {triple(7)}")
print(f"half(7)   = {half(7)}")

# composing functions
def compose(*funcs: Callable) -> Callable:
    """
    Returns a function that applies funcs right-to-left.
    compose(f, g, h)(x) = f(g(h(x)))
    """
    def composed(value):
        result = value
        for func in reversed(funcs):
            result = func(result)
        return result
    return composed

import math
pipeline = compose(math.ceil, math.sqrt, abs)
print(f"\ncompose(ceil, sqrt, abs)(-25) = {pipeline(-25)}")  # ceil(sqrt(25)) = 5


# ─────────────────────────────────────────────
# 7. functools.partial — Partial Application
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("functools.partial — Partial Application")
print("=" * 55)

# Freeze some arguments of a function, creating a specialized version
def power(base, exponent):
    return base ** exponent

square  = partial(power, exponent=2)  # freeze exponent=2
cube    = partial(power, exponent=3)
print(f"square(5) = {square(5)}")     # 25
print(f"cube(5)   = {cube(5)}")       # 125

# Useful with map / filter
from functools import partial as p
add_tax  = partial(lambda rate, price: price * (1 + rate), 0.1)   # 10% tax
prices   = [100, 250, 75, 430]
with_tax = list(map(add_tax, prices))
print(f"\nPrices   : {prices}")
print(f"With 10% tax: {with_tax}")

# sorted with partial key
data   = [{"name": "Charlie", "age": 30}, {"name": "Alice", "age": 25}, {"name": "Bob", "age": 35}]
by_age = sorted(data, key=lambda d: d["age"])
print(f"\nBy age: {[d['name'] for d in by_age]}")


# ─────────────────────────────────────────────
# 8. sorted, zip, enumerate — Functional Utilities
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("sorted, zip, enumerate")
print("=" * 55)

# sorted with custom key
words   = ["banana", "Apple", "cherry", "date", "FIG"]
by_len  = sorted(words, key=len)
by_low  = sorted(words, key=str.lower)
print(f"By length    : {by_len}")
print(f"Case-insens  : {by_low}")

# zip — pair up iterables
names  = ["Alice", "Bob", "Carol"]
scores = [92, 78, 85]
grades = ["A", "C+", "B"]

for record in zip(names, scores, grades):
    print(f"  {record}")

# unzip with zip(*...)
pairs   = [(1, "a"), (2, "b"), (3, "c")]
numbers, letters = zip(*pairs)
print(f"\nnumbers: {numbers}\nletters: {letters}")

# enumerate — index + value
fruits = ["apple", "banana", "cherry"]
for i, fruit in enumerate(fruits, start=1):
    print(f"  {i}. {fruit}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  lambda x: expr         → anonymous inline function
  map(f, it)             → apply f to every element (lazy)
  filter(f, it)          → keep elements where f(x) is True (lazy)
  reduce(f, it[, init])  → fold to single value (functools)
  sorted(it, key=f)      → sort using key function
  zip(a, b, c)           → pair elements across iterables
  enumerate(it, start=0) → (index, value) pairs

  functools:
    partial(f, *args)    → freeze arguments, partial application
    reduce(f, it)        → fold to one value
    lru_cache / cache    → memoize return values

  PRINCIPLES:
    Pure functions       → same input → same output, no side effects
    Immutability         → return new data, don't mutate input
    Higher-order fns     → functions that take/return functions
    Composition          → build complex behavior from tiny pieces
"""
print(summary)
