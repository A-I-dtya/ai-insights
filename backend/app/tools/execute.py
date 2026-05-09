from app.services.sql_services import (
    get_top_movies,
    get_movie_details,
    compare_movies,
    get_genre_trends,
    get_regional_performance,
    get_audience_insights,
    get_trending_content,
    get_marketing_roi,
)
from app.services.document_service import search_documents

# ─── Tool schemas (one entry per function) ────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_movies",
            "description": "Get top movies by revenue. Optionally filter by year.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "string", "description": "Number of movies, default 5"},
                    "year":  {"type": "string", "description": "Release year filter, optional"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_movie_details",
            "description": (
                "Get detailed info about a specific movie including financials, "
                "ratings, watch activity, and review sentiment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Movie title (partial match supported)"},
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_movies",
            "description": "Side-by-side comparison of two movies across revenue, ratings, and views.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title_a": {"type": "string", "description": "First movie title"},
                    "title_b": {"type": "string", "description": "Second movie title"},
                },
                "required": ["title_a", "title_b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_genre_trends",
            "description": (
                "Get genre-level performance: revenue, ratings, ROI, audience scores. "
                "Useful for understanding how each genre is performing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Filter by specific genre, optional"},
                    "year":  {"type": "string", "description": "Filter by year, optional"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_regional_performance",
            "description": (
                "Get city/region-level performance data: views, revenue, engagement. "
                "Use for questions about specific cities or top-performing regions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "city":  {"type": "string", "description": "Filter by city name, optional"},
                    "month": {"type": "string", "description": "Filter by month (1-12), optional"},
                    "year":  {"type": "string", "description": "Filter by year, optional"},
                    "limit": {"type": "string", "description": "Number of cities to return, default 10"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_audience_insights",
            "description": (
                "Get viewer demographics breakdown: age groups, subscription tier, "
                "device usage, or genre preference."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "segment": {
                        "type": "string",
                        "description": "One of: age, subscription, device, genre_preference",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_content",
            "description": (
                "Identify titles with the highest recent watch activity. "
                "Use for questions like 'what's trending' or 'rising titles'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "days":  {"type": "string", "description": "Lookback window in days (default 30)"},
                    "limit": {"type": "string", "description": "Number of titles, default 5"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_marketing_roi",
            "description": (
                "Get marketing campaign ROI broken down by movie, channel, and year. "
                "Use for questions about ad spend effectiveness."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "year":    {"type": "string", "description": "Filter by year, optional"},
                    "channel": {"type": "string", "description": "Filter by marketing channel, optional"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_internal_documents",
            "description": (
                "Search internal PDF documents (executive reports, campaign summaries, "
                "content roadmap, audience reports) for qualitative insights and explanations."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                },
                "required": ["query"],
            },
        },
    },
]


# ─── Dispatch tool calls to the right function ────────────────────────────────

DISPATCH = {
    "get_top_movies":           get_top_movies,
    "get_movie_details":        get_movie_details,
    "compare_movies":           compare_movies,
    "get_genre_trends":         get_genre_trends,
    "get_regional_performance": get_regional_performance,
    "get_audience_insights":    get_audience_insights,
    "get_trending_content":     get_trending_content,
    "get_marketing_roi":        get_marketing_roi,
    "search_internal_documents": search_documents,
}


def execute_tool(name: str, args: dict) -> dict:
    fn = DISPATCH.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": f"{name} failed: {e}"}
