# Phase 3 findings: who benefits from the email?

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
| Sleeping dogs (candidates) | $200-$500 past-spend customers under the Womens email. The bottom decile of the Womens uplift model shows an actual conversion lift of -0.39 pts. Needs a follow-up test to confirm. |

## Uplift model: honest assessment

Method: two-model (T-learner) gradient boosting on conversion, 5-fold cross-fitting averaged over
three random splits, so every score is out-of-sample.

- Women's email: the model works.

Its performance score (Qini) came out at 11.6, 11.4, and 12.2 across the three repeats. Nearly identical each time, which means the model is finding something real, not noise.

The customers it ranked in the top 30% produced about half (49%) of all the extra sales the email caused.

When I split customers into ten groups by model score, the top group showed a lift of +0.48 points and the bottom group a lift of −0.39 points. The model correctly separates people the email helps from people it doesn't.

The bottom group is actually negative: emailing them lowered sales. So the best plan skips them.

- Men's email: the model finds nothing, and that's the right answer.

Its Qini scores were 2.6, 3.2, and 1.3: small and jumping around, the signature of a model chasing noise.

The ten-group split confirms it. The group the model ranked lowest had a lift of +0.70 points, higher than several groups ranked above it. The model can't sort these customers.

Why not? Because the segment analysis shows the men's email helps almost everyone by about the same amount. There's no "who" to predict, so a working model should come back empty, and this one does.


## Limitations to state
Only 578 conversions in 64,000 customers. Uplift signal is weak by nature; segment CIs are wide.

Seven segmenting variables x two arms = many comparisons. Treat individual segment results as hypotheses; the overall pattern (Mens broad, Womens selective) is the robust finding.

Two-week window. No data on unsubscribes, fatigue or long-run effects.

## What this means for Phase 4
- Mens email: the profit question is mostly about cost per email vs. average lift.
- Womens email: targeting matters. Expect the profit-maximizing policy to exclude the bottom
  10-20% by uplift score, and possibly to skip existing customers without women's history entirely.
