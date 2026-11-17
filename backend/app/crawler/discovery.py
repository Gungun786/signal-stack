import urllib.parse
import datetime
import logging
from typing import List, Dict, Any
import httpx
from ddgs import DDGS
from app.crawler.crawler import crawler_client

logger = logging.getLogger("signal_stack.discovery")

class SourceDiscoveryEngine:
    """
    Discovery engine utilizing zero-cost public endpoints:
    - Google News RSS
    - DuckDuckGo Search
    - Hacker News Algolia API
    - Reddit JSON Search
    """

    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": "SignalStackBot/1.0 (Public Research Client)"},
            timeout=12.0,
            follow_redirects=True
        )

    def search_google_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries Google News RSS feed for real-time news articles."""
        encoded_q = urllib.parse.quote_plus(query)
        feed_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
        items = crawler_client.fetch_feed(feed_url)
        return items[:limit]

    def search_duckduckgo(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries DuckDuckGo for top web results."""
        results = []
        try:
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=limit)
                for r in ddg_gen:
                    title = r.get("title", "")
                    url = r.get("href", "")
                    body = r.get("body", "")
                    if url and title:
                        results.append({
                            "url": url,
                            "title": title,
                            "snippet": body,
                            "raw_content": body,
                            "publication_date": datetime.datetime.utcnow(),
                            "content_hash": crawler_client.calculate_hash(title + body)
                        })
        except Exception as e:
            logger.warning(f"DuckDuckGo search error for '{query}': {e}")
        return results

    def search_hacker_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries public Hacker News Algolia API."""
        results = []
        try:
            url = f"https://hn.algolia.com/api/v1/search?query={urllib.parse.quote_plus(query)}&tags=story"
            resp = self.client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                for hit in data.get("hits", [])[:limit]:
                    title = hit.get("title", "")
                    item_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    created_at_str = hit.get("created_at")
                    pub_date = datetime.datetime.utcnow()
                    if created_at_str:
                        try:
                            pub_date = datetime.datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        except Exception:
                            pass
                    
                    snippet = f"HN discussion ({hit.get('points', 0)} points, {hit.get('num_comments', 0)} comments)"
                    results.append({
                        "url": item_url,
                        "title": title,
                        "snippet": snippet,
                        "raw_content": snippet,
                        "publication_date": pub_date,
                        "content_hash": crawler_client.calculate_hash(title + item_url)
                    })
        except Exception as e:
            logger.warning(f"Hacker News Algolia search error for '{query}': {e}")
        return results

    def search_reddit(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Queries Reddit search JSON."""
        results = []
        try:
            url = f"https://www.reddit.com/search.json?q={urllib.parse.quote_plus(query)}&sort=relevance&limit={limit}"
            resp = self.client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SignalStack/1.0"})
            if resp.status_code == 200:
                data = resp.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    post = child.get("data", {})
                    title = post.get("title", "")
                    permalink = post.get("permalink", "")
                    full_url = f"https://reddit.com{permalink}" if permalink else post.get("url", "")
                    selftext = post.get("selftext", "")
                    created_utc = post.get("created_utc", 0)
                    pub_date = datetime.datetime.utcfromtimestamp(created_utc) if created_utc else datetime.datetime.utcnow()

                    snippet = f"r/{post.get('subreddit')}: {selftext[:300] if selftext else title}"
                    results.append({
                        "url": full_url,
                        "title": title,
                        "snippet": snippet,
                        "raw_content": selftext or title,
                        "publication_date": pub_date,
                        "content_hash": crawler_client.calculate_hash(title + full_url)
                    })
        except Exception as e:
            logger.warning(f"Reddit search error for '{query}': {e}")
        return results

discovery_engine = SourceDiscoveryEngine()
