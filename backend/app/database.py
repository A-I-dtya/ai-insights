import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = "data/analytics.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    Path("data").mkdir(exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY,
            title TEXT, genre TEXT,
            release_date TEXT, release_year INTEGER, director TEXT,
            budget_usd REAL, revenue_usd REAL,
            imdb_rating REAL, rt_score INTEGER, audience_score INTEGER,
            runtime_min INTEGER, language TEXT, synopsis TEXT
        );
        CREATE TABLE IF NOT EXISTS viewers (
            viewer_id INTEGER PRIMARY KEY,
            age INTEGER, gender TEXT, city TEXT, country TEXT,
            subscription_tier TEXT, join_date TEXT,
            preferred_genre TEXT, device TEXT
        );
        CREATE TABLE IF NOT EXISTS watch_activity (
            activity_id INTEGER PRIMARY KEY,
            viewer_id INTEGER, movie_id INTEGER,
            watch_date TEXT, watch_year INTEGER, watch_month INTEGER,
            watch_duration_min REAL, completion_pct REAL, device TEXT
        );
        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY,
            viewer_id INTEGER, movie_id INTEGER,
            rating REAL, review_text TEXT, review_date TEXT,
            helpful_votes INTEGER, sentiment TEXT
        );
        CREATE TABLE IF NOT EXISTS marketing_spend (
            spend_id INTEGER PRIMARY KEY,
            movie_id INTEGER, channel TEXT,
            month INTEGER, year INTEGER,
            spend_usd REAL, impressions INTEGER,
            clicks INTEGER, conversions INTEGER, roi REAL
        );
        CREATE TABLE IF NOT EXISTS regional_performance (
            perf_id INTEGER PRIMARY KEY,
            city TEXT, state TEXT, country TEXT,
            movie_id INTEGER, month INTEGER, year INTEGER,
            views INTEGER, revenue_usd REAL,
            avg_engagement_score REAL, avg_watch_time_min REAL
        );
    """)
    conn.commit()

    # Load CSVs if tables empty
    table_files = {
        "movies.csv": "movies",
        "viewers.csv": "viewers",
        "watch_activity.csv": "watch_activity",
        "reviews.csv": "reviews",
        "marketing_spend.csv": "marketing_spend",
        "regional_performance.csv": "regional_performance",
    }
    for filename, table in table_files.items():
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        if count == 0:
            df = pd.read_csv(f"data/csv/{filename}")
            df.to_sql(table, conn, if_exists="append", index=False)
            print(f"Loaded {len(df)} rows into {table}")

    conn.close()