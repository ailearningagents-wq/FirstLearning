"""
=============================================================
GENERATIVE AI / ML FOUNDATIONS
Topic 23: Neural Networks — From Scratch & PyTorch
=============================================================

Install (optional, for PyTorch section): pip install torch

WHY UNDERSTAND NEURAL NETS FROM SCRATCH?
------------------------------------------
Before using PyTorch/TensorFlow, understanding the math behind:
  • Forward pass  — input → output (matrix multiply + activate)
  • Loss function — how wrong are we?
  • Backward pass — compute gradients via chain rule
  • Optimizer     — update weights to reduce loss

helps you debug training, choose architectures, and understand
what libraries like PyTorch do under the hood.

COVERED:
  1. Perceptron — the basic unit
  2. Multi-layer neural network with NumPy (from scratch)
  3. Activation functions
  4. Loss functions
  5. Gradient descent & backpropagation
  6. PyTorch basics (tensors, autograd, nn.Module, training loop)
  7. Common architectures overview
"""

import numpy as np


# ─────────────────────────────────────────────
# 1. THE PERCEPTRON — Basic Unit
# ─────────────────────────────────────────────

print("=" * 55)
print("1. PERCEPTRON — Basic Unit")
print("=" * 55)

# A perceptron computes:  output = activate(W·x + b)
# W = weights  (learned)
# x = input features
# b = bias     (learned)

class Perceptron:
    """Single neuron — binary classifier."""
    def __init__(self, n_inputs: int, lr: float = 0.1):
        rng = np.random.default_rng(42)
        self.W  = rng.standard_normal(n_inputs) * 0.01
        self.b  = 0.0
        self.lr = lr

    def _sigmoid(self, z):
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def predict_prob(self, x):
        return self._sigmoid(np.dot(self.W, x) + self.b)

    def predict(self, x):
        return int(self.predict_prob(x) >= 0.5)

    def train_step(self, x, y):
        """One gradient descent step (binary cross-entropy loss)."""
        y_hat = self.predict_prob(x)
        error = y_hat - y                      # gradient of BCE w.r.t output
        self.W -= self.lr * error * x
        self.b -= self.lr * error
        loss = -(y * np.log(y_hat + 1e-8) + (1 - y) * np.log(1 - y_hat + 1e-8))
        return float(loss)


# Train on AND gate
AND_X = np.array([[0,0],[0,1],[1,0],[1,1]], dtype=float)
AND_y = np.array([0, 0, 0, 1], dtype=float)

p = Perceptron(n_inputs=2, lr=0.5)
for epoch in range(50):
    for x, y in zip(AND_X, AND_y):
        p.train_step(x, y)

print("AND gate after 50 epochs:")
for x, y in zip(AND_X, AND_y):
    pred = p.predict(x)
    print(f"  {x.astype(int)} → predicted={pred}  actual={int(y)}  {'✓' if pred==int(y) else '✗'}")


# ─────────────────────────────────────────────
# 2. ACTIVATION FUNCTIONS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. ACTIVATION FUNCTIONS")
print("=" * 55)

z = np.array([-3.0, -1.0, 0.0, 1.0, 3.0])

def relu(z):    return np.maximum(0, z)
def leaky_relu(z, alpha=0.01): return np.where(z > 0, z, alpha * z)
def sigmoid(z): return 1 / (1 + np.exp(-np.clip(z, -500, 500)))
def tanh(z):    return np.tanh(z)
def softmax(z):
    e = np.exp(z - z.max())
    return e / e.sum()

print(f"Input z     : {z}")
print(f"ReLU        : {relu(z)}")
print(f"Leaky ReLU  : {leaky_relu(z).round(2)}")
print(f"Sigmoid     : {sigmoid(z).round(3)}")
print(f"Tanh        : {tanh(z).round(3)}")
print(f"Softmax     : {softmax(z).round(3)}  sum={softmax(z).sum():.1f}")

print("""
  WHEN TO USE:
    ReLU        → hidden layers in most networks (fast, works well)
    Leaky ReLU  → when ReLU neurons "die" (never activate)
    Sigmoid     → output layer for BINARY classification  (→ probability)
    Softmax     → output layer for MULTI-CLASS classification (→ probabilities)
    Tanh        → RNNs, normalised output in [-1, 1]
""")


# ─────────────────────────────────────────────
# 3. LOSS FUNCTIONS
# ─────────────────────────────────────────────

print("=" * 55)
print("3. LOSS FUNCTIONS")
print("=" * 55)

# Mean Squared Error (regression)
def mse_loss(y_true, y_pred):
    return np.mean((y_true - y_pred) ** 2)

# Binary Cross-Entropy (binary classification)
def bce_loss(y_true, y_pred):
    eps = 1e-8
    return -np.mean(y_true * np.log(y_pred + eps) + (1 - y_true) * np.log(1 - y_pred + eps))

# Categorical Cross-Entropy (multi-class classification)
def cce_loss(y_true_onehot, y_pred_probs):
    eps = 1e-8
    return -np.sum(y_true_onehot * np.log(y_pred_probs + eps))

y_true_reg  = np.array([3.0, 5.0, 2.5])
y_pred_good = np.array([3.1, 4.9, 2.4])
y_pred_bad  = np.array([1.0, 8.0, 5.0])

print(f"MSE (good pred): {mse_loss(y_true_reg, y_pred_good):.4f}")
print(f"MSE (bad pred) : {mse_loss(y_true_reg, y_pred_bad):.4f}")

y_b_true = np.array([1.0, 0.0, 1.0])
print(f"\nBCE (confident correct): {bce_loss(y_b_true, np.array([0.95, 0.05, 0.90])):.4f}")
print(f"BCE (uncertain)        : {bce_loss(y_b_true, np.array([0.50, 0.50, 0.50])):.4f}")
print(f"BCE (confident wrong)  : {bce_loss(y_b_true, np.array([0.05, 0.95, 0.10])):.4f}")


# ─────────────────────────────────────────────
# 4. NEURAL NETWORK FROM SCRATCH (NumPy)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. 2-LAYER NEURAL NET (NumPy, from scratch)")
print("=" * 55)

class TwoLayerNet:
    """
    Architecture:  input → Dense(hidden) → ReLU → Dense(output) → Sigmoid
    Loss:          Binary Cross-Entropy
    Optimizer:     Stochastic Gradient Descent (SGD)
    """
    def __init__(self, n_in: int, n_hidden: int, n_out: int, lr: float = 0.01):
        rng = np.random.default_rng(42)
        # He initialisation (good for ReLU)
        self.W1 = rng.standard_normal((n_in, n_hidden)) * np.sqrt(2/n_in)
        self.b1 = np.zeros(n_hidden)
        self.W2 = rng.standard_normal((n_hidden, n_out)) * np.sqrt(2/n_hidden)
        self.b2 = np.zeros(n_out)
        self.lr = lr

    def _relu(self, z):    return np.maximum(0, z)
    def _sigmoid(self, z): return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def forward(self, X):
        self.z1 = X @ self.W1 + self.b1        # (N, hidden)
        self.a1 = self._relu(self.z1)           # activation
        self.z2 = self.a1 @ self.W2 + self.b2  # (N, out)
        self.a2 = self._sigmoid(self.z2)        # output probability
        return self.a2

    def backward(self, X, y):
        N = X.shape[0]
        # --- Output layer gradient (BCE + Sigmoid combined) ---
        dz2 = self.a2 - y.reshape(-1, 1)       # (N, out)
        dW2 = self.a1.T @ dz2 / N
        db2 = dz2.mean(axis=0)

        # --- Hidden layer gradient (ReLU ′) ---
        dz1 = (dz2 @ self.W2.T) * (self.z1 > 0)  # ReLU derivative: 1 if z>0, else 0
        dW1 = X.T @ dz1 / N
        db1 = dz1.mean(axis=0)

        # --- SGD update ---
        self.W2 -= self.lr * dW2
        self.b2 -= self.lr * db2
        self.W1 -= self.lr * dW1
        self.b1 -= self.lr * db1

    def loss(self, X, y):
        y_hat = self.forward(X)
        eps   = 1e-8
        y_c   = y.reshape(-1, 1)
        return float(-np.mean(y_c * np.log(y_hat + eps) + (1 - y_c) * np.log(1 - y_hat + eps)))

    def predict(self, X):
        return (self.forward(X) >= 0.5).astype(int).ravel()

    def accuracy(self, X, y):
        return float(np.mean(self.predict(X) == y))


# Generate XOR dataset (cannot be solved by a single perceptron!)
from sklearn.datasets import make_classification
np.random.seed(42)
X_xor = np.array([[0,0],[0,1],[1,0],[1,1],[0,0],[0,1],[1,0],[1,1]], dtype=float)
y_xor = np.array([0,1,1,0,0,1,1,0],  dtype=float)   # XOR labels

net = TwoLayerNet(n_in=2, n_hidden=4, n_out=1, lr=0.5)
losses = []
for epoch in range(3000):
    net.forward(X_xor)
    net.backward(X_xor, y_xor)
    if epoch % 500 == 0:
        l = net.loss(X_xor, y_xor)
        a = net.accuracy(X_xor, y_xor)
        losses.append(l)
        print(f"  Epoch {epoch:4d}  loss={l:.4f}  accuracy={a:.2f}")

print("\nXOR predictions after training:")
for x, y in zip(X_xor[:4], y_xor[:4]):
    p = net.predict(x.reshape(1,-1))[0]
    print(f"  {x.astype(int)} XOR → pred={p}  actual={int(y)}  {'✓' if p==int(y) else '✗'}")


# ─────────────────────────────────────────────
# 5. GRADIENT DESCENT VARIANTS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. GRADIENT DESCENT VARIANTS")
print("=" * 55)

print("""
  BATCH GD      : use ALL training data to compute one gradient update.
                  Stable, but slow and requires GPU memory for big datasets.

  STOCHASTIC GD : one sample per update.
                  Fast, but noisy and may not converge well.

  MINI-BATCH GD : use B samples (batch_size=32 or 64 or 256).
                  Balance between stability and speed. ← most common.

  OPTIMIZERS that improve on plain SGD:
    Momentum      : accumulates a velocity vector to accelerate in
                    consistent gradient directions.
    RMSProp       : adapts learning rate per parameter by dividing by
                    a running average of gradient magnitudes.
    Adam          : combines Momentum + RMSProp. Default choice for
                    most deep learning work.

  LEARNING RATE:
    Too high → loss oscillates or explodes.
    Too low  → training is extremely slow.
    Schedulers: step decay, cosine annealing, warmup+decay.
""")


# ─────────────────────────────────────────────
# 6. PYTORCH BASICS
# ─────────────────────────────────────────────

print("=" * 55)
print("6. PYTORCH BASICS")
print("=" * 55)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH = True
    print(f"PyTorch version: {torch.__version__}")
except ImportError:
    TORCH = False
    print("PyTorch not installed (pip install torch)")
    print("Showing pseudocode / concepts instead.\n")

if TORCH:
    # ── Tensors ──────────────────────────────────
    print("\n--- Tensors ---")
    t = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    print(f"tensor:\n{t}")
    print(f"shape : {t.shape}   dtype: {t.dtype}")

    # From NumPy (zero-copy when possible)
    np_arr = np.array([1, 2, 3], dtype=np.float32)
    t_from_np = torch.from_numpy(np_arr)
    t_to_np   = t.numpy()
    print(f"from numpy  : {t_from_np}")
    print(f"to numpy    : {t_to_np}")

    # ── Autograd ─────────────────────────────────
    print("\n--- Autograd ---")
    x = torch.tensor([2.0], requires_grad=True)
    y = x ** 3 + 2 * x           # y = x³ + 2x
    y.backward()                  # dy/dx = 3x² + 2 = 14 at x=2
    print(f"x={x.item()}, y={y.item():.1f}, dy/dx={x.grad.item():.1f}  (expected 14)")

    # ── nn.Module ────────────────────────────────
    print("\n--- nn.Module: Build a network ---")

    class MLPClassifier(nn.Module):
        def __init__(self, n_in, n_hidden, n_out):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(n_in, n_hidden),
                nn.ReLU(),
                nn.Dropout(0.3),             # regularisation
                nn.Linear(n_hidden, n_hidden // 2),
                nn.ReLU(),
                nn.Linear(n_hidden // 2, n_out),
            )

        def forward(self, x):
            return self.net(x)

    model = MLPClassifier(n_in=10, n_hidden=64, n_out=3)
    print(model)
    total_params = sum(p.numel() for p in model.parameters())
    trainable    = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"\nTotal params   : {total_params}")
    print(f"Trainable      : {trainable}")

    # ── Training Loop ────────────────────────────
    print("\n--- Training Loop ---")
    from sklearn.datasets import make_classification
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    X_np, y_np = make_classification(n_samples=500, n_features=10, n_classes=3,
                                      n_informative=6, random_state=42)
    X_tr, X_te, y_tr, y_te = train_test_split(X_np, y_np, test_size=0.2, random_state=42)
    sc = StandardScaler(); X_tr = sc.fit_transform(X_tr); X_te = sc.transform(X_te)

    X_tr_t = torch.tensor(X_tr, dtype=torch.float32)
    y_tr_t = torch.tensor(y_tr, dtype=torch.long)
    X_te_t = torch.tensor(X_te, dtype=torch.float32)
    y_te_t = torch.tensor(y_te, dtype=torch.long)

    model     = MLPClassifier(10, 64, 3)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    for epoch in range(50):
        model.train()
        optimizer.zero_grad()
        logits = model(X_tr_t)
        loss   = criterion(logits, y_tr_t)
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0 or epoch == 49:
            model.eval()
            with torch.no_grad():
                val_logits = model(X_te_t)
                val_acc = (val_logits.argmax(1) == y_te_t).float().mean()
            print(f"  Epoch {epoch:2d} | loss={loss.item():.4f} | val_acc={val_acc.item():.3f}")

else:
    # Pseudocode for reference
    print("""
  --- PyTorch PSEUDOCODE (install: pip install torch) ---

  import torch, torch.nn as nn, torch.optim as optim

  # 1. Tensors
  x = torch.tensor([1.0, 2.0, 3.0], requires_grad=True)
  y = x.pow(2).sum()
  y.backward()            # compute gradients
  print(x.grad)           # dy/dx

  # 2. Build a model
  model = nn.Sequential(
      nn.Linear(10, 64), nn.ReLU(), nn.Dropout(0.3),
      nn.Linear(64, 3),
  )

  # 3. Training loop
  optimizer = optim.Adam(model.parameters(), lr=1e-3)
  criterion = nn.CrossEntropyLoss()

  for epoch in range(100):
      model.train()
      optimizer.zero_grad()
      loss = criterion(model(X_train), y_train)
      loss.backward()
      optimizer.step()
  """)


# ─────────────────────────────────────────────
# 7. COMMON ARCHITECTURES OVERVIEW
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. COMMON ARCHITECTURES — OVERVIEW")
print("=" * 55)
print("""
  ARCHITECTURE     │ KEY LAYER         │ USE CASE
  ─────────────────┼───────────────────┼───────────────────────────────
  MLP / FNN        │ nn.Linear + act   │ Tabular data, classification
  CNN              │ nn.Conv2d         │ Images, spatial patterns
  RNN / LSTM / GRU │ nn.LSTM           │ Sequential data (legacy)
  Transformer      │ nn.MultiheadAttn  │ Text, images, audio (SOTA)
  VAE              │ encoder + μ,σ     │ Generative models (images)
  GAN              │ generator+discrim │ Image/text generation
  Diffusion        │ UNet + noise sched│ SOTA image generation (DALL·E)
  BERT             │ Bidirectional Tx  │ Text understanding, embedding
  GPT              │ Causal Tx decoder │ Text generation (LLMs)

  ATTENTION IS ALL YOU NEED (Transformers):
    • Self-attention: each token attends to ALL other tokens
    • Scaled dot-product: score = (Q @ K.T) / √d_k
    • Softmax → weights → weighted sum of V
    • This replaces recurrence → fully parallelisable on GPUs
""")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("=" * 55)
print("SUMMARY")
print("=" * 55)
print("""
  NEURAL NET FROM SCRATCH:
    forward:  z = X @ W + b → a = relu(z) → output = sigmoid(z2)
    backward: chain rule → dL/dW = (dL/da) * (da/dz) * (dz/dW)
    update:   W -= lr * dL/dW

  PYTORCH WORKFLOW:
    1. Define model:  nn.Module with forward()
    2. Loss:          nn.CrossEntropyLoss() or nn.MSELoss()
    3. Optimizer:     optim.Adam(model.parameters(), lr=1e-3)
    4. Training loop:
         optimizer.zero_grad()
         loss = criterion(model(X), y)
         loss.backward()          ← compute gradients
         optimizer.step()         ← update weights

  KEY HYPERPARAMETERS:
    learning_rate   typical: 1e-3 (Adam), 1e-2 (SGD+momentum)
    batch_size      typical: 32, 64, 128, 256
    epochs          monitor val loss; use early stopping
    hidden_size     larger = more capacity = more risk of overfit
    dropout         0.3–0.5 for regularisation
""")
