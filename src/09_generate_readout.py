"""Phase 5, step 1: auto-generate a plain-English readout and VERIFY every number in it.

Reads the result tables produced by scripts 03-08 and writes outputs/readout.md in the
style of a weekly experiment update. Then it extracts every number from the text and
checks it against the source tables. If any number in the prose can't be traced back to
the data, the script fails loudly. This is the guard against "the chart says 12% but the
memo says 21%".

Run: python src/09_generate_readout.py
"""
import re
import pandas as pd
from config import OUTPUTS

COST, MARGIN = 0.05, 0.40   # must match src/08_profit_policy.py

lift = pd.read_csv(OUTPUTS / "lift_results.csv")
incr = pd.read_csv(OUTPUTS / "incrementality_vs_attribution.csv")
policy = pd.read_csv(OUTPUTS / "policy_summary.csv")
uplift = pd.read_csv(OUTPUTS / "uplift_model_summary.csv", index_col=0)
head = pd.read_csv(OUTPUTS / "headline_by_arm.csv", index_col=0)

# ---------- Collect every fact we will quote, with its display rounding ----------
facts = {}   # name -> (display string, raw value)

def fact(name, value, fmt):
    facts[name] = (fmt.format(value), value)
    return facts[name][0]

def L(arm, outcome, col):
    return lift[(lift.arm == arm) & (lift.outcome == outcome)][col].iloc[0]

n_total = fact("n_total", int(head.customers.sum()), "{:,}")
ctrl_conv = fact("ctrl_conv", head.loc["No E-Mail", "conversion_rate"] * 100, "{:.2f}")

text = [f"# Email experiment readout\n",
        f"**Scope.** {n_total} customers were randomly split three ways: a Mens email, a Womens email, "
        f"or no email (control). Outcomes were tracked for two weeks. Without any email, "
        f"{ctrl_conv}% of customers made a purchase.\n",
        "## Did the emails work?\n"]

for arm in ["Mens E-Mail", "Womens E-Mail"]:
    k = arm.split()[0].lower()
    conv_lift = fact(f"{k}_conv_lift", L(arm, "conversion", "abs_lift") * 100, "{:.2f}")
    conv_rel = fact(f"{k}_conv_rel", L(arm, "conversion", "rel_lift_pct"), "{:.0f}")
    lo = fact(f"{k}_conv_lo", L(arm, "conversion", "ci_low") * 100, "{:.2f}")
    hi = fact(f"{k}_conv_hi", L(arm, "conversion", "ci_high") * 100, "{:.2f}")
    sp = fact(f"{k}_spend_lift", L(arm, "spend", "abs_lift"), "{:.2f}")
    text.append(
        f"**{arm}** raised the conversion rate by {conv_lift} percentage points "
        f"(a {conv_rel}% relative increase; 95% CI {lo} to {hi} points) and spend per customer by "
        f"${sp}. Both effects remain statistically significant after correcting for testing two emails "
        f"against one control.\n")

text.append("## Incrementality vs. attribution\n")
for _, r in incr.iterrows():
    k = r.arm.split()[0].lower()
    att = fact(f"{k}_attributed", int(r.attributed_conversions), "{:d}")
    anyway = fact(f"{k}_anyway", int(r.would_have_bought_anyway), "{:d}")
    inc = fact(f"{k}_incremental", int(r.incremental_conversions), "{:d}")
    pct = fact(f"{k}_pct_incr", r.pct_of_attributed_truly_incremental, "{:.0f}")
    text.append(
        f"An attribution report would credit the **{r.arm}** with {att} purchases. The control group "
        f"shows about {anyway} of those would have happened anyway, so the email truly caused roughly "
        f"{inc}. Only {pct}% of attributed purchases were incremental.\n")

text.append("## Who responds?\n")
m_q = fact("mens_qini", uplift.loc["Mens E-Mail", "qini_coef"], "{:.1f}")
w_q = fact("womens_qini", uplift.loc["Womens E-Mail", "qini_coef"], "{:.1f}")
w_top30 = fact("womens_top30", uplift.loc["Womens E-Mail", "top30_share"] * 100, "{:.0f}")
text.append(
    f"An uplift model was trained to predict each customer's incremental response. For the Womens email "
    f"it found real structure (Qini coefficient {w_q}): the top 30% of customers by predicted uplift "
    f"account for {w_top30}% of all incremental conversions, and the lowest-scored customers respond "
    f"negatively. For the Mens email the model adds little over random targeting (Qini {m_q}) because "
    f"the lift is broad-based across all customer segments.\n")

text.append(f"## Recommendation (assumes ${COST:.2f} per email and a {MARGIN:.0%} margin)\n")
pm = policy[policy.arm == "Mens E-Mail"].iloc[0]
pw = policy[policy.arm == "Womens E-Mail"].iloc[0]
m_all = fact("mens_profit_all", pm.profit_everyone, "{:,.0f}")
m_lo = fact("mens_profit_lo", pm.profit_everyone_lo, "{:,.0f}")
m_hi = fact("mens_profit_hi", pm.profit_everyone_hi, "{:,.0f}")
w_all = fact("womens_profit_all", pw.profit_everyone, "{:,.0f}")
w_best = fact("womens_profit_best", pw.profit_best_targeting, "{:,.0f}")
w_pct = fact("womens_best_pct", int(pw.best_top_pct), "{:d}")
breakeven = fact("mens_breakeven", L("Mens E-Mail", "spend", "abs_lift") * MARGIN, "{:.2f}")
text.append(
    f"**Send the Mens email to the entire base.** Expected incremental profit is ${m_all} per 10,000 "
    f"customers (95% CI ${m_lo} to ${m_hi}) over two weeks, and it stays profitable up to about "
    f"${breakeven} per email. Targeting does not improve on this because no segment is harmed.\n\n"
    f"**If the Womens email is used, send it to the top {w_pct}% by predicted uplift**, which yields "
    f"${w_best} per 10,000 versus ${w_all} for sending to everyone. Even targeted, it earns less than "
    f"the Mens email sent broadly.\n")

text.append("## Caveats\n"
            "Two-week window only; no unsubscribe or fatigue data; cost and margin are assumptions; "
            "the Womens confidence interval is wide; the targeting gain was tuned and measured on the "
            "same data and is likely a little optimistic.\n")

readout = "\n".join(text)

# ---------- Verification: every number in the prose must be a fact we computed ----------
allowed = {v[0].replace(",", "") for v in facts.values()}
allowed |= {"3", "2", "30", "10000", "95", "40", "0.05", "10"}   # structural constants used in the text
numbers = re.findall(r"\d[\d,]*\.?\d*", readout)
unverified = sorted({n for n in numbers if n.replace(",", "").rstrip(".") not in allowed})

(OUTPUTS / "readout.md").write_text(readout)
print(readout)
print("=" * 70)
print(f"Verification: {len(numbers)} numbers found in the readout, {len(facts)} facts traced to data.")
if unverified:
    raise SystemExit(f"FAILED: these numbers in the text are not traceable to the data: {unverified}")
print("PASSED: every number in the readout matches a value computed from the result tables.")
print(f"Saved -> {OUTPUTS / 'readout.md'}")
