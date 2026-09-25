"""Phase 5: Streamlit dashboard for the email experiment.

Run from the project root:
    streamlit run dashboard/app.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st

OUT = Path(__file__).resolve().parents[1] / "outputs"

st.set_page_config(page_title="Email incrementality", layout="wide")
st.title("Who should we email? Incrementality and targeting")
st.caption("Hillstrom randomized email experiment, 64,000 customers, two-week outcomes.")


@st.cache_data
def load():
    return {
        "head": pd.read_csv(OUT / "headline_by_arm.csv", index_col=0),
        "lift": pd.read_csv(OUT / "lift_results.csv"),
        "seg": pd.read_csv(OUT / "segment_lift.csv"),
        "incr": pd.read_csv(OUT / "incrementality_vs_attribution.csv"),
        "scores": pd.read_csv(OUT / "uplift_scores.csv"),
        "sweep": pd.read_csv(OUT / "policy_sweep.csv"),
    }


d = load()

with st.expander("Metric definitions", expanded=False):
    st.markdown("""
| Metric | Definition |
|---|---|
| **Visit rate** | Share of customers who visited the site within 2 weeks |
| **Conversion rate** | Share of customers who purchased within 2 weeks |
| **Spend per customer** | Average 2-week spend, including the $0 spenders |
| **Lift** | Treatment metric minus control metric. The part the email *caused* |
| **Incremental conversions** | (treatment rate − control rate) × emails sent |
| **Naive attribution** | Purchases among emailed customers, ignoring the control group |
| **Uplift score** | Model-predicted P(buy \\| email) − P(buy \\| no email) for one customer |
| **Incremental profit** | Incremental spend × margin − cost per email |
""")

# ---------------- Headline ----------------
st.header("1. Headline results")
cols = st.columns(3)
for col, arm in zip(cols, ["No E-Mail", "Mens E-Mail", "Womens E-Mail"]):
    r = d["head"].loc[arm]
    col.metric(arm, f"{r.conversion_rate:.2%} conversion",
               None if arm == "No E-Mail" else f"{(r.conversion_rate - d['head'].loc['No E-Mail','conversion_rate']):+.2%} vs control")
    col.write(f"Visit rate {r.visit_rate:.1%} · Spend/customer ${r.spend_per_customer:.2f}")

lift = d["lift"].copy()
lift["display"] = lift.apply(lambda r: f"{r.abs_lift*100:.2f} pts [{r.ci_low*100:.2f}, {r.ci_high*100:.2f}]"
                             if r.outcome != "spend" else f"${r.abs_lift:.2f} [${r.ci_low:.2f}, ${r.ci_high:.2f}]", axis=1)
st.dataframe(lift.pivot(index="arm", columns="outcome", values="display")[["visit", "conversion", "spend"]],
             use_container_width=True)
st.caption("Lift vs. control with 95% bootstrap confidence intervals. All six are significant after Holm correction.")

# ---------------- Incrementality ----------------
st.header("2. Incrementality vs. attribution")
inc = d["incr"].set_index("arm")
c1, c2 = st.columns(2)
for col, arm in zip([c1, c2], inc.index):
    r = inc.loc[arm]
    col.subheader(arm)
    col.bar_chart(pd.DataFrame({
        "conversions": [r.attributed_conversions, r.would_have_bought_anyway, r.incremental_conversions]},
        index=["Attributed", "Would have bought anyway", "Truly incremental"]))
    col.write(f"Only **{r.pct_of_attributed_truly_incremental:.0f}%** of attributed purchases were caused by the email.")

# ---------------- Segments ----------------
st.header("3. Who responds? Lift by segment")
seg = d["seg"]
f1, f2, f3 = st.columns(3)
var = f1.selectbox("Segment by", sorted(seg.segment_var.unique()),
                   format_func=lambda v: v.replace("_label", "").replace("_", " "))
arms = f2.multiselect("Email", sorted(seg.arm.unique()), default=sorted(seg.arm.unique()))
metric = f3.radio("Metric", ["Conversion lift (pts)", "Spend lift ($)"], horizontal=True)
sub = seg[(seg.segment_var == var) & (seg.arm.isin(arms))].copy()
if metric.startswith("Conversion"):
    sub["value"], sub["lo"], sub["hi"] = sub.conv_lift * 100, sub.conv_lift_lo * 100, sub.conv_lift_hi * 100
else:
    sub["value"], sub["lo"], sub["hi"] = sub.spend_lift, sub.spend_lift_lo, sub.spend_lift_hi
chart = sub.pivot(index="level", columns="arm", values="value")
st.bar_chart(chart)
show = sub[["level", "arm", "n_treat", "value", "lo", "hi"]].round(2)
show.columns = ["Segment", "Email", "Emailed customers", metric, "CI low", "CI high"]
st.dataframe(show, use_container_width=True, hide_index=True)
st.caption("If the interval spans zero, there is no clear evidence the email helped that group.")

# ---------------- Policy ----------------
st.header("4. The decision: profit by policy")
st.write("Change the assumptions and watch the recommendation move. Profit is per 10,000 customers over two weeks.")
a1, a2 = st.columns(2)
cost = a1.slider("Cost per email ($)", 0.00, 0.60, 0.05, 0.01)
margin = a2.slider("Margin on revenue", 0.10, 0.80, 0.40, 0.05)
BASE = 10_000
rows = []
for arm in ["Mens E-Mail", "Womens E-Mail"]:
    sc = d["scores"][d["scores"].arm_modeled == arm]
    l = d["lift"][(d["lift"].arm == arm) & (d["lift"].outcome == "spend")].iloc[0]
    p_all = BASE * (l.abs_lift * margin - cost)
    best_x, best_p = 1.0, p_all
    for x in np.arange(0.1, 1.0, 0.1):
        cut = sc.uplift_conv.quantile(1 - x)
        tgt = sc[sc.uplift_conv >= cut]
        sl = tgt[tgt.is_treat].spend.mean() - tgt[~tgt.is_treat].spend.mean()
        p = (len(tgt) / len(sc)) * BASE * (sl * margin - cost)
        if p > best_p * 1.02:
            best_x, best_p = x, p
    if max(p_all, best_p) <= 0:
        rec = "Email no one"
    elif best_x >= 0.999:
        rec = "Email everyone"
    else:
        rec = f"Email top {best_x:.0%} by uplift"
    rows.append({"Email": arm, "Everyone": p_all, "No one": 0.0,
                 "Best targeting": best_p, "Recommendation": rec})
pol = pd.DataFrame(rows).set_index("Email")
st.dataframe(pol.style.format({"Everyone": "${:,.0f}", "No one": "${:,.0f}", "Best targeting": "${:,.0f}"}),
             use_container_width=True)
best = pol["Best targeting"].idxmax() if pol["Best targeting"].max() > 0 else None
if best:
    st.success(f"**Recommendation at ${cost:.2f}/email and {margin:.0%} margin:** {pol.loc[best, 'Recommendation'].lower()} "
               f"with the **{best}**, worth about **${pol.loc[best, 'Best targeting']:,.0f}** per 10,000 customers.")
else:
    st.warning("At these assumptions no email policy is profitable.")

st.caption("Assumptions are placeholders. Two-week window; no fatigue or unsubscribe effects measured; "
           "targeting gain is measured on the same data it was tuned on and is likely a little optimistic.")
