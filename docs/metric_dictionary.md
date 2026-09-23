# Metric Dictionary

| Metric | Definition | Formula | Notes |
|---|---|---|---|
| Visit rate | Share of customers who visited the site within 2 weeks | visits / customers | Engagement metric |
| Conversion rate | Share of customers who purchased within 2 weeks | conversions / customers | Rare event (~0.9% overall) |
| Revenue per recipient | Average 2-week spend per customer in an arm, including $0 spenders | sum(spend) / customers | Heavily skewed; use bootstrap CIs |
| Lift (absolute) | Difference between a treatment arm and control | metric_treatment - metric_control | The incremental effect |
| Lift (relative) | Lift as a % of control | (metric_treatment - metric_control) / metric_control | |
| Incremental conversions | Extra purchases caused by the email | (conv_rate_treatment - conv_rate_control) x emails sent | vs. naive attribution = conv_rate_treatment x emails sent |
| Incremental revenue | Extra spend caused by the email | (rev_per_recipient_treatment - rev_per_recipient_control) x emails sent | |
| Incremental profit | Money made from the email after costs | incremental revenue x margin - cost per email x emails sent | Margin and cost are ASSUMPTIONS (Phase 4) |
| Uplift score | Model-predicted incremental effect for one customer | P(buy given email) - P(buy given no email) | Phase 3 |
