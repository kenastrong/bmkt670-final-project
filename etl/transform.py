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

# clean baseball ref files and align them with the correct game
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
    raise ValueError(f"Add these team codes to BREF_TO_MLB: {list(unknown)}")

# align on a common key: match each Bball-Ref row to its MLB game by date and
# doubleheader game number, then make sure the opponent agrees.
bref = bref[["date_id", "doubleheader_game", "bref_abbrev", "bref_opp_id",
             "bref_is_home", "dodgers_runs", "opp_runs", "win_loss",
             "division_rank", "streak", "attendance"]]
fact_game = mlb.merge(bref, on=["date_id", "doubleheader_game"], how="left")

wrong_opp = fact_game["bref_opp_id"].notna() & (
    fact_game["bref_opp_id"] != fact_game["opponent_id"])
print(f"  matched {fact_game['bref_opp_id'].notna().sum()} games on date + game number")
print(f"  {fact_game['bref_opp_id'].isna().sum()} MLB games had no B-Ref match")
print(f"  {wrong_opp.sum()} matches had a different opponent")

problems = fact_game[wrong_opp | fact_game["bref_opp_id"].isna()]
print("\n  Problem games by season:")
print(problems.groupby("season").size().to_string())
print(problems[["season", "date_id", "opponent_name", "bref_abbrev"]].head(10).to_string())

if wrong_opp.sum() > 0:
    raise ValueError("B-Ref and MLB disagree on an opponent. Check those dates.")

flips = (fact_game["bref_opp_id"].notna()
         & (fact_game["bref_is_home"] != fact_game["is_home"])).sum()
print(f"  {flips} games where MLB and B-Ref disagree on home/away")