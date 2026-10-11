# Where Each Field Comes From

| Table | Field | Comes from | How | Used for |
|---|---|---|---|---|
| dim_date | date_id | MLB Stats API | officialDate, converted to a date type | Key: links each game to its date|
| dim_date | season | MLB Stats API | season | Labels the season to ensure consistent use of 2025 data, could allow for other seasons to be added later on |
| dim_date | month | Calculated in Python | pandas `.dt.month` | Feature |
| dim_date | day_of_week | Calculated in Python | pandas `.dt.day_name()` | Feature |
| dim_date | is_weekend | Calculated in Python | True if Friday, Saturday, or Sunday | Feature |
| dim_date | is_holiday | Calculated in Python | pandas U.S. federal holiday calendar | Feature |
| dim_opponent | opponent_id | MLB Stats API | The team ID of whichever team in the game is not the Dodgers (119), from teams.home.team.id or teams.away.team.id | Key: links each game to its opponent |
| dim_opponent | opponent_name | MLB Stats API | The team name of whichever team in the game is not the Dodgers, from teams.home.team.name or teams.away.team.name  | Readable opponent name for ML table and dashboard, feature |
| dim_opponent | bref_abbrev | Created in Python | Hand-made map from each Bball-Ref code to its MLB team (SFG → San Francisco Giants) | Matches Bball-Ref rows to MLB games |
| fact_game | game_id | MLB Stats API | gamePk | Key: one ID per game; links stats to games |
| fact_game | date_id | MLB Stats API | officialDate | Key: links to dim_date |
| fact_game | opponent_id | MLB Stats API | The team id in the game that isn't the Dodgers (119) | Key: links to dim_opponent |
| fact_game | game_type | MLB Stats API | gameType | Filters to regular season games only (R) |
| fact_game | is_home | MLB Stats API | True if teams.home.team.id = 119 (Dodgers) | Filters to home games |
| fact_game | venue | MLB Stats API | venue.name | Filters to Dodger Stadium only |
| fact_game | start_time_local | MLB Stats API | gameDate (UTC) converted to Pacific time | Feature |
| fact_game | day_night | MLB Stats API | dayNight | Feature |
| fact_game | doubleheader_game | MLB Stats API | gameNumber | Matches doubleheaders to Bball-Ref's (1)/(2) dates |
| fact_game | probable_pitcher | MLB Stats API | Dodgers' probablePitcher.fullName | Feature (star pitchers may draw more fans when known before the game) |
| fact_game | dodgers_runs | Baseball-Reference | R, matched to each game by date and opponent | Builds win % and run-differential features |
| fact_game | opp_runs | Baseball-Reference | RA, matched by date and opponent | Builds win % and run-differential features |
| fact_game | win_loss | Baseball-Reference | W/L, first letter only | Builds recent win % feature |
| fact_game | division_rank | Baseball-Reference | Rank, matched by date and opponent | Builds a "rank going into the game" feature |
| fact_game | streak | Baseball-Reference | Streak (+ = wins, - = losses), matched by date and opponent | Builds a "streak going into the game" feature|
| fact_game | attendance | Baseball-Reference | Attendance, matched by date and opponent | Training the model on past attendance it learns from and is tested against |
| fact_stats | stats_id | Created by Postgres | Auto-numbered (SERIAL) | Key: primary key |
| fact_stats | game_id | Baseball Savant | game_pk, which equals MLB's gamePk | Key: links to fact_game |
| fact_stats | pit_pitches | Baseball Savant | pitches | Input to recent-pitching feature |
| fact_stats | pit_whiff_pct | Baseball Savant | swing_miss_percent | Input to recent-pitching feature |
| fact_stats | pit_avg_velo | Baseball Savant | velocity | Input to recent-pitching feature |
| fact_stats | pit_run_value | Baseball Savant | pitcher_run_value_per_100 | Input to recent-pitching feature |
| fact_stats | opp_hits | Baseball Savant | hits (hits allowed by Dodgers pitchers) | Input to recent-pitching feature |
| fact_stats | opp_avg | Baseball Savant | ba (opponents' batting average) | Input to recent-pitching feature |
| fact_stats | opp_obp | Baseball Savant | obp (opponents' on-base %) | Input to recent-pitching feature |
| fact_stats | opp_slg | Baseball Savant | slg (opponents' slugging %) | Input to recent-pitching feature |

## Source fields used but not stored
- **Baseball-Refernce `Date`** (e.g., "Thursday Mar 27"): has no year. 2025 is added, and the date is used with `Opp` to match each Bball-Ref row to its MLB game.
- **Baseball-Reference `Opp`**: matched through bballref_abbrev to find the opponent.
- **Baseball-Reference unlabeled home/away column** (`@` = away): used to double-check MLB's is_home.
- **MLB `gameDate`** (UTC): converted to Pacific time to produce start_time_local.
- **Savant `game_date`**: used to double-check the game_pk matches.
- **Savant `player_id` / `player_name`** (119 / LAD): confirm every row is Dodgers team totals.