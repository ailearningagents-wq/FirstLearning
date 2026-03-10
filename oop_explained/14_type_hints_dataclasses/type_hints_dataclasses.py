"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 14: Type Hints & Dataclasses
=============================================================

PART A — TYPE HINTS
--------------------
Type hints (PEP 484+) let you annotate function parameters and return
values with EXPECTED TYPES. Python does NOT enforce them at runtime —
but type checkers (mypy, pyright), IDEs, and linters use them.

Benefits:
  - Better IDE autocomplete and error catching
  - Self-documenting code
  - Catch type errors before runtime
  - Required for robust library / API design

PART B — DATACLASSES
---------------------
@dataclass (Python 3.7+) automatically generates boilerplate methods:
  __init__, __repr__, __eq__
Optionally generates: __lt__, __hash__, __slots__, etc.
"""

from __future__ import annotations       # forward references in annotations
from typing import (
    Optional, Union, List, Dict, Tuple, Set,
    Callable, Any, ClassVar,
    TypeVar, Generic,
)
from dataclasses import (
    dataclass, field, asdict, astuple, replace, fields,
)


# ═══════════════════════════════════════════════
# PART A: TYPE HINTS
# ═══════════════════════════════════════════════

# ─────────────────────────────────────────────
# 1. BASIC TYPE HINTS
# ─────────────────────────────────────────────

print("=" * 55)
print("TYPE HINTS — Basics")
print("=" * 55)

def greet(name: str) -> str:
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    return a + b

def is_adult(age: int) -> bool:
    return age >= 18

print(greet("Alice"))
print(add(3, 4))
print(is_adult(20))

# Variable annotations
x: int = 10
name: str = "Python"
scores: list[float] = [9.5, 8.0, 7.5]
mapping: dict[str, int] = {"a": 1, "b": 2}
print(f"Annotated vars: {x}, {name}, {scores}, {mapping}")


# ─────────────────────────────────────────────
# 2. OPTIONAL, UNION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("Optional and Union")
print("=" * 55)

# Optional[T] == Union[T, None]
def find_user(user_id: int) -> Optional[str]:
    users = {1: "Alice", 2: "Bob"}
    return users.get(user_id)       # returns str or None

print(find_user(1))    # Alice
print(find_user(99))   # None

# Union — accepts multiple types
def stringify(value: Union[int, float, str]) -> str:
    return str(value)

print(stringify(42))
print(stringify(3.14))
print(stringify("hello"))

# Python 3.10+ shorthand: int | str instead of Union[int, str]
def newer_style(value: int | str | None) -> str:
    return repr(value)

print(newer_style(10), newer_style("hi"), newer_style(None))


# ─────────────────────────────────────────────
# 3. COLLECTIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("Collection Type Hints")
print("=" * 55)

def process(items: list[int]) -> list[int]:
    return sorted(set(items))

def count_chars(text: str) -> dict[str, int]:
    return {ch: text.count(ch) for ch in set(text)}

def first_and_last(items: list[Any]) -> tuple[Any, Any]:
    return items[0], items[-1]

def unique(items: list[int]) -> set[int]:
    return set(items)

print(process([3, 1, 2, 1, 3]))
print(count_chars("hello"))
print(first_and_last([10, 20, 30]))
print(unique([1, 2, 2, 3, 3, 3]))


# ─────────────────────────────────────────────
# 4. CALLABLE, TypeVar, Generic
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("Callable, TypeVar, Generic")
print("=" * 55)

# Callable[[ArgTypes], ReturnType]
def apply(func: Callable[[int], int], value: int) -> int:
    return func(value)

print(apply(lambda x: x * 2, 7))

# TypeVar — generic placeholder
T = TypeVar("T")

def first(items: list[T]) -> T:
    return items[0]

print(first([1, 2, 3]))
print(first(["a", "b", "c"]))

# Generic class
class Stack(Generic[T]):
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()

    def peek(self) -> Optional[T]:
        return self._items[-1] if self._items else None

    def __len__(self) -> int:
        return len(self._items)

    def __repr__(self) -> str:
        return f"Stack({self._items})"

int_stack: Stack[int] = Stack()
int_stack.push(10)
int_stack.push(20)
int_stack.push(30)
print(f"Int stack: {int_stack}")
print(f"Pop: {int_stack.pop()}")


# ═══════════════════════════════════════════════
# PART B: DATACLASSES
# ═══════════════════════════════════════════════

print("\n" + "=" * 55)
print("DATACLASSES — Basics")
print("=" * 55)

@dataclass
class Point:
    """
    @dataclass generates:
      __init__(self, x, y)
      __repr__ → Point(x=3, y=4)
      __eq__   → compares x and y fields
    """
    x: float
    y: float


p1 = Point(3.0, 4.0)
p2 = Point(3.0, 4.0)
p3 = Point(1.0, 2.0)

print(f"p1        : {p1}")              # __repr__
print(f"p1 == p2  : {p1 == p2}")        # __eq__ — True
print(f"p1 == p3  : {p1 == p3}")        # __eq__ — False
print(f"p1 is p2  : {p1 is p2}")        # False — different objects


# ─────────────────────────────────────────────
# DATACLASS WITH DEFAULTS, FIELD, POST-INIT
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DATACLASSES — Defaults, field(), __post_init__")
print("=" * 55)

@dataclass
class Employee:
    name: str
    department: str
    salary: float = 50_000.0                    # default value
    skills: list[str] = field(default_factory=list)   # mutable default MUST use field()
    employee_id: int = field(default=0, repr=False)   # excluded from __repr__

    # Class variable — shared, NOT included as __init__ arg
    company: ClassVar[str] = "TechCorp"

    def __post_init__(self):
        """Runs after __init__ — validation and derived fields."""
        if self.salary < 0:
            raise ValueError("Salary cannot be negative.")
        self.name = self.name.strip().title()

    def give_raise(self, percent: float) -> None:
        self.salary *= (1 + percent / 100)

    def add_skill(self, skill: str) -> None:
        self.skills.append(skill)


e1 = Employee("alice smith", "Engineering", 80_000, ["Python", "SQL"])
e2 = Employee("bob jones",   "Marketing")

print(f"e1: {e1}")
print(f"e2: {e2}")
print(f"Company (class var): {Employee.company}")

e1.give_raise(10)
e2.add_skill("Excel")
e2.add_skill("PowerPoint")
print(f"\nAfter raise: e1.salary = ${e1.salary:,.0f}")
print(f"e2 skills: {e2.skills}")


# ─────────────────────────────────────────────
# ORDERED, FROZEN, SLOTS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DATACLASSES — order, frozen, slots")
print("=" * 55)

# order=True → generates __lt__, __le__, __gt__, __ge__
@dataclass(order=True)
class Version:
    major: int
    minor: int
    patch: int = 0

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"

versions = [Version(2, 0), Version(1, 9, 5), Version(2, 1), Version(1, 0)]
print("Sorted versions:", sorted(versions))
print(f"Latest: {max(versions)}")

# frozen=True → immutable (no assignment after creation; also makes it hashable)
@dataclass(frozen=True)
class Coordinate:
    lat:  float
    lon:  float

    @property
    def quadrant(self) -> str:
        ns = "N" if self.lat >= 0 else "S"
        ew = "E" if self.lon >= 0 else "W"
        return ns + ew

nyc  = Coordinate(40.71, -74.01)
london = Coordinate(51.51, -0.13)
print(f"\nNYC     : {nyc} → {nyc.quadrant}")
print(f"London  : {london} → {london.quadrant}")

try:
    nyc.lat = 0.0         # raises FrozenInstanceError
except Exception as e:
    print(f"FrozenInstanceError: {e}")

# Frozen dataclasses are hashable → can be used in sets/dicts
location_set = {nyc, london, Coordinate(40.71, -74.01)}  # duplicate NYC
print(f"Set of coords: {location_set}")


# ─────────────────────────────────────────────
# DATACLASS UTILITIES: asdict, astuple, replace, fields
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DATACLASS UTILITIES")
print("=" * 55)

@dataclass
class Config:
    host:    str  = "localhost"
    port:    int  = 8080
    debug:   bool = False
    max_conn: int = 100

cfg = Config(host="prod-server", port=443, debug=False)
print(f"Config      : {cfg}")

# asdict() — convert to dict (useful for JSON serialization)
cfg_dict = asdict(cfg)
print(f"asdict()    : {cfg_dict}")

# astuple() — convert to tuple
cfg_tuple = astuple(cfg)
print(f"astuple()   : {cfg_tuple}")

# replace() — create a modified COPY (original unchanged; works with frozen too)
debug_cfg = replace(cfg, debug=True, port=8080)
print(f"replace()   : {debug_cfg}")
print(f"Original    : {cfg}")      # unchanged

# fields() — inspect field metadata
print("\nFields:")
for f in fields(cfg):
    print(f"  {f.name:10} type={f.type.__name__ if hasattr(f.type, '__name__') else f.type!r:8} default={f.default!r}")


# ─────────────────────────────────────────────
# DATACLASS INHERITANCE
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DATACLASS INHERITANCE")
print("=" * 55)

@dataclass
class Animal:
    name: str
    age:  int

@dataclass
class Dog(Animal):
    breed: str
    is_trained: bool = False

@dataclass
class ServiceDog(Dog):
    handler:   str = "Unknown"
    certified: bool = False

d = Dog("Buddy", 3, "Labrador", True)
s = ServiceDog("Rex", 5, "German Shepherd", True, "John", True)

print(f"Dog        : {d}")
print(f"ServiceDog : {s}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  TYPE HINTS:
    param: Type          → annotate parameter
    -> ReturnType        → annotate return value
    Optional[T]          → T or None   (same as T | None in 3.10+)
    Union[A, B]          → A or B      (same as A | B in 3.10+)
    list[T], dict[K,V]   → generic containers
    Callable[[A], R]     → function type
    TypeVar, Generic     → generic classes

  @dataclass:
    @dataclass           → auto-gen __init__, __repr__, __eq__
    @dataclass(order=T)  → also __lt__, __le__, __gt__, __ge__
    @dataclass(frozen=T) → immutable, hashable
    field(default_factory=list) → mutable defaults
    __post_init__        → validation / derived fields
    ClassVar[T]          → class-level variable, not in __init__

  UTILITIES:
    asdict(obj)          → dict
    astuple(obj)         → tuple
    replace(obj, **kw)   → modified copy
    fields(cls/obj)      → field metadata
"""
print(summary)
