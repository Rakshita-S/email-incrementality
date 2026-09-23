-- Run from the project root: psql -U postgres -d hillstrom -f sql/02_load.sql
\copy customers FROM 'data/raw/hillstrom.csv' WITH (FORMAT csv, HEADER true);
SELECT COUNT(*) AS rows_loaded FROM customers;
