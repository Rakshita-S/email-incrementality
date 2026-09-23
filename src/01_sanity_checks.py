"""Phase 1, step 1: load the raw CSV and confirm the data is healthy.

Run: python src/01_sanity_checks.py
"""
import pandas as pd
from config import RAW_CSV, OUTPUTS, ARMS

df = pd.read_csv(RAW_CSV)

print("=== Shape ===")
print(df.shape)

print("\n=== Missing values ===")
print(df.isna().sum())

print("\n=== Group sizes ===")
print(df["segment"].value_counts())
assert set(df["segment"].unique()) == set(ARMS), "Unexpected treatment arms"

print("\n=== Spend by conversion (non-converters must be $0) ===")
print(df.groupby("conversion")["spend"].agg(["min", "max", "mean", "count"]))
assert (df.loc[df.conversion == 0, "spend"] == 0).all(), "Non-converters with spend > 0"

print("\n=== Headline outcomes by arm ===")
headline = (
    df.groupby("segment")
      .agg(customers=("visit", "size"),
           visit_rate=("visit", "mean"),
           conversion_rate=("conversion", "mean"),
           spend_per_customer=("spend", "mean"))
      .round(4)
)
print(headline)
headline.to_csv(OUTPUTS / "headline_by_arm.csv")
print(f"\nSaved -> {OUTPUTS / 'headline_by_arm.csv'}")
