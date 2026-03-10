"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 12: Exception Handling
=============================================================

WHAT ARE EXCEPTIONS?
---------------------
An exception is an error that occurs DURING PROGRAM EXECUTION.
If not handled, it crashes the program.
Exception handling lets you respond to errors gracefully.

EXCEPTION HIERARCHY (partial):
  BaseException
  └── Exception
      ├── ArithmeticError
      │   ├── ZeroDivisionError
      │   └── OverflowError
      ├── LookupError
      │   ├── IndexError
      │   └── KeyError
      ├── TypeError
      ├── ValueError
      ├── AttributeError
      ├── IOError / OSError
      │   └── FileNotFoundError
      ├── RuntimeError
      │   └── RecursionError
      └── StopIteration

STRUCTURE:
  try:
      risky code
  except ExceptionType as e:
      handle error
  else:
      runs only if NO exception was raised
  finally:
      ALWAYS runs (cleanup)
"""


# ─────────────────────────────────────────────
# 1. BASIC try / except
# ─────────────────────────────────────────────

print("=" * 55)
print("BASIC try / except")
print("=" * 55)

def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        print("  Error: division by zero!")
        return None
    return result

print(safe_divide(10, 2))         # 5.0
print(safe_divide(10, 0))         # handled


# ─────────────────────────────────────────────
# 2. MULTIPLE except CLAUSES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("MULTIPLE except CLAUSES")
print("=" * 55)

def parse_and_index(data: list, index: str):
    """Demonstrates catching different exception types."""
    try:
        idx    = int(index)           # may raise ValueError
        value  = data[idx]            # may raise IndexError
        result = 100 / value          # may raise ZeroDivisionError
        return result
    except ValueError:
        print(f"  ValueError: '{index}' is not a valid integer index.")
    except IndexError:
        print(f"  IndexError: index {index} is out of range (list has {len(data)} items).")
    except ZeroDivisionError:
        print(f"  ZeroDivisionError: element at [{index}] is zero.")
    return None


print(parse_and_index([2, 5, 0, 10], "1"))    # ok → 100/5
print(parse_and_index([2, 5, 0, 10], "abc"))  # ValueError
print(parse_and_index([2, 5, 0, 10], "99"))   # IndexError
print(parse_and_index([2, 5, 0, 10], "2"))    # ZeroDivisionError


# ─────────────────────────────────────────────
# 3. except (Tuple) — Catch multiple types at once
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CATCHING MULTIPLE TYPES AT ONCE")
print("=" * 55)

def flexible_parse(value):
    try:
        return int(value)
    except (ValueError, TypeError) as e:
        print(f"  Cannot convert {value!r}: {type(e).__name__}: {e}")
        return 0

print(flexible_parse("42"))
print(flexible_parse("abc"))
print(flexible_parse(None))


# ─────────────────────────────────────────────
# 4. else AND finally
# ─────────────────────────────────────────────
# else  → runs ONLY if no exception was raised in try
# finally → ALWAYS runs (perfect for cleanup/resource release)

print("\n" + "=" * 55)
print("else AND finally")
print("=" * 55)

def read_integer(prompt_value):
    print(f"\n  Trying to parse: {prompt_value!r}")
    try:
        n = int(prompt_value)
    except ValueError as e:
        print(f"  [except] Invalid input: {e}")
    else:
        # Only executes if try succeeded with no exception
        print(f"  [else] Successfully parsed: {n}")
        return n
    finally:
        # Executes NO MATTER WHAT — even if except ran, even if there's a return
        print("  [finally] Cleanup done.")
    return None

read_integer("123")
read_integer("bad")


# ─────────────────────────────────────────────
# 5. RAISE — Deliberately raising exceptions
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("raise")
print("=" * 55)

def set_age(age: int):
    if not isinstance(age, int):
        raise TypeError(f"age must be int, got {type(age).__name__}")
    if age < 0 or age > 150:
        raise ValueError(f"age must be 0-150, got {age}")
    return age

for test in [25, -1, 200, "old"]:
    try:
        result = set_age(test)
        print(f"  set_age({test!r}) → {result}")
    except (ValueError, TypeError) as e:
        print(f"  {type(e).__name__}: {e}")

# Re-raise the same exception after logging
def risky():
    try:
        return 1 / 0
    except ZeroDivisionError:
        print("  [risky] Logging the error before re-raising...")
        raise            # re-raises the current exception as-is

try:
    risky()
except ZeroDivisionError as e:
    print(f"  [caller] Caught re-raised: {e}")


# ─────────────────────────────────────────────
# 6. CUSTOM EXCEPTIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CUSTOM EXCEPTIONS")
print("=" * 55)

class AppError(Exception):
    """Base class for all application errors."""
    pass

class ValidationError(AppError):
    """Raised when input validation fails."""
    def __init__(self, field: str, message: str):
        self.field   = field
        self.message = message
        super().__init__(f"[{field}] {message}")

class InsufficientFundsError(AppError):
    """Raised when a withdrawal exceeds the available balance."""
    def __init__(self, requested: float, available: float):
        self.requested = requested
        self.available = available
        self.shortfall = requested - available
        super().__init__(
            f"Cannot withdraw ${requested:.2f}. "
            f"Available: ${available:.2f}. "
            f"Shortfall: ${self.shortfall:.2f}."
        )


class BankAccount:
    def __init__(self, owner: str, balance: float = 0):
        if not owner.strip():
            raise ValidationError("owner", "Owner name cannot be empty.")
        if balance < 0:
            raise ValidationError("balance", "Initial balance cannot be negative.")
        self.owner   = owner
        self._balance = balance

    def deposit(self, amount: float):
        if amount <= 0:
            raise ValidationError("amount", "Deposit amount must be positive.")
        self._balance += amount

    def withdraw(self, amount: float):
        if amount <= 0:
            raise ValidationError("amount", "Withdrawal amount must be positive.")
        if amount > self._balance:
            raise InsufficientFundsError(amount, self._balance)
        self._balance -= amount
        return amount

    @property
    def balance(self): return self._balance


acc = BankAccount("Alice", 500)
acc.deposit(200)
print(f"  Balance after deposit: ${acc.balance}")

try:
    acc.withdraw(800)
except InsufficientFundsError as e:
    print(f"  InsufficientFundsError: {e}")
    print(f"  Shortfall: ${e.shortfall:.2f}")

try:
    BankAccount("", 100)
except ValidationError as e:
    print(f"  ValidationError — field={e.field!r}: {e.message}")

try:
    acc.deposit(-50)
except ValidationError as e:
    print(f"  ValidationError — field={e.field!r}: {e.message}")

# Exception hierarchy — handle AppError catches ALL sub-errors
print("\n  isinstance checks:")
err = InsufficientFundsError(100, 50)
print(f"  is InsufficientFundsError: {isinstance(err, InsufficientFundsError)}")
print(f"  is AppError              : {isinstance(err, AppError)}")
print(f"  is Exception             : {isinstance(err, Exception)}")


# ─────────────────────────────────────────────
# 7. EXCEPTION CHAINING (raise ... from ...)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("EXCEPTION CHAINING")
print("=" * 55)

class DatabaseError(Exception):
    pass

def fetch_user(user_id: int):
    """Simulate a database failure."""
    try:
        if user_id < 0:
            raise ValueError(f"Invalid user_id: {user_id}")
        # Simulate DB call
        raise ConnectionError("DB connection refused")
    except ConnectionError as e:
        # Chain: "DatabaseError was raised FROM ConnectionError"
        raise DatabaseError(f"Failed to fetch user {user_id}") from e

try:
    fetch_user(42)
except DatabaseError as e:
    print(f"  DatabaseError: {e}")
    print(f"  Caused by    : {e.__cause__}")


# ─────────────────────────────────────────────
# 8. CONTEXT MANAGER for Exceptions (suppress)
# ─────────────────────────────────────────────

from contextlib import suppress

print("\n" + "=" * 55)
print("contextlib.suppress")
print("=" * 55)

# Silently ignore specific exceptions
with suppress(FileNotFoundError):
    open("/nonexistent/path/file.txt")
    print("  This won't print.")

print("  Program continues after suppressed exception!")

# Equivalent to:
try:
    open("/nonexistent/path/file.txt")
except FileNotFoundError:
    pass
print("  Program continues after manual suppression!")


# ─────────────────────────────────────────────
# 9. assert (Defensive Programming)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("assert STATEMENTS")
print("=" * 55)

def compute_percentage(part: float, total: float) -> float:
    assert total != 0, "total must not be zero"
    assert 0 <= part <= total, f"part ({part}) must be in [0, total ({total})]"
    return (part / total) * 100

print(f"  50/200 = {compute_percentage(50, 200):.1f}%")

try:
    compute_percentage(300, 200)
except AssertionError as e:
    print(f"  AssertionError: {e}")

# NOTE: assert can be disabled with python -O flag — use for dev checks,
# not for production validation (use raise ValueError instead for that)


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  STRUCTURE:
    try:          → code that might raise
    except E as e:→ handle specific exception(s)
    else:         → runs only if try had NO exception
    finally:      → ALWAYS runs (cleanup resources)

    raise ExceptionType(msg)    → manually raise
    raise                       → re-raise current exception
    raise NewErr(...) from orig → chain exceptions

  CUSTOM EXCEPTIONS:
    class MyError(Exception):
        def __init__(self, ...): super().__init__(msg)

  HIERARCHY:
    Catch child BEFORE parent — specific before broad.
    Never catch bare `except:` (catches SystemExit too).

  UTILITIES:
    contextlib.suppress(E)  → silently ignore specific exceptions
    assert condition, msg   → development-time checks
"""
print(summary)
