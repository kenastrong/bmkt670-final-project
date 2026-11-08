import os
from pathlib import Path 

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
from dotenv import load_dotenv

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