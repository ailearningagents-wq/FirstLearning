"""
=============================================================
IMPORTANT PYTHON CONCEPTS
Topic 18: Concurrency — Threading, Multiprocessing & asyncio
=============================================================

WHY CONCURRENCY?
-----------------
Modern programs often need to do multiple things at once:
  • fetch data from the network
  • process files on disk
  • run CPU-heavy calculations

Python offers three concurrency models:

  MODEL              │ BEST FOR                   │ GIL?
  ───────────────────┼────────────────────────────┼──────
  threading          │ I/O-bound tasks             │ Yes (limited)
  multiprocessing    │ CPU-bound tasks             │ No (separate processes)
  asyncio            │ High-concurrency I/O        │ Yes (single-threaded)

GIL = Global Interpreter Lock
  The GIL ensures that only ONE thread executes Python bytecode at a time.
  → Threads CAN'T parallelize CPU work in CPython.
  → Threads CAN overlap on I/O (waiting releases the GIL).

COVERED:
  1. Threading basics  (Thread, daemon threads)
  2. Thread safety — Lock, RLock
  3. Thread communication — Event, Queue
  4. concurrent.futures.ThreadPoolExecutor
  5. Multiprocessing basics — Process, Pool
  6. concurrent.futures.ProcessPoolExecutor
  7. asyncio basics — async/await, gather
  8. When to use what
"""

import time
import threading
import queue
import concurrent.futures
import multiprocessing
import asyncio


# ─────────────────────────────────────────────
# 1. THREADING BASICS
# ─────────────────────────────────────────────

print("=" * 55)
print("1. THREADING BASICS")
print("=" * 55)

def worker(name: str, delay: float) -> None:
    """Simulates I/O work by sleeping."""
    print(f"  [{name}] starting (delay={delay}s)")
    time.sleep(delay)                    # releases the GIL → other threads run
    print(f"  [{name}] done")


# Sequential (for comparison)
start = time.perf_counter()
worker("A-seq", 0.1)
worker("B-seq", 0.1)
worker("C-seq", 0.1)
sequential_time = time.perf_counter() - start
print(f"  Sequential time : {sequential_time:.2f}s")

# Threaded
start = time.perf_counter()
threads = [
    threading.Thread(target=worker, args=(f"T{i}", 0.1), daemon=True)
    for i in range(3)
]
for t in threads:
    t.start()
for t in threads:
    t.join()                             # wait for all threads to finish
threaded_time = time.perf_counter() - start
print(f"  Threaded time   : {threaded_time:.2f}s  ← ~3× faster")

# Thread with return value via subclassing
class WorkerThread(threading.Thread):
    def __init__(self, value: int):
        super().__init__()
        self.value  = value
        self.result = None

    def run(self):
        time.sleep(0.05)
        self.result = self.value * self.value


threads = [WorkerThread(i) for i in range(5)]
for t in threads:  t.start()
for t in threads:  t.join()
print(f"  Squared results : {[t.result for t in threads]}")


# ─────────────────────────────────────────────
# 2. THREAD SAFETY — Lock
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. THREAD SAFETY — Lock & RLock")
print("=" * 55)

# Race condition demo (unsafe)
unsafe_counter = 0

def unsafe_increment(n: int) -> None:
    global unsafe_counter
    for _ in range(n):
        unsafe_counter += 1   # read-modify-write: NOT atomic!


threads = [threading.Thread(target=unsafe_increment, args=(1000,)) for _ in range(5)]
for t in threads:  t.start()
for t in threads:  t.join()
print(f"  Unsafe counter (expected 5000): {unsafe_counter}")   # often < 5000

# Thread-safe with Lock
safe_counter = 0
lock = threading.Lock()

def safe_increment(n: int) -> None:
    global safe_counter
    for _ in range(n):
        with lock:            # acquire → execute → release
            safe_counter += 1


threads = [threading.Thread(target=safe_increment, args=(1000,)) for _ in range(5)]
for t in threads:  t.start()
for t in threads:  t.join()
print(f"  Safe  counter (expected 5000): {safe_counter}")      # always 5000

# Thread-safe shared state using a class
class ThreadSafeCounter:
    def __init__(self):
        self._value = 0
        self._lock  = threading.Lock()

    def increment(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    def value(self) -> int:
        with self._lock:
            return self._value


counter = ThreadSafeCounter()
threads = [threading.Thread(target=lambda: counter.increment(100)) for _ in range(10)]
for t in threads:  t.start()
for t in threads:  t.join()
print(f"  Thread-safe class (expected 1000): {counter.value()}")


# ─────────────────────────────────────────────
# 3. THREAD COMMUNICATION — Event & Queue
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. THREAD COMMUNICATION — Event, Queue")
print("=" * 55)

# threading.Event — signal between threads
def producer_event(event: threading.Event) -> None:
    print("  Producer: preparing data …")
    time.sleep(0.05)
    event.set()                         # signal consumers
    print("  Producer: data ready!")

def consumer_event(event: threading.Event, name: str) -> None:
    event.wait()                        # block until event is set
    print(f"  Consumer {name}: received data")


ev = threading.Event()
prod = threading.Thread(target=producer_event, args=(ev,), daemon=True)
cons = [threading.Thread(target=consumer_event, args=(ev, f"C{i}"), daemon=True) for i in range(3)]

for t in cons:  t.start()
prod.start()
prod.join()
for t in cons:  t.join()

# queue.Queue — thread-safe producer-consumer
print()
task_queue: "queue.Queue[int]" = queue.Queue()
results:    "queue.Queue[int]" = queue.Queue()

def queue_worker() -> None:
    while True:
        item = task_queue.get()         # blocks until item available
        if item is None:                # sentinel value → stop
            break
        results.put(item * item)
        task_queue.task_done()

N_WORKERS = 3
workers = [threading.Thread(target=queue_worker, daemon=True) for _ in range(N_WORKERS)]
for w in workers:  w.start()

for i in range(10):
    task_queue.put(i)

task_queue.join()           # wait until all items processed
for _ in range(N_WORKERS):
    task_queue.put(None)    # send sentinels to stop workers

sq = sorted([results.get_nowait() for _ in range(10)])
print(f"  Queue results (0..9 squared): {sq}")


# ─────────────────────────────────────────────
# 4. concurrent.futures — ThreadPoolExecutor
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. ThreadPoolExecutor (high-level threads)")
print("=" * 55)

def fetch_page(page_id: int) -> str:
    """Simulate fetching a web page."""
    time.sleep(0.05)
    return f"<html>page {page_id}</html>"

page_ids = list(range(8))

# Using map — preserves order, blocks until all done
start = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    pages = list(executor.map(fetch_page, page_ids))
elapsed = time.perf_counter() - start
print(f"  Fetched {len(pages)} pages in {elapsed:.2f}s")
print(f"  First page : {pages[0]}")

# Using submit + as_completed — process results as they arrive
def compute(n: int) -> int:
    time.sleep(0.03)
    return n ** 2

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(compute, n): n for n in range(6)}
    for future in concurrent.futures.as_completed(futures):
        n = futures[future]
        try:
            result = future.result()
            print(f"  compute({n}) = {result}")
        except Exception as e:
            print(f"  compute({n}) raised {e}")


# ─────────────────────────────────────────────
# 5. MULTIPROCESSING BASICS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. MULTIPROCESSING BASICS")
print("=" * 55)

def cpu_task(n: int) -> int:
    """CPU-bound: sum squares up to n."""
    return sum(i * i for i in range(n))

def run_multiprocessing_demo():
    numbers = [200_000, 300_000, 250_000, 100_000]

    # Sequential
    start = time.perf_counter()
    seq_results = [cpu_task(n) for n in numbers]
    seq_time = time.perf_counter() - start

    # ProcessPoolExecutor — bypass GIL with separate processes
    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor() as executor:
        pool_results = list(executor.map(cpu_task, numbers))
    pool_time = time.perf_counter() - start

    print(f"  Sequential time  : {seq_time:.3f}s")
    print(f"  ProcessPool time : {pool_time:.3f}s")
    print(f"  Results match    : {seq_results == pool_results}")
    cores = multiprocessing.cpu_count()
    print(f"  CPU cores        : {cores}")

# Guard required for multiprocessing on macOS/Windows
if __name__ == "__main__":
    run_multiprocessing_demo()
else:
    # When imported by main.py use a small inline demo
    print(f"  CPU cores available: {multiprocessing.cpu_count()}")
    result = cpu_task(100_000)
    print(f"  cpu_task(100_000) = {result}")


# ─────────────────────────────────────────────
# 6. asyncio — ASYNC / AWAIT
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("6. asyncio — async/await")
print("=" * 55)

# asyncio uses a single-threaded EVENT LOOP.
# When a coroutine hits `await`, it YIELDS CONTROL back to the loop,
# allowing other coroutines to run in the meantime.
# No GIL issues — no data races — no threads.

async def async_fetch(url_id: int) -> str:
    """Simulate async I/O (e.g. HTTP request)."""
    await asyncio.sleep(0.05)           # yields to event loop
    return f"data from {url_id}"

async def main_async():
    # Sequential coroutines
    start = time.perf_counter()
    for i in range(4):
        result = await async_fetch(i)
    seq_time = time.perf_counter() - start
    print(f"  Sequential async : {seq_time:.2f}s")

    # Concurrent coroutines with gather
    start = time.perf_counter()
    results = await asyncio.gather(*(async_fetch(i) for i in range(4)))
    concurrent_time = time.perf_counter() - start
    print(f"  Concurrent async : {concurrent_time:.2f}s  ← ~4× faster")
    print(f"  Results          : {results}")

    # asyncio.create_task — schedule without waiting immediately
    async def slow_greeting(name: str, delay: float) -> str:
        await asyncio.sleep(delay)
        return f"Hello, {name}!"

    task_a = asyncio.create_task(slow_greeting("Alice", 0.08))
    task_b = asyncio.create_task(slow_greeting("Bob",   0.05))

    b_result = await task_b
    a_result = await task_a
    print(f"  task_b (Bob)   : {b_result}")
    print(f"  task_a (Alice) : {a_result}")


asyncio.run(main_async())


# ─────────────────────────────────────────────
# 7. ASYNC CONTEXT MANAGERS & ITERATORS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. ASYNC CONTEXT MANAGERS & ITERATORS")
print("=" * 55)

class AsyncConnection:
    """Simulates an async database connection."""
    def __init__(self, host: str):
        self.host = host

    async def __aenter__(self):
        await asyncio.sleep(0.01)       # simulate connect
        print(f"  Connected to {self.host}")
        return self

    async def __aexit__(self, *args):
        await asyncio.sleep(0.01)       # simulate disconnect
        print(f"  Disconnected from {self.host}")

    async def query(self, sql: str) -> list[dict]:
        await asyncio.sleep(0.01)
        return [{"sql": sql, "rows": 42}]


async def async_context_demo():
    async with AsyncConnection("db.example.com") as conn:
        result = await conn.query("SELECT * FROM users")
        print(f"  Query result: {result}")

    # Async iterator
    class AsyncRange:
        def __init__(self, stop: int):
            self.current = 0
            self.stop    = stop

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.current >= self.stop:
                raise StopAsyncIteration
            self.current += 1
            await asyncio.sleep(0)     # yield to event loop
            return self.current

    items = []
    async for i in AsyncRange(5):
        items.append(i)
    print(f"  Async range: {items}")


asyncio.run(async_context_demo())


# ─────────────────────────────────────────────
# 8. WHEN TO USE WHICH MODEL
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("8. WHEN TO USE WHICH CONCURRENCY MODEL")
print("=" * 55)

guide = """
  TASK TYPE          │ BEST CHOICE          │ REASON
  ───────────────────┼──────────────────────┼──────────────────────────────
  I/O bound (many)   │ asyncio              │ lowest overhead, runs 1000s of
                     │                      │ concurrent ops in one thread
  I/O bound (simple) │ ThreadPoolExecutor   │ easy to retrofit existing code;
                     │                      │ GIL released during I/O wait
  CPU bound          │ ProcessPoolExecutor  │ bypasses GIL via separate procs
  Mixed large app    │ asyncio + process    │ async for I/O + processes for
                     │                      │ CPU-heavy sub-tasks

  QUICK DECISION TREE:
    • Is it waiting on network/disk? → asyncio or threads
    • Is it heavy number crunching?  → multiprocessing
    • Is the code base already sync? → ThreadPoolExecutor (easy refactor)
    • Do you need thousands of conn?  → asyncio (cheapest concurrency unit)

  PITFALLS:
    • Threads + shared state → always use Lock / Queue
    • Processes → cannot share regular Python objects (use Manager / Queue)
    • asyncio → do NOT block the event loop (avoid time.sleep,
                use await asyncio.sleep instead)
    • Never nest asyncio.run() — use asyncio.create_task() or gather()
"""
print(guide)


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("=" * 55)
print("SUMMARY")
print("=" * 55)
summary = """
  threading.Thread(target=fn, args=(...), daemon=True)
  t.start() / t.join()

  with threading.Lock():
      shared_var += 1      ← thread-safe modification

  threading.Event / queue.Queue ← inter-thread communication

  with ThreadPoolExecutor(max_workers=N) as ex:
      results = list(ex.map(fn, items))
      future  = ex.submit(fn, arg)

  with ProcessPoolExecutor() as ex:   ← real parallelism (no GIL)
      results = list(ex.map(cpu_fn, items))

  async def fetch():           ← coroutine definition
      await asyncio.sleep(1)   ← yield to event loop
      return result

  asyncio.run(main())          ← run the event loop once
  await asyncio.gather(c1, c2) ← run coroutines concurrently
  asyncio.create_task(coro)    ← schedule without waiting yet
"""
print(summary)
