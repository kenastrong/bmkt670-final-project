import json
from pathlib import Path

import requests

seasons = [2022, 2023, 2024, 2025, 2026]
URL = ("https://statsapi.mlb.com/api/v1/schedule")

RAW = Path("data/raw")
RAW.mkdir(parents=True, exist_ok=True)

for season in seasons:
    r = requests.get(
        URL,
        params={"sportId": 1, "teamId": 119, "season": season,
                "hydrate": "probablePitcher"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()

    with open(RAW / f"mlb_schedule_{season}_raw.json", "w") as f:
        json.dump(data, f)

    n_games = sum(len(d["games"]) for d in data.get("dates", []))
    print(f"{season}: downloaded {n_games} games")