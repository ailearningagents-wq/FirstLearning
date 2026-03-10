"""
=============================================================
GENERATIVE AI / ML FOUNDATIONS
Topic 21: Visualization — Matplotlib & Seaborn
=============================================================

Install: pip install matplotlib seaborn

WHY VISUALIZATION FOR AI?
---------------------------
• Understand data distributions before training.
• Monitor training (loss / accuracy curves).
• Inspect model predictions vs actuals.
• Communicate results to stakeholders.

Note: This module runs in NON-INTERACTIVE (Agg) mode so it works
in terminals / notebooks / CI pipelines. All figures are saved to
a temp directory and the paths are printed.

COVERED:
  1. Line plots (training curves)
  2. Scatter plots (data exploration)
  3. Bar charts (feature importance)
  4. Histograms & KDE (distributions)
  5. Heatmaps (correlation)
  6. Subplots / figure layout
  7. Seaborn statistical plots
"""

import os
import tempfile
import numpy as np

# ── Use non-interactive backend BEFORE importing pyplot ───────────
import matplotlib
matplotlib.use("Agg")             # render to file, not screen
import matplotlib.pyplot as plt

try:
    import seaborn as sns
    SEABORN = True
    sns.set_theme(style="whitegrid", palette="muted")
except ImportError:
    SEABORN = False
    print("seaborn not installed (pip install seaborn) — skipping seaborn plots")

OUTDIR = tempfile.mkdtemp(prefix="py_viz_")
print(f"Figures will be saved to: {OUTDIR}")

np.random.seed(42)


# ─────────────────────────────────────────────
# 1. LINE PLOT — Training & Validation Curves
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("1. LINE PLOT — Training / Validation Loss")
print("=" * 55)

epochs = np.arange(1, 51)
train_loss = 2.5 * np.exp(-0.1 * epochs) + 0.05 * np.random.randn(50)
val_loss   = 2.8 * np.exp(-0.09 * epochs) + 0.08 * np.random.randn(50) + 0.1

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(epochs, train_loss, label="Train loss", color="steelblue", linewidth=2)
ax.plot(epochs, val_loss,   label="Val loss",   color="tomato",    linewidth=2, linestyle="--")
ax.axhline(y=0.3, color="gray", linestyle=":", linewidth=1.5, label="Target")
ax.set_xlabel("Epoch")
ax.set_ylabel("Loss")
ax.set_title("Training & Validation Loss")
ax.legend()
ax.grid(True, alpha=0.3)

path = os.path.join(OUTDIR, "01_training_loss.png")
fig.savefig(path, dpi=100, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {path}")

# What to look for:
#   • Train loss should decrease — if not, LR is too low / model too small
#   • Val loss diverging from train = overfitting → add dropout/regularisation
#   • Both stagnate early = underfitting → larger model or longer training


# ─────────────────────────────────────────────
# 2. SCATTER PLOT — Data Exploration
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. SCATTER PLOT — Cluster Visualization")
print("=" * 55)

# Simulate 3-class embeddings in 2D (e.g. after t-SNE / PCA)
n = 150
classes = ["cat", "dog", "bird"]
colours = ["#e41a1c", "#377eb8", "#4daf4a"]
X_clusters = []
labels = []
for i, cls in enumerate(classes):
    centre = np.array([i * 3, i * 2])
    X_clusters.append(centre + 0.8 * np.random.randn(n // 3, 2))
    labels.extend([cls] * (n // 3))

X_all = np.vstack(X_clusters)
y_labels = np.array(labels)

fig, ax = plt.subplots(figsize=(7, 5))
for cls, col in zip(classes, colours):
    mask = y_labels == cls
    ax.scatter(X_all[mask, 0], X_all[mask, 1],
               label=cls, color=col, alpha=0.7, s=40)
ax.set_title("2-D Embeddings (simulated t-SNE)")
ax.set_xlabel("Dimension 1")
ax.set_ylabel("Dimension 2")
ax.legend(title="Class")

path = os.path.join(OUTDIR, "02_scatter_embeddings.png")
fig.savefig(path, dpi=100, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {path}")


# ─────────────────────────────────────────────
# 3. BAR CHART — Feature Importance
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. BAR CHART — Feature Importance")
print("=" * 55)

features = ["area_sqft", "neighbourhood", "bedrooms", "garage", "age_years"]
importance = np.array([0.45, 0.25, 0.15, 0.10, 0.05])
order = np.argsort(importance)[::-1]   # sort descending

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar([features[i] for i in order],
              importance[order],
              color=["#2196F3" if i == 0 else "#90CAF9" for i in range(len(features))])
ax.set_title("Random Forest — Feature Importance")
ax.set_ylabel("Importance")
ax.set_xlabel("Feature")
for bar, val in zip(bars, importance[order]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
            f"{val:.2f}", ha="center", va="bottom", fontsize=9)

path = os.path.join(OUTDIR, "03_feature_importance.png")
fig.savefig(path, dpi=100, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {path}")


# ─────────────────────────────────────────────
# 4. HISTOGRAMS & KDE — Distributions
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. HISTOGRAMS & KDE")
print("=" * 55)

model_outputs_class0 = np.random.beta(2, 5, 300)   # skewed low
model_outputs_class1 = np.random.beta(5, 2, 300)   # skewed high

fig, axes = plt.subplots(1, 2, figsize=(11, 4))

# Left: histogram
axes[0].hist(model_outputs_class0, bins=30, alpha=0.6, color="tomato",    label="Negative")
axes[0].hist(model_outputs_class1, bins=30, alpha=0.6, color="steelblue", label="Positive")
axes[0].set_title("Classifier Output Distributions")
axes[0].set_xlabel("Predicted Probability")
axes[0].set_ylabel("Count")
axes[0].legend()

# Right: KDE using matplotlib
from scipy.stats import gaussian_kde   # type: ignore
for data, col, lbl in [(model_outputs_class0, "tomato", "Negative"),
                        (model_outputs_class1, "steelblue", "Positive")]:
    kde = gaussian_kde(data)
    xs  = np.linspace(0, 1, 300)
    axes[1].plot(xs, kde(xs), label=lbl, color=col, linewidth=2)
    axes[1].fill_between(xs, kde(xs), alpha=0.15, color=col)
axes[1].set_title("KDE — Probability Density")
axes[1].set_xlabel("Predicted Probability")
axes[1].legend()

plt.tight_layout()
path = os.path.join(OUTDIR, "04_distributions.png")
fig.savefig(path, dpi=100, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {path}")


# ─────────────────────────────────────────────
# 5. HEATMAP — Correlation Matrix
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. HEATMAP — Correlation Matrix")
print("=" * 55)

# Synthetic feature correlation
area      = np.random.randint(600, 3000, 200).astype(float)
bedrooms  = np.clip(area / 600 + np.random.randn(200), 1, 6)
age       = np.random.uniform(0, 40, 200)
price     = 0.4 * area + 50 * bedrooms - 2 * age + 50 * np.random.randn(200)
garage    = (area > 1500).astype(float)

import pandas as pd
df_corr = pd.DataFrame({
    "area":     area,
    "bedrooms": bedrooms,
    "age":      age,
    "garage":   garage,
    "price":    price,
})
corr = df_corr.corr()

fig, ax = plt.subplots(figsize=(6, 5))
if SEABORN:
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdYlGn",
                center=0, square=True, ax=ax, linewidths=0.5)
else:
    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr))); ax.set_xticklabels(corr.columns, rotation=45)
    ax.set_yticks(range(len(corr))); ax.set_yticklabels(corr.columns)
    for i in range(len(corr)):
        for j in range(len(corr)):
            ax.text(j, i, f"{corr.values[i,j]:.2f}", ha="center", va="center", fontsize=8)
    plt.colorbar(im, ax=ax)
ax.set_title("Correlation Matrix")
plt.tight_layout()

path = os.path.join(OUTDIR, "05_correlation_heatmap.png")
fig.savefig(path, dpi=100, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {path}")
print(f"\nTop correlations with price:\n{corr['price'].sort_values(ascending=False).round(3)}")


# ─────────────────────────────────────────────
# 6. SUBPLOTS — Model Evaluation Dashboard
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("6. SUBPLOTS — Model Evaluation Dashboard")
print("=" * 55)

from matplotlib.gridspec import GridSpec

fig = plt.figure(figsize=(13, 9))
fig.suptitle("Model Evaluation Dashboard", fontsize=14, fontweight="bold")
gs = GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35)

# (A) Loss curves
ax_a = fig.add_subplot(gs[0, 0:2])
eps   = np.arange(1, 101)
t_loss = 1.8 / eps**0.5 + 0.05 * np.random.randn(100)
v_loss = 2.0 / eps**0.5 + 0.07 * np.random.randn(100) + 0.08
ax_a.plot(eps, t_loss, label="Train", color="steelblue")
ax_a.plot(eps, v_loss, label="Val",   color="tomato", linestyle="--")
ax_a.set_title("(A) Loss Curves"); ax_a.set_xlabel("Epoch"); ax_a.legend()

# (B) Accuracy curves
ax_b = fig.add_subplot(gs[0, 2])
t_acc = 1 - 0.6 * np.exp(-eps / 20) + 0.01 * np.random.randn(100)
v_acc = 1 - 0.7 * np.exp(-eps / 22) + 0.015 * np.random.randn(100)
ax_b.plot(eps, t_acc, color="steelblue"); ax_b.plot(eps, v_acc, color="tomato", linestyle="--")
ax_b.set_title("(B) Accuracy"); ax_b.set_xlabel("Epoch"); ax_b.set_ylim(0.3, 1.05)

# (C) Confusion matrix
ax_c = fig.add_subplot(gs[1, 0])
cm   = np.array([[82, 18], [12, 88]])
im   = ax_c.imshow(cm, cmap="Blues")
for i in range(2):
    for j in range(2):
        ax_c.text(j, i, str(cm[i, j]), ha="center", va="center",
                  color="white" if cm[i, j] > 50 else "black", fontsize=14)
ax_c.set_xticks([0,1]); ax_c.set_xticklabels(["Pred 0","Pred 1"])
ax_c.set_yticks([0,1]); ax_c.set_yticklabels(["True 0","True 1"])
ax_c.set_title("(C) Confusion Matrix")

# (D) Precision-Recall curve (simulated)
ax_d = fig.add_subplot(gs[1, 1])
recall    = np.linspace(0, 1, 50)
precision = 1 - 0.3 * recall ** 2 + 0.02 * np.random.randn(50)
precision = np.clip(precision, 0, 1)
ax_d.plot(recall, precision, color="#9C27B0", linewidth=2)
ax_d.fill_between(recall, precision, alpha=0.15, color="#9C27B0")
ax_d.set_title("(D) Precision-Recall"); ax_d.set_xlabel("Recall"); ax_d.set_ylabel("Precision")

# (E) Residual plot (regression)
ax_e = fig.add_subplot(gs[1, 2])
y_pred  = np.linspace(100, 900, 80)
residuals = 30 * np.random.randn(80)
ax_e.scatter(y_pred, residuals, alpha=0.5, color="teal", s=20)
ax_e.axhline(0, color="red", linestyle="--", linewidth=1)
ax_e.set_title("(E) Residuals"); ax_e.set_xlabel("Predicted"); ax_e.set_ylabel("Error")

path = os.path.join(OUTDIR, "06_dashboard.png")
fig.savefig(path, dpi=100, bbox_inches="tight")
plt.close(fig)
print(f"Saved → {path}")


# ─────────────────────────────────────────────
# 7. SEABORN — Statistical Plots
# ─────────────────────────────────────────────

if SEABORN:
    print("\n" + "=" * 55)
    print("7. SEABORN — Statistical Visualization")
    print("=" * 55)

    model_name = np.repeat(["Linear Reg", "Ridge", "Random Forest", "XGBoost"], 20)
    rmse_vals  = np.concatenate([
        np.random.normal(85, 10, 20),
        np.random.normal(80, 8,  20),
        np.random.normal(60, 6,  20),
        np.random.normal(55, 5,  20),
    ])
    df_box = pd.DataFrame({"Model": model_name, "RMSE": rmse_vals})

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Box plot
    sns.boxplot(data=df_box, x="Model", y="RMSE", ax=axes[0], palette="Set2")
    axes[0].set_title("RMSE Comparison — 20 Runs")
    axes[0].tick_params(axis="x", rotation=15)

    # Violin plot
    sns.violinplot(data=df_box, x="Model", y="RMSE", ax=axes[1], palette="Set2", inner="quartile")
    axes[1].set_title("RMSE Distribution — Violin")
    axes[1].tick_params(axis="x", rotation=15)

    plt.tight_layout()
    path = os.path.join(OUTDIR, "07_seaborn_box_violin.png")
    fig.savefig(path, dpi=100, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {path}")
else:
    print("\n[SKIPPED] seaborn not installed")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
print(f"""
  All figures saved to: {OUTDIR}

  MATPLOTLIB ESSENTIALS:
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, y, label="...", color="steelblue")
    ax.scatter(x, y, alpha=0.6, s=40)
    ax.bar(labels, values)
    ax.hist(data, bins=30)
    ax.set_title/xlabel/ylabel/legend()
    fig.savefig("out.png", dpi=100, bbox_inches="tight")
    plt.close(fig)   ← always close to free memory

  HEADLESS / CI MODE:
    import matplotlib; matplotlib.use("Agg")
    ← must be called BEFORE import matplotlib.pyplot

  SEABORN:
    sns.set_theme(style="whitegrid")
    sns.heatmap(corr, annot=True, cmap="RdYlGn")
    sns.boxplot(data=df, x="model", y="score")
    sns.violinplot(...)

  BEST PRACTICES FOR AI:
    • Always plot loss curves — catch overfitting early
    • Plot confusion matrix for classification
    • Plot residuals for regression (should be ~N(0,σ))
    • Use KDE to check if train/test distributions match
    • Correlation heatmap before feature selection
""")
