# MEMO: Email campaign results and recommendation

**To:** Marketing leadership  **From:** Analytics  **Re:** Mens/Womens email experiment, 64,000 customers

## Recommendation
**Send the Mens email to the entire customer base.** It roughly doubles the two-week purchase rate, is
profitable at any plausible email cost, and no customer group appears worse off for receiving it.
Do not send the Womens email to everyone; if used, exclude the lowest-responding 10% of customers.

## What we did
Customers were randomly assigned to a Mens email, a Womens email, or no email. Because assignment was
random (verified: all customer traits balanced across groups), the no-email group tells us what would
have happened anyway. The difference is the email's true, incremental effect.

## What we found
| | No email | Mens email | Womens email |
|---|---|---|---|
| Purchase rate (2 weeks) | 0.57% | 1.25% | 0.88% |
| Spend per customer | $0.65 | $1.42 | $1.08 |
| Incremental spend per email | — | **+$0.77** | +$0.42 |

**Attribution overstates impact by about 2x.** A standard report would credit the Mens email with 267
purchases. About 122 of those customers would have bought anyway. The email caused roughly 145.

**The two emails behave differently.** The Mens email lifts every segment we examined. The Womens
email works for new customers and prior womens-merchandise buyers, does little for existing customers
and phone shoppers, and may slightly *reduce* purchases among mid-spend customers.

## Expected value (assumes $0.05 per email, 40% margin; adjustable)
| Policy | Profit per 10,000 customers (2 weeks) |
|---|---|
| Mens email to everyone | **$2,600** (range $1,500 to $3,700) |
| Womens email to top 90% by predicted response | $1,500 |
| Womens email to everyone | $1,200 |
| No email | $0 |

The Mens email stays profitable until cost per email exceeds about $0.30.

## Risks
- Results cover two weeks. Repeated sends may cause fatigue or unsubscribes we cannot see here.
- Cost and margin are assumptions; break-even figures let you substitute real numbers.
- The Womens result has a wide uncertainty range and should be re-tested before scaling.

## Next step
Roll out the Mens email to the full base with a 10% holdout to keep measuring incrementality, and run
a follow-up test of the Womens email on the model's top-scoring segments only.
