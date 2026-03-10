"""
=============================================================
GENERATIVE AI / ML FOUNDATIONS
Topic 20: Pandas — Data Analysis & Manipulation
=============================================================

Install: pip install pandas

WHY PANDAS FOR AI?
-------------------
• Real-world ML starts with messy tabular data (CSVs, databases).
• Pandas lets you explore, clean, and transform data before feeding
  it into a model.
• "Data scientists spend 80% of time cleaning data" — Pandas is why
  that number isn't 99%.

COVERED:
  1. Series
  2. DataFrame creation & inspection
  3. Selection: loc, iloc
  4. Filtering & boolean indexing
  5. Missing data handling
  6. GroupBy & aggregation
  7. Apply & map
  8. Merging / joining DataFrames
  9. Common ML data-prep patterns
"""

import pandas as pd
import numpy as np

print("Pandas version:", pd.__version__)


# ─────────────────────────────────────────────
# 1. SERIES
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("1. SERIES — 1D labelled array")
print("=" * 55)

s = pd.Series([10, 20, 30, 40, 50], name="scores")
print(s)

# Custom index
s_named = pd.Series({"Alice": 92, "Bob": 85, "Carol": 78}, name="grade")
print(f"\n{s_named}")
print(f"Alice's grade : {s_named['Alice']}")
print(f"Above 80      :\n{s_named[s_named > 80]}")

# Vectorized operations (same as NumPy)
print(f"\nMean  : {s_named.mean():.1f}")
print(f"Max   : {s_named.max()}")
print(f"Rank  :\n{s_named.rank(ascending=False).astype(int)}")


# ─────────────────────────────────────────────
# 2. DATAFRAME CREATION & INSPECTION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("2. DATAFRAME CREATION & INSPECTION")
print("=" * 55)

np.random.seed(42)

# Synthetic ML dataset: house price prediction
n = 12
df = pd.DataFrame({
    "id":           range(1, n + 1),
    "area_sqft":    np.random.randint(600, 3000, n),
    "bedrooms":     np.random.randint(1, 6, n),
    "age_years":    np.random.randint(0, 40, n),
    "garage":       np.random.choice([True, False], n),
    "neighbourhood":np.random.choice(["downtown", "suburbs", "rural"], n),
    "price_k":      np.random.randint(150, 900, n),
})
# Inject some missing values (realistic!)
df.loc[[2, 7], "age_years"] = np.nan
df.loc[[4], "bedrooms"]     = np.nan

print(df.head(6))
print(f"\nShape    : {df.shape}  ({df.shape[0]} rows × {df.shape[1]} cols)")
print(f"\ndtypes:\n{df.dtypes}")
print(f"\ndescribe:\n{df.describe().round(1)}")
print(f"\nisnull sum:\n{df.isnull().sum()}")


# ─────────────────────────────────────────────
# 3. SELECTION — loc, iloc
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("3. SELECTION — loc (label) & iloc (position)")
print("=" * 55)

# .loc — label-based (uses the DataFrame index labels)
print("Row 0, all cols:")
print(df.loc[0])

print("\nRows 0-2, select columns:")
print(df.loc[0:2, ["area_sqft", "bedrooms", "price_k"]])

# .iloc — position-based (like 2D numpy indexing)
print("\nFirst 3 rows, first 3 cols (iloc):")
print(df.iloc[0:3, 0:3])

# Single column
print(f"\nAll prices:\n{df['price_k'].values}")

# Multiple columns → DataFrame
print(f"\nFeatures subset:\n{df[['area_sqft', 'bedrooms', 'price_k']].head(4)}")


# ─────────────────────────────────────────────
# 4. FILTERING & BOOLEAN INDEXING
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("4. FILTERING")
print("=" * 55)

# Single condition
big_houses = df[df["area_sqft"] > 2000]
print(f"Houses >2000 sqft ({len(big_houses)} found):\n{big_houses[['area_sqft','bedrooms','price_k']]}")

# Multiple conditions  (use & | ~, not and/or/not)
downtown_large = df[(df["neighbourhood"] == "downtown") & (df["area_sqft"] > 1000)]
print(f"\nDowntown & >1000sqft ({len(downtown_large)} found):\n{downtown_large[['neighbourhood','area_sqft','price_k']]}")

# .query() — SQL-like string syntax
expensive = df.query("price_k > 600 and bedrooms >= 3")
print(f"\nExpensive (>600k, >=3BR) via .query():\n{expensive[['bedrooms','price_k']]}")

# .isin()
target = df[df["neighbourhood"].isin(["downtown", "suburbs"])]
print(f"\nDowntown or suburbs: {len(target)} rows")


# ─────────────────────────────────────────────
# 5. MISSING DATA
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("5. MISSING DATA HANDLING")
print("=" * 55)

print(f"Missing counts:\n{df.isnull().sum()}")

# Strategy 1: Drop rows with any NaN
df_dropped = df.dropna()
print(f"\nAfter dropna: {len(df_dropped)} rows (from {len(df)})")

# Strategy 2: Fill with median (better for skewed data)
df_filled = df.copy()
df_filled["age_years"].fillna(df_filled["age_years"].median(), inplace=True)
df_filled["bedrooms"].fillna(df_filled["bedrooms"].median(), inplace=True)
print(f"After fillna(median): {df_filled.isnull().sum().sum()} nulls remain")

# Strategy 3: Forward-fill / back-fill (for time series)
ts = pd.Series([1.0, np.nan, np.nan, 4.0, np.nan, 6.0])
print(f"\nTime-series with NaN : {ts.values}")
print(f"Forward-filled        : {ts.ffill().values}")
print(f"Interpolated         : {ts.interpolate().values}")

# Use the filled df going forward
df = df_filled


# ─────────────────────────────────────────────
# 6. GROUPBY & AGGREGATION
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("6. GROUPBY & AGGREGATION")
print("=" * 55)

# Mean price per neighbourhood
price_by_area = df.groupby("neighbourhood")["price_k"].agg(
    count="count", mean="mean", median="median", max="max"
).round(1)
print(f"Price by neighbourhood:\n{price_by_area}")

# Multiple columns
summary = df.groupby("neighbourhood").agg(
    avg_area=("area_sqft", "mean"),
    avg_rooms=("bedrooms", "mean"),
    avg_price=("price_k",  "mean"),
).round(1)
print(f"\nSummary by neighbourhood:\n{summary}")

# Value counts
print(f"\nNeighbourhood counts:\n{df['neighbourhood'].value_counts()}")
print(f"Garage distribution :\n{df['garage'].value_counts(normalize=True).round(2)}")


# ─────────────────────────────────────────────
# 7. APPLY & MAP (feature engineering)
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("7. APPLY & MAP — feature engineering")
print("=" * 55)

# .map — transform one column using a dict or function
neigh_code = {"downtown": 2, "suburbs": 1, "rural": 0}
df["neigh_code"] = df["neighbourhood"].map(neigh_code)
print(f"Encoded neighbourhood:\n{df[['neighbourhood','neigh_code']].head(5)}")

# .apply on a column
df["price_tier"] = df["price_k"].apply(
    lambda p: "high" if p > 600 else ("mid" if p > 350 else "low")
)
print(f"\nPrice tier:\n{df[['price_k','price_tier']].head(6)}")

# .apply on rows (axis=1)
df["price_per_sqft"] = df.apply(
    lambda row: round(row["price_k"] * 1000 / row["area_sqft"], 2), axis=1
)
print(f"\nPrice per sqft sample:\n{df[['area_sqft','price_k','price_per_sqft']].head(5)}")


# ─────────────────────────────────────────────
# 8. MERGING & JOINING
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("8. MERGING & JOINING")
print("=" * 55)

# Two related DataFrames
customers = pd.DataFrame({
    "customer_id": [1, 2, 3, 4],
    "name":        ["Alice", "Bob", "Carol", "Dave"],
    "tier":        ["gold", "silver", "gold", "bronze"],
})

orders = pd.DataFrame({
    "order_id":   [101, 102, 103, 104, 105],
    "customer_id": [1,   3,   1,   2,   5],     # 5 has no customer
    "amount":     [250, 180, 320, 90, 410],
})

# Inner join (only matching rows)
inner = pd.merge(customers, orders, on="customer_id", how="inner")
print(f"Inner join (matching only):\n{inner[['name','tier','amount']]}")

# Left join (keep all customers, NaN if no order)
left = pd.merge(customers, orders, on="customer_id", how="left")
print(f"\nLeft join (all customers):\n{left[['name','order_id','amount']]}")

# Concatenate (stack rows)
df_a = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
df_b = pd.DataFrame({"x": [5, 6], "y": [7, 8]})
stacked = pd.concat([df_a, df_b], ignore_index=True)
print(f"\nConcat rows:\n{stacked}")


# ─────────────────────────────────────────────
# 9. ML DATA-PREP PATTERNS
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("9. ML DATA-PREP PATTERNS")
print("=" * 55)

# Feature matrix X and target y
feature_cols = ["area_sqft", "bedrooms", "age_years", "neigh_code", "garage"]
df["garage"] = df["garage"].astype(int)     # bool → int
X = df[feature_cols].values                 # → NumPy array for sklearn
y = df["price_k"].values

print(f"X shape: {X.shape}")
print(f"y shape: {y.shape}")
print(f"X[:3]  :\n{X[:3]}")
print(f"y[:3]  : {y[:3]}")

# Train / validation split (manual 80/20)
split = int(0.8 * len(df))
idx   = np.random.permutation(len(df))
X_train, X_val = X[idx[:split]], X[idx[split:]]
y_train, y_val = y[idx[:split]], y[idx[split:]]
print(f"\nSplit: train={len(X_train)}, val={len(X_val)}")

# Standardise (zero mean, unit variance)
mean_ = X_train.mean(axis=0)
std_  = X_train.std(axis=0) + 1e-8      # avoid div-by-zero
X_train_scaled = (X_train - mean_) / std_
X_val_scaled   = (X_val   - mean_) / std_   # use TRAINING stats on val!
print(f"Scaled X_train[:2]:\n{X_train_scaled[:2].round(3)}")

# One-hot encode with get_dummies
df_ohe = pd.get_dummies(df[["neighbourhood"]], prefix="neigh")
print(f"\nOne-hot encoded:\n{df_ohe.head(4)}")

# Correlation matrix (feature selection hint)
corr = df[feature_cols + ["price_k"]].corr().round(2)
print(f"\nCorrelation with price_k:\n{corr['price_k'].sort_values(ascending=False)}")


# ─────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────

print("\n" + "=" * 55)
print("SUMMARY")
print("=" * 55)
print("""
  CREATION:
    pd.Series(data)
    pd.DataFrame(dict)      pd.read_csv("file.csv")

  SELECTION:
    df["col"]               → Series
    df[["a","b"]]           → DataFrame
    df.loc[0:3, ["a","b"]] → label-based
    df.iloc[0:3, 0:2]      → position-based

  FILTER:
    df[df["x"] > 5]
    df.query("x > 5 and y < 10")

  MISSING:
    df.isnull().sum()        df.dropna()
    df["col"].fillna(median) df["col"].interpolate()

  AGGREGATION:
    df.groupby("col").agg(mean="mean", ...)
    df["col"].value_counts()

  FEATURE ENGINEERING:
    df["col"].map(dict)
    df["col"].apply(fn)
    pd.get_dummies(df[["cat_col"]])

  ML PIPELINE:
    X = df[feature_cols].values   # numpy array
    y = df["target"].values
    X_scaled = (X - X.mean(0)) / X.std(0)
""")
