"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 5: Abstraction
=============================================================

WHAT IS ABSTRACTION?
---------------------
Abstraction means HIDING COMPLEXITY and showing only the ESSENTIAL information
to the user. You expose WHAT something does, not HOW it does it.

EXAMPLES IN REAL LIFE:
  - Driving a car: you use a steering wheel, pedals — you don't see the engine.
  - ATM machine: press buttons to withdraw cash — you don't see the banking logic.
  - Python's list.sort(): you call it — you don't see Timsort's implementation.

IN OOP:
  - Abstract classes define a CONTRACT: "Every subclass MUST implement these methods."
  - This enforces a consistent interface across all subclasses.

Python's ABC (Abstract Base Class) module:
  - ABC          → Inherit from this to make a class abstract
  - @abstractmethod → Mark a method that MUST be overridden in subclasses
"""

from abc import ABC, abstractmethod
import math


# ─────────────────────────────────────────────
# 1. ABSTRACT CLASS — The Contract
# ─────────────────────────────────────────────

class Shape(ABC):
    """
    Abstract Base Class for all shapes.

    Rules:
      - Cannot instantiate Shape directly → Shape() raises TypeError
      - Any subclass MUST implement: area(), perimeter(), describe()
      - Subclasses MAY use the concrete draw() method as-is
    """

    def __init__(self, color: str):
        self.color = color

    # ── ABSTRACT METHODS ── must be implemented by every subclass
    @abstractmethod
    def area(self) -> float:
        """Return the area of the shape."""
        ...

    @abstractmethod
    def perimeter(self) -> float:
        """Return the perimeter of the shape."""
        ...

    # ── CONCRETE METHOD ── available to all subclasses, no override required
    def describe(self):
        """Print a summary using abstract methods — works for ANY subclass."""
        print(
            f"{self.__class__.__name__:12} | color={self.color:8} | "
            f"area={self.area():.2f} | perimeter={self.perimeter():.2f}"
        )

    def draw(self):
        """Simulates drawing — concrete shared behavior."""
        print(f"Drawing a {self.color} {self.__class__.__name__}...")


# ─────────────────────────────────────────────
# DEMONSTRATE: Cannot instantiate abstract class
# ─────────────────────────────────────────────

print("=" * 60)
print("ATTEMPTING TO INSTANTIATE ABSTRACT CLASS")
print("=" * 60)

try:
    shape = Shape("red")           # This should raise TypeError
except TypeError as e:
    print(f"TypeError: {e}")
    print("→ Correct! You cannot instantiate an abstract class.\n")


# ─────────────────────────────────────────────
# 2. CONCRETE SUBCLASSES — Fulfill the Contract
# ─────────────────────────────────────────────

class Circle(Shape):
    def __init__(self, color: str, radius: float):
        super().__init__(color)
        self.radius = radius

    def area(self) -> float:                        # implements @abstractmethod
        return math.pi * self.radius ** 2

    def perimeter(self) -> float:                   # implements @abstractmethod
        return 2 * math.pi * self.radius


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
        s = (self.a + self.b + self.c) / 2
        return math.sqrt(s * (s - self.a) * (s - self.b) * (s - self.c))

    def perimeter(self) -> float:
        return self.a + self.b + self.c


print("=" * 60)
print("CONCRETE SUBCLASSES — All implement abstract methods")
print("=" * 60)

shapes = [
    Circle("Red", 5),
    Rectangle("Blue", 4, 6),
    Triangle("Green", 3, 4, 5),
]

for shape in shapes:
    shape.describe()
    shape.draw()
    print()


# ─────────────────────────────────────────────
# 3. ABSTRACT PROPERTIES
# ─────────────────────────────────────────────

class Vehicle(ABC):
    """
    Abstract Vehicle.
    Enforces that all vehicles must expose fuel_type and max_speed as properties.
    """

    def __init__(self, make: str, model: str, year: int):
        self.make  = make
        self.model = model
        self.year  = year

    @property
    @abstractmethod
    def fuel_type(self) -> str:
        """Must return the type of fuel this vehicle uses."""
        ...

    @property
    @abstractmethod
    def max_speed(self) -> float:
        """Must return top speed in km/h."""
        ...

    @abstractmethod
    def start_engine(self):
        """Must implement how this vehicle starts."""
        ...

    def info(self):
        """Concrete method that calls abstract properties."""
        print(
            f"{self.year} {self.make} {self.model} | "
            f"Fuel: {self.fuel_type} | Max Speed: {self.max_speed} km/h"
        )


class Car(Vehicle):
    @property
    def fuel_type(self) -> str:
        return "Gasoline"

    @property
    def max_speed(self) -> float:
        return 220.0

    def start_engine(self):
        print(f"{self.make} {self.model}: Vroom! Engine started.")


class ElectricCar(Vehicle):
    def __init__(self, make: str, model: str, year: int, battery_kwh: float):
        super().__init__(make, model, year)
        self.battery_kwh = battery_kwh

    @property
    def fuel_type(self) -> str:
        return "Electric"

    @property
    def max_speed(self) -> float:
        return 250.0

    def start_engine(self):
        print(f"{self.make} {self.model}: Silently started on electric power.")


class Bicycle(Vehicle):
    @property
    def fuel_type(self) -> str:
        return "Human-powered"

    @property
    def max_speed(self) -> float:
        return 30.0

    def start_engine(self):
        print(f"{self.make} {self.model}: No engine — start pedaling!")


print("=" * 60)
print("ABSTRACT PROPERTIES — Vehicles")
print("=" * 60)

vehicles = [
    Car("Toyota", "Camry", 2022),
    ElectricCar("Tesla", "Model S", 2023, 100),
    Bicycle("Trek", "FX3", 2021),
]

for v in vehicles:
    v.info()
    v.start_engine()
    print()


# ─────────────────────────────────────────────
# 4. ABSTRACT CLASS WITH PARTIAL IMPLEMENTATION
# ─────────────────────────────────────────────
# Abstract classes CAN have implemented methods — subclasses inherit them.

class Logger(ABC):
    """
    Abstract Logger. Concrete log_info, log_error.
    Abstract log_warning (must be overridden).
    """

    def log_info(self, message: str):
        print(f"[INFO]  {message}")

    def log_error(self, message: str):
        print(f"[ERROR] {message}")

    @abstractmethod
    def log_warning(self, message: str):
        """Subclasses decide how warnings are presented."""
        ...

    @abstractmethod
    def save(self, filename: str):
        """Subclasses decide where to save logs."""
        ...


class ConsoleLogger(Logger):
    def log_warning(self, message: str):
        print(f"\033[93m[WARN]  {message}\033[0m")   # Yellow text in terminal

    def save(self, filename: str):
        print(f"Console logs don't persist to '{filename}'.")


class FileLogger(Logger):
    def __init__(self):
        self._buffer = []

    def log_warning(self, message: str):
        entry = f"[WARN]  {message}"
        self._buffer.append(entry)
        print(entry)

    def log_info(self, message: str):
        super().log_info(message)                    # extends parent
        self._buffer.append(f"[INFO]  {message}")

    def save(self, filename: str):
        print(f"Saving {len(self._buffer)} log entries to '{filename}'.")


print("=" * 60)
print("ABSTRACT CLASS WITH PARTIAL IMPLEMENTATION — Logger")
print("=" * 60)

print("\n--- Console Logger ---")
cl = ConsoleLogger()
cl.log_info("System started.")
cl.log_warning("Low disk space.")
cl.log_error("Connection failed.")
cl.save("app.log")

print("\n--- File Logger ---")
fl = FileLogger()
fl.log_info("App initialized.")
fl.log_warning("Memory usage high.")
fl.log_error("Unhandled exception.")
fl.save("production.log")


# ─────────────────────────────────────────────
# 5. CHECKING ABSTRACT CLASS MEMBERSHIP
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("INSTANCE AND SUBCLASS CHECKS")
print("=" * 60)

car = Car("Honda", "Civic", 2020)
print(f"isinstance(car, Vehicle) : {isinstance(car, Vehicle)}")   # True
print(f"isinstance(car, ABC)     : {isinstance(car, ABC)}")       # True (ABC in hierarchy)
print(f"issubclass(Car, Vehicle) : {issubclass(Car, Vehicle)}")   # True

# List of abstract methods not yet implemented
print(f"\nAbstract methods remaining in Vehicle: {Vehicle.__abstractmethods__}")
print(f"Abstract methods remaining in Car    : {Car.__abstractmethods__}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
summary = """
  from abc import ABC, abstractmethod

  class MyABC(ABC):            → Abstract Base Class (cannot instantiate)
      @abstractmethod
      def my_method(self): ... → MUST be overridden in ALL subclasses

  class Concrete(MyABC):
      def my_method(self):     → Fulfills the contract
          return "done"

  Key Benefits:
    ✔ Enforces a consistent interface across all subclasses
    ✔ Makes code self-documenting ("this class must do X, Y, Z")
    ✔ Prevents accidental instantiation of incomplete base classes
    ✔ Enables writing code against an interface, not a specific class
"""
print(summary)
