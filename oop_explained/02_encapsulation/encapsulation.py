"""
=============================================================
OBJECT-ORIENTED PROGRAMMING IN PYTHON
Topic 2: Encapsulation
=============================================================

WHAT IS ENCAPSULATION?
-----------------------
Encapsulation is the practice of BUNDLING data (attributes) and the methods
that operate on that data into a single unit (class), and RESTRICTING direct
access to some of that data to prevent accidental misuse.

Think of it like a CAPSULE (medicine pill):
  - The active ingredients (data) are sealed inside.
  - You interact with it through a defined interface (swallow the pill).
  - You don't directly touch or mix the ingredients yourself.

ACCESS LEVELS IN PYTHON:
  public    → self.name       (anyone can access)
  protected → self._name      (convention: "internal use", not enforced)
  private   → self.__name     (name-mangled, harder to access from outside)
"""

# ─────────────────────────────────────────────
# 1. PUBLIC ATTRIBUTES (default)
# ─────────────────────────────────────────────

class PublicExample:
    """All attributes are publicly accessible."""

    def __init__(self, value: int):
        self.value = value          # public: accessible everywhere

    def show(self):
        print(f"Value: {self.value}")


pub = PublicExample(42)
pub.show()
pub.value = 99         # ← direct modification allowed
pub.show()


# ─────────────────────────────────────────────
# 2. PROTECTED ATTRIBUTES (single underscore _)
# ─────────────────────────────────────────────
# Convention only — Python does NOT enforce this.
# Signals to other developers: "don't touch this directly from outside."

class BankAccountBasic:
    """Demonstrates protected attributes."""

    def __init__(self, owner: str, balance: float):
        self.owner = owner
        self._balance = balance      # protected by convention

    def deposit(self, amount: float):
        if amount > 0:
            self._balance += amount
            print(f"Deposited ${amount:.2f}. New balance: ${self._balance:.2f}")

    def get_balance(self):
        return self._balance


account = BankAccountBasic("Alice", 1000.0)
account.deposit(500)
print(f"Balance via method : ${account.get_balance():.2f}")
print(f"Balance via direct : ${account._balance:.2f}")  # works, but discouraged


# ─────────────────────────────────────────────
# 3. PRIVATE ATTRIBUTES (double underscore __)
# ─────────────────────────────────────────────
# Python applies "name mangling": __attr becomes _ClassName__attr
# This makes accidental overriding in subclasses harder.

class SecureBankAccount:
    """
    A bank account with strong encapsulation.

    - __balance is private (name-mangled to _SecureBankAccount__balance)
    - __pin    is private
    - Access is controlled exclusively through methods
    """

    INTEREST_RATE = 0.05    # class attribute — public constant

    def __init__(self, owner: str, initial_balance: float, pin: int):
        self.owner = owner                       # public
        self.__balance = initial_balance         # private
        self.__pin = pin                         # private
        self.__transaction_history = []          # private

    # ── GETTER — controlled read access ──
    def get_balance(self, pin: int) -> float:
        """Return balance only if the correct PIN is provided."""
        if self.__verify_pin(pin):
            return self.__balance
        else:
            raise PermissionError("Incorrect PIN. Access denied.")

    # ── SETTER — controlled write access ──
    def deposit(self, amount: float):
        """Add money to the account with validation."""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.__balance += amount
        self.__log_transaction("Deposit", amount)

    def withdraw(self, amount: float, pin: int):
        """Remove money from the account with PIN and balance validation."""
        if not self.__verify_pin(pin):
            raise PermissionError("Incorrect PIN.")
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if amount > self.__balance:
            raise ValueError(f"Insufficient funds. Balance: ${self.__balance:.2f}")
        self.__balance -= amount
        self.__log_transaction("Withdrawal", amount)

    def apply_interest(self):
        """Apply annual interest to the account."""
        interest = self.__balance * self.INTEREST_RATE
        self.__balance += interest
        self.__log_transaction("Interest", interest)

    def get_history(self, pin: int):
        """Return transaction history with PIN verification."""
        if self.__verify_pin(pin):
            return list(self.__transaction_history)  # return a copy, not the original
        raise PermissionError("Incorrect PIN.")

    # ── PRIVATE HELPER METHODS ──
    def __verify_pin(self, pin: int) -> bool:
        """Internal PIN verification — not accessible outside the class."""
        return self.__pin == pin

    def __log_transaction(self, tx_type: str, amount: float):
        """Internal logging — encapsulated from outside."""
        entry = f"{tx_type}: ${amount:.2f} | Balance after: ${self.__balance:.2f}"
        self.__transaction_history.append(entry)


# ─────────────────────────────────────────────
# USING THE SECURE BANK ACCOUNT
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("SECURE BANK ACCOUNT DEMO")
print("=" * 50)

acc = SecureBankAccount(owner="Bob", initial_balance=2000.0, pin=1234)

acc.deposit(500)
acc.withdraw(200, pin=1234)
acc.apply_interest()

print(f"\nBalance (correct PIN) : ${acc.get_balance(pin=1234):.2f}")

print("\nTransaction History:")
for record in acc.get_history(pin=1234):
    print(f"  {record}")


# ─────────────────────────────────────────────
# DEMONSTRATING NAME MANGLING
# ─────────────────────────────────────────────

print("\n--- Name Mangling ---")
# acc.__balance          → AttributeError (cannot access directly)
# acc._SecureBankAccount__balance  → technically possible but strongly discouraged
print(f"Mangled name access: ${acc._SecureBankAccount__balance:.2f}  ← (possible but BAD practice)")


# ─────────────────────────────────────────────
# WRONG PIN EXAMPLE
# ─────────────────────────────────────────────

print("\n--- Wrong PIN ---")
try:
    acc.get_balance(pin=9999)
except PermissionError as e:
    print(f"PermissionError caught: {e}")

try:
    acc.withdraw(100, pin=0000)
except PermissionError as e:
    print(f"PermissionError caught: {e}")


# ─────────────────────────────────────────────
# 4. USING PROPERTIES FOR PYTHONIC ENCAPSULATION
# ─────────────────────────────────────────────
# @property provides a clean interface — looks like an attribute, acts like a method.
# (Full details are in 08_properties — here's a quick preview)

class Temperature:
    """
    Temperature class using @property for encapsulation.
    Stores value in Celsius internally; validates on set.
    """

    def __init__(self, celsius: float):
        self._celsius = None          # initialize first
        self.celsius = celsius        # use the setter for validation

    @property
    def celsius(self) -> float:
        """Getter — read self.celsius like a normal attribute."""
        return self._celsius

    @celsius.setter
    def celsius(self, value: float):
        """Setter — validates before storing."""
        if value < -273.15:
            raise ValueError("Temperature below absolute zero is not possible!")
        self._celsius = value

    @property
    def fahrenheit(self) -> float:
        """Computed property — always up to date."""
        return self._celsius * 9 / 5 + 32


print("\n--- Temperature (Property Encapsulation Preview) ---")
t = Temperature(100)
print(f"Celsius   : {t.celsius}°C")
print(f"Fahrenheit: {t.fahrenheit}°F")

t.celsius = -10
print(f"Updated   : {t.celsius}°C = {t.fahrenheit}°F")

try:
    t.celsius = -300   # below absolute zero
except ValueError as e:
    print(f"ValueError: {e}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 50)
print("SUMMARY")
print("=" * 50)
summary = """
  public    self.x      → freely accessible anywhere
  protected self._x     → "internal use" by convention (not enforced)
  private   self.__x    → name-mangled (_ClassName__x), harder to access outside

  Benefits of Encapsulation:
    ✔ Prevents invalid/accidental state changes
    ✔ Hides implementation details (change internals without breaking callers)
    ✔ Provides a clear, controlled interface (getters/setters/@property)
    ✔ Makes debugging easier (data changes only through known paths)
"""
print(summary)
