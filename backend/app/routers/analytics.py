from fastapi import APIRouter
from app.services.sql_services import (
    get_top_movies,
    get_genre_trends,
    get_regional_performance,
    get_audience_insights,
    get_trending_content,
    get_marketing_roi,
)
from app.database import get_connection

router = APIRouter(prefix = "/analytics", tags = ["analytics"])

@router.get("/overview")
def overview(year: int | None = None):
    """KPI stats for the dashboard top row. Optionally filtered by year."""
    with get_connection() as conn:
        if year:
            y = int(year)
            stats = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM movies WHERE release_year = ?) AS total_movies,
                    (SELECT COUNT(DISTINCT viewer_id) FROM watch_activity WHERE watch_year = ?) AS total_viewers,
                    (SELECT COUNT(*) FROM watch_activity WHERE watch_year = ?) AS total_views,
                    (SELECT ROUND(SUM(revenue_usd)/1e6, 1) FROM movies WHERE release_year = ?) AS total_revenue_m,
                    (SELECT ROUND(AVG(imdb_rating), 2) FROM movies WHERE release_year = ? AND revenue_usd > 0) AS avg_rating
            """, (y, y, y, y, y)).fetchone()
        else:
            stats = conn.execute("""
                SELECT
                    (SELECT COUNT(*) FROM movies)         AS total_movies,
                    (SELECT COUNT(*) FROM viewers)        AS total_viewers,
                    (SELECT COUNT(*) FROM watch_activity) AS total_views,
                    (SELECT ROUND(SUM(revenue_usd)/1e6, 1) FROM movies) AS total_revenue_m,
                    (SELECT ROUND(AVG(imdb_rating), 2) FROM movies WHERE revenue_usd > 0) AS avg_rating
            """).fetchone()
    return dict(stats)


@router.get("/genres")
def genres(year: int | None = None):
    return get_genre_trends(year=year)


@router.get("/regional")
def regional(month: int | None = None, year: int | None = None, limit: int = 10):
    return get_regional_performance(month=month, year=year, limit=limit)


@router.get("/audience")
def audience(segment: str = "age"):
    return get_audience_insights(segment=segment)


@router.get("/trending")
def trending(days: int = 30, limit: int = 5):
    return get_trending_content(days=days, limit=limit)


@router.get("/movies")
def movies(year: int | None = None, genre: str | None = None, limit: int = 10):
    return get_top_movies(year=year, genre=genre, limit=limit)


@router.get("/marketing")
def marketing(year: int | None = None):
    return get_marketing_roi(year=year)