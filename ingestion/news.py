from newsapi import NewsApiClient
from datetime import datetime, timedelta
from logger import get_logger
from config import NEWS_API_KEY, NEWS_QUERIES

logger = get_logger("news")


def fetch_articles(query, days_back=2):
    client = NewsApiClient(api_key=NEWS_API_KEY)
    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    try:
        response = client.get_everything(
            q=query,
            from_param=from_date,
            language="en",
            sort_by="publishedAt",
            page_size=20,
        )

        articles = []
        for article in response.get("articles", []):
            articles.append({
                "source": "news_api",
                "query": query,
                "title": article.get("title", ""),
                "description": article.get("description", ""),
                "content": article.get("content", ""),
                "url": article.get("url", ""),
                "published_at": article.get("publishedAt"),
                "source_name": article.get("source", {}).get("name", ""),
                "fetched_at": datetime.utcnow().isoformat(),
            })

        return articles

    except Exception as e:
        logger.error(f"news fetch failed for '{query}' - {e}")
        return []


def fetch_all(queries=None):
    queries = queries or NEWS_QUERIES
    all_articles = []

    for query in queries:
        articles = fetch_articles(query)
        all_articles.extend(articles)
        logger.info(f"'{query}': {len(articles)} articles fetched")

    return all_articles
