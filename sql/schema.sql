DROP TABLE IF EXISTS ml_features_attendance CASCADE;
DROP TABLE IF EXISTS fact_stats CASCADE;
DROP TABLE IF EXISTS fact_game CASCADE;
DROP TABLE IF EXISTS dim_opponent CASCADE;
DROP TABLE IF EXISTS dim_date CASCADE;

-- One row = one calendar date that the Dodgers played on in 2025
CREATE TABLE dim_date (
    date_id      DATE PRIMARY KEY,
    season       INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    day_of_week  TEXT    NOT NULL,
    is_weekend   BOOLEAN NOT NULL,
    is_holiday   BOOLEAN NOT NULL
);

-- One row = one MLB team the Dodgers played in 2025
CREATE TABLE dim_opponent (
    opponent_id    INTEGER PRIMARY KEY,
    opponent_name  TEXT NOT NULL,
    bref_abbrev    TEXT,
    is_nl_west     BOOLEAN NOT NULL,
    abbreviation   TEXT NOT NULL
);

-- One row = one Dodgers game in 2025
CREATE TABLE fact_game (
    game_id            INTEGER PRIMARY KEY,
    date_id            DATE    NOT NULL REFERENCES dim_date(date_id),
    opponent_id        INTEGER NOT NULL REFERENCES dim_opponent(opponent_id),
    game_type          TEXT    NOT NULL,
    is_home            BOOLEAN NOT NULL,
    venue              TEXT,
    start_time_local   TIMESTAMP,
    day_night          TEXT,
    doubleheader_game  INTEGER,
    probable_pitcher   TEXT,
    dodgers_runs       INTEGER,
    opp_runs           INTEGER,
    win_loss           TEXT,
    division_rank      INTEGER,
    streak             TEXT,
    attendance         INTEGER
);

-- One row = Dodgers pitching stats for one game from Statcast
CREATE TABLE fact_stats (
    stats_id          SERIAL  PRIMARY KEY,
    game_id           INTEGER NOT NULL UNIQUE REFERENCES fact_game(game_id),
    pit_pitches       INTEGER,
    pit_whiff_pct     NUMERIC(5,2),
    pit_avg_velo      NUMERIC(4,1),
    pit_run_value     NUMERIC(6,2),
    opp_hits          INTEGER,
    opp_avg           NUMERIC(4,3),
    opp_obp           NUMERIC(4,3),
    opp_slg           NUMERIC(4,3)
);

-- One row = one Dodgers regular-season home game at Dodger Stadium (the prediction unit)
CREATE TABLE ml_features_attendance (
    game_id                 INTEGER PRIMARY KEY REFERENCES fact_game(game_id),
    date_id                 DATE    NOT NULL REFERENCES dim_date(date_id),
    season                  INTEGER NOT NULL,
    split                   TEXT    NOT NULL CHECK (split IN ('train', 'validate', 'test')),
    attendance              INTEGER NOT NULL, -- target
    month                   INTEGER NOT NULL, -- joined feature
    start_hour              INTEGER, -- joined feature
    opponent_name           TEXT    NOT NULL, -- joined feature
    opponent_abbrev         TEXT    NOT NULL, -- joined feature
    opp_win_pct_before      NUMERIC(4,3), -- joined feature
    is_weekend              INTEGER NOT NULL, -- encoded categorical variables
    is_holiday              INTEGER NOT NULL, -- encoded categorical variables
    is_night                INTEGER NOT NULL, -- encoded categorical variables
    is_nl_west              INTEGER NOT NULL, -- encoded categorical variables
    dow_mon                 INTEGER NOT NULL, -- encoded categorical variables
    dow_tue                 INTEGER NOT NULL, -- encoded categorical variables
    dow_wed                 INTEGER NOT NULL, -- encoded categorical variables
    dow_thu                 INTEGER NOT NULL, -- encoded categorical variables
    dow_fri                 INTEGER NOT NULL, -- encoded categorical variables
    dow_sat                 INTEGER NOT NULL, -- encoded categorical variables
    dow_sun                 INTEGER NOT NULL, -- encoded categorical variables
    win_pct_before          NUMERIC(4,3),     -- derived feature, season win % entering the game
    win_pct_last10          NUMERIC(4,3),     -- derived feature, win % over the previous 10 games
    run_diff_last10         NUMERIC(5,2),     -- derived feature, avg run differential, previous 10 games
    division_rank_before    INTEGER,          -- derived feature, division rank entering the game
    streak_before           INTEGER,          -- derived feature, streak entering the game
    whiff_pct_last10        NUMERIC(5,2),     -- derived feature, avg pitching whiff %, previous 10 games
    att_last5_home          NUMERIC(8,1),     -- derived feature, avg attendance, previous 5 home games
    days_since_last_home    INTEGER           -- derived feature, days since the previous home game
);