"""Phase 2, step 1: how much lift did each email cause, and how sure are we?

For each treatment arm vs. control, for each outcome (visit, conversion, spend):
  - absolute lift  = mean(treatment) - mean(control)
  - relative lift  = absolute lift / mean(control)
  - 95% bootstrap confidence interval for the absolute lift
  - a p-value from a classical test (z-test for rates, Welch t-test for spend)
  - Holm-adjusted p-values, because we test TWO emails against ONE control

Why bootstrap? Spend is extremely skewed: 99% of customers spent $0 and a few
spent hundreds. Resampling the data thousands of times gives an honest interval
without assuming a bell curve.

Run: python src/03_lift_analysis.py
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import RAW_CSV, OUTPUTS, CONTROL, OUTCOMES

N_BOOT = 5000
SEED = 42
rng = np.random.default_rng(SEED)

df = pd.read_csv(RAW_CSV)
control = df[df.segment == CONTROL]
treatments = [a for a in df.segment.unique() if a != CONTROL]


def two_proportion_ztest(x1, n1, x2, n2):
    """Two-sided z-test for the difference between two proportions."""
    p1, p2 = x1 / n1, x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    z = (p1 - p2) / se
    return z, 2 * (1 - stats.norm.cdf(abs(z)))


def holm_adjust(pvals):
    """Holm step-down correction for multiple comparisons."""
    pvals = np.asarray(pvals, float)
    order = np.argsort(pvals)
    m = len(pvals)
    adjusted = np.empty(m)
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, (m - rank) * pvals[idx])
        running_max = max(running_max, val)
        adjusted[idx] = running_max
    return adjusted


def bootstrap_diff(t, c, n_boot=N_BOOT):
    """Bootstrap the difference in means between treatment (t) and control (c)."""
    t, c = np.asarray(t, float), np.asarray(c, float)
    t_means = np.empty(n_boot)
    c_means = np.empty(n_boot)
    for i in range(n_boot):
        t_means[i] = t[rng.integers(0, len(t), len(t))].mean()
        c_means[i] = c[rng.integers(0, len(c), len(c))].mean()
    diffs = t_means - c_means
    return np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)


rows = []
for arm in treatments:
    treat = df[df.segment == arm]
    for outcome in OUTCOMES:
        t, c = treat[outcome], control[outcome]
        abs_lift = t.mean() - c.mean()
        rel_lift = abs_lift / c.mean()
        lo, hi = bootstrap_diff(t, c)

        if outcome in ("visit", "conversion"):
            _, p = two_proportion_ztest(t.sum(), len(t), c.sum(), len(c))
            test = "z-test (proportions)"
        else:
            _, p = stats.ttest_ind(t, c, equal_var=False)
            test = "Welch t-test"

        rows.append({
            "arm": arm, "outcome": outcome,
            "control_mean": c.mean(), "treatment_mean": t.mean(),
            "abs_lift": abs_lift, "rel_lift_pct": rel_lift * 100,
            "ci_low": lo, "ci_high": hi,
            "test": test, "p_value": p,
        })

results = pd.DataFrame(rows)

# Two emails vs one control = two comparisons per outcome. Holm correction keeps
# the chance of ANY false positive at 5%, and is less conservative than Bonferroni.
results["p_holm"] = np.nan
for outcome in OUTCOMES:
    mask = results.outcome == outcome
    results.loc[mask, "p_holm"] = holm_adjust(results.loc[mask, "p_value"])
results["significant_5pct"] = results.p_holm < 0.05

pd.set_option("display.width", 160)
print("=== Lift vs. control, with 95% bootstrap CIs ===")
print(results.round(5).to_string(index=False))
results.to_csv(OUTPUTS / "lift_results.csv", index=False)

# Plot: absolute lift with CI for each arm and outcome
fig, axes = plt.subplots(1, 3, figsize=(13, 4))
labels = {"visit": "Visit rate", "conversion": "Conversion rate", "spend": "Spend per customer ($)"}
for ax, outcome in zip(axes, OUTCOMES):
    sub = results[results.outcome == outcome]
    y = np.arange(len(sub))
    scale = 100 if outcome != "spend" else 1
    ax.errorbar(sub.abs_lift * scale, y,
                xerr=[(sub.abs_lift - sub.ci_low) * scale, (sub.ci_high - sub.abs_lift) * scale],
                fmt="o", capsize=5)
    ax.axvline(0, color="grey", linestyle="--")
    ax.set_yticks(y); ax.set_yticklabels(sub.arm)
    ax.set_title(labels[outcome])
    ax.set_xlabel("Lift vs. control" + (" (percentage points)" if outcome != "spend" else " ($)"))
plt.tight_layout()
plt.savefig(OUTPUTS / "lift_with_ci.png", dpi=150)
print(f"\nSaved -> {OUTPUTS / 'lift_results.csv'}, {OUTPUTS / 'lift_with_ci.png'}")
