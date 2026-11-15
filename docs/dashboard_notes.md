# Dashboard Notes

**Who uses it?** Dodger's Game-Day Operations Manager

**What decision does it help with?** How many staff and parking attendants to schedule and when a game could benefit from a promotion to boost attendance.

**One question per page:**
| Page | Question | What's on it |
|---|---|---|
| 1. What happened | How has attendance changed? | Average Attendance by Season (line chart); Average Attendance by Day of Week (bar chart); season filter |
| 2. How good are the predicitions | Can we trust the model? | Predicted vs. Actual for 2025-2026 (scatter plot); Model MAE vs Baseline MAE; Biggest-Misses Table |
| 3. What should we do | How should we staff each game? | 3 Recommendations; 1 Limit; "Plan the next game" Prediction Tool; AI Summaries for 2026 Games |
| 4. Explore | How does a certain measure change over time? | Pick a measure and season(s); line chart of that measure across the season(s) |

## AI Feature
ai/generate_summaries.py sends each 2026 game's facts to Claude Haiku 5.5 which creates and saves a 2–3 sentence summary to the ai_summaries table, shown on Page 3. (I chose to do a drop down selection tool to pick each game for these summaries on page 3 as there would be 81 summaries printed if they were all printed out at the same time)

**Prompt**

"Write a 2-3 sentence summary of this Dodgers home game for a game-day operations manager.
Use only the facts below and do not add information."

"Date: {date_id} ({day}), {"night" if is_night else "day"} game
Opponent: {opponent}
Dodgers win % before the game: {float(win_pct):.3f}
Average attendance, last 5 home games: {float(last5):,.0f}
Model predicted attendance: {float(predicted):,.0f}
Actual attendance: {actual:,}
Miss (actual minus predicted): {actual - float(predicted):+,.0f} fans"

**3 summaries checked:**
| Game | AI summary | Check against data |
|---|---|---|
| April 10 vs. TEX | The Dodgers hosted Texas on Friday, April 10, for a night game, entering with a 0.750 winning percentage. Actual attendance was 53,675, about 2,323 fans above the model's prediction of 51,352 and above the recent five-game home average of 51,245. | Correct. Data: Friday, night game (is_night = 1), win % 0.750, 5-game average 51,244.6, predicted 51,351.8, actual 53,675. All match once rounded, and 53,675 − 51,352 = 2,323. |
| June 16 vs. TB | On Tuesday, June 16, 2026, the Dodgers hosted Tampa Bay (TB) in a night game, with the team entering at a .630 win percentage. Actual attendance was 49,070, which was 572 fewer than the model's predicted 49,642 and below the 50,884 average of the last five home games. | Correct. Data: Tuesday, night game (is_night = 1), win % 0.630, 5-game average 50,884.2, predicted 49,641.6, actual 49,070. All match once rounded, and 49,642 − 49,070 = 572. |
| August 22 vs. PIT | On Saturday, August 22, 2026, the Dodgers hosted Pittsburgh in a day game with a pre-game win percentage of .605. Actual attendance was 53,417, about 6,144 fans above the model's predicted 47,273 and well above the recent home average of 47,728 over the last five home games. | Correct. Data: Saturday, day game (is_night = 0), win % 0.605, 5-game average 47,727.6, predicted 47,273.4, actual 53,417. All match once rounded, and 53,417 − 47,273 = 6,144. |

All three matched the database on day, opponent, day/night, win %, recent average, prediction, and actual attendance, and none added facts beyond what was asked in the prompt.

**Cost of one run:** 81 summaries used 12,981 input and 8,926 output tokens, costing only $0.0058 total.

## One thing I'd add with more time
I would add a **promotions and giveaways** column. 7 of the model's 10 biggest misses were games that brought in many more fans than it predicted. This could be likely due to the fact that the model couldn't see any special events. Adding the Dodgers' promotions calendar would allowed the model and the dashboard to account for them when predicting attendance, and it would help the operations manager plan promotion nights more directly tying to attendance numbers if the effect is proven to be significant.