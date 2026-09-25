# Phase 3 findings: who benefits from the email?

*Draft written from outputs/segment_lift.csv, uplift_deciles_*.csv and qini_curves.png. Edit in your own words.*

## The two emails behave very differently

**Mens E-Mail: a broad-based win.** The conversion lift is positive and statistically clear in almost
every segment: new and existing customers, all three channels, all regions, all recency buckets, and
customers with or without a men's purchase history. It is strongest for heavy past spenders
($750-$1,000: +2.0 pts) and multichannel shoppers (+1.0 pt), but nobody looks harmed by it.

**Womens E-Mail: works for some, not for others.** The lift is concentrated in
- new customers (+0.53 pts) but not existing customers (+0.09 pts, CI includes zero)
- customers who bought women's merchandise before (+0.51) but not those who didn't (+0.06)
- web and multichannel shoppers, but not phone shoppers (+0.17, CI includes zero)
- mid-history customers ($200-$500 past spend) show a *negative* point estimate on both conversion
  and spend. The intervals include zero, so this is a hypothesis, not a finding, but it is worth flagging.

## Customer types (uplift framework)

| Type | Where we see them |
|---|---|
| Persuadables | New customers; heavy past spenders; multichannel shoppers. Both emails, but especially Mens. |
| Sure things | Existing customers with women's history under the Womens email: control conversion is already ~0.8% and the email adds almost nothing. |
| Lost causes | Phone-channel customers under the Womens email: low baseline, and the email barely moves it. |
| Sleeping dogs (candidates) | $200-$500 past-spend customers under the Womens email. The bottom decile of the Womens uplift model shows an actual conversion lift of -0.5 pts. Needs a follow-up test to confirm. |

## Uplift model: honest assessment

Method: two-model (T-learner) gradient boosting on conversion, 5-fold cross-fitting averaged over
three random splits, so every score is out-of-sample.

- **Womens E-Mail:** the model finds real structure. Qini coefficient ~12 incremental conversions,
  stable across splits (10.6 / 11.0 / 12.4). Targeting the top 30% by predicted uplift captures ~46%
  of all incremental conversions. The Qini curve peaks around 85% and then *falls*, meaning the
  lowest-scored ~15% of customers reduce total incremental sales. Not emailing them is better than
  emailing them.
- **Mens E-Mail:** the model adds almost nothing over random targeting. Qini coefficient ~2 and
  unstable (2.9 / 0.9 / 2.3). This is *not* a failure of the model: the segment table shows the
  Mens lift is roughly uniform across the population, so there is little heterogeneity to find.
  For the Mens email, the decision is closer to "everyone or no one" than "who".

## Limitations to state
- Only 578 conversions in 64,000 customers. Uplift signal is weak by nature; segment CIs are wide.
- Seven segmenting variables x two arms = many comparisons. Treat individual segment results as
  hypotheses; the overall pattern (Mens broad, Womens selective) is the robust finding.
- Two-week window. No data on unsubscribes, fatigue or long-run effects.

## What this means for Phase 4
- Mens email: the profit question is mostly about cost per email vs. average lift.
- Womens email: targeting matters. Expect the profit-maximizing policy to exclude the bottom
  10-20% by uplift score, and possibly to skip existing customers without women's history entirely.
