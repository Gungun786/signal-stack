import hashlib
import logging
import urllib.robotparser
from urllib.parse import urlparse
import datetime
from typing import Optional, Dict, Any, List
import httpx
import feedparser
import trafilatura
from bs4 import BeautifulSoup

logger = logging.getLogger("signal_stack.crawler")

USER_AGENT = "SignalStackBot/1.0 (+https://github.com/signal-stack/signal-stack; intelligence-engine)"

class WebCrawler:
    def __init__(self):
        self.robots_cache: Dict[str, urllib.robotparser.RobotFileParser] = {}
        self.client = httpx.Client(
            headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"},
            timeout=15.0,
            follow_redirects=True
        )

    def is_allowed_by_robots(self, target_url: str) -> bool:
        """Checks robots.txt compliance before initiating requests."""
        try:
            parsed = urlparse(target_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = f"{base_url}/robots.txt"

            if base_url not in self.robots_cache:
                rp = urllib.robotparser.RobotFileParser()
                rp.set_url(robots_url)
                try:
                    resp = self.client.get(robots_url, timeout=5.0)
                    if resp.status_code == 200:
                        rp.parse(resp.text.splitlines())
                    else:
                        rp.allow_all = True
                except Exception:
                    rp.allow_all = True
                self.robots_cache[base_url] = rp

            return self.robots_cache[base_url].can_fetch(USER_AGENT, target_url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {target_url}: {e}")
            return True

    def calculate_hash(self, text: str) -> str:
        """Calculates deterministic SHA-256 hash of normalized text."""
        normalized = "".join(text.split()).lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Parses an RSS or Atom feed."""
        items = []
        try:
            resp = self.client.get(feed_url, timeout=12.0)
            if resp.status_code != 200:
                logger.warning(f"Failed to fetch feed {feed_url}: status {resp.status_code}")
                return items

            feed = feedparser.parse(resp.text)
            for entry in feed.entries[:25]:
                title = entry.get("title", "No Title").strip()
                link = entry.get("link", feed_url).strip()
                summary = entry.get("summary", "") or entry.get("description", "")
                
                # Strip HTML from summary
                soup = BeautifulSoup(summary, "html.parser")
                clean_snippet = soup.get_text(separator=" ", strip=True)

                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        pub_date = datetime.datetime(*entry.published_parsed[:6])
                    except Exception:
                        pass
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    try:
                        pub_date = datetime.datetime(*entry.updated_parsed[:6])
                    except Exception:
                        pass

                content_hash = self.calculate_hash(title + clean_snippet)
                items.append({
                    "url": link,
                    "title": title,
                    "snippet": clean_snippet[:500] if clean_snippet else title,
                    "raw_content": clean_snippet,
                    "publication_date": pub_date or datetime.datetime.utcnow(),
                    "content_hash": content_hash
                })
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
        return items

    def fetch_page(self, page_url: str) -> Optional[Dict[str, Any]]:
        """Fetches and extracts clean content from a standard web page."""
        if not self.is_allowed_by_robots(page_url):
            logger.info(f"Skipping {page_url} (disallowed by robots.txt)")
            return None

        try:
            resp = self.client.get(page_url, timeout=15.0)
            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code} fetching {page_url}")
                return None

            html = resp.text
            # Use trafilatura for main body extraction
            extracted_text = trafilatura.extract(html, include_comments=False, include_tables=True)
            soup = BeautifulSoup(html, "html.parser")
            
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)
            else:
                title = page_url

            final_text = extracted_text if extracted_text else soup.get_text(separator=" ", strip=True)
            content_hash = self.calculate_hash(title + final_text[:1000])

            return {
                "url": str(resp.url),
                "title": title,
                "snippet": final_text[:600],
                "raw_content": final_text[:10000],
                "publication_date": datetime.datetime.utcnow(),
                "content_hash": content_hash
            }
        except Exception as e:
            logger.error(f"Error fetching page {page_url}: {e}")
            return None

crawler_client = WebCrawler()
