-- Pre-treatment covariates should be balanced across arms.
-- These were fixed BEFORE the email was sent, so any imbalance is chance or a broken randomizer.
SELECT segment,
       COUNT(*)                        AS n,
       ROUND(AVG(recency), 3)          AS avg_recency,
       ROUND(AVG(history), 2)          AS avg_history,
       ROUND(AVG(mens)*100, 2)         AS pct_mens,
       ROUND(AVG(womens)*100, 2)       AS pct_womens,
       ROUND(AVG(newbie)*100, 2)       AS pct_newbie,
       ROUND(AVG((channel = 'Web')::int)*100, 2)    AS pct_web,
       ROUND(AVG((channel = 'Phone')::int)*100, 2)  AS pct_phone,
       ROUND(AVG((zip_code = 'Urban')::int)*100, 2) AS pct_urban,
       ROUND(AVG((zip_code = 'Rural')::int)*100, 2) AS pct_rural
FROM customers
GROUP BY segment
ORDER BY segment;
