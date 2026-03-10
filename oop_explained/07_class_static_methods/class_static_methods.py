"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 7: Class Methods & Static Methods
=============================================================

THREE KINDS OF METHODS:
-----------------------
  1. Instance Method  → def method(self, ...)
       - Has access to: self (instance), class via self.__class__
       - Use when: behavior depends on instance state

  2. Class Method     → @classmethod + def method(cls, ...)
       - Has access to: cls (the class itself), NOT instance
       - Use when: alternative constructors, factory methods,
                   or behavior that applies to the class as a whole

  3. Static Method    → @staticmethod + def method(...)
       - Has access to: NOTHING (no self, no cls)
       - Essentially a plain function grouped inside a class for organization
       - Use when: utility/helper logic related to the class but not to any instance
"""


# ─────────────────────────────────────────────
# EXAMPLE: Temperature Converter
# ─────────────────────────────────────────────

class Temperature:
    """
    Represents temperature in Celsius.
    Demonstrates all three method types.
    """

    # Class attribute — shared across ALL instances
    ABSOLUTE_ZERO_C = -273.15

    def __init__(self, celsius: float):
        if celsius < self.ABSOLUTE_ZERO_C:
            raise ValueError(f"Temperature below absolute zero ({self.ABSOLUTE_ZERO_C}°C)")
        self._celsius = celsius

    # ── INSTANCE METHOD ─────────────────────────────
    def to_fahrenheit(self) -> float:
        """Converts this instance's temperature to Fahrenheit."""
        return self._celsius * 9 / 5 + 32

    def to_kelvin(self) -> float:
        """Converts to Kelvin."""
        return self._celsius - self.ABSOLUTE_ZERO_C

    def __repr__(self) -> str:
        return f"Temperature({self._celsius}°C)"

    def __str__(self) -> str:
        return (
            f"{self._celsius:.2f}°C = "
            f"{self.to_fahrenheit():.2f}°F = "
            f"{self.to_kelvin():.2f}K"
        )

    # ── CLASS METHODS (Alternative Constructors) ──────
    # @classmethod receives `cls` — the class itself.
    # Useful for creating objects from different input formats.

    @classmethod
    def from_fahrenheit(cls, fahrenheit: float) -> "Temperature":
        """
        Factory / alternative constructor.
        Creates a Temperature from a Fahrenheit value.
        Use: temp = Temperature.from_fahrenheit(98.6)
        """
        celsius = (fahrenheit - 32) * 5 / 9
        return cls(celsius)      # cls() → Temperature() — works with subclasses too!

    @classmethod
    def from_kelvin(cls, kelvin: float) -> "Temperature":
        """Creates a Temperature from a Kelvin value."""
        celsius = kelvin + cls.ABSOLUTE_ZERO_C
        return cls(celsius)

    @classmethod
    def absolute_zero(cls) -> "Temperature":
        """Returns a Temperature representing absolute zero."""
        return cls(cls.ABSOLUTE_ZERO_C)

    # ── STATIC METHODS (Utility / Pure Functions) ──────
    # @staticmethod receives no self or cls.
    # It's a regular function that "lives" in the class namespace for organization.

    @staticmethod
    def celsius_to_fahrenheit(c: float) -> float:
        """Pure conversion utility — no instance needed."""
        return c * 9 / 5 + 32

    @staticmethod
    def fahrenheit_to_celsius(f: float) -> float:
        return (f - 32) * 5 / 9

    @staticmethod
    def is_valid_celsius(c: float) -> bool:
        """Validate a Celsius value without creating an object."""
        return c >= -273.15


# ─────────────────────────────────────────────
# USING INSTANCE METHODS
# ─────────────────────────────────────────────

print("=" * 55)
print("INSTANCE METHODS")
print("=" * 55)

t1 = Temperature(100)
t2 = Temperature(37)

print(f"Boiling : {t1}")
print(f"Body    : {t2}")
print(f"Boiling in Fahrenheit: {t1.to_fahrenheit():.2f}°F")
print(f"Body in Kelvin       : {t2.to_kelvin():.2f}K")


# ─────────────────────────────────────────────
# USING CLASS METHODS (Alternative Constructors)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CLASS METHODS (Alternative Constructors)")
print("=" * 55)

body_temp   = Temperature.from_fahrenheit(98.6)
boiling     = Temperature.from_kelvin(373.15)
abs_zero    = Temperature.absolute_zero()

print(f"Body (from F): {body_temp}")
print(f"Boiling (from K): {boiling}")
print(f"Absolute zero   : {abs_zero}")


# ─────────────────────────────────────────────
# USING STATIC METHODS (Utilities)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("STATIC METHODS (Utility Functions)")
print("=" * 55)

# Call directly on the class — no instance needed
print(f"100°C in Fahrenheit  : {Temperature.celsius_to_fahrenheit(100)}°F")
print(f"32°F in Celsius      : {Temperature.fahrenheit_to_celsius(32)}°C")
print(f"Is -300°C valid?     : {Temperature.is_valid_celsius(-300)}")
print(f"Is -200°C valid?     : {Temperature.is_valid_celsius(-200)}")

# Can also call on an instance (works, but not idiomatic)
print(f"Via instance (works) : {t1.celsius_to_fahrenheit(0)}°F")


# ─────────────────────────────────────────────
# CLASS METHODS WITH INHERITANCE
# ─────────────────────────────────────────────
# @classmethod uses `cls`, so it creates the CORRECT subclass instance.
# This is a key advantage over using __init__ directly.

class BodyTemperature(Temperature):
    """Subclass that only accepts human body temperature range (35–42°C)."""

    NORMAL   = 37.0
    FEVER    = 38.0

    def __init__(self, celsius: float):
        if not (35 <= celsius <= 42):
            raise ValueError(f"Body temperature {celsius}°C is out of range (35–42°C).")
        super().__init__(celsius)

    def status(self) -> str:
        if self._celsius >= self.FEVER:
            return "Fever"
        elif self._celsius >= self.NORMAL - 0.5:
            return "Normal"
        else:
            return "Hypothermia"


print("\n" + "=" * 55)
print("CLASSMETHOD WITH INHERITANCE")
print("=" * 55)

# from_fahrenheit uses `cls` → creates BodyTemperature, not Temperature
bt = BodyTemperature.from_fahrenheit(99.5)
print(f"Type  : {type(bt).__name__}")      # BodyTemperature, not Temperature!
print(f"Temp  : {bt}")
print(f"Status: {bt.status()}")


# ─────────────────────────────────────────────
# EXAMPLE 2: Counter (Class Method Tracking State)
# ─────────────────────────────────────────────

class Counter:
    """
    Each instance increments a shared class-level count.
    @classmethod accesses and modifies this shared state.
    """

    _count = 0          # class attribute
    _instances = []     # class attribute — tracks all instances

    def __init__(self, label: str):
        Counter._count += 1
        self.id = Counter._count
        self.label = label
        Counter._instances.append(self)

    @classmethod
    def get_count(cls) -> int:
        """Returns total number of Counter instances created."""
        return cls._count

    @classmethod
    def get_all(cls) -> list:
        """Returns all Counter instances."""
        return list(cls._instances)

    @classmethod
    def reset(cls):
        """Resets the counter (useful in testing)."""
        cls._count = 0
        cls._instances.clear()

    @staticmethod
    def describe_purpose() -> str:
        """Static — no instance or class needed, just info about the class."""
        return "Counter instances track creation order and total count."

    def __repr__(self) -> str:
        return f"Counter(id={self.id}, label={self.label!r})"


print("\n" + "=" * 55)
print("CLASSMETHOD TRACKING STATE — Counter")
print("=" * 55)

c1 = Counter("alpha")
c2 = Counter("beta")
c3 = Counter("gamma")

print(f"Total counters   : {Counter.get_count()}")
print(f"All instances    : {Counter.get_all()}")
print(f"Purpose (static) : {Counter.describe_purpose()}")

Counter.reset()
print(f"After reset      : {Counter.get_count()}")


# ─────────────────────────────────────────────
# EXAMPLE 3: Date class (classic @classmethod use case)
# ─────────────────────────────────────────────

class Date:
    """Custom Date class with multiple constructor forms."""

    def __init__(self, year: int, month: int, day: int):
        self.year  = year
        self.month = month
        self.day   = day

    @classmethod
    def from_string(cls, date_string: str) -> "Date":
        """Parse 'YYYY-MM-DD' string."""
        year, month, day = map(int, date_string.split("-"))
        return cls(year, month, day)

    @classmethod
    def today(cls) -> "Date":
        """Create a Date for today using platform date."""
        import datetime
        d = datetime.date.today()
        return cls(d.year, d.month, d.day)

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Check if a year is a leap year — pure utility, no instance needed."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    @staticmethod
    def days_in_month(month: int, year: int) -> int:
        """Return days in a given month (accounts for leap year)."""
        days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if month == 2 and Date.is_leap_year(year):
            return 29
        return days[month]

    def __str__(self) -> str:
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"

    def __repr__(self) -> str:
        return f"Date({self.year}, {self.month}, {self.day})"


print("\n" + "=" * 55)
print("CLASSMETHOD FACTORY — Date")
print("=" * 55)

d1 = Date(2024, 3, 15)
d2 = Date.from_string("2025-12-25")        # classmethod factory
d3 = Date.today()                           # classmethod factory

print(f"Date from constructor : {d1}")
print(f"Date from string      : {d2}")
print(f"Today                 : {d3}")

print(f"\nIs 2024 a leap year?  : {Date.is_leap_year(2024)}")
print(f"Is 2023 a leap year?  : {Date.is_leap_year(2023)}")
print(f"Days in Feb 2024      : {Date.days_in_month(2, 2024)}")
print(f"Days in Feb 2023      : {Date.days_in_month(2, 2023)}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  METHOD TYPE       DECORATOR       FIRST ARG   ACCESS
  ─────────────────────────────────────────────────────
  Instance method   (none)          self        instance + class
  Class method      @classmethod    cls         class only (not instance)
  Static method     @staticmethod   (none)      neither

  WHEN TO USE:
    Instance method  → logic depends on object state (self.attr)
    Class method     → alternative constructors, factory methods,
                       class-level state management
    Static method    → pure utility functions related to the class
                       (validation, conversion, helper math)

  KEY: @classmethod with `cls` works correctly with inheritance —
       creates the subclass instance, not the base class.
"""
print(summary)
