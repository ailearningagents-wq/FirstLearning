"""
=============================================================
GENERATIVE AI / ML FOUNDATIONS
Topic 22: Scikit-learn — Machine Learning
=============================================================

Install: pip install scikit-learn

THE SCIKIT-LEARN PHILOSOPHY:
------------------------------
Every model follows the same 3-method API:
  model.fit(X_train, y_train)      ← learn from data
  model.predict(X_test)            ← make predictions
  model.score(X_test, y_test)      ← evaluate (accuracy / R²)

This uniformity lets you swap models with ONE line of code.

COVERED:
  1. Datasets & train/test split
  2. Preprocessing (scaling, encoding)
  3. Classification (Logistic, RandomForest, SVM)
  4. Regression (Linear, Ridge, SVR)
  5. Pipeline (chain steps cleanly)
  6. Cross-validation & hyperparameter tuning
  7. Model evaluation (metrics, confusion matrix, ROC)
  8. Feature importance & selection
"""

import numpy as np
import warnings
warnings.filterwarnings("ignore")

from sklearn.datasets import (
    make_classification, make_regression, load_iris
)
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV
)
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, LabelEncoder, OneHotEncoder
)
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression, LinearRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.svm import SVC
from sklearn.metrics import (
    accuracy_score, classification_report,
    confusion_matrix, mean_squared_error, r2_score
)
import sklearn
print("scikit-learn version:", sklearn.__version__)


# ─────────────────────────────────────────────
# 1. DATASETS & TRAIN/TEST SPLIT
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("1. DATASETS & TRAIN/TEST SPLIT")
print("=" * 55)

# Synthetic classification dataset
X_cls, y_cls = make_classification(
    n_samples      = 1000,
    n_features     = 10,
    n_informative  = 6,    # only 6 features matter
    n_redundant    = 2,
    n_classes      = 3,
    random_state   = 42,
)
print(f"Classification: X={X_cls.shape}, classes={np.unique(y_cls)}")

# Synthetic regression dataset
X_reg, y_reg = make_regression(
    n_samples    = 500,
    n_features   = 8,
    n_informative= 5,
    noise        = 20,
    random_state = 42,
)
print(f"Regression:     X={X_reg.shape}, y range=[{y_reg.min():.0f}, {y_reg.max():.0f}]")

# 80/20 stratified split (stratify keeps class proportions)
X_tr, X_te, y_tr, y_te = train_test_split(
    X_cls, y_cls, test_size=0.2, random_state=42, stratify=y_cls
)
print(f"\nSplit: train={len(X_tr)}, test={len(X_te)}")
print(f"Train class dist : {dict(zip(*np.unique(y_tr, return_counts=True)))}")
print(f"Test  class dist : {dict(zip(*np.unique(y_te, return_counts=True)))}")

# Real dataset — Iris (classic 3-class classification)
iris = load_iris()
print(f"\nIris: {iris.data.shape} samples, features={iris.feature_names}")
print(f"Classes: {iris.target_names.tolist()}")


# ─────────────────────────────────────────────
# 2. PREPROCESSING
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. PREPROCESSING")
print("=" * 55)

# StandardScaler — zero mean, unit variance
scaler = StandardScaler()
X_tr_scaled = scaler.fit_transform(X_tr)   # fit on TRAIN only
X_te_scaled = scaler.transform(X_te)       # apply same transform to test

print(f"Before scaling — mean: {X_tr[:, 0].mean():.2f}, std: {X_tr[:, 0].std():.2f}")
print(f"After  scaling — mean: {X_tr_scaled[:, 0].mean():.2f}, std: {X_tr_scaled[:, 0].std():.2f}")

# MinMaxScaler — scale to [0, 1]
mm = MinMaxScaler()
X_mm = mm.fit_transform(X_tr)
print(f"MinMax range   — min: {X_mm.min():.2f}, max: {X_mm.max():.2f}")

# LabelEncoder — string labels → integers
labels = ["cat", "dog", "bird", "cat", "dog"]
le = LabelEncoder()
encoded = le.fit_transform(labels)
print(f"\nLabelEncoder: {labels} → {encoded}")
print(f"Classes: {le.classes_}")

# OneHotEncoder — categorical → binary columns
cat_data = np.array([["red"], ["blue"], ["green"], ["red"]])
ohe = OneHotEncoder(sparse_output=False)
ohe_result = ohe.fit_transform(cat_data)
print(f"\nOneHot: {cat_data.ravel()} → \n{ohe_result}")
print(f"Categories: {ohe.categories_}")


# ─────────────────────────────────────────────
# 3. CLASSIFICATION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. CLASSIFICATION")
print("=" * 55)

models_cls = {
    "Logistic Regression": LogisticRegression(max_iter=500, random_state=42),
    "Random Forest (100)": RandomForestClassifier(n_estimators=100, random_state=42),
    "SVM (RBF kernel)":    SVC(kernel="rbf", C=1.0, probability=True, random_state=42),
}

results_cls = {}
for name, model in models_cls.items():
    model.fit(X_tr_scaled, y_tr)
    acc = model.score(X_te_scaled, y_te)
    results_cls[name] = acc
    print(f"  {name:<28} accuracy = {acc:.3f}")

best_cls = max(results_cls, key=results_cls.get)
print(f"\nBest: {best_cls}  ({results_cls[best_cls]:.3f})")

# Detailed report for the best model
best_model = models_cls[best_cls]
y_pred = best_model.predict(X_te_scaled)
print(f"\nClassification Report ({best_cls}):")
print(classification_report(y_te, y_pred, digits=3))

# Confusion matrix
cm = confusion_matrix(y_te, y_pred)
print(f"Confusion matrix:\n{cm}")


# ─────────────────────────────────────────────
# 4. REGRESSION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. REGRESSION")
print("=" * 55)

X_r_tr, X_r_te, y_r_tr, y_r_te = train_test_split(
    X_reg, y_reg, test_size=0.2, random_state=42
)
scaler_r = StandardScaler()
X_r_tr_s = scaler_r.fit_transform(X_r_tr)
X_r_te_s = scaler_r.transform(X_r_te)

models_reg = {
    "Linear Regression":  LinearRegression(),
    "Ridge (α=1)":        Ridge(alpha=1.0),
    "Gradient Boosting":  GradientBoostingRegressor(n_estimators=100, random_state=42),
}

for name, model in models_reg.items():
    model.fit(X_r_tr_s, y_r_tr)
    y_pred  = model.predict(X_r_te_s)
    rmse    = mean_squared_error(y_r_te, y_pred) ** 0.5
    r2      = r2_score(y_r_te, y_pred)
    print(f"  {name:<25} RMSE={rmse:.1f}  R²={r2:.4f}")


# ─────────────────────────────────────────────
# 5. PIPELINE — Chain Steps Cleanly
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. PIPELINE")
print("=" * 55)

# A Pipeline ensures:
#   • Scaler is fit only on training data
#   • The same transform is applied consistently at test time
#   • No data leakage
iris_X, iris_y = iris.data, iris.target
X_i_tr, X_i_te, y_i_tr, y_i_te = train_test_split(
    iris_X, iris_y, test_size=0.2, random_state=42, stratify=iris_y
)

pipe = Pipeline([
    ("scaler",    StandardScaler()),
    ("classifier", RandomForestClassifier(n_estimators=50, random_state=42)),
])

pipe.fit(X_i_tr, y_i_tr)
acc = pipe.score(X_i_te, y_i_te)
print(f"Iris pipeline accuracy: {acc:.3f}")

# Predict with the full pipeline — scaler is applied automatically
sample = X_i_te[:3]
preds  = pipe.predict(sample)
probs  = pipe.predict_proba(sample)
for i, (pred, prob) in enumerate(zip(preds, probs)):
    print(f"  Sample {i}: predicted '{iris.target_names[pred]}'  "
          f"probs={prob.round(3)}")

# Pipeline works with GridSearchCV too
param_grid = {"classifier__n_estimators": [25, 50, 100],
              "classifier__max_depth":    [None, 5, 10]}
grid = GridSearchCV(pipe, param_grid, cv=5, scoring="accuracy", n_jobs=-1)
grid.fit(X_i_tr, y_i_tr)
print(f"\nGridSearchCV best params : {grid.best_params_}")
print(f"GridSearchCV best CV acc : {grid.best_score_:.3f}")
print(f"Test accuracy (best)     : {grid.score(X_i_te, y_i_te):.3f}")


# ─────────────────────────────────────────────
# 6. CROSS-VALIDATION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("6. CROSS-VALIDATION")
print("=" * 55)

# 5-fold CV on Iris with RandomForest
cv_pipe = Pipeline([("scaler", StandardScaler()),
                    ("clf",    RandomForestClassifier(n_estimators=50, random_state=42))])
cv_scores = cross_val_score(cv_pipe, iris_X, iris_y, cv=5, scoring="accuracy")
print(f"5-fold CV scores : {cv_scores.round(3)}")
print(f"Mean ± std       : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

# Why CV?  A single train/test split can get lucky.
# 5-fold CV uses ALL data for both training and evaluation.


# ─────────────────────────────────────────────
# 7. MODEL EVALUATION METRICS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. MODEL EVALUATION METRICS")
print("=" * 55)

from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import label_binarize

# Binary classification metrics
X_bin, y_bin = make_classification(n_samples=500, n_features=8, n_classes=2,
                                    random_state=42)
X_b_tr, X_b_te, y_b_tr, y_b_te = train_test_split(X_bin, y_bin, test_size=0.2,
                                                     random_state=42)
lr = LogisticRegression(max_iter=300)
lr.fit(X_b_tr, y_b_tr)
y_b_pred      = lr.predict(X_b_te)
y_b_prob      = lr.predict_proba(X_b_te)[:, 1]

tp = np.sum((y_b_pred == 1) & (y_b_te == 1))
fp = np.sum((y_b_pred == 1) & (y_b_te == 0))
tn = np.sum((y_b_pred == 0) & (y_b_te == 0))
fn = np.sum((y_b_pred == 0) & (y_b_te == 1))

precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall    = tp / (tp + fn) if (tp + fn) > 0 else 0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
auc       = roc_auc_score(y_b_te, y_b_prob)

print(f"Accuracy  : {accuracy_score(y_b_te, y_b_pred):.3f}")
print(f"Precision : {precision:.3f}   (of all Predicted-Positive, how many correct?)")
print(f"Recall    : {recall:.3f}   (of all Actual-Positive, how many found?)")
print(f"F1-Score  : {f1:.3f}   (harmonic mean of Precision & Recall)")
print(f"ROC-AUC   : {auc:.3f}   (1.0=perfect, 0.5=random)")


# ─────────────────────────────────────────────
# 8. FEATURE IMPORTANCE
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("8. FEATURE IMPORTANCE")
print("=" * 55)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_tr_scaled, y_tr)
importances = rf.feature_importances_
feature_names = [f"f{i}" for i in range(X_cls.shape[1])]

# Sort by importance
order = np.argsort(importances)[::-1]
print("Feature importances (RandomForest):")
for i in order:
    bar = "█" * int(importances[i] * 100)
    print(f"  {feature_names[i]}: {bar:<20} {importances[i]:.3f}")

# SelectFromModel — keep only important features
from sklearn.feature_selection import SelectFromModel
selector = SelectFromModel(rf, threshold="mean", prefit=True)
X_selected = selector.transform(X_te_scaled)
print(f"\nOriginal features  : {X_te_scaled.shape[1]}")
print(f"Selected features  : {X_selected.shape[1]}")
mask = selector.get_support()
kept = [feature_names[i] for i, m in enumerate(mask) if m]
print(f"Kept: {kept}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
print("""
  CORE API (every model):
    model.fit(X_train, y_train)
    model.predict(X_test)
    model.score(X_test, y_test)
    model.predict_proba(X_test)   ← classifiers only

  PREPROCESSING:
    StandardScaler().fit_transform(X_train)    → zero mean, unit var
    MinMaxScaler().fit_transform(X_train)      → [0, 1]
    OneHotEncoder(sparse_output=False)         → binary columns

  PIPELINE (prevents data leakage!):
    pipe = Pipeline([("scaler", StandardScaler()),
                     ("clf",   LogisticRegression())])
    pipe.fit(X_train, y_train)
    pipe.predict(X_test)

  CROSS-VALIDATION:
    cross_val_score(pipe, X, y, cv=5)

  GRID SEARCH:
    GridSearchCV(pipe, {"clf__C": [0.1, 1, 10]}, cv=5)

  METRICS (classification):
    accuracy_score / precision / recall / f1 / roc_auc_score
    classification_report(y_true, y_pred)
    confusion_matrix(y_true, y_pred)

  METRICS (regression):
    mean_squared_error → RMSE = sqrt(MSE)
    r2_score (1.0=perfect, 0.0=guessing mean, <0=worse than mean)
""")
