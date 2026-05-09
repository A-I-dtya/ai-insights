from app.database import get_connection


# ─── 1. Top movies by revenue ─────────────────────────────────────────────────

def get_top_movies(limit: int = 5, year: int = None) -> dict:
    sql = "SELECT title, genre, revenue_usd, imdb_rating FROM movies"
    params = []
    if year:
        sql += " WHERE release_year = ?"
        params.append(int(year))
    sql += " ORDER BY revenue_usd DESC LIMIT ?"
    params.append(min(int(limit or 5), 20))

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {"movies": [dict(r) for r in rows]}


# ─── 2. Detailed info on one movie ────────────────────────────────────────────

def get_movie_details(title: str) -> dict:
    safe_title = title[:100]

    with get_connection() as conn:
        movie = conn.execute(
            "SELECT * FROM movies WHERE LOWER(title) LIKE ? LIMIT 1",
            (f"%{safe_title.lower()}%",)
        ).fetchone()

        if not movie:
            return {"error": f"No movie found matching '{safe_title}'"}

        mid = movie["movie_id"]

        views = conn.execute(
            "SELECT COUNT(*) AS cnt, AVG(completion_pct) AS avg_completion "
            "FROM watch_activity WHERE movie_id = ?",
            (mid,)
        ).fetchone()

        reviews = conn.execute(
            "SELECT AVG(rating) AS avg_rating, COUNT(*) AS review_count "
            "FROM reviews WHERE movie_id = ?",
            (mid,)
        ).fetchone()

    return {
        "movie": dict(movie),
        "total_views": views["cnt"],
        "avg_completion_pct": round(views["avg_completion"] or 0, 1),
        "avg_review_rating": reviews["avg_rating"],
        "review_count": reviews["review_count"],
    }


# ─── 3. Compare two movies ────────────────────────────────────────────────────

def compare_movies(title_a: str, title_b: str) -> dict:
    a = get_movie_details(title_a)
    b = get_movie_details(title_b)

    if "error" in a:
        return a
    if "error" in b:
        return b

    def summary(d: dict) -> dict:
        m = d["movie"]
        return {
            "title": m["title"],
            "genre": m["genre"],
            "revenue_usd": m["revenue_usd"],
            "budget_usd": m["budget_usd"],
            "imdb_rating": m["imdb_rating"],
            "audience_score": m["audience_score"],
            "total_views": d["total_views"],
            "avg_completion_pct": d["avg_completion_pct"],
            "avg_review_rating": d["avg_review_rating"],
        }

    return {
        "movies": [summary(a), summary(b)],
        "winner": {
            "revenue": a["movie"]["title"]
                if (a["movie"]["revenue_usd"] or 0) >= (b["movie"]["revenue_usd"] or 0)
                else b["movie"]["title"],
            "rating": a["movie"]["title"]
                if (a["movie"]["imdb_rating"] or 0) >= (b["movie"]["imdb_rating"] or 0)
                else b["movie"]["title"],
        },
    }


# ─── 4. Genre-level performance trends ────────────────────────────────────────

def get_genre_trends(genre: str = None, year: int = None) -> dict:
    sql = """
        SELECT genre,
               COUNT(*) AS movie_count,
               ROUND(AVG(imdb_rating), 2) AS avg_rating,
               ROUND(AVG(audience_score), 1) AS avg_audience_score,
               SUM(revenue_usd) AS total_revenue,
               SUM(budget_usd) AS total_budget
        FROM movies
        WHERE revenue_usd > 0
    """
    params = []
    if genre:
        sql += " AND LOWER(genre) LIKE ?"
        params.append(f"%{genre.lower()[:50]}%")
    if year:
        sql += " AND release_year = ?"
        params.append(int(year))
    sql += " GROUP BY genre ORDER BY total_revenue DESC"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()

    results = []
    for r in rows:
        d = dict(r)
        budget = d["total_budget"] or 1
        d["roi"] = round((d["total_revenue"] - budget) / budget, 2)
        results.append(d)

    return {"genres": results}


# ─── 5. Regional / city-level performance ─────────────────────────────────────

def get_regional_performance(
    city: str = None,
    month: int = None,
    year: int = None,
    limit: int = 10,
) -> dict:
    sql = """
        SELECT city, country,
               SUM(views) AS total_views,
               SUM(revenue_usd) AS total_revenue,
               ROUND(AVG(avg_engagement_score), 2) AS avg_engagement,
               ROUND(AVG(avg_watch_time_min), 1) AS avg_watch_time
        FROM regional_performance
        WHERE 1=1
    """
    params = []
    if city:
        sql += " AND LOWER(city) LIKE ?"
        params.append(f"%{city.lower()[:50]}%")
    if month:
        sql += " AND month = ?"
        params.append(int(month))
    if year:
        sql += " AND year = ?"
        params.append(int(year))
    sql += " GROUP BY city, country ORDER BY avg_engagement DESC LIMIT ?"
    params.append(min(int(limit or 10), 50))

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {"regions": [dict(r) for r in rows]}


# ─── 6. Audience demographics ─────────────────────────────────────────────────

def get_audience_insights(segment: str = "age") -> dict:
    valid = {"age", "subscription", "device", "genre_preference"}
    if segment not in valid:
        segment = "age"

    with get_connection() as conn:
        if segment == "age":
            rows = conn.execute("""
                SELECT
                    CASE
                        WHEN age < 25 THEN '<25'
                        WHEN age < 35 THEN '25-34'
                        WHEN age < 45 THEN '35-44'
                        WHEN age < 55 THEN '45-54'
                        ELSE '55+'
                    END AS age_group,
                    COUNT(*) AS viewers
                FROM viewers
                GROUP BY age_group
                ORDER BY viewers DESC
            """).fetchall()
        elif segment == "subscription":
            rows = conn.execute(
                "SELECT subscription_tier, COUNT(*) AS viewers FROM viewers "
                "GROUP BY subscription_tier ORDER BY viewers DESC"
            ).fetchall()
        elif segment == "device":
            rows = conn.execute(
                "SELECT device, COUNT(*) AS viewers FROM viewers "
                "GROUP BY device ORDER BY viewers DESC"
            ).fetchall()
        else:  # genre_preference
            rows = conn.execute(
                "SELECT preferred_genre, COUNT(*) AS viewers FROM viewers "
                "GROUP BY preferred_genre ORDER BY viewers DESC"
            ).fetchall()

    return {"segment": segment, "data": [dict(r) for r in rows]}


# ─── 7. Trending content (recent watch activity) ──────────────────────────────

def get_trending_content(days: int = 30, limit: int = 5) -> dict:
    days = max(7, min(int(days or 30), 90))
    limit = max(1, min(int(limit or 5), 20))

    with get_connection() as conn:
        latest = conn.execute(
            "SELECT MAX(watch_date) FROM watch_activity"
        ).fetchone()[0]

        if not latest:
            return {"trending": [], "window_days": days}

        rows = conn.execute("""
            SELECT m.title, m.genre,
                   COUNT(*) AS recent_views,
                   ROUND(AVG(wa.completion_pct), 1) AS avg_completion
            FROM watch_activity wa
            JOIN movies m ON m.movie_id = wa.movie_id
            WHERE wa.watch_date >= DATE(?, ?)
            GROUP BY m.movie_id
            ORDER BY recent_views DESC
            LIMIT ?
        """, (latest, f"-{days} days", limit)).fetchall()

    return {
        "trending": [dict(r) for r in rows],
        "window_days": days,
        "reference_date": latest,
    }


# ─── 8. Marketing ROI by channel / movie ──────────────────────────────────────

def get_marketing_roi(year: int = None, channel: str = None) -> dict:
    sql = """
        SELECT m.title, ms.channel, ms.year,
               SUM(ms.spend_usd) AS total_spend,
               SUM(ms.impressions) AS total_impressions,
               SUM(ms.clicks) AS total_clicks,
               SUM(ms.conversions) AS total_conversions,
               ROUND(AVG(ms.roi), 2) AS avg_roi
        FROM marketing_spend ms
        JOIN movies m ON m.movie_id = ms.movie_id
        WHERE 1=1
    """
    params = []
    if year:
        sql += " AND ms.year = ?"
        params.append(int(year))
    if channel:
        sql += " AND LOWER(ms.channel) LIKE ?"
        params.append(f"%{channel.lower()[:50]}%")
    sql += " GROUP BY m.title, ms.channel, ms.year ORDER BY avg_roi DESC LIMIT 20"

    with get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {"marketing_data": [dict(r) for r in rows]}
