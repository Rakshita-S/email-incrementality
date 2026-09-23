"""Phase 1, step 2: were customers randomly assigned to the three arms?

If randomization worked, pre-treatment traits (set before any email went out)
should look the same across arms. We check with:
  - a balance table (means / proportions per arm)
  - a chi-square test for categorical traits
  - a one-way ANOVA for numeric traits
Large p-values (> 0.05) mean "no evidence of imbalance", which is what we want.

Run: python src/02_randomization_check.py
"""
import pandas as pd
from scipy import stats
from config import RAW_CSV, OUTPUTS

df = pd.read_csv(RAW_CSV)

numeric = ["recency", "history", "mens", "womens", "newbie"]
categorical = ["channel", "zip_code", "history_segment"]

print("=== Balance table (means / proportions by arm) ===")
balance = df.groupby("segment")[numeric].mean().round(4)
print(balance)

print("\n=== Categorical distributions by arm (% of customers) ===")
for col in categorical:
    ct = pd.crosstab(df["segment"], df[col], normalize="index").mul(100).round(2)
    print(f"\n{col}:")
    print(ct)

print("\n=== Statistical tests (p > 0.05 = balanced) ===")
rows = []
for col in numeric:
    groups = [g[col].values for _, g in df.groupby("segment")]
    f, p = stats.f_oneway(*groups)
    rows.append({"variable": col, "test": "ANOVA", "statistic": round(f, 3), "p_value": round(p, 4)})
for col in categorical:
    chi2, p, dof, _ = stats.chi2_contingency(pd.crosstab(df["segment"], df[col]))
    rows.append({"variable": col, "test": "chi-square", "statistic": round(chi2, 3), "p_value": round(p, 4)})

tests = pd.DataFrame(rows)
print(tests.to_string(index=False))
tests.to_csv(OUTPUTS / "randomization_tests.csv", index=False)
balance.to_csv(OUTPUTS / "balance_table.csv")

flagged = tests[tests.p_value < 0.05]
print("\nVERDICT:", "Randomization looks clean." if flagged.empty
      else f"Check these variables: {', '.join(flagged.variable)}")
print(f"Saved -> {OUTPUTS / 'randomization_tests.csv'}, {OUTPUTS / 'balance_table.csv'}")
