"""Shared paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "hillstrom.csv"
OUTPUTS = ROOT / "outputs"
OUTPUTS.mkdir(exist_ok=True)

CONTROL = "No E-Mail"
ARMS = ["Mens E-Mail", "Womens E-Mail", "No E-Mail"]
OUTCOMES = ["visit", "conversion", "spend"]
PRE_TREATMENT = ["recency", "history", "mens", "womens", "newbie", "channel", "zip_code"]
