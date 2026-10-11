import pandas as pd

data = "data/manual/savant_data.csv"

df = pd.read_csv(data)
print(f"Loaded {len(df)} rows")
print("Columns:", list(df.columns))

expected = {"game_pk", "game_date", "pitches", "swing_miss_percent",
            "velocity", "pitcher_run_value_per_100",
            "hits", "ba", "obp", "slg"}
missing = expected - set(df.columns)
if missing:
    raise ValueError(f"Missing columns: {missing}")