import json
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

seasons = [2022, 2023, 2024, 2025, 2026]
split = {2022: "train", 2023: "train", 2024: "train", 2025: "validate", 2026: "test"}
dodgers_id = 119

RAW = Path("data/raw")
MANUAL = Path("data/manual")
CLEAN = Path("data/clean")
CLEAN.mkdir(parents=True, exist_ok=True)

# Baseball-Reference team codes -> MLB team ids.
# The Athletics were OAK through 2024 and ATH from 2025: both map to 133.
bballref_to_mlb = {
    "ARI": 109, "ATL": 144, "BAL": 110, "BOS": 111, "CHC": 112, "CHW": 145,
    "CIN": 113, "CLE": 114, "COL": 115, "DET": 116, "HOU": 117, "KCR": 118,
    "LAA": 108, "LAD": 119, "MIA": 146, "MIL": 158, "MIN": 142, "NYM": 121,
    "NYY": 147, "OAK": 133, "ATH": 133, "PHI": 143, "PIT": 134, "SDP": 135,
    "SFG": 137, "SEA": 136, "STL": 138, "TBR": 139, "TEX": 140, "TOR": 141,
    "WSN": 120,
}
nl_west_rivals = {109, 115, 135, 137}  # Dodgers division rivals: D-backs, Rockies, Padres, Giants

# MLB team ids -> MLB's own abbreviations, so the tables are easier to read
mlb_abbrev = {
    108: "LAA", 109: "AZ", 110: "BAL", 111: "BOS", 112: "CHC", 113: "CIN",
    114: "CLE", 115: "COL", 116: "DET", 117: "HOU", 118: "KC", 119: "LAD",
    120: "WSH", 121: "NYM", 133: "ATH", 134: "PIT", 135: "SD", 136: "SEA",
    137: "SF", 138: "STL", 139: "TB", 140: "TEX", 141: "TOR", 142: "MIN",
    143: "PHI", 144: "ATL", 145: "CWS", 146: "MIA", 147: "NYY", 158: "MIL",
}

print("Total Game Schedule Cleaned")
rows = []
for season in seasons:
    with open(RAW / f"mlb_schedule_{season}_raw.json") as f:
        data = json.load(f)
    for day in data["dates"]:
        for g in day["games"]:
            home = g["teams"]["home"]
            away = g["teams"]["away"]
            is_home = home["team"]["id"] == dodgers_id
            if is_home:
                us, opp = home, away
            else:
                us, opp = away, home

            # leagueRecord is the record AFTER this game, so take this
            # game's result back out to get the opponent's record going into the game
            wins = opp.get("leagueRecord", {}).get("wins", 0)
            losses = opp.get("leagueRecord", {}).get("losses", 0)
            if opp.get("isWinner") is True:
                wins -= 1
            elif opp.get("isWinner") is False:
                losses -= 1
            if wins + losses > 0:
                opp_pct = wins / (wins + losses)
            else:
                opp_pct = np.nan

            rows.append({
                "game_id": g["gamePk"], # key that links all tabels
                "date_id": g["officialDate"], # key to dim date 
                "season": season, 
                "game_type": g["gameType"],
                "status": g["status"]["detailedState"], # used to filter out postponed games
                "is_home": is_home,
                "venue": g["venue"]["name"],
                "game_date_utc": g["gameDate"], # align time stamps 
                "day_night": g.get("dayNight"),
                "doubleheader_game": g.get("gameNumber", 1),
                "probable_pitcher": us.get("probablePitcher", {}).get("fullName"), # dashboard
                "opponent_id": opp["team"]["id"], # key to dim opponent
                "opponent_name": opp["team"]["name"], # makes names readable 
                "opp_win_pct_before": opp_pct, # derived feature
            })

mlb = pd.DataFrame(rows)
print(f"  read {len(mlb)} games") # gives number of rows before dropping any 

before = len(mlb)
mlb = mlb[mlb["game_type"] == "R"] # drops any games that were not considered regular season games
print(f"  dropped {before - len(mlb)} spring training, exhibition, and postseason games")

before = len(mlb)
mlb = mlb[~mlb["status"].str.contains("Postponed|Cancelled")] # postponed game is listed twice: once as "Postponed", once on its make-up date
mlb = mlb.drop_duplicates("game_id", keep="last")
print(f"  dropped {before - len(mlb)} postponed, cancelled, or duplicate listings")

# convert times and dates to one format and one time zoe, gameDate is in UTC convert to Pacific standard time
mlb["start_time_local"] = (
    pd.to_datetime(mlb["game_date_utc"], utc=True)
    .dt.tz_convert("America/Los_Angeles")
    .dt.tz_localize(None)
)
mlb["date_id"] = pd.to_datetime(mlb["date_id"])
print(f"  kept {len(mlb)} regular-season games")
print("")

# clean baseball ref files and align them with the correct game
print("Baseball Reference Data Cleaned")
parts = []
for season in seasons:
    b = pd.read_csv(MANUAL / f"bballref_dodgers_{season}.csv", dtype=str)
    b = b[pd.to_numeric(b["Gm#"], errors="coerce").notna()]  # drop repeated header rows
    b["season"] = season
    parts.append(b)
bref = pd.concat(parts, ignore_index=True)
print(f"  read {len(bref)} games")

# "Saturday Sep 13 (1)" -> doubleheader game 1, date 2025-09-13
bref["doubleheader_game"] = bref["Date"].str.extract(r"\((\d)\)")[0].fillna(1).astype(int)
date_text = bref["Date"].str.replace(r"\s*\(\d\)", "", regex=True)
bref["date_id"] = pd.to_datetime(
    date_text + " " + bref["season"].astype(str), format="%A %b %d %Y"
)

bref["bref_abbrev"] = bref["Opp"]
bref["bref_opp_id"] = bref["Opp"].map(bballref_to_mlb)
bref["bref_is_home"] = bref["Unnamed: 4"] != "@"
bref["dodgers_runs"] = pd.to_numeric(bref["R"])
bref["opp_runs"] = pd.to_numeric(bref["RA"])
bref["win_loss"] = bref["W/L"].str[0]  # "W-wo" -> "W" or "L"
bref["division_rank"] = pd.to_numeric(bref["Rank"], errors="coerce")
streak = bref["Streak"].fillna("")  # "+++" -> 3, "--" -> -2
bref["streak"] = np.where(streak.str.startswith("+"), streak.str.len(), -streak.str.len())
bref["attendance"] = pd.to_numeric(bref["Attendance"].str.replace(",", ""),
                                   errors="coerce")

unknown = bref.loc[bref["bref_opp_id"].isna(), "Opp"].unique()
if len(unknown) > 0:
    raise ValueError(f"Add these team codes to bballref_to_mlb: {list(unknown)}")

# align on a common key: match each Bball-Ref row to its MLB game by date and
# doubleheader game number, then make sure the opponent agrees.
bref = bref[["date_id", "doubleheader_game", "bref_abbrev", "bref_opp_id",
             "bref_is_home", "dodgers_runs", "opp_runs", "win_loss",
             "division_rank", "streak", "attendance"]]
fact_game = mlb.merge(bref, on=["date_id", "doubleheader_game"], how="left")

wrong_opp = fact_game["bref_opp_id"].notna() & (
    fact_game["bref_opp_id"] != fact_game["opponent_id"])
print(f"  matched {fact_game['bref_opp_id'].notna().sum()} games on date + game number")
print(f"  {fact_game['bref_opp_id'].isna().sum()} MLB games had no Bball-Ref match")
print(f"  {wrong_opp.sum()} matches had a different opponent")

if wrong_opp.sum() > 0:
    raise ValueError("Bball-Ref and MLB disagree on an opponent. Check those dates.")

flips = (fact_game["bref_opp_id"].notna()
         & (fact_game["bref_is_home"] != fact_game["is_home"])).sum()
print(f"  {flips} games where MLB and Bball-Ref disagree on home/away")
print("")

print("Baseball Savant Data Cleaned")
savant = pd.read_csv(MANUAL / "savant_data2022-2026.csv", encoding="utf-8-sig")
print(f"  read {len(savant)} rows")

if (savant["player_name"] != "LAD").any():
    raise ValueError("Some Savant rows are not Dodgers team totals")

# match column names to schema names
fact_stats = savant.rename(columns={
    "game_pk": "game_id",
    "pitches": "pit_pitches",
    "swing_miss_percent": "pit_whiff_pct",
    "velocity": "pit_avg_velo",
    "pitcher_run_value_per_100": "pit_run_value",
    "hits": "opp_hits",
    "ba": "opp_avg",
    "obp": "opp_obp",
    "slg": "opp_slg",
})

# keep only needed columns and games 
fact_stats = fact_stats[["game_id", "pit_pitches", "pit_whiff_pct", "pit_avg_velo",
                         "pit_run_value", "opp_hits", "opp_avg", "opp_obp", "opp_slg"]]
fact_stats = fact_stats.drop_duplicates("game_id")
fact_stats = fact_stats[fact_stats["game_id"].isin(fact_game["game_id"])]
print(f"  matched {len(fact_stats)} games on game_pk")
print(f"  {len(fact_game) - len(fact_stats)} games have no Statcast row")
print(" ")

# dimension tables
dim_date = pd.DataFrame({"date_id": fact_game["date_id"].drop_duplicates()})
dim_date["season"] = dim_date["date_id"].dt.year
dim_date["month"] = dim_date["date_id"].dt.month
dim_date["day_of_week"] = dim_date["date_id"].dt.day_name()
dim_date["is_weekend"] = dim_date["day_of_week"].isin(["Friday", "Saturday", "Sunday"])
holidays = USFederalHolidayCalendar().holidays(start="2022-01-01", end="2026-12-31")
dim_date["is_holiday"] = dim_date["date_id"].isin(holidays)
dim_date = dim_date.sort_values("date_id")

# one row per team, last keeps the most recent name and code OAK switch to ATH
dim_opponent = (
    fact_game.sort_values("start_time_local")
    .groupby("opponent_id", as_index=False)
    .agg(opponent_name=("opponent_name", "last"), bref_abbrev=("bref_abbrev", "last"))
)

dim_opponent["is_nl_west"] = dim_opponent["opponent_id"].isin(nl_west_rivals)
dim_opponent["abbreviation"] = dim_opponent["opponent_id"].map(mlb_abbrev)
print("Dimension Table Count Check")
print(f"  {len(dim_date)} dates, {len(dim_opponent)} opponents")
print(" ")

# reshaping wide tables was not needed as all three sources are already one row
# per game (no week-by-week or month-by-month columns), so no melt is needed as shown in assignment instructions

# derived features 
# .shift(1) moves every value down one row, so each game only sees the games before it
g = fact_game.merge(fact_stats[["game_id", "pit_whiff_pct"]], on="game_id", how="left")
g = g.sort_values("start_time_local").reset_index(drop=True)
g["won"] = np.where(g["win_loss"].isna(), np.nan, (g["win_loss"] == "W").astype(float))
g["run_diff"] = g["dodgers_runs"] - g["opp_runs"]

by_season = g.groupby("season")
g["win_pct_before"] = by_season["won"].transform(
    lambda x: x.shift(1).expanding().mean())
g["win_pct_last10"] = by_season["won"].transform(
    lambda x: x.shift(1).rolling(10, min_periods=1).mean())
g["run_diff_last10"] = by_season["run_diff"].transform(
    lambda x: x.shift(1).rolling(10, min_periods=1).mean())
g["whiff_pct_last10"] = by_season["pit_whiff_pct"].transform(
    lambda x: x.shift(1).rolling(10, min_periods=1).mean())
g["division_rank_before"] = by_season["division_rank"].shift(1)
g["streak_before"] = by_season["streak"].shift(1)

# filter to prediction unit
print("Filtered Data to Predicted Unit")
# 2026 season the stadium was called UNIQLO Field at Dodger Stadium
is_ds_home = g["is_home"] & g["venue"].str.contains("Dodger Stadium") 
print(f"  kept {is_ds_home.sum()} home games at Dodger Stadium")
print(f"  dropped {(~g['is_home']).sum()} away games")
print(f"  dropped {(g['is_home'] & ~is_ds_home).sum()} 'home' games not played at Dodger Stadium")
home = g[is_ds_home].copy()

# attendance features look only at previous home games across the seasons
home["att_last5_home"] = home["attendance"].shift(1).rolling(5, min_periods=1).mean()
home["days_since_last_home"] = home["date_id"].diff().dt.days # fans may be more likey to attend a game after the team has been gone

before = len(home)
home = home[home["attendance"].notna()]
print(f"  dropped {before - len(home)} home games with no attendance recorded")
print(" ")

# build ML table
ml = home.merge(dim_date.drop(columns="season"), on="date_id", how="left")
ml = ml.merge(dim_opponent[["opponent_id", "is_nl_west", "abbreviation"]],
              on="opponent_id", how="left")
ml = ml.rename(columns={"abbreviation": "opponent_abbrev"})

ml["split"] = ml["season"].map(split)
ml["start_hour"] = ml["start_time_local"].dt.hour

# encode categories as 0/1
ml["is_night"] = (ml["day_night"] == "night").astype(int)
ml["is_weekend"] = ml["is_weekend"].astype(int)
ml["is_holiday"] = ml["is_holiday"].astype(int)
ml["is_nl_west"] = ml["is_nl_west"].astype(int)
for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
    ml["dow_" + day[:3].lower()] = (ml["day_of_week"] == day).astype(int)

# handle missing values (see docs/missing_data.md) medians use training rows only
train = ml["split"] == "train"
offseason_gap = ml.loc[ml["days_since_last_home"] > 60, "days_since_last_home"].median()
fills = {
    "win_pct_before": 0.5,
    "win_pct_last10": 0.5,
    "run_diff_last10": 0,
    "division_rank_before": 1,
    "streak_before": 0,
    "opp_win_pct_before": 0.5,
    "whiff_pct_last10": ml.loc[train, "whiff_pct_last10"].median(),
    "att_last5_home": ml.loc[train, "attendance"].median(),
    "days_since_last_home": offseason_gap,
}

for col, value in fills.items():
    n_missing = ml[col].isna().sum()
    if n_missing > 0:
        print(f"  filled {n_missing} missing {col} with {value}")
        ml[col] = ml[col].fillna(value)

ml = ml[["game_id", "date_id", "season", "split", "attendance", "month",
         "start_hour", "opponent_name", "opponent_abbrev", "opp_win_pct_before",
         "is_weekend", "is_holiday", "is_night", "is_nl_west", "dow_mon", "dow_tue",
         "dow_wed", "dow_thu", "dow_fri", "dow_sat", "dow_sun", "win_pct_before",
         "win_pct_last10", "run_diff_last10", "division_rank_before",
         "streak_before", "whiff_pct_last10", "att_last5_home",
         "days_since_last_home"]]

ml = ml.round({"opp_win_pct_before": 3, "win_pct_before": 3, "win_pct_last10": 3,
               "run_diff_last10": 2, "whiff_pct_last10": 2, "att_last5_home": 1})
print(" ")

# save CSV files per table and find % missing values if any
print("Save CSV files")
fact_game = fact_game[["game_id", "date_id", "opponent_id", "season", "game_type",
                       "is_home", "venue", "start_time_local", "day_night",
                       "doubleheader_game", "probable_pitcher", "opp_win_pct_before",
                       "dodgers_runs", "opp_runs", "win_loss", "division_rank",
                       "streak", "attendance"]].round({"opp_win_pct_before": 3})

tables = {
    "dim_date": dim_date,
    "dim_opponent": dim_opponent,
    "fact_game": fact_game,
    "fact_stats": fact_stats,
    "ml_features_attendance": ml,
}

for name, df in tables.items():
    df.to_csv(CLEAN / f"{name}.csv", index=False)
    print(f"  saved {name}.csv ({len(df)} rows)")
    missing = df.isna().sum()
    if missing.sum() > 0:
        print(missing[missing > 0].to_string())