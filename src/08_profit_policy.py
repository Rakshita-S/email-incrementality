"""Phase 4: turn the analysis into a money decision.

ASSUMPTIONS (change them here; they are labelled as assumptions everywhere they appear):
    COST_PER_EMAIL = $0.05
    MARGIN         = 40% of revenue is profit

Incremental profit from emailing a customer:
    incremental_spend x MARGIN - COST_PER_EMAIL

Three policies, per email arm:
    1. Email everyone
    2. Email no one          (profit = 0 by definition)
    3. Email the top X% by predicted uplift (X swept from 10% to 100%)

Profit is reported per 10,000 customers in the customer base so the numbers are
easy to scale. Then we sweep cost and margin to see when the recommendation flips.

Run: python src/08_profit_policy.py
"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import OUTPUTS, CONTROL

COST_PER_EMAIL = 0.05     # ASSUMPTION
MARGIN = 0.40             # ASSUMPTION
BASE = 10_000             # report profit per this many customers

lift = pd.read_csv(OUTPUTS / "lift_results.csv")
scores = pd.read_csv(OUTPUTS / "uplift_scores.csv")
arms = sorted(scores.arm_modeled.unique())


def profit_per_customer(spend_lift, cost=COST_PER_EMAIL, margin=MARGIN):
    return spend_lift * margin - cost


def policy_top_x(sub, x, cost=COST_PER_EMAIL, margin=MARGIN):
    """Email the top x fraction by predicted uplift. Return profit per BASE customers.

    We rank by the model's (out-of-sample) score, then measure what ACTUALLY
    happened to the targeted group using the experiment: treated vs control
    within that group. That keeps the evaluation honest.
    """
    if x <= 0:
        return 0.0, 0.0
    cutoff = sub.uplift_conv.quantile(1 - x)
    tgt = sub[sub.uplift_conv >= cutoff]
    t, c = tgt[tgt.is_treat], tgt[~tgt.is_treat]
    spend_lift = t.spend.mean() - c.spend.mean()
    frac = len(tgt) / len(sub)
    return frac * BASE * profit_per_customer(spend_lift, cost, margin), spend_lift


print(f"ASSUMPTIONS: cost per email = ${COST_PER_EMAIL:.2f}, margin = {MARGIN:.0%}. "
      f"Profit shown per {BASE:,} customers in the base.\n")

summary_rows, sweep_rows = [], []
fig, axes = plt.subplots(1, len(arms), figsize=(6 * len(arms), 4.5))
for ax, arm in zip(np.atleast_1d(axes), arms):
    sub = scores[scores.arm_modeled == arm]
    row = lift[(lift.arm == arm) & (lift.outcome == "spend")].iloc[0]

    # Policy 1: everyone (with CI carried from the bootstrap in Phase 2)
    p_all = BASE * profit_per_customer(row.abs_lift)
    p_all_lo = BASE * profit_per_customer(row.ci_low)
    p_all_hi = BASE * profit_per_customer(row.ci_high)

    # Policy 3: top X% sweep
    xs = np.arange(0.1, 1.01, 0.1)
    profits = []
    for x in xs:
        p, sl = policy_top_x(sub, x)
        profits.append(p)
        sweep_rows.append({"arm": arm, "top_pct": round(x * 100), "spend_lift_in_targeted": sl,
                           "profit_per_10k": p})
    best_i = int(np.argmax(profits))
    best_x, best_p = xs[best_i], profits[best_i]

    print(f"=== {arm} ===")
    print(f"  Email everyone : ${p_all:,.0f}   (95% CI ${p_all_lo:,.0f} to ${p_all_hi:,.0f})")
    print(f"  Email no one   : $0")
    print(f"  Best targeting : email top {best_x:.0%} -> ${best_p:,.0f}")
    print(f"  Gain from targeting vs everyone: ${best_p - p_all:,.0f} "
          f"({(best_p - p_all) / abs(p_all):+.0%})")
    print("  Top-X sweep:", "  ".join(f"{x:.0%}: ${p:,.0f}" for x, p in zip(xs, profits)), "\n")

    summary_rows.append({"arm": arm, "profit_everyone": p_all, "profit_everyone_lo": p_all_lo,
                         "profit_everyone_hi": p_all_hi, "profit_no_one": 0,
                         "best_top_pct": round(best_x * 100), "profit_best_targeting": best_p})

    ax.plot(xs * 100, profits, "o-", label="Email top X% by uplift")
    ax.axhline(p_all, color="tab:green", linestyle="--", label="Email everyone")
    ax.axhline(0, color="grey", linestyle=":", label="Email no one")
    ax.set_xlabel("% of customers emailed (best-scored first)")
    ax.set_ylabel(f"Incremental profit per {BASE:,} customers ($)")
    ax.set_title(f"{arm}: profit by policy\n(assumes ${COST_PER_EMAIL:.2f}/email, {MARGIN:.0%} margin)")
    ax.legend()
plt.tight_layout()
plt.savefig(OUTPUTS / "profit_by_policy.png", dpi=150)

pd.DataFrame(summary_rows).to_csv(OUTPUTS / "policy_summary.csv", index=False)
pd.DataFrame(sweep_rows).to_csv(OUTPUTS / "policy_sweep.csv", index=False)

# ---- Sensitivity: how does the best policy change with cost and margin? ----
costs = [0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50]
margins = [0.20, 0.30, 0.40, 0.50, 0.60]
sens_rows = []
fig, axes = plt.subplots(1, len(arms), figsize=(6.5 * len(arms), 4.5))
for ax, arm in zip(np.atleast_1d(axes), arms):
    sub = scores[scores.arm_modeled == arm]
    row = lift[(lift.arm == arm) & (lift.outcome == "spend")].iloc[0]
    grid = np.zeros((len(margins), len(costs)))
    labels = [["" for _ in costs] for _ in margins]
    for i, m in enumerate(margins):
        for j, c in enumerate(costs):
            p_all = BASE * profit_per_customer(row.abs_lift, c, m)
            best_x, best_p = 0, 0.0
            for x in np.arange(0.1, 1.01, 0.1):
                p, _ = policy_top_x(sub, x, c, m)
                if p > best_p:
                    best_x, best_p = x, p
            if best_p <= 0:
                choice, val = "No one", 0.0
            elif best_x >= 0.999 or best_p <= p_all * 1.02:   # targeting must beat everyone by >2%
                choice, val = "Everyone", p_all
            else:
                choice, val = f"Top {best_x:.0%}", best_p
            grid[i, j] = val
            labels[i][j] = f"{choice}\n${val:,.0f}"
            sens_rows.append({"arm": arm, "cost_per_email": c, "margin": m,
                              "best_policy": choice, "profit_per_10k": val})
    im = ax.imshow(grid, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(range(len(costs))); ax.set_xticklabels([f"${c:.2f}" for c in costs])
    ax.set_yticks(range(len(margins))); ax.set_yticklabels([f"{m:.0%}" for m in margins])
    ax.set_xlabel("Cost per email"); ax.set_ylabel("Margin")
    ax.set_title(f"{arm}: best policy and profit per {BASE:,}")
    for i in range(len(margins)):
        for j in range(len(costs)):
            ax.text(j, i, labels[i][j], ha="center", va="center", fontsize=7)
plt.tight_layout()
plt.savefig(OUTPUTS / "policy_sensitivity.png", dpi=150)

sens = pd.DataFrame(sens_rows)
sens.to_csv(OUTPUTS / "policy_sensitivity.csv", index=False)
print("=== Sensitivity: best policy by cost and margin ===")
for arm in arms:
    print(f"\n{arm}")
    print(sens[sens.arm == arm].pivot(index="margin", columns="cost_per_email", values="best_policy").to_string())

# Break-even cost: the email cost at which "everyone" stops being profitable
print("\n=== Break-even cost per email (at assumed margin) ===")
for arm in arms:
    row = lift[(lift.arm == arm) & (lift.outcome == "spend")].iloc[0]
    print(f"  {arm}: ${row.abs_lift * MARGIN:.3f} per email  (CI ${row.ci_low * MARGIN:.3f} to ${row.ci_high * MARGIN:.3f})")

print(f"\nSaved -> policy_summary.csv, policy_sweep.csv, policy_sensitivity.csv, "
      f"profit_by_policy.png, policy_sensitivity.png in {OUTPUTS}")
