import pandas as pd

data = "data/manual/bballref_dodgers_2025.csv"

df = pd.read_csv(data)
print(f"Loaded {len(df)} rows")
print("Columns:", list(df.columns))

# home/away column (4) not labeled (@ = away)
expected = {"Date", "Unnamed: 4", "Opp", "W/L", "R", "RA",
            "Rank", "Streak", "Attendance"}
missing = expected - set(df.columns)
if missing:
    raise ValueError(f"Missing columns: {missing}")