# Phase 4: the business decision

*Draft built from outputs/policy_summary.csv, policy_sweep.csv and policy_sensitivity.csv. Rewrite in your own words.*

## Assumptions (labelled, adjustable in src/08_profit_policy.py)
- Cost per email: **$0.05**
- Margin on revenue: **40%**
- Profit horizon: the two-week window measured in the experiment. No long-run effects counted.
- Profit reported per 10,000 customers in the base.

## Results at the assumed cost and margin

| Policy | Mens E-Mail | Womens E-Mail |
|---|---|---|
| Email everyone | **$2,579** (95% CI $1,469 to $3,714) | $1,198 (95% CI $201 to $2,226) |
| Email no one | $0 | $0 |
| Best targeting | Top 100% = everyone | **Top 90%: $1,542** (+29% vs everyone) |

## Recommendation

**Send the Mens email to the whole customer base.** Even at the low end of its confidence interval it
clears $1,400 per 10,000 customers, and the break-even cost per email is about $0.31, six times the
assumed cost. The uplift model finds no subgroup worth excluding, so targeting adds cost without profit.

**If the Womens email is used, do not send it to everyone.** Excluding the bottom ~10% of customers
by predicted uplift raises profit by roughly a third, because that group shows a *negative* response.
Even so, the Womens email earns less than half of what the Mens email earns per customer, so as a
single campaign the Mens email is the better use of the send.

Per 10,000 customers, the recommended policy (Mens to everyone) is worth about **$2,600 in
incremental profit** over two weeks vs. about $1,200 for the naive alternative (Womens to everyone),
and $0 for not emailing.

## When would the recommendation change?

- **Mens email:** stays "everyone" until cost per email passes roughly $0.20 at a 40% margin. Above
  $0.30 per email it becomes marginal; above $0.50 it loses money. Targeting the top 40% only makes
  sense in that expensive-email zone.
- **Womens email:** "top 90%" is the answer across almost all realistic cost/margin combinations. It
  stops being worth sending at all above about $0.20 per email at a 40% margin.
- **Margin:** each 10-point rise in margin adds roughly $770 per 10,000 to the Mens email's profit.

## Risks and limitations
- **Wide intervals.** The Womens "everyone" policy's CI runs from $201 to $2,226. Treat point
  estimates as central guesses, not promises.
- **Optimistic targeting estimate.** The best X% was chosen on the same data used to evaluate it.
  The true gain from targeting is probably a little smaller than +29%. A holdout campaign would confirm.
- **Two weeks only.** Repeated emailing may cause fatigue or unsubscribes that this data cannot show.
- **Assumed costs.** $0.05 and 40% are placeholders. The break-even figures let a manager plug in
  real numbers.
- **One-email framing.** We compared each email against control separately. A "send each customer
  whichever email the model predicts is better" policy is a natural next step.

## The one-sentence version for the memo
Send the Mens email to every customer: it roughly doubles conversion, is profitable up to about
$0.30 per email, and no customer group appears worse off for receiving it.
