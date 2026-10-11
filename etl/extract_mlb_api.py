import json
from pathlib import Path
import requests 

URL = ("https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=119&season=2025&hydrate=probablePitcher")

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

r = requests.get(URL, timeout=30)
r.raise_for_status()
data = r.json()

print("URL requested:", r.url)
print("totalGames reported by API:", data.get("totalGames"))

with open(RAW / "mlb_schedule_2025_raw.json", "w") as f:
    json.dump(data, f)

n_games = sum(len(d["games"]) for d in data.get("dates", []))
print(f"Downloaded {n_games} games")