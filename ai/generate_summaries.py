import os

import anthropic
import psycopg2
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)
cur = conn.cursor()

# Get the facts for each test game
cur.execute("""
    SELECT p.game_id, f.date_id, d.day_of_week, m.opponent_abbrev, m.is_night,
           m.win_pct_before, m.att_last5_home, p.predicted, p.actual
    FROM predictions p
    JOIN fact_game f ON p.game_id = f.game_id
    JOIN dim_date d ON f.date_id = d.date_id
    JOIN ml_features_attendance m ON p.game_id = m.game_id
    WHERE p.split = 'test'
    ORDER BY f.date_id;
""")
games = cur.fetchall()

cur.execute("DELETE FROM ai_summaries;")
input_tokens = 0
output_tokens = 0

for game_id, date_id, day, opponent, is_night, win_pct, last5, predicted, actual in games:
    prompt = f"""Write a 2-3 sentence summary of this Dodgers home game for a game-day operations manager.
Use only the facts below and do not add information.

Date: {date_id} ({day}), {"night" if is_night else "day"} game
Opponent: {opponent}
Dodgers win % before the game: {float(win_pct):.3f}
Average attendance, last 5 home games: {float(last5):,.0f}
Model predicted attendance: {float(predicted):,.0f}
Actual attendance: {actual:,}
Miss (actual minus predicted): {actual - float(predicted):+,.0f} fans"""

    response = client.messages.create(
        model="claude-haiku-5-5",
        max_tokens=200,
        thinking={"type": "disabled"},
        messages=[{"role": "user", "content": prompt}],
    )
    summary = [block.text for block in response.content if block.type == "text"][0]

    cur.execute("INSERT INTO ai_summaries (game_id, summary) VALUES (%s, %s)", (game_id, summary))
    input_tokens += response.usage.input_tokens
    output_tokens += response.usage.output_tokens
    print(f"{date_id} vs {opponent}: {summary}\n")

conn.commit()
conn.close()

cost = input_tokens / 1_000_000 * 0.10 + output_tokens / 1_000_000 * 0.50
print(f"Saved {len(games)} summaries")
print(f"Tokens: {input_tokens:,} in, {output_tokens:,} out. Cost: ${cost:.4f}")