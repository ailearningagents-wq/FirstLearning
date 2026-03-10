"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 6: Special (Dunder / Magic) Methods
=============================================================

WHAT ARE DUNDER METHODS?
-------------------------
Dunder = "Double UNDERscore" → __method__
Python calls these automatically in response to built-in operations.

They allow your custom classes to behave like built-in types:
  - Support arithmetic: obj1 + obj2
  - Support comparisons: obj1 < obj2
  - Work with len(), str(), repr(), bool(), abs(), hash()
  - Support iteration: for item in obj
  - Support context managers: with obj as x
  - Support indexing: obj[key], obj[0:5]

CATEGORIES:
  Construction   → __new__, __init__, __del__
  Representation → __str__, __repr__, __format__
  Arithmetic     → __add__, __sub__, __mul__, __truediv__, __pow__, __neg__
  Comparison     → __eq__, __lt__, __le__, __gt__, __ge__, __ne__
  Container      → __len__, __getitem__, __setitem__, __delitem__, __contains__
  Iteration      → __iter__, __next__
  Context Mgr    → __enter__, __exit__
  Callable       → __call__
  Hashing        → __hash__
"""


# ─────────────────────────────────────────────
# 1. __str__ vs __repr__
# ─────────────────────────────────────────────
# __str__  → human-readable string  (str(obj), print(obj))
# __repr__ → unambiguous developer representation (repr(obj), REPL)
#            Ideally, repr() should return a string that could recreate the object.

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        """Friendly output — for end users."""
        return f"Point({self.x}, {self.y})"

    def __repr__(self) -> str:
        """Unambiguous — for developers/debugging."""
        return f"Point(x={self.x!r}, y={self.y!r})"

    def __format__(self, spec: str) -> str:
        """Supports format(p, 'polar') or f'{p:polar}'."""
        import math
        if spec == "polar":
            r = math.sqrt(self.x**2 + self.y**2)
            theta = math.degrees(math.atan2(self.y, self.x))
            return f"r={r:.2f}, θ={theta:.1f}°"
        return str(self)


print("=" * 55)
print("__str__ vs __repr__ vs __format__")
print("=" * 55)

p = Point(3, 4)
print(f"str(p)       : {str(p)}")          # calls __str__
print(f"repr(p)      : {repr(p)}")         # calls __repr__
print(f"f'{{p}}'     : {p}")               # calls __str__
print(f"format polar : {format(p, 'polar')}")


# ─────────────────────────────────────────────
# 2. ARITHMETIC OPERATORS
# ─────────────────────────────────────────────

class Fraction:
    """
    Represents a mathematical fraction p/q.
    Demonstrates arithmetic dunder methods.
    """

    def __init__(self, numerator: int, denominator: int):
        if denominator == 0:
            raise ZeroDivisionError("Denominator cannot be zero.")
        # Simplify using GCD
        from math import gcd
        g = gcd(abs(numerator), abs(denominator))
        sign = -1 if denominator < 0 else 1
        self.num = sign * numerator // g
        self.den = sign * denominator // g

    def __str__(self)  -> str: return f"{self.num}/{self.den}"
    def __repr__(self) -> str: return f"Fraction({self.num}, {self.den})"

    def __add__(self, other: "Fraction") -> "Fraction":
        return Fraction(
            self.num * other.den + other.num * self.den,
            self.den * other.den
        )

    def __sub__(self, other: "Fraction") -> "Fraction":
        return Fraction(
            self.num * other.den - other.num * self.den,
            self.den * other.den
        )

    def __mul__(self, other: "Fraction") -> "Fraction":
        return Fraction(self.num * other.num, self.den * other.den)

    def __truediv__(self, other: "Fraction") -> "Fraction":
        return Fraction(self.num * other.den, self.den * other.num)

    def __neg__(self) -> "Fraction":
        return Fraction(-self.num, self.den)

    def __abs__(self) -> "Fraction":
        return Fraction(abs(self.num), self.den)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Fraction): return NotImplemented
        return self.num == other.num and self.den == other.den

    def __lt__(self, other: "Fraction") -> bool:
        return self.num * other.den < other.num * self.den

    def __le__(self, other: "Fraction") -> bool:
        return self == other or self < other

    def __float__(self) -> float:
        return self.num / self.den


print("\n" + "=" * 55)
print("ARITHMETIC DUNDER METHODS — Fraction")
print("=" * 55)

a = Fraction(1, 2)
b = Fraction(1, 3)

print(f"a     = {a}")
print(f"b     = {b}")
print(f"a + b = {a + b}")           # calls __add__
print(f"a - b = {a - b}")           # calls __sub__
print(f"a * b = {a * b}")           # calls __mul__
print(f"a / b = {a / b}")           # calls __truediv__
print(f"-a    = {-a}")              # calls __neg__
print(f"a == b: {a == b}")          # calls __eq__
print(f"a < b : {a < b}")           # calls __lt__
print(f"a <= b: {a <= b}")          # calls __le__
print(f"float(a): {float(a)}")      # calls __float__


# ─────────────────────────────────────────────
# 3. CONTAINER DUNDERS
# ─────────────────────────────────────────────

class NumberList:
    """
    A custom list-like container.
    Demonstrates __len__, __getitem__, __setitem__, __delitem__, __contains__.
    """

    def __init__(self, *args):
        self._data = list(args)

    def __len__(self) -> int:
        return len(self._data)                   # len(nl)

    def __getitem__(self, index):
        return self._data[index]                 # nl[0], nl[1:3]

    def __setitem__(self, index, value):
        self._data[index] = value                # nl[0] = 99

    def __delitem__(self, index):
        del self._data[index]                    # del nl[0]

    def __contains__(self, item) -> bool:
        return item in self._data                # 5 in nl

    def __iter__(self):
        return iter(self._data)                  # for x in nl

    def __str__(self) -> str:
        return f"NumberList{self._data}"

    def append(self, item):
        self._data.append(item)


print("\n" + "=" * 55)
print("CONTAINER DUNDER METHODS — NumberList")
print("=" * 55)

nl = NumberList(10, 20, 30, 40, 50)
print(f"nl           : {nl}")
print(f"len(nl)      : {len(nl)}")             # __len__
print(f"nl[0]        : {nl[0]}")               # __getitem__
print(f"nl[1:3]      : {nl[1:3]}")             # __getitem__ with slice
print(f"30 in nl     : {30 in nl}")            # __contains__
print(f"99 in nl     : {99 in nl}")

nl[0] = 999                                     # __setitem__
print(f"After nl[0]=999: {nl}")

del nl[4]                                       # __delitem__
print(f"After del nl[4]: {nl}")

print("Iterating:")
for item in nl:                                  # __iter__
    print(f"  {item}")


# ─────────────────────────────────────────────
# 4. __iter__ AND __next__ — Custom Iteration
# ─────────────────────────────────────────────

class CountDown:
    """
    An iterator that counts down from n to 1.
    __iter__ returns the iterator object.
    __next__ returns the next value, raises StopIteration when done.
    """

    def __init__(self, start: int):
        self.start = start
        self.current = start

    def __iter__(self):
        self.current = self.start    # reset on each iteration
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


print("\n" + "=" * 55)
print("__iter__ and __next__ — CountDown")
print("=" * 55)

countdown = CountDown(5)
for n in countdown:               # calls __iter__, then __next__ repeatedly
    print(f"  {n}...")
print("  GO!")

# Same object, iterate again (reset works because __iter__ resets self.current)
print("Second time:")
print(*countdown, sep="... ")
print("\nGO!")


# ─────────────────────────────────────────────
# 5. CONTEXT MANAGER — __enter__ and __exit__
# ─────────────────────────────────────────────

class ManagedFile:
    """
    Custom context manager that wraps file operations.
    __enter__: setup (open file)
    __exit__:  teardown (close file, handle exceptions)
    """

    def __init__(self, filename: str, mode: str = "r"):
        self.filename = filename
        self.mode = mode
        self.file = None

    def __enter__(self):
        """Called when entering `with` block. Returns value bound to `as` variable."""
        print(f"Opening file: {self.filename}")
        self.file = open(self.filename, self.mode)
        return self.file              # → the `f` in `with ManagedFile(...) as f`

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Called when leaving `with` block (even if an exception occurred).
        exc_type/value/traceback are None if no exception.
        Return True to suppress exceptions; False/None to propagate them.
        """
        if self.file:
            self.file.close()
            print(f"File closed: {self.filename}")
        if exc_type:
            print(f"Exception handled: {exc_type.__name__}: {exc_value}")
            return False    # don't suppress — let it propagate


class Timer:
    """Context manager to time a code block."""
    import time as _time

    def __enter__(self):
        import time
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        import time
        self.elapsed = time.perf_counter() - self._start
        print(f"Elapsed: {self.elapsed:.6f} seconds")
        return False

    @property
    def elapsed_ms(self) -> float:
        return self.elapsed * 1000


print("\n" + "=" * 55)
print("CONTEXT MANAGERS — __enter__ / __exit__")
print("=" * 55)

# Write a temp file, then read it back
import tempfile, os
tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
tmp.write("Hello, context manager!")
tmp.close()

with ManagedFile(tmp.name, "r") as f:
    content = f.read()
    print(f"File content: {content!r}")

os.unlink(tmp.name)

with Timer() as t:
    total = sum(range(1_000_000))
print(f"Sum = {total}, took {t.elapsed_ms:.2f} ms")


# ─────────────────────────────────────────────
# 6. __call__ — Making Objects Callable
# ─────────────────────────────────────────────

class Multiplier:
    """An object that acts like a function — can be called with ()."""

    def __init__(self, factor: float):
        self.factor = factor

    def __call__(self, value: float) -> float:
        return value * self.factor


class Memoize:
    """A callable class that caches results of an expensive function."""

    def __init__(self, func):
        self.func = func
        self._cache = {}

    def __call__(self, *args):
        if args not in self._cache:
            self._cache[args] = self.func(*args)
        return self._cache[args]


print("\n" + "=" * 55)
print("__call__ — Callable Objects")
print("=" * 55)

double = Multiplier(2)
triple = Multiplier(3)

print(f"double(5) = {double(5)}")    # calls __call__
print(f"triple(5) = {triple(5)}")

@Memoize
def fibonacci(n: int) -> int:
    if n <= 1: return n
    return fibonacci(n - 1) + fibonacci(n - 2)

print(f"fibonacci(10) = {fibonacci(10)}")
print(f"fibonacci(30) = {fibonacci(30)}")
print(f"Cache entries : {len(fibonacci._cache)}")


# ─────────────────────────────────────────────
# 7. __hash__ and __eq__
# ─────────────────────────────────────────────
# If you define __eq__, Python sets __hash__ = None (unhashable).
# To use objects as dict keys or in sets, also define __hash__.

class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r, self.g, self.b = r, g, b

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Color): return NotImplemented
        return (self.r, self.g, self.b) == (other.r, other.g, other.b)

    def __hash__(self) -> int:
        return hash((self.r, self.g, self.b))  # tuple hash

    def __repr__(self) -> str:
        return f"Color(r={self.r}, g={self.g}, b={self.b})"


print("\n" + "=" * 55)
print("__hash__ — Using Objects as Dict Keys / Set Members")
print("=" * 55)

red   = Color(255, 0, 0)
green = Color(0, 255, 0)
red2  = Color(255, 0, 0)

print(f"red == red2   : {red == red2}")
print(f"red is red2   : {red is red2}")   # different objects, same value
print(f"hash(red)==hash(red2): {hash(red)==hash(red2)}")

color_set = {red, green, red2}           # red and red2 are "equal" in a set
print(f"Set of colors : {color_set}")    # only 2 — red2 is a duplicate

color_labels = {red: "Primary Red", green: "Primary Green"}
print(f"Dict lookup   : {color_labels[red2]}")  # red2 == red → same bucket


# ─────────────────────────────────────────────
# SUMMARY TABLE
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DUNDER METHODS QUICK REFERENCE")
print("=" * 55)
summary = """
  Construction   : __init__, __new__, __del__
  Strings        : __str__, __repr__, __format__
  Arithmetic     : __add__, __sub__, __mul__, __truediv__, __pow__,
                   __neg__, __abs__, __radd__ (reflected)
  Comparisons    : __eq__, __ne__, __lt__, __le__, __gt__, __ge__
  Containers     : __len__, __getitem__, __setitem__, __delitem__,
                   __contains__, __iter__, __next__
  Context Mgr    : __enter__, __exit__
  Callable       : __call__
  Hashing        : __hash__
  Boolean        : __bool__

  Python calls these for you — you just define them!
"""
print(summary)
