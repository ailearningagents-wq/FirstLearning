"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 4: Polymorphism
=============================================================

WHAT IS POLYMORPHISM?
----------------------
Polymorphism means "MANY FORMS". It allows objects of DIFFERENT classes to be
treated through the SAME interface, even though they may behave differently.

"One interface, many implementations."

TYPES OF POLYMORPHISM IN PYTHON:
  1. Method Overriding   → Child class redefines parent's method
  2. Duck Typing         → "If it walks like a duck, it's a duck"
  3. Operator Overloading → Operators (+, -, *, ==) behave differently per type
  4. Method Overloading  → Python handles this via default args / *args

ANALOGY:
  A remote control (interface) works with a TV, AC, or speaker.
  The "press power" action means different things to each device,
  but you use the same button.
"""

import math

# ─────────────────────────────────────────────
# 1. POLYMORPHISM VIA METHOD OVERRIDING
# ─────────────────────────────────────────────

class Shape:
    """Base class — defines a common interface."""

    def __init__(self, color: str = "white"):
        self.color = color

    def area(self) -> float:
        """Every shape must compute its own area."""
        raise NotImplementedError

    def perimeter(self) -> float:
        """Every shape must compute its own perimeter."""
        raise NotImplementedError

    def describe(self):
        """This method is POLYMORPHIC — calls area/perimeter differently per subclass."""
        print(
            f"{self.__class__.__name__:12} | Color: {self.color:8} | "
            f"Area: {self.area():8.2f} | Perimeter: {self.perimeter():.2f}"
        )


class Circle(Shape):
    def __init__(self, color: str, radius: float):
        super().__init__(color)
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2       # overrides Shape.area()

    def perimeter(self) -> float:
        return 2 * math.pi * self.radius        # overrides Shape.perimeter()


class Rectangle(Shape):
    def __init__(self, color: str, width: float, height: float):
        super().__init__(color)
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Triangle(Shape):
    def __init__(self, color: str, a: float, b: float, c: float):
        super().__init__(color)
        self.a, self.b, self.c = a, b, c

    def area(self) -> float:
        s = (self.a + self.b + self.c) / 2      # semi-perimeter (Heron's formula)
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))

    def perimeter(self) -> float:
        return self.a + self.b + self.c


class Square(Rectangle):
    """Square IS-A Rectangle with equal sides."""
    def __init__(self, color: str, side: float):
        super().__init__(color, side, side)


print("=" * 70)
print("POLYMORPHISM via METHOD OVERRIDING — Shapes")
print("=" * 70)

# All shapes go into the SAME list — treated uniformly via the Shape interface
shapes = [
    Circle("Red", 7),
    Rectangle("Blue", 4, 6),
    Triangle("Green", 3, 4, 5),
    Square("Purple", 5),
]

# The for loop doesn't care WHICH shape it is — polymorphism at work
for shape in shapes:
    shape.describe()          # calls the correct area() and perimeter() automatically

# Compute total area polymorphically
total_area = sum(shape.area() for shape in shapes)
print(f"\nTotal area of all shapes: {total_area:.2f}")


# ─────────────────────────────────────────────
# 2. DUCK TYPING
# ─────────────────────────────────────────────
# "If it walks like a duck and quacks like a duck, it's a duck."
# Python doesn't care about class hierarchy — only about whether the method exists.

class Dog:
    def __init__(self, name): self.name = name
    def speak(self): return f"{self.name} says: Woof!"

class Cat:
    def __init__(self, name): self.name = name
    def speak(self): return f"{self.name} says: Meow!"

class Robot:
    def __init__(self, name): self.name = name
    def speak(self): return f"{self.name} says: Beep boop."

class Person:
    def __init__(self, name): self.name = name
    def speak(self): return f"{self.name} says: Hello!"


def make_it_speak(entity):
    """
    This function doesn't care what TYPE entity is.
    It only requires that entity has a speak() method.
    → This is DUCK TYPING.
    """
    print(entity.speak())


print("\n" + "=" * 50)
print("DUCK TYPING")
print("=" * 50)

creatures = [Dog("Rex"), Cat("Luna"), Robot("R2D2"), Person("Alice")]

for creature in creatures:
    make_it_speak(creature)    # works for all — same interface, different behavior


# ─────────────────────────────────────────────
# 3. OPERATOR OVERLOADING (special __dunder__ methods)
# ─────────────────────────────────────────────
# Python operators call __dunder__ methods under the hood.
# Overloading them makes your objects work naturally with +, -, *, ==, <, etc.

class Vector:
    """
    2D Mathematical Vector.
    Demonstrates operator overloading for natural math syntax.
    """

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Vector({self.x}, {self.y})"

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def __add__(self, other: "Vector") -> "Vector":
        """v1 + v2"""
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vector") -> "Vector":
        """v1 - v2"""
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector":
        """v * scalar — scalar multiplication"""
        return Vector(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector":
        """scalar * v — right-hand scalar multiplication"""
        return self.__mul__(scalar)

    def __eq__(self, other: object) -> bool:
        """v1 == v2"""
        if not isinstance(other, Vector):
            return NotImplemented
        return self.x == other.x and self.y == other.y

    def __abs__(self) -> float:
        """abs(v) — magnitude of vector"""
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __neg__(self) -> "Vector":
        """-v — negation"""
        return Vector(-self.x, -self.y)

    def dot(self, other: "Vector") -> float:
        """Dot product: v1 · v2"""
        return self.x * other.x + self.y * other.y


print("\n" + "=" * 50)
print("OPERATOR OVERLOADING — Vectors")
print("=" * 50)

v1 = Vector(3, 4)
v2 = Vector(1, 2)

print(f"v1           = {v1}")
print(f"v2           = {v2}")
print(f"v1 + v2      = {v1 + v2}")         # calls __add__
print(f"v1 - v2      = {v1 - v2}")         # calls __sub__
print(f"v1 * 3       = {v1 * 3}")          # calls __mul__
print(f"2 * v1       = {2 * v1}")          # calls __rmul__
print(f"-v1          = {-v1}")             # calls __neg__
print(f"|v1|         = {abs(v1):.2f}")     # calls __abs__ (magnitude = 5)
print(f"v1 == v2     = {v1 == v2}")        # calls __eq__
print(f"v1 == Vector(3,4) = {v1 == Vector(3, 4)}")
print(f"v1 · v2      = {v1.dot(v2)}")      # dot product


# ─────────────────────────────────────────────
# 4. POLYMORPHISM WITH FUNCTIONS AND BUILT-INS
# ─────────────────────────────────────────────
# Python's built-in functions like len(), str(), repr() are polymorphic too.

class Stack:
    def __init__(self):
        self._items = []

    def push(self, item): self._items.append(item)
    def pop(self): return self._items.pop()

    def __len__(self):    return len(self._items)        # len(stack)
    def __str__(self):    return f"Stack{self._items}"   # str(stack)
    def __repr__(self):   return f"Stack({self._items!r})"
    def __bool__(self):   return len(self._items) > 0    # if stack:
    def __contains__(self, item): return item in self._items  # item in stack


print("\n" + "=" * 50)
print("POLYMORPHISM WITH BUILT-INS")
print("=" * 50)

s = Stack()
s.push(10)
s.push(20)
s.push(30)

print(f"Stack       : {s}")
print(f"len(stack)  : {len(s)}")           # calls __len__
print(f"bool(stack) : {bool(s)}")          # calls __bool__
print(f"20 in stack : {20 in s}")          # calls __contains__
print(f"99 in stack : {99 in s}")
print(f"Popped      : {s.pop()}")
print(f"After pop   : {s}")


# ─────────────────────────────────────────────
# 5. RUNTIME POLYMORPHISM — Strategy Pattern
# ─────────────────────────────────────────────
# Different behaviors plugged in at runtime via a common interface.

class SortStrategy:
    """Abstract strategy interface."""
    def sort(self, data: list) -> list:
        raise NotImplementedError

class BubbleSort(SortStrategy):
    def sort(self, data: list) -> list:
        arr = data[:]
        n = len(arr)
        for i in range(n):
            for j in range(n - i - 1):
                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
        return arr

class PythonSort(SortStrategy):
    def sort(self, data: list) -> list:
        return sorted(data)                      # uses Python's Timsort

class ReverseSort(SortStrategy):
    def sort(self, data: list) -> list:
        return sorted(data, reverse=True)


class Sorter:
    """Context class — uses whichever strategy is injected."""
    def __init__(self, strategy: SortStrategy):
        self._strategy = strategy

    def set_strategy(self, strategy: SortStrategy):
        self._strategy = strategy

    def sort(self, data: list) -> list:
        return self._strategy.sort(data)         # POLYMORPHIC call


print("\n" + "=" * 50)
print("RUNTIME POLYMORPHISM — Strategy Pattern")
print("=" * 50)

data = [5, 2, 9, 1, 7, 3]

sorter = Sorter(BubbleSort())
print(f"BubbleSort  : {sorter.sort(data)}")

sorter.set_strategy(PythonSort())
print(f"PythonSort  : {sorter.sort(data)}")

sorter.set_strategy(ReverseSort())
print(f"ReverseSort : {sorter.sort(data)}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
summary = """
  Method Overriding   → Child class provides its own implementation
  Duck Typing         → "Does it have the method?" — type doesn't matter
  Operator Overloading→ __add__, __eq__, __len__, __str__, etc.
  Runtime Polymorphism→ Swap strategies/behaviors at runtime

  Core Benefit:
    Write code that works with a general interface →
    works correctly for ANY conforming class (current or future).

    for shape in shapes:
        shape.area()   ← doesn't know OR care which shape it is
"""
print(summary)
