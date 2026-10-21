# Predicting Los Angeles Dodgers Home Game Attendance 

## Business Question
How many fans will attend an upcoming Los Angeles Dodgers home game at Dodger Stadium?

## Target Variable
Game Attendance

## Prediction Unit
One row in my ML feature table = one Dodgers 2025 regular-season home game at Dodger Stadium

## Data Sources
| Source | What it provides | Access |
| MLB Stats API | game ID, date, start time, game type, home/away team names and IDs, venue, day/night, doubleheader game number, probable starting pitcher | Free JSON API pulled from https://statsapi.mlb.com/api/v1/schedule?sportId=1&teamId=119&season=YEAR&hydrate=probablePitcher
| Baseball-Reference | date, opponent, home/away, W/L, runs for and against, division rank, streak, attendance | Hand-downloaded CSV on October 20, 2026, URL: https://www.baseball-reference.com/teams/LAD/YEAR-schedule-scores.shtml, scroll to Team Game-by-Game Schedule, Share & Export, Get table as CSV, Copy CSV text, paste into new file in data/manual as bballref_dodgers_2025.csv |
| Baseball Savant (Statcast) | pitches, game_date, game_PK, whiff%, pitch velocity, pitcher run value, and opponents hits, batting average, and slugging against Dodgers pitchers | Hand-downloaded CSV on October 20, 2026, URL: https://baseballsavant.mlb.com/statcast_search?hfGT=R%7C&hfSea=2026%7C2025%7C2024%7C2023%7C2022%7C&player_type=pitcher&hfTeam=119%7C&group_by=team-date&sort_col=pitches&sort_order=desc#results, Player Type = Pitchers, Season = 2022-2026, Season Type = Regular Season, Team = Dodgers, Group By: Team & Game, exported as CSV and saved in data/manual as savant.csv |


## How to Run
1. Create and activate a virtual environment
2. Install packages: pip install -r requirements.txt
3. Create a .env file with DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD 
4. Pull the data: run each script in etl/ (python etl/extract_mlb_api.py, python etl/check_bball_ref.py, python etl/check_savant.py)  
5. Build the database: run sql/schema.sql in pgAdmin or psql
6. Confirm it worked: python db_check.py (should print all table names)
7. Rebuild database: python run_pipeline.py (extract -> transform -> load -> quality checks)


## AI Usage
I used Claude to help me troubleshoot my Git and Postgres setup, help plan what variables to pull from each of my data sources, help draft starter scripts and help draft my field-source table. Claude helped me plan how to clean and combine the sources for the database and ML table and helped draft the code for this process in the trasnform.py. It gave me ideas on how to handle my missing-data and explained some of the complex code line by line for I could understand what each line of code in each program does in the full scope of my project. I also used Claude to help when VS code threw errors to find where my mistakes were, many of which were small spelling errors deep in the code. I chose the final variables, related them to their respective tables, tested, ran, and adjusted everything from this help myself manually.