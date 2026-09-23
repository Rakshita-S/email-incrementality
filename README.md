# Who Should We Email? An Incrementality and Targeting Study

Analysis of the Hillstrom "MineThatData" randomized email experiment (64,000 customers,
three arms: Mens E-Mail, Womens E-Mail, No E-Mail).

**Question:** Did the emails cause extra sales, and who should we email to maximize profit?

## Project structure

```
data/raw/          Raw CSV (not committed to git)
sql/               Postgres schema, load, and analysis queries
src/               Python analysis scripts, run in order
outputs/           Tables and figures produced by the scripts
docs/              Metric dictionary, memo, notes
notebooks/         Exploratory work
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then edit DATABASE_URL
```

Load into Postgres:
```bash
psql -U postgres -f sql/01_schema.sql
psql -U postgres -d hillstrom -f sql/02_load.sql
```

Run the Phase 1 scripts:
```bash
python src/01_sanity_checks.py
python src/02_randomization_check.py
```

## Phases
1. Setup and sanity checks (this folder so far)
2. Experiment analysis: lift, confidence intervals, power, incrementality vs. attribution
3. Segments and uplift model
4. Profit-based targeting policy
5. Dashboard, automated readout, memo

## Data
Hillstrom, K. (2008). MineThatData E-Mail Analytics Data Mining Challenge.
Check the license and column definitions on the source page before publishing.

## Assumptions and limitations
- Outcomes cover two weeks only; no long-term effects measured.
- No unsubscribe or fatigue data.
- Cost per email and margin are assumptions, stated explicitly in Phase 4.
