"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 1: Classes and Objects
=============================================================

WHAT IS OOP?
------------
Object-Oriented Programming (OOP) is a programming paradigm that organizes
code around "objects" — bundles of data and behavior — rather than just
functions and logic.

Core Pillars of OOP:
  1. Encapsulation  - Hiding internal details
  2. Inheritance    - Reusing code via parent-child classes
  3. Polymorphism   - One interface, many forms
  4. Abstraction    - Hiding complexity, showing essentials

-----------------------------------------
TOPIC 1: CLASSES AND OBJECTS
-----------------------------------------

CLASS:
  A class is a BLUEPRINT or TEMPLATE for creating objects.
  It defines what attributes (data) and methods (behavior) an object will have.

OBJECT:
  An object is an INSTANCE of a class — a real thing created from the blueprint.

ANALOGY:
  Class  → Blueprint of a car (design on paper)
  Object → An actual car built from that blueprint
"""

# ─────────────────────────────────────────────
# DEFINING A SIMPLE CLASS
# ─────────────────────────────────────────────

class Dog:
    """
    A simple class representing a Dog.

    Class Attributes:  Shared by ALL instances of the class.
    Instance Attributes: Unique to EACH object (defined inside __init__).
    """

    # Class attribute — shared by all Dog objects
    species = "Canis familiaris"

    # __init__ is the constructor — called automatically when an object is created
    # 'self' refers to the current instance being created
    def __init__(self, name: str, age: int, breed: str):
        """
        Constructor method.
        self.name, self.age, self.breed are INSTANCE attributes.
        Each Dog object gets its own copy of these.
        """
        self.name = name       # instance attribute
        self.age = age         # instance attribute
        self.breed = breed     # instance attribute

    # ── INSTANCE METHODS ──
    # Methods that operate on a specific instance (use 'self')

    def bark(self) -> str:
        """Returns a bark string for this dog."""
        return f"{self.name} says: Woof! Woof!"

    def describe(self) -> str:
        """Returns a description of the dog."""
        return (
            f"Name  : {self.name}\n"
            f"Age   : {self.age} year(s)\n"
            f"Breed : {self.breed}\n"
            f"Species: {Dog.species}"
        )

    def birthday(self):
        """Increments the dog's age by 1."""
        self.age += 1
        print(f"Happy Birthday, {self.name}! You are now {self.age} years old.")


# ─────────────────────────────────────────────
# CREATING OBJECTS (INSTANCES)
# ─────────────────────────────────────────────

# Each call to Dog() creates a NEW, independent object
dog1 = Dog(name="Buddy", age=3, breed="Golden Retriever")
dog2 = Dog(name="Luna",  age=5, breed="Labrador")
dog3 = Dog(name="Max",   age=1, breed="Poodle")


# ─────────────────────────────────────────────
# ACCESSING ATTRIBUTES AND METHODS
# ─────────────────────────────────────────────

print("=" * 50)
print("DOG DETAILS")
print("=" * 50)

print("\n--- Dog 1 ---")
print(dog1.describe())

print("\n--- Dog 2 ---")
print(dog2.describe())

print("\n--- Barking ---")
print(dog1.bark())
print(dog2.bark())

# Calling a method that modifies the object
print("\n--- Birthday ---")
dog3.birthday()
print(f"After birthday: {dog3.name} is {dog3.age} years old.")


# ─────────────────────────────────────────────
# CLASS ATTRIBUTE vs INSTANCE ATTRIBUTE
# ─────────────────────────────────────────────

print("\n--- Class Attribute (shared) ---")
print(f"dog1 species: {dog1.species}")   # Accessed via instance
print(f"dog2 species: {dog2.species}")   # Same value
print(f"Dog  species: {Dog.species}")    # Accessed via class directly

# Modifying an instance attribute doesn't affect other instances
dog1.name = "Buddy Jr."
print(f"\nAfter rename → dog1: {dog1.name}, dog2: {dog2.name}")


# ─────────────────────────────────────────────
# MULTIPLE OBJECTS ARE INDEPENDENT
# ─────────────────────────────────────────────

print("\n--- Object Identity ---")
print(f"Are dog1 and dog2 the same object? {dog1 is dog2}")  # False
print(f"dog1 id: {id(dog1)}")
print(f"dog2 id: {id(dog2)}")


# ─────────────────────────────────────────────
# DYNAMIC ATTRIBUTE ADDITION (Python-specific)
# ─────────────────────────────────────────────

# Python allows adding new attributes to an object at runtime
dog1.color = "Golden"
print(f"\nDynamically added attribute → dog1.color: {dog1.color}")
# dog2 does not have .color — this is specific to dog1 only


# ─────────────────────────────────────────────
# CHECKING TYPE AND INSTANCE
# ─────────────────────────────────────────────

print("\n--- Type Checking ---")
print(f"type(dog1)         : {type(dog1)}")
print(f"isinstance(dog1, Dog): {isinstance(dog1, Dog)}")
print(f"isinstance(dog1, str): {isinstance(dog1, str)}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
summary = """
  - class Dog:          → defines the blueprint
  - def __init__(self): → constructor, runs when object is created
  - self.name = name    → instance attribute (unique per object)
  - Dog.species         → class attribute (shared by all)
  - dog1 = Dog(...)     → creates an object (instance)
  - dog1.bark()         → calls a method on the object
"""
print(summary)
