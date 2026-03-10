"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 3: Inheritance
=============================================================

WHAT IS INHERITANCE?
---------------------
Inheritance allows a class (child/subclass) to ACQUIRE the attributes and
methods of another class (parent/superclass), enabling code reuse and
establishing an "IS-A" relationship.

  Dog IS-A Animal     → Dog inherits from Animal
  Car IS-A Vehicle    → Car inherits from Vehicle
  Manager IS-A Employee → Manager inherits from Employee

KEY TERMS:
  Parent / Base / Superclass  → the class being inherited FROM
  Child  / Derived / Subclass → the class that inherits

TYPES OF INHERITANCE:
  1. Single       → One parent
  2. Multi-level  → Chain: A → B → C
  3. Multiple     → Two or more parents
  4. Hierarchical → One parent, many children
"""

# ─────────────────────────────────────────────
# BASE CLASS (Parent)
# ─────────────────────────────────────────────

class Animal:
    """
    Base class representing a generic Animal.
    All animals have a name, age, and can eat/sleep.
    """

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def eat(self):
        print(f"{self.name} is eating.")

    def sleep(self):
        print(f"{self.name} is sleeping.")

    def describe(self):
        print(f"Animal: {self.name}, Age: {self.age}")

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, age={self.age})"


# ─────────────────────────────────────────────
# 1. SINGLE INHERITANCE
# ─────────────────────────────────────────────

class Dog(Animal):
    """
    Dog IS-A Animal.
    Inherits name, age, eat(), sleep(), describe() from Animal.
    Adds its own breed attribute and bark() method.
    Overrides describe().
    """

    def __init__(self, name: str, age: int, breed: str):
        # super().__init__() calls the parent's __init__
        # This ensures name and age are properly initialized
        super().__init__(name, age)
        self.breed = breed          # Dog-specific attribute

    def bark(self):
        """Dog-specific behavior."""
        print(f"{self.name} says: Woof!")

    def describe(self):
        """
        METHOD OVERRIDING — replacing the parent's describe() with a custom version.
        We call super().describe() to reuse the parent logic and extend it.
        """
        super().describe()          # runs Animal.describe()
        print(f"Breed: {self.breed}")


class Cat(Animal):
    """
    Cat IS-A Animal.
    Adds color attribute and meow() method.
    """

    def __init__(self, name: str, age: int, color: str):
        super().__init__(name, age)
        self.color = color

    def meow(self):
        print(f"{self.name} says: Meow!")

    def purr(self):
        print(f"{self.name} is purring...")


print("=" * 50)
print("SINGLE INHERITANCE")
print("=" * 50)

dog = Dog("Buddy", 3, "Golden Retriever")
cat = Cat("Whiskers", 4, "Orange")

dog.describe()          # Dog's overridden method
dog.eat()               # Inherited from Animal
dog.bark()              # Dog's own method

print()
cat.describe()          # Animal's method (Cat didn't override it)
cat.eat()               # Inherited
cat.meow()              # Cat's own method

# isinstance checks
print(f"\nisinstance(dog, Dog)   : {isinstance(dog, Dog)}")
print(f"isinstance(dog, Animal): {isinstance(dog, Animal)}")  # True! Dog IS-A Animal
print(f"issubclass(Dog, Animal): {issubclass(Dog, Animal)}")


# ─────────────────────────────────────────────
# 2. MULTI-LEVEL INHERITANCE
# ─────────────────────────────────────────────
# Chain: Animal → Mammal → Dog → GuideDog

class Mammal(Animal):
    """Mammal IS-A Animal. Adds warm-blooded behavior."""

    def __init__(self, name: str, age: int, fur_color: str):
        super().__init__(name, age)
        self.fur_color = fur_color

    def nurse_young(self):
        print(f"{self.name} is nursing its young.")

    def regulate_temperature(self):
        print(f"{self.name} is warm-blooded and regulates its own temperature.")


class DomesticDog(Mammal):
    """DomesticDog IS-A Mammal IS-A Animal."""

    def __init__(self, name: str, age: int, fur_color: str, breed: str):
        super().__init__(name, age, fur_color)
        self.breed = breed

    def fetch(self, item: str):
        print(f"{self.name} fetches the {item}!")


class GuideDog(DomesticDog):
    """GuideDog IS-A DomesticDog IS-A Mammal IS-A Animal."""

    def __init__(self, name: str, age: int, breed: str, owner: str):
        super().__init__(name, age, "Yellow", breed)   # guide dogs are typically yellow labs
        self.owner = owner
        self.is_certified = False

    def certify(self):
        self.is_certified = True
        print(f"{self.name} is now a certified guide dog for {self.owner}!")

    def guide(self):
        if self.is_certified:
            print(f"{self.name} is guiding {self.owner} safely.")
        else:
            print(f"{self.name} is still in training.")


print("\n" + "=" * 50)
print("MULTI-LEVEL INHERITANCE")
print("=" * 50)

guide = GuideDog("Rex", 5, "Labrador", "David")
guide.eat()               # from Animal
guide.nurse_young()       # from Mammal
guide.fetch("ball")       # from DomesticDog
guide.guide()             # GuideDog method
guide.certify()
guide.guide()

# Method Resolution Order (MRO) — Python's lookup order
print(f"\nMRO for GuideDog:")
for cls in GuideDog.__mro__:
    print(f"  {cls}")


# ─────────────────────────────────────────────
# 3. MULTIPLE INHERITANCE
# ─────────────────────────────────────────────
# One class inherits from TWO or more parent classes.
# Python uses C3 Linearization (MRO) to resolve method conflicts.

class Swimmer:
    """Mixin: Adds swimming ability."""
    def swim(self):
        print(f"{self.name} is swimming.")

class Runner:
    """Mixin: Adds running ability."""
    def run(self):
        print(f"{self.name} is running.")

    def speed(self):
        return "fast"

class Flyer:
    """Mixin: Adds flying ability."""
    def fly(self):
        print(f"{self.name} is flying.")

    def speed(self):
        return "very fast"


class Duck(Animal, Swimmer, Runner, Flyer):
    """
    Duck IS-A Animal AND can Swim AND Run AND Fly.
    This is multiple inheritance.
    """

    def __init__(self, name: str, age: int):
        super().__init__(name, age)     # calls Animal.__init__ via MRO

    def quack(self):
        print(f"{self.name} says: Quack!")


print("\n" + "=" * 50)
print("MULTIPLE INHERITANCE")
print("=" * 50)

duck = Duck("Donald", 3)
duck.eat()        # from Animal
duck.swim()       # from Swimmer
duck.run()        # from Runner
duck.fly()        # from Flyer
duck.quack()      # Duck's own

# MRO determines which speed() is called first
print(f"\nduck.speed(): '{duck.speed()}'  ← from Runner (first in MRO after Animal)")
print(f"\nMRO for Duck:")
for cls in Duck.__mro__:
    print(f"  {cls}")


# ─────────────────────────────────────────────
# 4. HIERARCHICAL INHERITANCE
# ─────────────────────────────────────────────
# ONE parent, MANY children

class Shape:
    """Base shape class."""
    def __init__(self, color: str):
        self.color = color

    def area(self) -> float:
        raise NotImplementedError("Subclasses must implement area()")

    def describe(self):
        print(f"{self.__class__.__name__} | Color: {self.color} | Area: {self.area():.2f}")


class Circle(Shape):
    import math
    def __init__(self, color: str, radius: float):
        super().__init__(color)
        self.radius = radius

    def area(self) -> float:
        import math
        return math.pi * self.radius ** 2


class Rectangle(Shape):
    def __init__(self, color: str, width: float, height: float):
        super().__init__(color)
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height


class Triangle(Shape):
    def __init__(self, color: str, base: float, height: float):
        super().__init__(color)
        self.base = base
        self.height = height

    def area(self) -> float:
        return 0.5 * self.base * self.height


print("\n" + "=" * 50)
print("HIERARCHICAL INHERITANCE — Shapes")
print("=" * 50)

shapes = [
    Circle("Red", 5),
    Rectangle("Blue", 4, 6),
    Triangle("Green", 3, 8),
]

for shape in shapes:
    shape.describe()


# ─────────────────────────────────────────────
# CALLING PARENT METHODS WITH super()
# ─────────────────────────────────────────────

print("\n--- super() demonstration ---")

class Vehicle:
    def __init__(self, make: str, model: str):
        self.make = make
        self.model = model

    def start(self):
        print(f"{self.make} {self.model} engine started.")

class ElectricVehicle(Vehicle):
    def __init__(self, make: str, model: str, battery_kwh: float):
        super().__init__(make, model)         # ← calls Vehicle.__init__
        self.battery_kwh = battery_kwh

    def start(self):
        super().start()                        # ← calls Vehicle.start()
        print(f"Battery: {self.battery_kwh} kWh. Running silently on electric power.")


ev = ElectricVehicle("Tesla", "Model 3", 75)
ev.start()


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
summary = """
  Single       → class Dog(Animal)
  Multi-level  → class GuideDog(DomesticDog(Mammal(Animal)))
  Multiple     → class Duck(Animal, Swimmer, Runner, Flyer)
  Hierarchical → class Circle(Shape), Rectangle(Shape), Triangle(Shape)

  Key Concepts:
    super()            → Call parent class method
    Method Overriding  → Child redefines parent's method
    isinstance()       → Check if object is instance of a class/parent
    issubclass()       → Check class hierarchy
    __mro__            → Method Resolution Order (lookup chain)
"""
print(summary)
