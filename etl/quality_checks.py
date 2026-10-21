import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

seasons = [2022, 2023, 2024, 2025, 2026]

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

def query(sql):
    cur.execute(sql)
    return cur.fetchone()[0]

def show(passed, label, value):
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {label}: {value}")


# No duplicate games in fact_game
duplicates = query("SELECT COUNT(*) - COUNT(DISTINCT game_id) FROM fact_game;")
show(duplicates == 0, "Duplicate game_ids in fact_game", duplicates)

# Valid range: attendance above 0 and no more than Dodger Stadium's 56,000 capacity
bad = query("""
    SELECT COUNT(*) FROM ml_features_attendance
    WHERE attendance <= 0 OR attendance > 56000;
""")
show(bad == 0, "Home games with impossible attendance", bad)

# Valid range: any win percentages between 0 and 1
bad = query("""
    SELECT COUNT(*) FROM ml_features_attendance
    WHERE win_pct_before NOT BETWEEN 0 AND 1
       OR win_pct_last10 NOT BETWEEN 0 AND 1
       OR opp_win_pct_before NOT BETWEEN 0 AND 1;
""")
show(bad == 0, "Win % values outside 0-1", bad)

# Timestamps align: Pacific start time falls on the game's actual date
bad = query("""
    SELECT COUNT(*) FROM fact_game
    WHERE start_time_local::date <> date_id AND venue LIKE '%Dodger Stadium%';
""")
show(bad == 0, "Home games whose start date doesn't match date_id", bad)

# Missingness: % of ML rows missing any core feature (limit 5%)
pct = query("""
    SELECT ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ml_features_attendance), 1)
    FROM ml_features_attendance
    WHERE win_pct_before IS NULL OR win_pct_last10 IS NULL OR run_diff_last10 IS NULL
       OR whiff_pct_last10 IS NULL OR att_last5_home IS NULL
       OR opp_win_pct_before IS NULL OR days_since_last_home IS NULL;
""")
show(pct < 5, "% of ML rows missing a core feature (limit 5%)", f"{pct}%")

# No orphaned rows: every ML row points to a real game
orphans = query("""
    SELECT COUNT(*) FROM ml_features_attendance m
    LEFT JOIN fact_game f ON m.game_id = f.game_id
    WHERE f.game_id IS NULL;
""")
show(orphans == 0, "ML rows with no matching game", orphans)

# Row counts reconcile: games in the raw Baseball-Reference files vs. matched games
bref_rows = 0
for season in seasons:
    b = pd.read_csv(f"data/manual/bballref_dodgers_{season}.csv", dtype=str)
    bref_rows += pd.to_numeric(b["Gm#"], errors="coerce").notna().sum()
matched = query("SELECT COUNT(*) FROM fact_game WHERE win_loss IS NOT NULL;")
show(bref_rows == matched, "Baseball-Reference games raw vs matched", f"{bref_rows} vs {matched}")

conn.close()