import os

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
        st.caption("Average attendance for each day of the week in the selected seasons. Thursday, Friday and Saturday games bring in the hightest average attendance while Wednesdays bring in the lowest in the last 3 seasons since 2024")