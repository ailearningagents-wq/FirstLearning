"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 15: File I/O & Context Managers
=============================================================

FILE I/O IN PYTHON:
  open(path, mode)  → opens a file and returns a file object
  Modes:
    'r'   → read text (default)
    'w'   → write text (truncates existing)
    'a'   → append text
    'x'   → exclusive create (fails if file exists)
    'rb'  → read binary
    'wb'  → write binary
    'r+'  → read and write
  Encoding: always specify encoding='utf-8' for portability

ALWAYS use `with` (context manager) — it guarantees the file is closed
even if an exception occurs.

COVERED:
  1. Reading files (read, readline, readlines, iteration)
  2. Writing and appending
  3. Binary files
  4. CSV files (csv module)
  5. JSON files (json module)
  6. pathlib (modern file system operations)
  7. tempfile (temporary files)
  8. os.path and shutil basics
"""

import os
import json
import csv
import tempfile
import shutil
from pathlib import Path


# Helper: use a temp directory for all file operations — no leftover files
WORK_DIR = Path(tempfile.mkdtemp(prefix="python_fileio_"))
print(f"Working directory: {WORK_DIR}\n")


# ─────────────────────────────────────────────
# 1. WRITING FILES
# ─────────────────────────────────────────────

print("=" * 55)
print("WRITING FILES")
print("=" * 55)

poem_path = WORK_DIR / "poem.txt"

# write mode: 'w' creates or OVERWRITES
with open(poem_path, "w", encoding="utf-8") as f:
    f.write("Roses are red,\n")
    f.write("Violets are blue,\n")
    f.write("Python is awesome,\n")
    f.write("And so are you!\n")

print(f"Written: {poem_path.name} ({poem_path.stat().st_size} bytes)")

# writelines — write a list of strings (each must include \n if needed)
lines_path = WORK_DIR / "numbers.txt"
with open(lines_path, "w", encoding="utf-8") as f:
    f.writelines(f"{i}\n" for i in range(1, 11))

print(f"Written: {lines_path.name}")


# ─────────────────────────────────────────────
# 2. READING FILES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("READING FILES")
print("=" * 55)

# read() — entire file as ONE string
with open(poem_path, "r", encoding="utf-8") as f:
    content = f.read()
print("read() →\n" + content)

# readline() — one line at a time
print("readline() →")
with open(poem_path, "r", encoding="utf-8") as f:
    line = f.readline()
    while line:
        print(f"  {line!r}")
        line = f.readline()

# readlines() — all lines as a list
with open(poem_path, "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"\nreadlines() → {len(lines)} lines")

# BEST PRACTICE: iterate line by line (memory efficient for large files)
print("\nLine iteration (most Pythonic):")
with open(poem_path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        print(f"  Line {i}: {line.rstrip()}")


# ─────────────────────────────────────────────
# 3. APPENDING
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("APPENDING")
print("=" * 55)

log_path = WORK_DIR / "app.log"

import datetime

def log(message: str, level: str = "INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level:5}] {message}\n")

log("Application started.")
log("Processing data...")
log("Invalid input detected.", "WARN")
log("Process complete.")

with open(log_path) as f:
    print("Log contents:")
    print(f.read())


# ─────────────────────────────────────────────
# 4. JSON FILES
# ─────────────────────────────────────────────

print("=" * 55)
print("JSON FILES")
print("=" * 55)

users = [
    {"id": 1, "name": "Alice",   "age": 30, "active": True,  "tags": ["admin", "user"]},
    {"id": 2, "name": "Bob",     "age": 25, "active": True,  "tags": ["user"]},
    {"id": 3, "name": "Charlie", "age": 35, "active": False, "tags": []},
]

json_path = WORK_DIR / "users.json"

# Write JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(users, f, indent=2, ensure_ascii=False)

print(f"Written JSON: {json_path.name}")

# Read JSON
with open(json_path, "r", encoding="utf-8") as f:
    loaded = json.load(f)

print(f"Loaded {len(loaded)} users:")
for u in loaded:
    print(f"  {u['name']:8} age={u['age']} active={u['active']}")

# json.dumps / json.loads for string (not file) I/O
config = {"host": "localhost", "port": 8080, "debug": False}
json_str = json.dumps(config, indent=2)
print(f"\nJSON string:\n{json_str}")

back = json.loads(json_str)
print(f"Parsed back: {back}")


# ─────────────────────────────────────────────
# 5. CSV FILES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("CSV FILES")
print("=" * 55)

csv_path = WORK_DIR / "scores.csv"

# Write CSV
headers = ["Name", "Math", "Science", "English"]
rows    = [
    ["Alice",   95, 88, 92],
    ["Bob",     72, 65, 80],
    ["Carol",   88, 91, 85],
    ["Dave",    60, 70, 75],
]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Written CSV: {csv_path.name}")

# Read CSV with DictReader — each row is a dict
with open(csv_path, "r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    records = list(reader)

print("Loaded CSV:")
for r in records:
    avg = sum(int(r[s]) for s in ["Math", "Science", "English"]) / 3
    print(f"  {r['Name']:6} → avg {avg:.1f}")


# ─────────────────────────────────────────────
# 6. pathlib — Modern Path Operations
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("pathlib — Modern File System")
print("=" * 55)

# Path construction
p = Path("/Users/example/documents/report.txt")
print(f"Path       : {p}")
print(f"name       : {p.name}")         # report.txt
print(f"stem       : {p.stem}")         # report
print(f"suffix     : {p.suffix}")       # .txt
print(f"parent     : {p.parent}")       # /Users/example/documents
print(f"parts      : {p.parts}")

# Path operations
data_dir = WORK_DIR / "data"
data_dir.mkdir(exist_ok=True)

sample = data_dir / "sample.txt"
sample.write_text("Hello from pathlib!\nLine 2.\n", encoding="utf-8")
print(f"\nWrote via pathlib: {sample}")
print(f"Content: {sample.read_text(encoding='utf-8')!r}")

# Glob — find files matching pattern
for f in WORK_DIR.glob("*.txt"):
    print(f"  Found: {f.name} ({f.stat().st_size} B)")

# Recursive glob
for f in WORK_DIR.rglob("*.*"):
    print(f"  rglob: {f.relative_to(WORK_DIR)}")

# Existence checks
print(f"\nsample.exists() : {sample.exists()}")
print(f"sample.is_file(): {sample.is_file()}")
print(f"data_dir.is_dir(): {data_dir.is_dir()}")

# Rename / move within pathlib
renamed = sample.rename(data_dir / "sample_renamed.txt")
print(f"\nRenamed to: {renamed.name}")


# ─────────────────────────────────────────────
# 7. BINARY FILES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("BINARY FILE I/O")
print("=" * 55)

bin_path = WORK_DIR / "data.bin"

# Write binary — pack integers as bytes
import struct

values = [1, 2, 3, 255, 1000]
with open(bin_path, "wb") as f:
    for v in values:
        f.write(struct.pack(">H", v))   # big-endian unsigned short (2 bytes each)

print(f"Binary file size: {bin_path.stat().st_size} bytes (5 × 2 = 10)")

# Read back
with open(bin_path, "rb") as f:
    raw = f.read()
    unpacked = [struct.unpack(">H", raw[i:i+2])[0] for i in range(0, len(raw), 2)]

print(f"Read back: {unpacked}")


# ─────────────────────────────────────────────
# 8. SEEKING & TELL
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("seek() and tell()")
print("=" * 55)

with open(poem_path, "r", encoding="utf-8") as f:
    print(f"Position at start     : {f.tell()}")
    first_line = f.readline()
    print(f"After readline()      : {f.tell()} → {first_line.rstrip()!r}")

    f.seek(0)           # go back to beginning
    print(f"After seek(0)         : {f.tell()}")
    print(f"First line again      : {f.readline().rstrip()!r}")

    f.seek(0, 2)        # seek to END (os.SEEK_END = 2)
    print(f"File size via seek(end): {f.tell()} bytes")


# ─────────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────────
shutil.rmtree(WORK_DIR)
print(f"\nCleaned up temp dir: {WORK_DIR.name}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────
print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  OPEN MODES:
    'r'   read text          'rb'  read binary
    'w'   write text         'wb'  write binary
    'a'   append text        'x'   exclusive create
    'r+'  read+write         always encoding='utf-8'

  READING:
    f.read()       → whole file as string
    f.readline()   → one line
    f.readlines()  → list of lines
    for line in f  → memory-efficient line iteration ← PREFERRED

  WRITING:
    f.write(str)       → write string
    f.writelines(iter) → write multiple strings

  FORMATS:
    json.dump/load   → JSON files
    csv.writer/DictReader → CSV files

  pathlib.Path:
    Path(str) / "subdir" / "file.txt"   → path construction
    p.read_text(), p.write_text()        → one-liner I/O
    p.exists(), p.is_file(), p.is_dir()  → existence checks
    p.glob("*.txt"), p.rglob("**/*.py")  → pattern matching
    p.mkdir(exist_ok=True)               → create directory

  ALWAYS use `with open(path) as f:` — guarantees file close on exit.
"""
print(summary)
