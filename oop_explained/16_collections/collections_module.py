"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 16: Collections & Built-in Data Structures
=============================================================

COVERED:
  1. list          → ordered, mutable, duplicates allowed
  2. tuple         → ordered, immutable
  3. dict          → key→value, ordered (3.7+), mutable
  4. set / frozenset → unordered, unique, fast membership
  5. collections.defaultdict → dict with default factory
  6. collections.Counter     → counting / frequency
  7. collections.OrderedDict → dict with order methods
  8. collections.namedtuple  → tuple with named fields
  9. collections.deque       → double-ended queue (O(1) ends)
  10. heapq                  → priority queue (min-heap)
  11. bisect                 → binary search in sorted lists
  12. String methods         → comprehensive reference
"""

from collections import defaultdict, Counter, OrderedDict, namedtuple, deque
import heapq
import bisect


# ─────────────────────────────────────────────
# 1. LIST — Ordered, Mutable
# ─────────────────────────────────────────────

print("=" * 55)
print("LIST — Key Operations")
print("=" * 55)

lst = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
print(f"Original   : {lst}")

lst.append(7)                   # add to end O(1)
lst.insert(2, 99)               # insert at index O(n)
lst.remove(1)                   # remove first occurrence O(n)
popped = lst.pop()              # remove from end O(1) → 7
popped_i = lst.pop(0)          # remove from index O(n)
lst.sort()                      # in-place sort
lst.sort(reverse=True)

print(f"After ops  : {lst}")
print(f"Popped     : {popped}, {popped_i}")
print(f"Index of 5 : {lst.index(5)}")
print(f"Count of 5 : {lst.count(5)}")
print(f"Reversed   : {list(reversed(lst))}")
print(f"Sliced[1:4]: {lst[1:4]}")
print(f"Sliced[::2]: {lst[::2]}")

# List as stack (LIFO)
stack = []
stack.append("a"); stack.append("b"); stack.append("c")
print(f"\nStack LIFO pop: {stack.pop()}, {stack.pop()}")


# ─────────────────────────────────────────────
# 2. TUPLE — Ordered, Immutable
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("TUPLE — Immutable Sequences")
print("=" * 55)

coords = (40.71, -74.01)
rgb    = (255, 128, 0)
single = (42,)              # NOTE: comma needed for single-element tuple

print(f"coords       : {coords}")
print(f"Unpack x,y   : {coords[0]}, {coords[1]}")

# Tuple unpacking
lat, lon = coords
r, g, b  = rgb
print(f"lat={lat}, lon={lon}")
print(f"r={r}, g={g}, b={b}")

# Extended unpacking
first, *middle, last = [1, 2, 3, 4, 5]
print(f"first={first}, middle={middle}, last={last}")

# Tuples as dict keys (hashable unlike lists)
distances = {
    ("NYC", "LA"): 2800,
    ("NYC", "CHI"): 790,
}
print(f"NYC→LA: {distances[('NYC','LA')]} miles")

# Named access via index is OK for small tuples;
# prefer namedtuple or dataclass for readable code (see below)


# ─────────────────────────────────────────────
# 3. DICT — Key→Value, Ordered (3.7+)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("DICT — Key-Value Store")
print("=" * 55)

d = {"apple": 3, "banana": 5, "cherry": 2}

# CRUD
d["date"]  = 4                      # add
d["apple"] = 10                     # update
del d["banana"]                     # delete

print(f"dict          : {d}")
print(f"keys          : {list(d.keys())}")
print(f"values        : {list(d.values())}")
print(f"items         : {list(d.items())}")
print(f"get (safe)    : {d.get('banana', 0)}")   # 0 if not found
print(f"setdefault    : {d.setdefault('elderberry', 7)}")  # add if missing
print(f"pop           : {d.pop('date')}")         # remove and return

# Merge dicts (Python 3.9+: d1 | d2)
extra = {"fig": 6, "grape": 8}
merged = {**d, **extra}                           # works in all 3+ versions
print(f"merged        : {merged}")

# dict comprehension
inverted = {v: k for k, v in d.items()}
print(f"inverted      : {inverted}")

# Iteration patterns
print("\nIterating:")
for key, val in d.items():
    print(f"  {key:15} → {val}")


# ─────────────────────────────────────────────
# 4. SET / FROZENSET
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SET — Unique, Unordered, Fast Membership")
print("=" * 55)

a = {1, 2, 3, 4, 5}
b = {3, 4, 5, 6, 7}

print(f"a             : {a}")
print(f"b             : {b}")
print(f"a | b (union) : {a | b}")
print(f"a & b (inter) : {a & b}")
print(f"a - b (diff)  : {a - b}")
print(f"a ^ b (sym.d) : {a ^ b}")
print(f"a <= b (sub?) : {a <= b}")
subset_check = {1, 2} <= a
print(f"{{1,2}} <= a   : {subset_check}")

a.add(99)
a.discard(99)              # remove if exists — NO KeyError
a.discard(999)             # safe
try:
    a.remove(999)          # raises KeyError if missing
except KeyError:
    print(f"remove(999): KeyError (use discard for safety)")

# Fast membership check — O(1) vs O(n) for list
big_set  = set(range(100_000))
big_list = list(range(100_000))
print(f"\n99999 in set  : {99999 in big_set}")
print(f"99999 in list : {99999 in big_list}")

# frozenset — immutable set (can be used as dict key or set member)
fs = frozenset([1, 2, 3])
pair_set  = {frozenset([1, 2]), frozenset([3, 4])}
print(f"frozenset: {fs}")


# ─────────────────────────────────────────────
# 5. collections.defaultdict
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("collections.defaultdict")
print("=" * 55)

# Automatically creates a default value for missing keys
# No more KeyError or "if key not in d: d[key] = []"

words = "the quick brown fox jumps over the lazy dog the fox".split()

# Group letters by first letter
by_letter = defaultdict(list)
for word in words:
    by_letter[word[0]].append(word)

print("Words by first letter:")
for letter in sorted(by_letter):
    print(f"  {letter}: {by_letter[letter]}")

# Count word frequencies
freq = defaultdict(int)
for word in words:
    freq[word] += 1

print("\nWord frequencies:")
for word, count in sorted(freq.items()):
    print(f"  {word:8} : {count}")

# Nested defaultdict
nested = defaultdict(lambda: defaultdict(int))
nested["Math"]["Alice"] = 95
nested["Math"]["Bob"]   = 78
nested["Science"]["Alice"] = 88
for subject, scores in nested.items():
    print(f"\n{subject}: {dict(scores)}")


# ─────────────────────────────────────────────
# 6. collections.Counter
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("collections.Counter")
print("=" * 55)

sentence = "to be or not to be that is the question"
word_count = Counter(sentence.split())
print(f"Most common 3: {word_count.most_common(3)}")
print(f"'to' appears : {word_count['to']} times")
print(f"Total words  : {sum(word_count.values())}")

letter_count = Counter("mississippi")
print(f"\nLetter freq  : {dict(letter_count)}")

# Counter arithmetic
c1 = Counter(["a", "b", "a", "c"])
c2 = Counter(["b", "b", "c", "d"])
print(f"\nc1 + c2: {c1 + c2}")     # combine
print(f"c1 - c2: {c1 - c2}")     # subtract (removes non-positive)
print(f"c1 & c2: {c1 & c2}")     # intersection (min)
print(f"c1 | c2: {c1 | c2}")     # union (max)


# ─────────────────────────────────────────────
# 7. collections.namedtuple
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("collections.namedtuple")
print("=" * 55)

# Like a tuple but with named fields — immutable, memory efficient
Point   = namedtuple("Point", ["x", "y"])
Color   = namedtuple("Color", ["red", "green", "blue"])
Student = namedtuple("Student", ["name", "age", "gpa"], defaults=[0.0])

p = Point(3, 4)
c = Color(255, 128, 0)
s = Student("Alice", 20, 3.9)

print(f"Point     : {p}")
print(f"x={p.x}, y={p.y}  (named access)")
print(f"x={p[0]}, y={p[1]} (index access — still works)")
print(f"Color     : {c}")
print(f"Student   : {s}")

# _asdict() — convert to dict
print(f"\nPoint._asdict(): {p._asdict()}")

# _replace() — create modified copy
p2 = p._replace(x=10)
print(f"_replace(x=10): {p2}")


# ─────────────────────────────────────────────
# 8. collections.deque
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("collections.deque — Double-Ended Queue")
print("=" * 55)

# O(1) append/prepend/pop from BOTH ends
# Unlike list, list.insert(0) / list.pop(0) are O(n)

dq = deque([1, 2, 3, 4, 5])
dq.appendleft(0)              # O(1) prepend
dq.append(6)                  # O(1) append to end
left  = dq.popleft()          # O(1)
right = dq.pop()              # O(1)

print(f"deque     : {dq}")
print(f"popleft   : {left}")
print(f"pop       : {right}")

# Rotate
dq.rotate(2)                  # shift right by 2
print(f"rotate(2) : {dq}")
dq.rotate(-3)                 # shift left by 3
print(f"rotate(-3): {dq}")

# maxlen — fixed-size sliding window
window = deque(maxlen=3)
for i in range(7):
    window.append(i)
    print(f"  Added {i} → window: {list(window)}")


# ─────────────────────────────────────────────
# 9. heapq — Priority Queue (Min-Heap)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("heapq — Priority Queue (Min-Heap)")
print("=" * 55)

# heapq implements a MIN-heap: smallest element always at index 0
# For max-heap: negate values

nums = [5, 1, 9, 3, 7, 2, 8]
heap = nums[:]
heapq.heapify(heap)             # convert list to heap in-place O(n)
print(f"Heap     : {heap}")

heapq.heappush(heap, 0)         # push element O(log n)
print(f"Pushed 0 : {heap}")

smallest = heapq.heappop(heap)  # pop smallest O(log n)
print(f"Popped   : {smallest}")
print(f"After pop: {heap}")

# nlargest / nsmallest — efficient for small k
print(f"\n3 largest  : {heapq.nlargest(3, nums)}")
print(f"3 smallest : {heapq.nsmallest(3, nums)}")

# Priority queue pattern: (priority, item)
task_queue = []
heapq.heappush(task_queue, (2, "Medium task"))
heapq.heappush(task_queue, (1, "Urgent task"))
heapq.heappush(task_queue, (3, "Low priority"))
heapq.heappush(task_queue, (1, "Also urgent"))

print("\nTask queue (by priority):")
while task_queue:
    pri, task = heapq.heappop(task_queue)
    print(f"  [{pri}] {task}")


# ─────────────────────────────────────────────
# 10. bisect — Binary Search
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("bisect — Binary Search in Sorted Lists")
print("=" * 55)

sorted_list = [10, 20, 30, 40, 50, 60, 70]

# Find insertion point (O(log n))
pos = bisect.bisect_left(sorted_list, 35)   # where 35 would go
print(f"bisect_left(35)  → insert at index {pos}")

pos_r = bisect.bisect_right(sorted_list, 40)  # after existing 40
print(f"bisect_right(40) → insert at index {pos_r}")

# insort — insert and keep sorted
bisect.insort(sorted_list, 35)
print(f"After insort(35) : {sorted_list}")

# Grade lookup with bisect
breakpoints = [60, 70, 80, 90]
grades      = ["F", "D", "C", "B", "A"]

def grade(score: int) -> str:
    return grades[bisect.bisect_left(breakpoints, score)]

for s in [45, 63, 75, 82, 95]:
    print(f"  Score {s:3d} → {grade(s)}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  STRUCTURE         USE WHEN
  ─────────────────────────────────────────────────────────
  list              Ordered, mutable, indexed sequence
  tuple             Immutable record; multiple return values
  dict              Key→value mapping, fast lookup O(1)
  set               Unique elements, fast membership, set ops
  frozenset         Immutable set (hashable, usable as key)
  defaultdict       Dict that auto-creates missing keys
  Counter           Count occurrences; frequency analysis
  namedtuple        Lightweight immutable record with named fields
  deque             Fast O(1) insert/pop at BOTH ends; sliding window
  heapq             Priority queue; get smallest/largest efficiently
  bisect            Binary search + sorted insert
"""
print(summary)
