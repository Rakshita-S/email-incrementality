"""Phase 2, step 2: how small an effect could this experiment reliably detect?

"Power" is the chance of detecting a real effect if one exists. The standard
target is 80%. The Minimum Detectable Effect (MDE) is the smallest true lift
that we'd catch 80% of the time at our sample size.

Why it matters: if the MDE is bigger than a business-meaningful effect, a
"not significant" result doesn't mean "no effect", it means "we couldn't tell".

Run: python src/04_power_analysis.py
"""
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import RAW_CSV, OUTPUTS, CONTROL

ALPHA = 0.05 / 2   # Bonferroni-style: two treatment arms tested against control
POWER = 0.80

df = pd.read_csv(RAW_CSV)
control = df[df.segment == CONTROL]
n_c = len(control)
n_t = int(df[df.segment != CONTROL].groupby("segment").size().mean())

z_alpha = stats.norm.ppf(1 - ALPHA / 2)
z_beta = stats.norm.ppf(POWER)


def mde_proportion(p0, n1, n2):
    se = np.sqrt(p0 * (1 - p0) * (1 / n1 + 1 / n2))
    return (z_alpha + z_beta) * se


def mde_mean(sd, n1, n2):
    se = sd * np.sqrt(1 / n1 + 1 / n2)
    return (z_alpha + z_beta) * se


rows = []
for outcome in ["visit", "conversion"]:
    p0 = control[outcome].mean()
    mde = mde_proportion(p0, n_t, n_c)
    rows.append({"outcome": outcome, "control_baseline": p0,
                 "mde_absolute": mde, "mde_relative_pct": mde / p0 * 100})
sd = control["spend"].std()
mde = mde_mean(sd, n_t, n_c)
rows.append({"outcome": "spend", "control_baseline": control["spend"].mean(),
             "mde_absolute": mde, "mde_relative_pct": mde / control["spend"].mean() * 100})

mde_table = pd.DataFrame(rows)
print(f"Sample sizes: ~{n_t:,} per treatment arm, {n_c:,} control")
print(f"alpha = {ALPHA:.3f} (two-sided, corrected for 2 comparisons), power = {POWER:.0%}\n")
print("=== Minimum detectable effect (absolute and % of control) ===")
print(mde_table.round(5).to_string(index=False))
mde_table.to_csv(OUTPUTS / "power_mde.csv", index=False)


# Power curve for conversion: how does power change with the true lift?
def power_proportion(p0, lift, n1, n2):
    p1 = p0 + lift
    se0 = np.sqrt(p0 * (1 - p0) * (1 / n1 + 1 / n2))
    se1 = np.sqrt((p0 * (1 - p0) / n2) + (p1 * (1 - p1) / n1))
    crit = z_alpha * se0
    return 1 - stats.norm.cdf((crit - lift) / se1) + stats.norm.cdf((-crit - lift) / se1)


p0 = control["conversion"].mean()
lifts = np.linspace(0, 0.008, 100)
powers = [power_proportion(p0, l, n_t, n_c) for l in lifts]

plt.figure(figsize=(7, 4))
plt.plot(lifts * 100, powers)
plt.axhline(0.8, color="grey", linestyle="--", label="80% power")
observed = df[df.segment == "Mens E-Mail"].conversion.mean() - p0
plt.axvline(observed * 100, color="red", linestyle=":", label="Observed Mens lift")
plt.xlabel("True conversion lift (percentage points)")
plt.ylabel("Power")
plt.title("Power to detect a conversion lift at this sample size")
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUTS / "power_curve_conversion.png", dpi=150)
print(f"\nSaved -> {OUTPUTS / 'power_mde.csv'}, {OUTPUTS / 'power_curve_conversion.png'}")
