import os
from pathlib import Path 

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from sklearn.metrics import mean_absolute_error
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression

# Read the ML table from Postgres and splits it
load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()
cur.execute("SELECT * FROM ml_features_attendance;")
df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])

# Print how many rows each has
train = df[df["split"] == "train"]
validate = df[df["split"] == "validate"]
test = df[df["split"] == "test"]
print("Train:", len(train))
print("Validate:", len(validate))
print("Test:", len(test))
print()

# Make 3 charts to explore training data 
# Chart 1: distribution of attendance
plt.hist(train["attendance"].astype(float), bins=15)
plt.title("Home attendance 2022-2024 (train)")
plt.xlabel("Attendance")
plt.ylabel("Number of games")
plt.savefig("docs/figures/attendance_histogram.png")
plt.close()

# Chart 2: attendance vs. recent attendance
plt.scatter(train["att_last5_home"].astype(float), train["attendance"].astype(float))
plt.title("Attendance vs. average of previous 5 home games (train)")
plt.xlabel("Average attendance from previous 5 home games")
plt.ylabel("Attendance")
plt.savefig("docs/figures/attendance_vs_last5.png")
plt.close()

# Chart 3: attendance by day of week
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_name = pd.to_datetime(train["date_id"]).dt.day_name()
by_day = train["attendance"].astype(float).groupby(day_name).mean().reindex(days)
plt.bar(by_day.index, by_day.values)
plt.title("Average attendance by day of week (train)")
plt.ylabel("Average attendance")
plt.tight_layout()
plt.savefig("docs/figures/attendance_by_day.png")
plt.close()

# Build a baseline 
baseline_guess = train["attendance"].mean()
baseline_mae = mean_absolute_error(
    validate["attendance"], [baseline_guess] * len(validate)
)
print(f"Baseline Guess: {baseline_guess:,.0f} fans")
print(f"Baseline MAE: {baseline_mae:,.0f} fans")
print()

# Train 3 models on training games, score each on validate games
# Only use feature columns
features = [
    "month", "start_hour", "opp_win_pct_before", "is_holiday", "is_night", "is_nl_west",
    "dow_tue", "dow_wed", "dow_thu", "dow_fri", "dow_sat", "dow_sun",
    "win_pct_before", "win_pct_last10", "run_diff_last10", "division_rank_before",
    "streak_before", "whiff_pct_last10", "att_last5_home", "days_since_last_home",
]

x_train = train[features]
x_validate = validate[features]

models = {
    "linear_regression": LinearRegression(),
    "random_forest": RandomForestRegressor(random_state=42),
    "gradient_boosting": GradientBoostingRegressor(random_state=42),
}

# Model comparison
print("Model Comparison")
scores = {}
print("baseline: 3,724")
for name, model in models.items():
    model.fit(x_train, train["attendance"])
    scores[name] = mean_absolute_error(validate["attendance"], model.predict(x_validate))
    print(f"  {name}: {scores[name]:,.0f}")
print()

# Choose best model and test it once: linear regression
print("Linear Regression Test")
best_model = models["linear_regression"]
test_mae = mean_absolute_error(test["attendance"], best_model.predict(test[features]))
print(f"  test MAE: {test_mae:,.0f}")
print()

# Find linear regression's top 5 features
print("Linear Regression's top 5 features") 
coefficients = pd.Series(best_model.coef_, index=features)
print(coefficients.sort_values(key=abs, ascending=False).head(5))
