-- Row count (expect 64,000)
SELECT COUNT(*) FROM customers;

-- Group sizes (expect ~21,300 each)
SELECT segment, COUNT(*) FROM customers GROUP BY segment ORDER BY segment;

-- Missing values
SELECT
  COUNT(*) - COUNT(spend)   AS missing_spend,
  COUNT(*) - COUNT(channel) AS missing_channel,
  COUNT(*) - COUNT(segment) AS missing_segment
FROM customers;

-- Spend should be 0 for non-converters
SELECT conversion, MIN(spend), MAX(spend), ROUND(AVG(spend), 2), COUNT(*)
FROM customers GROUP BY conversion;

-- Headline outcomes by arm
SELECT segment,
       COUNT(*)                      AS customers,
       ROUND(AVG(visit)*100, 2)      AS visit_rate_pct,
       ROUND(AVG(conversion)*100, 2) AS conversion_rate_pct,
       ROUND(AVG(spend), 3)          AS spend_per_customer
FROM customers
GROUP BY segment
ORDER BY segment;
