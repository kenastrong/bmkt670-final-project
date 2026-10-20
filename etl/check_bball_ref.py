import pandas as pd

seasons = [2022, 2023, 2024, 2025, 2026]

# home/away column (4) not labeled (@ = away)
expected = {"Date", "Unnamed: 4", "Opp", "W/L", "R", "RA",
            "Rank", "Streak", "Attendance"}

for season in seasons:
    data = f"data/manual/bballref_dodgers_{season}.csv"
    df = pd.read_csv(data)
    print(f"Loaded {len(df)} rows")
    print("Columns:", list(df.columns))

    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")