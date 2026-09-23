-- Run as: psql -U postgres -f sql/01_schema.sql
CREATE DATABASE hillstrom;
\c hillstrom

DROP TABLE IF EXISTS customers;
CREATE TABLE customers (
    recency          INT,       -- months since last purchase
    history_segment  TEXT,      -- bucketed past spend
    history          NUMERIC,   -- past year spend in dollars
    mens             INT,       -- 1 = bought mens merchandise in past year
    womens           INT,       -- 1 = bought womens merchandise in past year
    zip_code         TEXT,      -- Urban / Suburban / Rural
    newbie           INT,       -- 1 = new customer in past 12 months
    channel          TEXT,      -- Phone / Web / Multichannel
    segment          TEXT,      -- treatment arm: Mens E-Mail / Womens E-Mail / No E-Mail
    visit            INT,       -- visited site within 2 weeks
    conversion       INT,       -- purchased within 2 weeks
    spend            NUMERIC    -- dollars spent within 2 weeks
);
