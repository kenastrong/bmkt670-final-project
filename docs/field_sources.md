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
| dim_opponent | is_nl_west | Calculated in Python | True if the opponent is SF, SD, AZ, or COL | Feature (division rivals) |
| dim_opponent | abbreviation | Created in Python | Legend from MLB team Id to MLB abbreviation (137 → SF) | Readable label for the dashboard |
| fact_game | game_id | MLB Stats API | gamePk | Key: one ID per game; links stats to games |
| fact_game | date_id | MLB Stats API | officialDate | Key: links to dim_date |
| fact_game | opponent_id | MLB Stats API | The team id in the game that isn't the Dodgers (119) | Key: links to dim_opponent |
| fact_game | season | MLB Stats API | Season of the schedule request | Splits data by season/year |
| fact_game | game_type | MLB Stats API | gameType | Filters to regular season games only (R) |
| fact_game | is_home | MLB Stats API | True if teams.home.team.id = 119 (Dodgers) | Filters to home games |
| fact_game | venue | MLB Stats API | venue.name | Filters to Dodger Stadium only |
| fact_game | start_time_local | MLB Stats API | gameDate (UTC) converted to Pacific time | Feature |
| fact_game | day_night | MLB Stats API | dayNight | Feature |
| fact_game | doubleheader_game | MLB Stats API | gameNumber | Matches doubleheaders to Bball-Ref's (1)/(2) dates |
| fact_game | probable_pitcher | MLB Stats API | Dodgers' probablePitcher.fullName | Feature (star pitchers may draw more fans when known before the game) 
| fact_game | opp_win_pct_before | Calculated in Python | Opponent's leagueRecord after the game minus this game's result | Feature (opponent strength before game) |
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
| ml_features_attendance | game_id | Joined | copied from fact_game.game_id | Key: one row per home game which links back to fact_game for other game details |
| ml_features_attendance | date_id | Joined | copied from fact_game.date_id | Key: links to dim_date which lets the dashboard list upcoming games by date |
| ml_features_attendance | season | Joined | copied from fact_game.season | Defines which year a game belongs to |
| ml_features_attendance | split | Calculated in Python | 2022–2024 = train, 2025 = validate, 2026 = test | Splits the data by time so the model is tested on seasons it hasn't seen yet |
| ml_features_attendance | attendance | Joined | copied from fact_game.attendance | Target - training the model |
| ml_features_attendance | month | Joined | dim_date.month | Feature |
| ml_features_attendance | start_hour | Calculated in Python | Hour of start_time_local | Feature (day vs. evening comparison) |
| ml_features_attendance | opponent_name | Joined | dim_opponent.opponent_name | Dashboard - readable label |
| ml_features_attendance | opponent_abbrev | Joined | dim_opponent.abbreviation | Dashboard - shortened readable label |
| ml_features_attendance | opp_win_pct_before | Joined | fact_game.opp_win_pct_before (opponent's record going into the game) | Feature |
| ml_features_attendance | is_weekend | Joined | dim_date.is_weekend as 0/1 | Encoded feature |
| ml_features_attendance | is_holiday | Joined | dim_date.is_holiday as 0/1 | Encoded feature |
| ml_features_attendance | is_night | Calculated in Python | 1 if day_night = "night", else 0 | Encoded feature |
| ml_features_attendance | is_nl_west | Joined | dim_opponent.is_nl_west as 0/1 | Encoded feature |
| ml_features_attendance | dow_mon … dow_sun | Calculated in Python | One 0/1 column per day of week (7 columns) | Encoded feature |
| ml_features_attendance | win_pct_before | Calculated in Python | Season win % from earlier games only | Derived feature |
| ml_features_attendance | win_pct_last10 | Calculated in Python | Win % over the previous 10 games | Derived feature |
| ml_features_attendance | run_diff_last10 | Calculated in Python | Average (runs − runs allowed) over the previous 10 games | Derived feature |
| ml_features_attendance | division_rank_before | Calculated in Python | Previous game's division rank | Derived feature |
| ml_features_attendance | streak_before | Calculated in Python | Previous game's streak | Derived feature |
| ml_features_attendance | whiff_pct_last10 | Calculated in Python | Average pit_whiff_pct over the previous 10 games | Derived feature |
| ml_features_attendance | att_last5_home | Calculated in Python | Average attendance of the previous 5 home games | Derived feature |
| ml_features_attendance | days_since_last_home | Calculated in Python | Days since the previous home game | Derived feature |

## Source fields used but not stored
- **Baseball-Refernce `Date`** (e.g., "Thursday Mar 27"): has no year. Season is added, and the date is used with `Opp` to match each Bball-Ref row to its MLB game.
- **Baseball-Reference `Gm#`**: used to drop repeated header rows.
- **Baseball-Reference unlabeled home/away column** (`@` = away): used to double-check MLB's is_home.
- **MLB `gameDate`** (UTC): converted to Pacific time to produce start_time_local.
- **MLB `status.detailedState`**: filters out postponed and cancelled listings. A postponed game appears again on its make-up date with the same gamePk (4 duplicate listings removed).
- **MLB `leagueRecord` and `isWinner`**: used to calculate opp_win_pct_before.
- **Savant `player_name`** (119 / LAD): confirm every row is Dodgers team totals.