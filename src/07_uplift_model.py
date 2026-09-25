"""Phase 3, step 2: an uplift model. Predict each customer's INCREMENTAL effect.

A normal model predicts P(buy). An uplift model predicts
    uplift = P(buy | email) - P(buy | no email)
i.e. how much the email changes this customer's behaviour.

Method: the two-model ("T-learner") approach.
  1. Train model_T on emailed customers  -> P(buy | email, features)
  2. Train model_C on control customers  -> P(buy | no email, features)
  3. uplift = model_T(x) - model_C(x)

Honest evaluation: we use 5-fold cross-fitting, so every customer's uplift
score comes from models that never saw that customer. We then check whether
customers the model ranks highest really do show a bigger lift (decile table)
and summarise with a Qini curve vs. random targeting.

Run: python src/07_uplift_model.py
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import RAW_CSV, OUTPUTS, CONTROL

SEED = 42
SEEDS = [42, 7, 123]   # repeat cross-fitting with different splits and average, for stability
N_FOLDS = 5
FEATURES = ["recency", "history", "mens", "womens", "newbie", "channel", "zip_code"]

df = pd.read_csv(RAW_CSV)
X_all = pd.get_dummies(df[FEATURES], columns=["channel", "zip_code"], drop_first=False).astype(float)
treatments = [a for a in df.segment.unique() if a != CONTROL]


def make_model():
    return HistGradientBoostingClassifier(
        max_depth=3, learning_rate=0.05, max_iter=200,
        min_samples_leaf=100, l2_regularization=1.0, random_state=SEED)


def cross_fit_uplift(arm, seed=SEED):
    """Out-of-sample uplift score for every customer in {arm, control}."""
    mask = df.segment.isin([arm, CONTROL])
    sub = df[mask].copy()
    X = X_all[mask]
    is_treat = (sub.segment == arm).values
    y = sub.conversion.values
    uplift = np.zeros(len(sub))
    p_t_all = np.zeros(len(sub))
    p_c_all = np.zeros(len(sub))

    # stratify on treatment x outcome so every fold has converters in both arms
    strat = is_treat.astype(int) * 2 + y
    skf = StratifiedKFold(N_FOLDS, shuffle=True, random_state=seed)
    for train_idx, test_idx in skf.split(X, strat):
        tr_t = train_idx[is_treat[train_idx]]
        tr_c = train_idx[~is_treat[train_idx]]
        m_t = make_model().fit(X.iloc[tr_t], y[tr_t])
        m_c = make_model().fit(X.iloc[tr_c], y[tr_c])
        p_t = m_t.predict_proba(X.iloc[test_idx])[:, 1]
        p_c = m_c.predict_proba(X.iloc[test_idx])[:, 1]
        p_t_all[test_idx], p_c_all[test_idx] = p_t, p_c
        uplift[test_idx] = p_t - p_c

    sub["p_buy_if_email"] = p_t_all
    sub["p_buy_if_no_email"] = p_c_all
    sub["uplift_conv"] = uplift
    sub["is_treat"] = is_treat
    return sub


def decile_table(sub):
    """Actual lift within each decile of predicted uplift. The key sanity check."""
    sub = sub.copy()
    sub["decile"] = pd.qcut(sub.uplift_conv.rank(method="first"), 10, labels=range(1, 11))  # 10 = highest predicted uplift
    rows = []
    for d, g in sub.groupby("decile", observed=True):
        t, c = g[g.is_treat], g[~g.is_treat]
        rows.append({
            "decile": int(d), "n": len(g),
            "predicted_uplift": g.uplift_conv.mean(),
            "actual_control_conv": c.conversion.mean(),
            "actual_treat_conv": t.conversion.mean(),
            "actual_conv_lift": t.conversion.mean() - c.conversion.mean(),
            "actual_spend_lift": t.spend.mean() - c.spend.mean(),
        })
    return pd.DataFrame(rows).sort_values("decile", ascending=False)


def qini_curve(sub, score_col):
    """Cumulative incremental conversions when targeting top-ranked customers first."""
    s = sub.sort_values(score_col, ascending=False).reset_index(drop=True)
    n = len(s)
    cum_t_conv = (s.conversion * s.is_treat).cumsum()
    cum_c_conv = (s.conversion * ~s.is_treat).cumsum()
    cum_t_n = s.is_treat.cumsum().replace(0, np.nan)
    cum_c_n = (~s.is_treat).cumsum().replace(0, np.nan)
    # incremental conversions among the treated, scaled to treated population
    incr = cum_t_conv - cum_c_conv * (cum_t_n / cum_c_n)
    frac = np.arange(1, n + 1) / n
    return frac, incr.fillna(0).values


results = {}
all_scores = []
fig, axes = plt.subplots(1, len(treatments), figsize=(6 * len(treatments), 4.5))
for ax, arm in zip(np.atleast_1d(axes), treatments):
    print(f"\n{'=' * 70}\n{arm} vs. {CONTROL}\n{'=' * 70}")
    # Cross-fit once per seed, report Qini stability, then average the scores
    runs = [cross_fit_uplift(arm, seed) for seed in SEEDS]
    per_seed_qini = []
    for r in runs:
        f, inc = qini_curve(r, "uplift_conv")
        per_seed_qini.append(np.trapezoid(inc, f) - np.trapezoid(np.linspace(0, inc[-1], len(f)), f))
    print("Qini coefficient by random split:", [round(float(q), 1) for q in per_seed_qini],
          "-> a stable model gives similar values; wide swings mean weak signal")
    sub = runs[0].copy()
    for col in ["p_buy_if_email", "p_buy_if_no_email", "uplift_conv"]:
        sub[col] = np.mean([r[col].values for r in runs], axis=0)
    dec = decile_table(sub)
    show = dec.copy()
    for col in ["predicted_uplift", "actual_control_conv", "actual_treat_conv", "actual_conv_lift"]:
        show[col] = (show[col] * 100).round(2)
    show["actual_spend_lift"] = show.actual_spend_lift.round(3)
    print("Decile table (10 = highest predicted uplift). Percent for conv columns, $ for spend.")
    print(show.to_string(index=False))

    frac, incr_model = qini_curve(sub, "uplift_conv")
    rng = np.random.default_rng(SEED)
    sub["random_score"] = rng.random(len(sub))
    _, incr_random = qini_curve(sub, "random_score")
    total = incr_model[-1]
    auuc_model = np.trapezoid(incr_model, frac)
    auuc_random = np.trapezoid(np.linspace(0, total, len(frac)), frac)
    qini_coef = auuc_model - auuc_random
    print(f"\nQini coefficient (area between model curve and random line): {qini_coef:,.1f} incremental conversions")
    print(f"Top 30% of customers by predicted uplift capture "
          f"{incr_model[int(0.3 * len(frac))] / total:.0%} of total incremental conversions.")
    results[arm] = {"qini_coef": qini_coef, "total_incremental": total,
                    "top30_share": incr_model[int(0.3 * len(frac))] / total}

    ax.plot(frac * 100, incr_model, label="Uplift model")
    ax.plot(frac * 100, np.linspace(0, total, len(frac)), "--", color="grey", label="Random targeting")
    ax.set_xlabel("% of customers targeted (ranked by predicted uplift)")
    ax.set_ylabel("Cumulative incremental conversions")
    ax.set_title(f"Qini curve: {arm}")
    ax.legend()

    dec.to_csv(OUTPUTS / f"uplift_deciles_{arm.split()[0].lower()}.csv", index=False)
    sub["arm_modeled"] = arm
    all_scores.append(sub)

plt.tight_layout()
plt.savefig(OUTPUTS / "qini_curves.png", dpi=150)

scores = pd.concat(all_scores)
scores.to_csv(OUTPUTS / "uplift_scores.csv", index=False)
pd.DataFrame(results).T.to_csv(OUTPUTS / "uplift_model_summary.csv")
print(f"\nSaved -> uplift_scores.csv, uplift_deciles_*.csv, uplift_model_summary.csv, qini_curves.png in {OUTPUTS}")
