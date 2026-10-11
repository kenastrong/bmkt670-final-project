# Predicting Los Angelos Dodgers Home Game Attendance 

## Business Question
How many fans will attend an upcoming Los Angeles Dodgers home game at Dodger Stadium?

## Target Variable
Game Attendance

## Prediction Unit
One row in my ML feature table = one Dodgers 2025 regular-season home game at Dodger Stadium

## Data Sources
| Source | What it provides | Access |
| MLB Stats API | game ID, date, start time, game type, home/away team names and IDs, venue, day/night, doubleheader game number, probable starting pitcher | Free JSON API pulled from https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=119&season=2025&hydrate=probablePitcher
| Baseball-Reference | date, opponent, home/away, W/L, runs for and against, division rank, streak, attendance | Hand-downloaded CSV on October 11, 2026, URL: https://www.baseball-reference.com/teams/LAD/2025-schedule-scores.shtml, scroll to Team Game-by-Game Schedule, Share & Export, Get table as CSV, Copy CSV text, paste into new file in data/manual as bballref_dodgers_2025.csv |
| Baseball Savant (Statcast) | pitches, game_date, game_PK, whiff%, pitch velocity, pitcher run value, and opponents hits, batting average, and slugging against Dodgers pitchers | Hand-downloaded CSV on October 11, 2026, URL: https://baseballsavant.mlb.com/statcast_search?hfGT=R%7C&hfSea=2025%7C&player_type=pitcher&hfTeam=119%7C&group_by=team-date&sort_col=pitches&sort_order=desc#results, Player Type = Pitchers, Season = 2025, Season Type = Regular Season, Team = Dodgers, Group By: Team & Game, exported as CSV and saved in data/manual as savant.csv |


## How to Run
1. Create and activate a virtual environment
2. Install packages: pip install -r requirements.txt
3. Create a .env file with DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD 
4. Pull the data: run each script in etl/ (e.g., python etl/extract_games.py)  
5. Build the database: run sql/schema.sql in pgAdmin or psql
6. Confirm it worked: python db_check.py (should print all table names)


## AI Usage
I used Claude to help me troubleshoot my Git and Postgres setup, help plan what variables to pull from each of my data sources, help draft starter scripts and help draft my field-source table. I chose variables, ralted them to the tables, tested, ran, and adjusted everything from this help myself manually.