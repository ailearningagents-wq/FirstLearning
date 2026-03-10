"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 11: Comprehensions
=============================================================

WHAT ARE COMPREHENSIONS?
-------------------------
Comprehensions are concise, readable one-line expressions for building
collections (list, dict, set) or lazy sequences (generator).

FORMS:
  List       → [expr for x in iterable if condition]
  Dict       → {key: value for x in iterable if condition}
  Set        → {expr for x in iterable if condition}
  Generator  → (expr for x in iterable if condition)

WHY USE THEM?
  - Cleaner than equivalent for-loops
  - Usually faster (internally optimized)
  - Expressive and Pythonic
  - Can be nested for multi-dimensional transformations
"""

import pprint

# ─────────────────────────────────────────────
# 1. LIST COMPREHENSIONS
# ─────────────────────────────────────────────

print("=" * 55)
print("LIST COMPREHENSIONS")
print("=" * 55)

# Basic: squares of 0-9
squares = [x ** 2 for x in range(10)]
print(f"Squares         : {squares}")

# With filter condition
evens = [x for x in range(20) if x % 2 == 0]
print(f"Even (0-19)     : {evens}")

# Transform + filter
even_squares = [x ** 2 for x in range(10) if x % 2 == 0]
print(f"Even squares    : {even_squares}")

# String processing
words   = ["  hello  ", "  WORLD  ", "  Python  ", "  list  "]
cleaned = [w.strip().capitalize() for w in words]
print(f"Cleaned words   : {cleaned}")

# Conditional expression (ternary) inside comprehension
labels  = ["even" if x % 2 == 0 else "odd" for x in range(8)]
print(f"Labels (0-7)    : {labels}")

# Nested comprehension: flatten a 2D matrix
matrix  = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flat    = [cell for row in matrix for cell in row]
print(f"Flatten matrix  : {flat}")

# Nested: build a multiplication table as list of lists
times_table = [[r * c for c in range(1, 6)] for r in range(1, 6)]
print("Times table (5×5):")
for row in times_table:
    print(f"  {row}")

# Typical for-loop vs comprehension comparison
# For-loop version:
result_loop = []
for x in range(10):
    if x % 3 == 0:
        result_loop.append(x ** 2)

# Comprehension version (equivalent, shorter, faster):
result_comp = [x ** 2 for x in range(10) if x % 3 == 0]
print(f"\nFor-loop equiv  : {result_loop}")
print(f"Comprehension   : {result_comp}")
print(f"Equal?          : {result_loop == result_comp}")


# ─────────────────────────────────────────────
# 2. DICT COMPREHENSIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DICT COMPREHENSIONS")
print("=" * 55)

# Basic: number → square mapping
sq_map = {x: x ** 2 for x in range(1, 8)}
print(f"Square map      : {sq_map}")

# Invert a dictionary (swap keys and values)
original = {"a": 1, "b": 2, "c": 3}
inverted = {v: k for k, v in original.items()}
print(f"Inverted dict   : {inverted}")

# Filter items from a dict
scores = {"Alice": 92, "Bob": 45, "Carol": 78, "Dave": 33, "Eve": 89}
passing = {name: score for name, score in scores.items() if score >= 60}
print(f"Passing scores  : {passing}")

# Normalize keys (lowercase)
raw = {"Name": "Alice", "AGE": 30, "CITY": "NYC"}
normalized = {k.lower(): v for k, v in raw.items()}
print(f"Normalized keys : {normalized}")

# From two parallel lists (zip)
keys   = ["x", "y", "z"]
values = [10, 20, 30]
paired = {k: v for k, v in zip(keys, values)}
print(f"From zip        : {paired}")

# Nested — word frequency counter
sentence  = "the quick brown fox jumps over the lazy dog the fox"
word_freq = {word: sentence.split().count(word) for word in set(sentence.split())}
print(f"Word frequency  : {dict(sorted(word_freq.items()))}")


# ─────────────────────────────────────────────
# 3. SET COMPREHENSIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SET COMPREHENSIONS")
print("=" * 55)

# Unique squares
nums        = [1, -1, 2, -2, 3, 3, 4]
unique_sq   = {x ** 2 for x in nums}
print(f"Unique squares  : {sorted(unique_sq)}")

# Unique first letters
words       = ["apple", "avocado", "banana", "blueberry", "cherry", "apricot"]
first_chars = {w[0] for w in words}
print(f"First chars     : {sorted(first_chars)}")

# Set ops on comprehensions
evens_set   = {x for x in range(20) if x % 2 == 0}
threes_set  = {x for x in range(20) if x % 3 == 0}
print(f"Divisible by 2 or 3: {sorted(evens_set | threes_set)}")
print(f"Divisible by 2 and 3: {sorted(evens_set & threes_set)}")


# ─────────────────────────────────────────────
# 4. GENERATOR EXPRESSIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("GENERATOR EXPRESSIONS")
print("=" * 55)

# Lazy — computed on demand; use ( ) instead of [ ]
gen  = (x ** 2 for x in range(10))
print(f"Type  : {type(gen)}")
print(f"Values: {list(gen)}")

# Efficient for large/streaming data
import sys

list_mem = sys.getsizeof([x * x for x in range(100_000)])
gen_mem  = sys.getsizeof(x * x for x in range(100_000))
print(f"\nMemory: list={list_mem:,}B vs gen={gen_mem}B")

# Works directly with aggregation functions
total = sum(x * x for x in range(1, 101))
print(f"\nSum 1²+2²+…+100² = {total}")

any_negative = any(x < 0 for x in [3, 1, -2, 5])
all_positive = all(x > 0 for x in [3, 1, -2, 5])
print(f"any negative     : {any_negative}")
print(f"all positive     : {all_positive}")

# Short-circuits — stops at first match (unlike list comprehension)
first_even = next((x for x in range(1_000_000) if x % 2 == 0), None)
print(f"First even >= 0  : {first_even}")


# ─────────────────────────────────────────────
# 5. NESTED COMPREHENSIONS (ADVANCED)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("NESTED COMPREHENSIONS")
print("=" * 55)

# Matrix transpose
matrix    = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
transposed = [[row[i] for row in matrix] for i in range(3)]
print("Original matrix:")
for row in matrix: print(f"  {row}")
print("Transposed:")
for row in transposed: print(f"  {row}")

# Cartesian product via nested comprehension
coords = [(x, y) for x in range(3) for y in range(3) if x != y]
print(f"\n(x, y) where x≠y : {coords}")

# Nested dict comprehension: grade matrix
students = ["Alice", "Bob", "Carol"]
subjects = ["Math", "Science", "English"]
import random; random.seed(42)
grades = {
    student: {subject: random.randint(60, 100) for subject in subjects}
    for student in students
}
print("\nGrade matrix:")
pprint.pprint(grades)

# Average per student using nested comprehension
averages = {
    student: sum(marks.values()) / len(marks)
    for student, marks in grades.items()
}
print("\nAverages:", {k: round(v, 1) for k, v in averages.items()})


# ─────────────────────────────────────────────
# 6. WALRUS OPERATOR (:=) IN COMPREHENSIONS
# ─────────────────────────────────────────────
# Python 3.8+ — assigns AND uses a value inside a comprehension
# Avoids computing the same expensive expression twice.

print("\n" + "=" * 55)
print("WALRUS OPERATOR := (Python 3.8+)")
print("=" * 55)

import math

# Without walrus — computes sqrt twice
# [math.sqrt(x) for x in data if math.sqrt(x) > 1.5]

# With walrus — compute once, use twice
data = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
results = [root for x in data if (root := math.sqrt(x)) > 1.2]
print(f"sqrt > 1.2 : {[round(r, 3) for r in results]}")

# Also useful to capture intermediate transformed values
cleaned = [upper for s in ["  hi ", " bye ", " ok "] if (upper := s.strip().upper())]
print(f"Cleaned    : {cleaned}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  TYPE         SYNTAX                     RETURNS
  ─────────────────────────────────────────────────
  List         [expr for x in it if c]    list
  Dict         {k: v for x in it if c}    dict
  Set          {expr for x in it if c}    set
  Generator    (expr for x in it if c)    generator (lazy)

  FEATURES:
    Filter    → if condition at the end
    Transform → expression at the start
    Nested    → [... for x in outer for y in inner]
    Ternary   → [a if cond else b for x in it]
    Walrus    → [y for x in it if (y := f(x)) > 0]

  BEST PRACTICE:
    ✔ Use comprehensions for simple, readable transformations
    ✔ Prefer generator expressions for large data (memory efficient)
    ✔ Avoid deeply nested comprehensions — split into variables for clarity
"""
print(summary)
