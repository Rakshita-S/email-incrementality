"""Phase 3, step 1: does the email work equally well for everyone?

The overall lift is an average. Here we split customers by traits fixed BEFORE
the email (so the split is safe inside a randomized experiment) and measure the
lift within each group, with a 95% confidence interval.

Watch for: groups with a big lift (persuadables), groups with high control
conversion but small lift (sure things), and any group with a negative lift
(sleeping dogs).

Run: python src/06_segment_lift.py
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import RAW_CSV, OUTPUTS, CONTROL

df = pd.read_csv(RAW_CSV)
df["newbie_label"] = df.newbie.map({1: "New customer", 0: "Existing customer"})
df["mens_label"] = df.mens.map({1: "Bought mens before", 0: "No mens history"})
df["womens_label"] = df.womens.map({1: "Bought womens before", 0: "No womens history"})
df["recency_bucket"] = pd.cut(df.recency, [0, 3, 6, 9, 12], labels=["1-3 mo", "4-6 mo", "7-9 mo", "10-12 mo"])

SEGMENT_VARS = ["newbie_label", "channel", "history_segment", "zip_code",
                "mens_label", "womens_label", "recency_bucket"]
treatments = [a for a in df.segment.unique() if a != CONTROL]
z = stats.norm.ppf(0.975)

rows = []
for var in SEGMENT_VARS:
    for level, g in df.groupby(var, observed=True):
        c = g[g.segment == CONTROL]
        for arm in treatments:
            t = g[g.segment == arm]
            if len(t) < 100 or len(c) < 100:
                continue
            # conversion lift with normal-approximation CI
            pt, pc = t.conversion.mean(), c.conversion.mean()
            se_conv = np.sqrt(pt * (1 - pt) / len(t) + pc * (1 - pc) / len(c))
            # spend lift with Welch CI
            st, sc = t.spend.mean(), c.spend.mean()
            se_spend = np.sqrt(t.spend.var() / len(t) + c.spend.var() / len(c))
            rows.append({
                "segment_var": var, "level": str(level), "arm": arm,
                "n_treat": len(t), "n_control": len(c),
                "control_conv": pc, "treat_conv": pt,
                "conv_lift": pt - pc, "conv_lift_lo": pt - pc - z * se_conv, "conv_lift_hi": pt - pc + z * se_conv,
                "control_spend": sc, "treat_spend": st,
                "spend_lift": st - sc, "spend_lift_lo": st - sc - z * se_spend, "spend_lift_hi": st - sc + z * se_spend,
            })

seg = pd.DataFrame(rows)
seg.to_csv(OUTPUTS / "segment_lift.csv", index=False)

pd.set_option("display.width", 200)
print("=== Conversion lift by segment (percentage points) ===")
show = seg.copy()
for col in ["control_conv", "treat_conv", "conv_lift", "conv_lift_lo", "conv_lift_hi"]:
    show[col] = (show[col] * 100).round(2)
print(show[["segment_var", "level", "arm", "n_treat", "control_conv", "treat_conv",
            "conv_lift", "conv_lift_lo", "conv_lift_hi"]].to_string(index=False))

print("\n=== Spend lift by segment ($ per customer) ===")
print(seg[["segment_var", "level", "arm", "spend_lift", "spend_lift_lo", "spend_lift_hi"]]
      .round(3).to_string(index=False))

# Flag interesting groups
print("\n=== Flags ===")
neg = seg[seg.spend_lift < 0]
if len(neg):
    print("Negative spend lift (possible sleeping dogs):")
    print(neg[["segment_var", "level", "arm", "spend_lift", "spend_lift_hi"]].round(3).to_string(index=False))
else:
    print("No segment shows a negative spend lift.")
top = seg.sort_values("spend_lift", ascending=False).head(5)
print("\nLargest spend lift (strongest persuadable groups):")
print(top[["segment_var", "level", "arm", "spend_lift", "spend_lift_lo", "spend_lift_hi"]].round(3).to_string(index=False))

# Chart: conversion lift by segment, one panel per variable
fig, axes = plt.subplots(len(SEGMENT_VARS), 1, figsize=(9, 2.2 * len(SEGMENT_VARS)))
colors = {"Mens E-Mail": "tab:blue", "Womens E-Mail": "tab:orange"}
for ax, var in zip(axes, SEGMENT_VARS):
    sub = seg[seg.segment_var == var]
    levels = list(dict.fromkeys(sub.level))
    for i, arm in enumerate(treatments):
        s = sub[sub.arm == arm].set_index("level").reindex(levels)
        y = np.arange(len(levels)) + (i - 0.5) * 0.3
        ax.errorbar(s.conv_lift * 100, y,
                    xerr=[(s.conv_lift - s.conv_lift_lo) * 100, (s.conv_lift_hi - s.conv_lift) * 100],
                    fmt="o", capsize=3, color=colors[arm], label=arm)
    ax.axvline(0, color="grey", linestyle="--")
    ax.set_yticks(np.arange(len(levels))); ax.set_yticklabels(levels)
    ax.set_title(var.replace("_label", "").replace("_", " "), loc="left", fontsize=10)
axes[0].legend(loc="lower right", fontsize=8)
axes[-1].set_xlabel("Conversion lift vs. control (percentage points)")
plt.tight_layout()
plt.savefig(OUTPUTS / "segment_conversion_lift.png", dpi=150)
print(f"\nSaved -> {OUTPUTS / 'segment_lift.csv'}, {OUTPUTS / 'segment_conversion_lift.png'}")
