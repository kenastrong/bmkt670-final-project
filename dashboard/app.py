import os

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def run_query(sql):
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )
    cur = conn.cursor()
    cur.execute(sql)
    df = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
    conn.close()
    return df

st.sidebar.title("Dodgers Attendance Dashboard")
st.sidebar.caption("For Game-Day Operations Manager")
page = st.sidebar.radio("Page", [
    "1. What happened",
    "2. How good are the predictions",
    "3. What should we do",
    "4. Explore",
])

# Page 1
if page == "1. What happened":
    st.title("What happened")
    st.write("How has home-game attendance changed and what affects it?")

    games = run_query("""
        SELECT d.season, d.day_of_week, f.attendance
        FROM fact_game f
        JOIN dim_date d ON f.date_id = d.date_id
        WHERE f.is_home AND f.venue LIKE '%Dodger Stadium%' AND f.attendance IS NOT NULL;
    """)

    # Seasons Filter
    all_seasons = sorted(games["season"].unique())
    seasons = st.multiselect("Seasons", all_seasons, default=all_seasons)
    games = games[games["season"].isin(seasons)]

    # KPI boxes
    col1, col2, col3 = st.columns(3)
    col1.metric("Home Games", len(games))
    col2.metric("Average Attendance", f"{games['attendance'].mean():,.0f}")
    col3.metric("Stadium Capacity", "56,000")

    # Organize charts to be side by side
    left, right = st.columns(2)

    # Average Attendance by Season
    with left:
        st.subheader("Average Attendance by Season")
        by_season = games.groupby("season")["attendance"].mean()
        fig, ax = plt.subplots()
        ax.plot(by_season.index.astype(str), by_season.values, marker="o")
        ax.set_ylim(40000, 56000)
        ax.yaxis.set_major_formatter("{x:,.0f}")
        ax.set_ylabel("Average Attendance")
        st.pyplot(fig)
        st.caption("Average attendance across selected seasons showing how crowds have changed over time. Average attendance has steadily increased over the last 3 seasons since 2024.")

    # Average Attendance by Day of Week
    with right:
        st.subheader("Average Attendance by Day of Week")
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        by_day = games.groupby("day_of_week")["attendance"].mean().reindex(days)
        fig, ax = plt.subplots()
        bars = ax.bar(by_day.index.str[:3], by_day.values)
        ax.bar_label(bars, fmt="{:,.0f}", fontsize=8)
        ax.yaxis.set_major_formatter("{x:,.0f}")
        ax.set_ylabel("Average attendance")
        st.pyplot(fig)
        st.caption("Average attendance for each day of the week in the selected seasons. Thursday, Friday and Saturday games bring in the hightest average attendance "
        "while Wednesdays bring in the lowest in the last 3 seasons since 2024")

# Page 2
elif page == "2. How good are the predictions":
    st.title("How good are the predictions")
    st.write("Can we trust the model? Validate (2025) and Test (2026) games only")

    df = run_query("""
        SELECT p.game_id, p.split, p.actual, p.predicted, p.error,
               f.date_id, d.day_of_week, m.opponent_abbrev
        FROM predictions p
        JOIN fact_game f ON p.game_id = f.game_id
        JOIN dim_date d ON f.date_id = d.date_id
        JOIN ml_features_attendance m ON p.game_id = m.game_id;
    """)
    df[["predicted", "error"]] = df[["predicted", "error"]].astype(float)
    df["miss"] = df["error"].abs()

    # Baseline MAE
    train_mean = df[df["split"] == "train"]["actual"].mean()
    validate = df[df["split"] == "validate"]
    baseline_mae = (validate["actual"] - train_mean).abs().mean()

    # Model MAE
    preds = df[df["split"] != "train"].copy()
    mae = preds.groupby("split")["miss"].mean()

    # MAE tiles
    col1, col2, col3 = st.columns(3)
    col1.metric("Baseline MAE (2025)", f"{baseline_mae:,.0f} fans")
    col2.metric("Model MAE (2025, validate)", f"{mae['validate']:,.0f} fans")
    col3.metric("Model MAE (2026, test)", f"{mae['test']:,.0f} fans")

    # Predicted vs. actual attendance
    st.subheader("Predicted vs. Actual Attendance")
    fig, ax = plt.subplots()
    for split in ["validate", "test"]:
        rows = preds[preds["split"] == split]
        ax.scatter(rows["predicted"], rows["actual"], label=split, alpha=0.7)
    low = preds[["actual", "predicted"]].min().min()
    high = preds[["actual", "predicted"]].max().max()
    ax.plot([low, high], [low, high], "--", color="gray")
    ax.xaxis.set_major_formatter("{x:,.0f}")
    ax.yaxis.set_major_formatter("{x:,.0f}")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.legend()
    st.pyplot(fig)
    st.caption("Each dot is one game in either the 2025 (validate) or 2026 (test) season. Dots on the dashed line are perfect predictions by the model. "
    "The model tended to underpredict some of the most attendend games (above 50,000) while also missing a few really low 2025 crowds (below 44,000)")

    # Biggest misses table
    st.subheader("Biggest Misses")
    st.caption("A miss is unusual if it's more than 2× the model's typical miss.")
    preds["x_typical"] = (preds["miss"] / preds["split"].map(mae)).round(1)
    preds["flag"] = preds["x_typical"].apply(lambda x: "Unusual" if x > 2 else "")
    top = preds.sort_values("miss", ascending=False).head(10).copy()
    top[["actual", "predicted", "error"]] = top[["actual", "predicted", "error"]].round(0).astype(int)
    st.dataframe(
        top[["date_id", "day_of_week", "opponent_abbrev", "split", "actual", "predicted", "error", "x_typical", "flag"]],
        hide_index=True,
    )

    # Most unusual miss
    st.write(
        "**Most unusual miss: Wednesday, June 17, 2026 vs. Tampa Bay Rays.** "
        "The model predicted 41,757 fans as it was a midweek game against a non-rival team, "
        "but 50,705 fans actually came (3.6× the typical miss). The model didn't know about anything that made this series "
        "special for attendance purposes, like a promotion or giveaway night, or maybe a popular starting pitcher for either team."
    )

# Page 3
elif page == "3. What should we do":
    st.title("What should we do")
    st.write("How should we plan staffing, parking and promotions for upcoming home game?")

    # 3 recommendations and 1 limit
    st.subheader("Recommendations")
    st.success("**1. Don't cut staff for Monday or Wednesday games just based on the model alone.** 6 of the 10 biggest misses were Monday or Wednesday games that drew far more fans than predicted (Page 2).")
    st.success("**2. Plan parking and traffic for the largest crowds Thursday through Saturday.** These 3 days average about 50,000 fans (Page 1).")
    st.success("**3. Run promotions on Wednesdays.** They average the fewest fans, about 46,300 (Page 1), so they have the most empty seats to fill and promotions like bobblehead giveaways will encourage people to come.")
    st.warning("**Limit:** This model doesn't see promotions, giveaways, or special events. For games with these elements, use the prediction as a minimum guess, not an accurate forecast. Its biggest miss, a June 17 Wednesday game against Tampa Bay, drew almost 9,000 more fans than predicted and could have been missed due to a promotion or special event (Page 2).")

    # Prediction tool
    st.subheader("Plan the next game")
    st.caption("Enter what you'll know before game day, the model predicts that games attendance")
    model = joblib.load("model/attendance_model.joblib")
    row = run_query("""
        SELECT m.* FROM ml_features_attendance m
        JOIN fact_game f ON m.game_id = f.game_id
        ORDER BY f.date_id DESC LIMIT 1;
    """)[model.feature_names_in_].astype(float)

    c1, c2, c3 = st.columns(3)
    day = c1.selectbox("Day of week", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    night = c2.selectbox("Start", ["Night", "Day"]) == "Night"
    row["att_last5_home"] = c3.number_input("Avg attendance, last 5 home games", 30000, 56000, 49000, step=500)

    c4, c5, c6 = st.columns(3)
    row["month"] = c4.selectbox("Month", [4, 5, 6, 7, 8, 9], format_func=lambda m: ["April", "May", "June", "July", "August", "September"][m - 4])
    row["win_pct_before"] = c5.number_input("Dodgers win %", 0.0, 1.0, 0.600, step=0.010, format="%.3f")
    row["opp_win_pct_before"] = c6.number_input("Opponent win %", 0.0, 1.0, 0.500, step=0.010, format="%.3f")

    prediction = model.predict(row)[0]
    st.metric("Predicted attendance", f"{prediction:,.0f} fans")
    st.write(f"Typical miss is about 2,500 fans, so plan for **{prediction - 2500:,.0f} to {min(prediction + 2500, 56000):,.0f}**.")

    # AI summaries
    st.subheader("AI summaries for 2026 games")
    st.caption("Written by Claude Haiku 5.5 from each game's facts.")
    summaries = run_query("""
        SELECT f.date_id || ' vs ' || m.opponent_abbrev AS game, s.summary
        FROM ai_summaries s
        JOIN fact_game f ON s.game_id = f.game_id
        JOIN ml_features_attendance m ON s.game_id = m.game_id
        ORDER BY f.date_id;
    """)
    pick = st.selectbox("Game", summaries["game"])
    st.info(summaries[summaries["game"] == pick]["summary"].iloc[0])