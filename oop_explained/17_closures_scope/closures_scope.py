"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 17: Closures, Scope & Variable Binding
=============================================================

WHAT IS SCOPE?
---------------
Scope defines WHERE a variable is accessible.

Python uses LEGB rule to look up names:
  L → Local      — inside the current function
  E → Enclosing  — in any enclosing (outer) function (closures)
  G → Global     — module-level
  B → Built-ins  — Python's built-in names (len, print, range, ...)

Python searches L → E → G → B and uses the FIRST match found.

WHAT IS A CLOSURE?
-------------------
A closure is a function that REMEMBERS variables from its enclosing
scope even after the outer function has returned.
The remembered variables are called "free variables".

COVERED:
  1. LEGB scope rules
  2. global and nonlocal keywords
  3. Closures and free variables
  4. Closure factories (function factories)
  5. Closures vs classes
  6. Common closure pitfall (late binding)
"""


# ─────────────────────────────────────────────
# 1. LEGB SCOPE RULES
# ─────────────────────────────────────────────

x = "GLOBAL"          # G — module-level

def outer():
    x = "ENCLOSING"   # E — enclosing scope for inner()

    def inner():
        x = "LOCAL"   # L — local to inner()
        print(f"inner sees    : {x}")   # LOCAL

    inner()
    print(f"outer sees    : {x}")       # ENCLOSING

outer()
print(f"module sees   : {x}")           # GLOBAL

# Built-in is looked up last
print(f"len is built-in: {len([1,2,3])}")   # B — built-in


print("\n" + "=" * 55)
print("LEGB SCOPE LOOKUP ORDER")
print("=" * 55)

y = 10  # global

def demonstrate_legb():
    y = 20                   # local shadows global
    print(f"inside y = {y}") # 20 — Local found before Global

demonstrate_legb()
print(f"outside y = {y}")    # 10 — global unchanged


# ─────────────────────────────────────────────
# 2. global AND nonlocal KEYWORDS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("global AND nonlocal")
print("=" * 55)

count = 0   # module-level global

def increment():
    global count          # tells Python: 'count' here refers to the GLOBAL
    count += 1

increment()
increment()
increment()
print(f"global count = {count}")    # 3

# nonlocal — modify a variable in the ENCLOSING (not global) scope
def make_counter(start: int = 0):
    value = start

    def increment(step: int = 1):
        nonlocal value           # refers to 'value' in make_counter's scope
        value += step
        return value

    def reset():
        nonlocal value
        value = start

    def get():
        return value             # no nonlocal needed — just reading

    return increment, reset, get


inc, rst, get = make_counter(10)
print(f"\nCounter start : {get()}")     # 10
print(f"increment()   : {inc()}")      # 11
print(f"increment(5)  : {inc(5)}")     # 16
print(f"reset()       : ", end=""); rst(); print(get())   # 10


# ─────────────────────────────────────────────
# 3. CLOSURES — Functions That Remember
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CLOSURES")
print("=" * 55)

def make_adder(n: int):
    """
    Returns a function that adds `n` to its argument.
    `n` is a FREE VARIABLE — captured and remembered in the closure.
    """
    def adder(x: int) -> int:
        return x + n        # `n` is captured from make_adder's scope
    return adder            # adder is a CLOSURE


add5  = make_adder(5)
add10 = make_adder(10)
add_n = make_adder(-3)

print(f"add5(7)   = {add5(7)}")     # 12
print(f"add10(7)  = {add10(7)}")    # 17
print(f"add_n(10) = {add_n(10)}")   # 7

# Inspecting the closure
print(f"\nFunction name : {add5.__name__}")
print(f"Free vars     : {add5.__code__.co_freevars}")      # ('n',)
print(f"Closure cells : {add5.__closure__[0].cell_contents}")  # 5


# ─────────────────────────────────────────────
# 4. CLOSURE FACTORIES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CLOSURE FACTORIES")
print("=" * 55)

# Power functions factory
def make_power(exponent: int):
    def power(base: float) -> float:
        return base ** exponent
    power.__name__ = f"power_{exponent}"
    return power

square = make_power(2)
cube   = make_power(3)
root   = make_power(0.5)

print(f"square(5)  = {square(5)}")    # 25
print(f"cube(3)    = {cube(3)}")      # 27
print(f"root(16)   = {root(16)}")     # 4.0

# Multiplier factory
def make_multiplier(factor: float):
    def multiply(x: float) -> float:
        return x * factor
    return multiply

double = make_multiplier(2)
half   = make_multiplier(0.5)
percent = make_multiplier(0.01)

prices = [100, 250, 75]
print(f"\nPrices       : {prices}")
print(f"Doubled      : {list(map(double, prices))}")
print(f"Halved       : {list(map(half, prices))}")

# Validator factory
def make_range_validator(lo: float, hi: float):
    """Returns a function that checks if a value is in [lo, hi]."""
    def validate(value: float) -> bool:
        if not (lo <= value <= hi):
            raise ValueError(f"{value} out of range [{lo}, {hi}]")
        return True
    validate.__name__ = f"validate_{lo}_{hi}"
    return validate

validate_score    = make_range_validator(0, 100)
validate_age      = make_range_validator(0, 150)
validate_humidity = make_range_validator(0.0, 1.0)

for fn, val in [(validate_score, 95), (validate_age, 200), (validate_humidity, 0.75)]:
    try:
        result = fn(val)
        print(f"  {fn.__name__}({val}) = {result}")
    except ValueError as e:
        print(f"  ValueError: {e}")


# ─────────────────────────────────────────────
# 5. STATEFUL CLOSURES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("STATEFUL CLOSURES (nonlocal state)")
print("=" * 55)

def make_accumulator(initial: float = 0):
    """Closure that maintains running total state."""
    total = initial

    def add(value: float) -> float:
        nonlocal total
        total += value
        return total

    def reset():
        nonlocal total
        total = initial

    add.reset = reset     # attach reset as attribute for convenience
    return add


acc = make_accumulator()
print(f"acc(10) = {acc(10)}")
print(f"acc(25) = {acc(25)}")
print(f"acc(5)  = {acc(5)}")
acc.reset()
print(f"After reset: acc(1) = {acc(1)}")


# ─────────────────────────────────────────────
# 6. CLOSURES vs CLASSES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CLOSURES vs CLASSES — two ways to encapsulate state")
print("=" * 55)

# Closure approach
def counter_closure(start: int = 0):
    count = start
    def increment(n=1):
        nonlocal count
        count += n
        return count
    def value():
        return count
    return increment, value

inc, val = counter_closure()
inc(); inc(); inc(5)
print(f"Closure counter: {val()}")     # 7

# Class approach
class CounterClass:
    def __init__(self, start: int = 0):
        self.count = start
    def increment(self, n: int = 1):
        self.count += n
        return self.count
    def value(self) -> int:
        return self.count

c = CounterClass()
c.increment(); c.increment(); c.increment(5)
print(f"Class counter  : {c.value()}")  # 7

# When to choose:
# Closure → simpler, fewer operations (1-3 functions, no inheritance needed)
# Class   → complex state, many methods, inheritance, needs repr/pickle/etc.


# ─────────────────────────────────────────────
# 7. COMMON PITFALL: LATE BINDING IN LOOPS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("PITFALL: Late Binding in Closures")
print("=" * 55)

# BUG: all functions share the SAME `i` variable — captured by reference
buggy = [lambda: i for i in range(5)]
print("Buggy (all i=4):", [f() for f in buggy])    # [4,4,4,4,4]

# FIX 1: default argument captures value at definition time
fixed_default = [lambda i=i: i for i in range(5)]
print("Fixed (defaults):", [f() for f in fixed_default])  # [0,1,2,3,4]

# FIX 2: use a factory closure to force early binding
def make_fn(value):
    return lambda: value

fixed_factory = [make_fn(i) for i in range(5)]
print("Fixed (factory) :", [f() for f in fixed_factory])  # [0,1,2,3,4]

# FIX 3: list comprehension (each `i` is fresh)
results = [i * i for i in range(5)]
print("Comprehension   :", results)


# ─────────────────────────────────────────────
# 8. VARIABLE LIFETIME AND __del__
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("Variable Lifetime & Reference Counting")
print("=" * 55)

import sys

a = [1, 2, 3]
b = a                 # both point to same object
print(f"ref count of a (approx): {sys.getrefcount(a)}")  # 3 (a, b, + arg to getrefcount)

del b                 # removes one reference
print(f"after del b, a still: {a}")    # object still alive — a holds a ref

# Python uses reference counting + cyclic garbage collector
import gc
print(f"GC enabled    : {gc.isenabled()}")
print(f"GC thresholds : {gc.get_threshold()}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  LEGB LOOKUP ORDER:
    Local → Enclosing → Global → Built-in

  KEYWORDS:
    global x    → assign to module-level x from inside a function
    nonlocal x  → assign to enclosing function's x (not global)

  CLOSURE:
    def outer():
        captured = 10       ← free variable
        def inner():
            return captured ← captures outer's binding
        return inner

  inner.__code__.co_freevars  → names of captured variables
  inner.__closure__[i].cell_contents → captured values

  PITFALL — Late Binding:
    [lambda: i for i in range(5)]  → all return 4 (last i)!
    FIX: lambda i=i: i             → capture value, not name

  CLOSURE vs CLASS:
    Use a closure for simple 1-3 operation stateful functions.
    Use a class for complex state and multiple behaviors.
"""
print(summary)
