"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 8: Properties (@property)
=============================================================

WHAT ARE PROPERTIES?
---------------------
@property lets you define GETTER, SETTER, and DELETER methods that are
accessed like regular ATTRIBUTES — clean syntax with hidden validation logic.

WHY USE PROPERTIES?
  - Access control: validate data before storing it
  - Computed values: compute on the fly instead of storing
  - Encapsulation without exposing raw attributes
  - Backward compatibility: convert a public attribute to controlled access
     without changing the external API

COMPARISON:
  Without property:
      obj.set_age(25)      → verbose, Java-style
      obj.get_age()

  With property:
      obj.age = 25         → looks like attribute access
      print(obj.age)       → but runs validation code behind the scenes
"""


# ─────────────────────────────────────────────
# 1. BASIC @property (read-only computed value)
# ─────────────────────────────────────────────

class Circle:
    """
    Circle stores only the radius.
    diameter and area are COMPUTED PROPERTIES — always up to date.
    """
    import math as _math

    def __init__(self, radius: float):
        self._radius = radius

    @property
    def radius(self) -> float:
        """Getter — read access to radius."""
        return self._radius

    @radius.setter
    def radius(self, value: float):
        """Setter — validates before storing."""
        if value < 0:
            raise ValueError("Radius cannot be negative.")
        self._radius = value

    @property
    def diameter(self) -> float:
        """Read-only computed property — no setter needed."""
        import math
        return self._radius * 2

    @property
    def area(self) -> float:
        """Computed property — recalculates every time."""
        import math
        return math.pi * self._radius ** 2

    @property
    def circumference(self) -> float:
        import math
        return 2 * math.pi * self._radius

    def __repr__(self) -> str:
        return f"Circle(radius={self._radius})"


print("=" * 55)
print("BASIC @property — Circle")
print("=" * 55)

c = Circle(5)
print(f"radius        : {c.radius}")           # getter
print(f"diameter      : {c.diameter}")         # computed property
print(f"area          : {c.area:.4f}")         # computed property
print(f"circumference : {c.circumference:.4f}")

c.radius = 10                                   # setter
print(f"\nAfter setting radius=10:")
print(f"radius        : {c.radius}")
print(f"area          : {c.area:.4f}")         # auto-updated!

try:
    c.radius = -5                               # triggers ValueError
except ValueError as e:
    print(f"\nValueError: {e}")

try:
    c.diameter = 20                             # read-only — no setter
except AttributeError as e:
    print(f"AttributeError: {e}")


# ─────────────────────────────────────────────
# 2. PROPERTY WITH GETTER, SETTER, DELETER
# ─────────────────────────────────────────────

class Person:
    """
    Person with validated name and age properties.
    Also demonstrates @property.deleter.
    """

    def __init__(self, name: str, age: int):
        # These call the SETTERS (not the raw assignment)
        self.name = name
        self.age  = age

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty.")
        if not all(ch.isalpha() or ch.isspace() for ch in value):
            raise ValueError("Name must contain only letters and spaces.")
        self._name = value.title()              # normalize to Title Case

    @name.deleter
    def name(self):
        """Deleter — called when `del obj.name` is used."""
        print(f"Deleting name of person (was: {self._name})")
        del self._name

    @property
    def age(self) -> int:
        return self._age

    @age.setter
    def age(self, value: int):
        if not isinstance(value, int):
            raise TypeError("Age must be an integer.")
        if not (0 <= value <= 150):
            raise ValueError(f"Age {value} is out of valid range (0–150).")
        self._age = value

    @property
    def is_adult(self) -> bool:
        """Computed/derived property — no setter."""
        return self._age >= 18

    @property
    def info(self) -> str:
        return f"{self.name} | Age: {self.age} | Adult: {self.is_adult}"


print("\n" + "=" * 55)
print("GETTER / SETTER / DELETER — Person")
print("=" * 55)

p = Person("alice smith", 25)
print(f"info    : {p.info}")               # name normalized to 'Alice Smith'

p.name = "  bob jones  "                   # strips and title-cases
p.age  = 17
print(f"Updated : {p.info}")

try:
    p.age = 200
except ValueError as e:
    print(f"ValueError: {e}")

try:
    p.name = "J4n3 D0e"
except ValueError as e:
    print(f"ValueError: {e}")

del p.name                                 # calls the deleter


# ─────────────────────────────────────────────
# 3. CACHING WITH PROPERTIES
# ─────────────────────────────────────────────

class DataProcessor:
    """
    Expensive computation cached in a property.
    Cache is invalidated when the underlying data changes.
    """

    def __init__(self, data: list):
        self._data = data
        self._sorted_cache = None        # cache invalidation flag
        self._stats_cache = None

    @property
    def data(self) -> list:
        return list(self._data)          # return a copy to prevent external mutation

    @data.setter
    def data(self, values: list):
        if not isinstance(values, list):
            raise TypeError("data must be a list.")
        self._data = values
        self._sorted_cache = None        # invalidate cache on data change
        self._stats_cache = None

    @property
    def sorted_data(self) -> list:
        """Lazy-computed and cached — only sorts once."""
        if self._sorted_cache is None:
            print("  [Computing sorted_data...]")
            self._sorted_cache = sorted(self._data)
        return self._sorted_cache

    @property
    def stats(self) -> dict:
        """Compute statistics once; recompute only when data changes."""
        if self._stats_cache is None:
            print("  [Computing stats...]")
            n = len(self._data)
            mean = sum(self._data) / n if n else 0
            self._stats_cache = {
                "count": n,
                "min"  : min(self._data) if n else None,
                "max"  : max(self._data) if n else None,
                "mean" : round(mean, 2),
                "sum"  : sum(self._data),
            }
        return dict(self._stats_cache)   # return a copy


print("\n" + "=" * 55)
print("CACHING WITH PROPERTIES")
print("=" * 55)

dp = DataProcessor([5, 3, 8, 1, 9, 2, 7])

print("First access (computes):")
print(f"  sorted: {dp.sorted_data}")
print(f"  stats : {dp.stats}")

print("\nSecond access (cached — no recompute message):")
print(f"  sorted: {dp.sorted_data}")
print(f"  stats : {dp.stats}")

print("\nChange data (invalidates cache):")
dp.data = [100, 50, 75]
print(f"  sorted: {dp.sorted_data}")     # recomputes
print(f"  stats : {dp.stats}")           # recomputes


# ─────────────────────────────────────────────
# 4. PROPERTY FOR UNIT CONVERSION
# ─────────────────────────────────────────────

class Rectangle:
    """
    Rectangle with properties for area and aspect ratio.
    Setting area scales width proportionally.
    """

    def __init__(self, width: float, height: float):
        self.width  = width
        self.height = height

    @property
    def width(self) -> float:
        return self._width

    @width.setter
    def width(self, value: float):
        if value <= 0:
            raise ValueError("Width must be positive.")
        self._width = value

    @property
    def height(self) -> float:
        return self._height

    @height.setter
    def height(self, value: float):
        if value <= 0:
            raise ValueError("Height must be positive.")
        self._height = value

    @property
    def area(self) -> float:
        return self._width * self._height

    @area.setter
    def area(self, target_area: float):
        """Scale width to achieve target area, keeping height constant."""
        if target_area <= 0:
            raise ValueError("Area must be positive.")
        self._width = target_area / self._height

    @property
    def perimeter(self) -> float:
        return 2 * (self._width + self._height)

    @property
    def aspect_ratio(self) -> float:
        return self._width / self._height

    def __repr__(self) -> str:
        return f"Rectangle(width={self._width:.2f}, height={self._height:.2f})"


print("\n" + "=" * 55)
print("PROPERTIES FOR DERIVED ATTRIBUTES — Rectangle")
print("=" * 55)

r = Rectangle(8, 4)
print(f"Rectangle  : {r}")
print(f"Area       : {r.area}")
print(f"Perimeter  : {r.perimeter}")
print(f"Aspect     : {r.aspect_ratio:.2f}")

r.area = 64                                # setter scales width
print(f"\nAfter area=64: {r}")


# ─────────────────────────────────────────────
# 5. PROPERTY IN INHERITANCE
# ─────────────────────────────────────────────

class Animal:
    def __init__(self, name: str):
        self._name = None
        self.name = name                   # triggers setter

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value:
            raise ValueError("Name cannot be empty.")
        self._name = value.strip()

    @property
    def sound(self) -> str:
        return "(unknown sound)"


class Dog(Animal):
    @property
    def sound(self) -> str:                # override the property
        return "Woof!"


class Cat(Animal):
    @property
    def sound(self) -> str:
        return "Meow!"


print("\n" + "=" * 55)
print("PROPERTIES IN INHERITANCE")
print("=" * 55)

animals = [Dog("Buddy"), Cat("Whiskers"), Animal("Unknown")]
for a in animals:
    print(f"{a.name:12} → {a.sound}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  @property              → getter (read access)
  @attr.setter           → setter (write access with validation)
  @attr.deleter          → deleter (del obj.attr)

  USAGE:
    class MyClass:
        @property
        def value(self): return self._value

        @value.setter
        def value(self, v):
            if v < 0: raise ValueError(...)
            self._value = v

  obj.value = 10   → calls setter
  x = obj.value    → calls getter
  del obj.value    → calls deleter

  KEY BENEFITS:
    ✔ Clean attribute-like syntax (no get_x() / set_x())
    ✔ Validated writes — impossible to set invalid state
    ✔ Computed attributes always in sync
    ✔ Cache expensive computations, invalidate on change
    ✔ Backward compatible — change internal details freely
"""
print(summary)
