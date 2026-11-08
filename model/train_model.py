import os

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