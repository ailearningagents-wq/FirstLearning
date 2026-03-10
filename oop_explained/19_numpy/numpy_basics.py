"""
=============================================================
GENERATIVE AI / ML FOUNDATIONS
Topic 19: NumPy — Numerical Computing
=============================================================

Install: pip install numpy

WHY NumPy FOR AI?
------------------
• All machine learning happens with numbers (weights, pixels, tokens).
• Pure Python loops are ~100x slower than NumPy's C-backed vectorized ops.
• PyTorch, TensorFlow, Scikit-learn all sit on top of NumPy arrays.
• GPU programming (CUDA) mirrors NumPy's array API.

COVERED:
  1. Array creation & dtypes
  2. Shape, reshape, flatten
  3. Indexing & slicing (including fancy & boolean)
  4. Vectorized operations & broadcasting
  5. Linear algebra (dot, matmul, eig, svd)
  6. Random number generation (seeded for reproducibility)
  7. NumPy patterns critical for AI/ML
"""

import numpy as np

print("NumPy version:", np.__version__)


# ─────────────────────────────────────────────
# 1. ARRAY CREATION & DTYPES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("1. ARRAY CREATION & DTYPES")
print("=" * 55)

# From Python lists
a = np.array([1, 2, 3, 4, 5])
print(f"1D array   : {a}  dtype={a.dtype}")

# 2D array (matrix)
matrix = np.array([[1, 2, 3],
                   [4, 5, 6],
                   [7, 8, 9]], dtype=np.float32)  # float32 — GPU-friendly
print(f"2D matrix  :\n{matrix}")
print(f"dtype      : {matrix.dtype}")

# Factory functions
print("\n--- Factory functions ---")
print(f"zeros(3,3) :\n{np.zeros((3, 3))}")
print(f"ones(2,4)  : {np.ones((2, 4))}")
print(f"eye(3)     :\n{np.eye(3)}")                    # identity matrix
print(f"arange(0,1,0.2) : {np.arange(0, 1, 0.2)}")
print(f"linspace(0,1,5) : {np.linspace(0, 1, 5)}")    # equal-spaced points
print(f"full(3, 7) : {np.full(3, 7)}")

# dtype conversions
arr_int  = np.array([1, 2, 3])
arr_f32  = arr_int.astype(np.float32)
arr_bool = arr_int.astype(bool)
print(f"\nint64 → float32 : {arr_f32}")
print(f"int64 → bool    : {arr_bool}")


# ─────────────────────────────────────────────
# 2. SHAPE, RESHAPE, FLATTEN
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. SHAPE, RESHAPE, FLATTEN")
print("=" * 55)

x = np.arange(24)
print(f"Original (24,)   : {x}")
print(f"Reshape (4, 6)   :\n{x.reshape(4, 6)}")
print(f"Reshape (2,3,4)  shape: {x.reshape(2, 3, 4).shape}")

# -1 means "infer this dimension"
print(f"reshape(-1, 8)   : shape {x.reshape(-1, 8).shape}")

# Flatten vs ravel (ravel returns a view where possible)
img = np.array([[255, 0, 128], [64, 192, 32]])
print(f"\nImage shape : {img.shape}")
print(f"Flattened   : {img.flatten()}")    # always a copy
print(f"Ravelled    : {img.ravel()}")      # view if contiguous

# Expand / squeeze dimensions (critical when working with batches)
tensor = np.array([1.0, 2.0, 3.0])          # shape (3,)
expanded = np.expand_dims(tensor, axis=0)   # shape (1, 3) — add batch dim
squeezed = np.squeeze(expanded)             # back to (3,)
print(f"\nOriginal  : {tensor.shape}")
print(f"Expanded  : {expanded.shape}")
print(f"Squeezed  : {squeezed.shape}")


# ─────────────────────────────────────────────
# 3. INDEXING & SLICING
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. INDEXING & SLICING")
print("=" * 55)

m = np.array([[10, 20, 30],
              [40, 50, 60],
              [70, 80, 90]])

print(f"m[1, 2]       = {m[1, 2]}")           # 60
print(f"m[0, :]       = {m[0, :]}")            # first row
print(f"m[:, 1]       = {m[:, 1]}")            # second column
print(f"m[0:2, 1:3]   =\n{m[0:2, 1:3]}")      # 2×2 slice

# Fancy indexing (select arbitrary rows/cols)
rows = np.array([0, 2])
cols = np.array([1, 2])
print(f"fancy rows [0,2] =\n{m[rows, :]}")
print(f"fancy m[[0,2],[1,2]] = {m[rows, cols]}")

# Boolean / mask indexing
arr = np.array([3, -1, 4, -1, 5, 9, -2])
mask = arr > 0
print(f"\nOriginal : {arr}")
print(f"mask>0   : {mask}")
print(f"arr[mask]: {arr[mask]}")               # only positives
arr[arr < 0] = 0                               # replace negatives with 0
print(f"  clipped: {arr}")                     # ReLU-like operation!


# ─────────────────────────────────────────────
# 4. VECTORIZED OPERATIONS & BROADCASTING
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. VECTORIZED OPS & BROADCASTING")
print("=" * 55)

import time

# Speed comparison: loop vs vectorized
n = 1_000_000
data = np.random.rand(n)

start = time.perf_counter()
result_loop = [x ** 2 for x in data]
loop_time = time.perf_counter() - start

start = time.perf_counter()
result_np = data ** 2
np_time = time.perf_counter() - start

print(f"Loop time    : {loop_time:.4f}s")
print(f"NumPy time   : {np_time:.4f}s  ({loop_time/np_time:.0f}× faster)")

# Element-wise operations
a = np.array([1.0, 2.0, 3.0])
b = np.array([4.0, 5.0, 6.0])
print(f"\na + b  = {a + b}")
print(f"a * b  = {a * b}")
print(f"a ** 2 = {a ** 2}")
print(f"np.exp(a) = {np.exp(a).round(3)}")    # e^x — used in softmax

# Broadcasting: smaller array "stretches" to match larger shape
# Rule: dimensions align from the right; size-1 dims expand
A = np.array([[1, 2, 3],
              [4, 5, 6]])       # shape (2, 3)
v = np.array([10, 20, 30])     # shape (3,)  → broadcasts to (2, 3)
print(f"\nA + v (broadcast) =\n{A + v}")

# Add bias vector to each row (common in neural nets)
bias = np.array([[100], [200]])  # shape (2, 1)
print(f"A + col_bias =\n{A + bias}")

# Aggregations
arr = np.array([[1, 2, 3], [4, 5, 6]])
print(f"\nsum all   : {arr.sum()}")
print(f"sum axis0 : {arr.sum(axis=0)}")  # column sums
print(f"sum axis1 : {arr.sum(axis=1)}")  # row sums
print(f"mean      : {arr.mean():.2f}")
print(f"std       : {arr.std():.4f}")
print(f"argmax    : {arr.argmax()}")      # index of max (flattened)


# ─────────────────────────────────────────────
# 5. LINEAR ALGEBRA (the math behind AI)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. LINEAR ALGEBRA")
print("=" * 55)

# Dot product  (1D × 1D → scalar)
u = np.array([1, 2, 3])
v = np.array([4, 5, 6])
print(f"dot(u,v)     = {np.dot(u, v)}")    # 1*4 + 2*5 + 3*6 = 32

# Matrix multiplication:  (m×k) × (k×n) = (m×n)
W = np.array([[1, 0], [0, 1], [2, -1]], dtype=float)   # 3×2  weight matrix
x = np.array([[3], [4]], dtype=float)                  # 2×1  input vector
out = W @ x                                            # @ = matmul
print(f"W @ x (linear layer output):\n{out}")

# Transpose
print(f"\nW shape {W.shape}, W.T shape {W.T.shape}")

# Norms (used in regularization & loss)
vec = np.array([3.0, 4.0])
print(f"L2 norm (len) : {np.linalg.norm(vec)}")        # 5.0
print(f"L1 norm       : {np.linalg.norm(vec, ord=1)}")  # 7.0

# Determinant and inverse
A = np.array([[2, 1], [5, 3]], dtype=float)
print(f"\ndet(A)  = {np.linalg.det(A)}")
print(f"inv(A)  =\n{np.linalg.inv(A)}")
print(f"A @ inv = \n{(A @ np.linalg.inv(A)).round()}")   # ≈ identity

# Eigendecomposition (PCA, spectral methods)
cov = np.array([[4, 2], [2, 3]], dtype=float)
eigenvalues, eigenvectors = np.linalg.eig(cov)
print(f"\neigenvalues  : {eigenvalues.round(3)}")
print(f"eigenvectors :\n{eigenvectors.round(3)}")

# SVD — Singular Value Decomposition (used in NLP, compression, PCA)
M = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
U, S, Vt = np.linalg.svd(M)
print(f"\nSVD of 3×3 matrix — singular values: {S.round(3)}")
print(f"Rank (non-zero singular values): {np.sum(S > 1e-10)}")   # 2 → rank-2


# ─────────────────────────────────────────────
# 6. RANDOM NUMBER GENERATION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("6. RANDOM (seeded for reproducibility)")
print("=" * 55)

rng = np.random.default_rng(seed=42)    # modern API (recommended)

print(f"uniform [0,1)   : {rng.random(5).round(3)}")
print(f"normal (μ=0,σ=1): {rng.standard_normal(5).round(3)}")
print(f"integers 0-9    : {rng.integers(0, 10, size=8)}")
print(f"choice(['a','b','c']): {rng.choice(['a','b','c'], size=6)}")

# Shuffling (e.g. dataset batches)
arr = np.arange(10)
rng.shuffle(arr)
print(f"shuffled 0-9    : {arr}")

# Generate a synthetic classification dataset
np.random.seed(42)
n_samples = 100
X_class0 = np.random.randn(n_samples // 2, 2) + np.array([2, 2])   # cluster at (2,2)
X_class1 = np.random.randn(n_samples // 2, 2) + np.array([-2, -2]) # cluster at (-2,-2)
X = np.vstack([X_class0, X_class1])
y = np.array([0] * 50 + [1] * 50)
print(f"\nSynthetic dataset: X.shape={X.shape}, y.shape={y.shape}")
print(f"Class counts: 0={np.sum(y==0)}, 1={np.sum(y==1)}")


# ─────────────────────────────────────────────
# 7. KEY AI/ML PATTERNS IN NUMPY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. KEY AI/ML PATTERNS IN NUMPY")
print("=" * 55)

# --- Softmax (turns logits into probabilities) ---
def softmax(logits: np.ndarray) -> np.ndarray:
    exp = np.exp(logits - logits.max())   # subtract max → numerical stability
    return exp / exp.sum()

logits = np.array([2.0, 1.0, 0.5, -1.0])
probs  = softmax(logits)
print(f"Softmax logits→probs : {probs.round(3)}  sum={probs.sum():.2f}")

# --- ReLU (activation function) ---
def relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(0, x)

z = np.array([-3.0, -1.0, 0.0, 1.0, 3.0])
print(f"ReLU({z}) = {relu(z)}")

# --- Sigmoid ---
def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))

print(f"Sigmoid({z}) = {sigmoid(z).round(3)}")

# --- Cosine similarity (embeddings / RAG) ---
def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-10))

v1 = np.array([1.0, 2.0, 3.0])
v2 = np.array([1.0, 2.0, 3.0])   # identical → similarity = 1
v3 = np.array([-1.0, -2.0, -3.0]) # opposite → similarity = -1
print(f"\nCosine(v1, v2) = {cosine_sim(v1, v2):.3f}")
print(f"Cosine(v1, v3) = {cosine_sim(v1, v3):.3f}")

# --- One-hot encoding ---
def one_hot(labels: np.ndarray, n_classes: int) -> np.ndarray:
    out = np.zeros((len(labels), n_classes))
    out[np.arange(len(labels)), labels] = 1
    return out

labels = np.array([0, 2, 1, 2])
oh = one_hot(labels, 3)
print(f"\nOne-hot encoded:\n{oh}")

# --- Normalize (zero mean, unit variance) ---
data = np.array([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
normalized = (data - data.mean()) / data.std()
print(f"\nNormalized: {normalized.round(3)}")

# --- Batch matrix multiply (batch of logits → probs) ---
# Shape (B, T, d_model) × (d_model, d_k) in transformer attention
B, T, d = 2, 3, 4
batch = np.random.randn(B, T, d)
W_proj = np.random.randn(d, 2)
output = batch @ W_proj     # shape (B, T, 2)
print(f"\nBatch matmul: ({B},{T},{d}) @ ({d},2) = {output.shape}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
print("""
  CREATION:   np.array(), zeros, ones, eye, arange, linspace
  SHAPE:      .shape, .reshape(-1,n), .flatten(), expand_dims()
  INDEXING:   a[1,2], a[:, 0], a[mask], a[[0,2], :]
  OPS:        +, -, *, /, ** — all element-wise; @  for matmul
  BROADCAST:  shapes align from right; size-1 dims expand
  LINALG:     np.dot, @, np.linalg.norm/inv/eig/svd
  RANDOM:     rng = np.random.default_rng(seed=42)
  DTYPE:      use float32 for GPU/ML models (half the memory of float64)

  AI PATTERNS:
    softmax: exp(x) / Σexp(x)  → probabilities
    relu:    max(0, x)          → non-linearity
    sigmoid: 1/(1+e^-x)        → binary probability
    cosine_sim = dot(a,b) / (|a|·|b|)   → embedding similarity
    one_hot: np.zeros((n,C)); out[range(n), labels] = 1
""")
