# Handling Missing Data on Purpose

| Table | Column | % missing | Decision | Why |
|---|---|---|---|---|
| fact_game | probable_pitcher | 0.2% (2 rows) | Leave as NULL | These are considered bullpen games with no true listed starter. NULL is an accurate value and this column is not a model feature so NULL will not affect the model. |
| fact_game | opp_win_pct_before | 0.9% (7 rows) | Leave as NULL in this table| These games were the opponent's first game of the season so the opponent had no record yet fact_game keeps NULL because it is again accurate and will not affect the model while the ML table fills it (see below). |
| fact_game | attendance | 0.2% (2 rows) | Leave as NULL | Both are away games with no attendance listed on Baseball-Reference. Away games are not in the prediction unit, so no rows are dropped from the ML table and they stay in fact_game because the games still count towards how the team has been playing for other values. |
| ml_features_attendance | win_pct_before | 0.5% (2 rows) | Fill with 0.5 | Two seasons opened with a home game, so the first game had no earlier games. 0.5 is a neutral average value for these calculations. |
| ml_features_attendance | win_pct_last10 | 0.5% (2 rows) | Fill with 0.5 | Same two season-opening games with no earlier games to average and an average value to fill with. |
| ml_features_attendance | run_diff_last10 | 0.5% (2 rows) | Fill with 0 | Same two games as above, 0 means even (neither ahead nor behind). |
| ml_features_attendance | division_rank_before | 0.5% (2 rows) | Fill with 1 | Same two games as above, every team is tied for first before their Opening Day. |
| ml_features_attendance | streak_before | 0.5% (2 rows) | Fill with 0 | Same two games as above, no streak exists before the first game so filled with no streak. |
| ml_features_attendance | opp_win_pct_before | 1.0% (4 rows) | Fill with 0.5 | Four home games were the opponent's first game of the season, so the opponent had no record yet. 0.50 is the neutral value. |
| ml_features_attendance | whiff_pct_last10 | 0.5% (2 rows) | Fill with the training-set median (25.43) | No earlier pitching in a season's first game, and there is no value that is considered a "natural" neutral value. The median uses 2022–2024 (train) rows only, so validate/test data does not leak into training. |
| ml_features_attendance | att_last5_home | 0.2% (1 row) | Fill with the training-set median attendance (48,693) | The 2022 home opener is the first home game in the data, so there are no earlier home games to average. Median from train rows only (same as above). |
| ml_features_attendance | days_since_last_home | 0.2% (1 row) | Fill with the typical offseason gap of about 184 days | Same game as above, there is no earlier home game in the data. Home openers always follow the offseason, so it gets the median gap of the other home openers with stats recorded. |

`dim_date`, `dim_opponent`, and `fact_stats` have no missing values.
After these fillings, `ml_features_attendance` has 0 missing values.
No rows were dropped.