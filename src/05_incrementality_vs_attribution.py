"""Phase 2, step 3: incrementality vs. naive attribution. The core insight.

Naive attribution says: "X customers who got the email bought, so the email
produced X sales." But the control group tells us how many would have bought
ANYWAY. Only the difference was caused by the email.

    attributed   = conversions among emailed customers
    baseline     = conversions we'd expect with no email (control rate x emails)
    incremental  = attributed - baseline

Run: python src/05_incrementality_vs_attribution.py
"""
import pandas as pd
from config import RAW_CSV, OUTPUTS, CONTROL

df = pd.read_csv(RAW_CSV)
control = df[df.segment == CONTROL]
ctrl_conv_rate = control.conversion.mean()
ctrl_spend_pp = control.spend.mean()

rows = []
for arm in [a for a in df.segment.unique() if a != CONTROL]:
    t = df[df.segment == arm]
    n = len(t)
    attributed_conv = t.conversion.sum()
    baseline_conv = ctrl_conv_rate * n
    incr_conv = attributed_conv - baseline_conv

    attributed_rev = t.spend.sum()
    baseline_rev = ctrl_spend_pp * n
    incr_rev = attributed_rev - baseline_rev

    rows.append({
        "arm": arm, "emails_sent": n,
        "attributed_conversions": attributed_conv,
        "would_have_bought_anyway": round(baseline_conv),
        "incremental_conversions": round(incr_conv),
        "pct_of_attributed_truly_incremental": incr_conv / attributed_conv * 100,
        "attributed_revenue": attributed_rev,
        "incremental_revenue": incr_rev,
        "pct_of_revenue_truly_incremental": incr_rev / attributed_rev * 100,
    })

out = pd.DataFrame(rows)
pd.set_option("display.width", 160)
print("=== Attribution vs. incrementality ===")
print(out.round(1).to_string(index=False))
out.to_csv(OUTPUTS / "incrementality_vs_attribution.csv", index=False)

# Plain-English summary, auto-generated from the numbers
lines = ["# Incrementality vs. attribution\n"]
for _, r in out.iterrows():
    lines.append(
        f"**{r.arm}** went to {r.emails_sent:,} customers. Naive attribution credits it with "
        f"{int(r.attributed_conversions)} purchases and ${r.attributed_revenue:,.0f} in revenue. "
        f"But the control group shows about {int(r.would_have_bought_anyway)} of those customers "
        f"would have bought anyway. The email actually caused roughly "
        f"{int(r.incremental_conversions)} extra purchases and ${r.incremental_revenue:,.0f} extra revenue. "
        f"Only {r.pct_of_attributed_truly_incremental:.0f}% of the attributed conversions were truly incremental.\n"
    )
lines.append(
    "\n**Why this matters:** an attribution report would overstate the email's impact by roughly "
    f"{100 / out.pct_of_attributed_truly_incremental.mean():.1f}x. Decisions based on attribution "
    "would overspend on customers who were going to buy regardless."
)
summary = "\n".join(lines)
(OUTPUTS / "incrementality_summary.md").write_text(summary)
print("\n" + summary)
print(f"\nSaved -> {OUTPUTS / 'incrementality_vs_attribution.csv'}, {OUTPUTS / 'incrementality_summary.md'}")
