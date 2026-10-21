import os
from pathlib import Path
import pandas as pd
import psycopg2
from dotenv import load_dotenv

# Load in dependency order
tables = ["dim_date", "dim_opponent", "fact_game", "fact_stats", "ml_features_attendance"]

load_dotenv()
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

# re-run schema.sql so running multiple times doesn't create duplicates
cur.execute(Path("sql/schema.sql").read_text())

for table in tables:
    df = pd.read_csv(f"data/clean/{table}.csv")
    df = df.astype(object).where(df.notna(), None)  # blanks become NULL

    cols = ", ".join(df.columns)
    slots = ", ".join(["%s"] * len(df.columns))
    cur.executemany(f"INSERT INTO {table} ({cols}) VALUES ({slots})", df.values.tolist())

conn.commit()
conn.close()