import datetime
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import Source, CrawledItem, Company
from app.crawler.crawler import crawler_client
from app.crawler.discovery import discovery_engine

logger = logging.getLogger("signal_stack.monitor")

class MonitoringEngine:
    """
    Crawls and harvests new items from approved sources.
    Performs content hashing and deduplication.
    Tracks source health and error telemetry.
    """

    def crawl_source(self, db: Session, source: Source) -> List[CrawledItem]:
        logger.info(f"Monitoring source #{source.id}: {source.name} ({source.category})")
        items_fetched: List[Dict[str, Any]] = []

        try:
            # 1. Internal source check
            if source.category == "internal" or source.url.startswith("local://"):
                source.health_status = "healthy"
                source.last_success_at = datetime.datetime.utcnow()
                db.commit()
                return []

            # 2. Check if DuckDuckGo search query source
            if source.feed_url and source.feed_url.startswith("ddg://"):
                query = source.feed_url.replace("ddg://", "").replace("+", " ")
                items_fetched = discovery_engine.search_duckduckgo(query, limit=6)
            # 3. Check if HN Algolia query
            elif "hn.algolia.com" in (source.feed_url or ""):
                query = source.name.split()[0]
                items_fetched = discovery_engine.search_hacker_news(query, limit=10)
            # 4. Check if standard RSS feed available (e.g. Google News RSS)
            elif source.feed_url:
                items_fetched = crawler_client.fetch_feed(source.feed_url)
            # 5. Fallback to standard web page crawl
            else:
                page_data = crawler_client.fetch_page(source.url)
                if page_data:
                    items_fetched = [page_data]

            # Update source health
            source.last_crawled_at = datetime.datetime.utcnow()
            if items_fetched:
                source.health_status = "healthy"
                source.last_success_at = datetime.datetime.utcnow()
                source.failure_count = 0
                source.last_error = None
            else:
                source.failure_count += 1
                if source.failure_count >= 3:
                    source.health_status = "warning"
                if source.failure_count >= 6:
                    source.health_status = "dead"
                source.last_error = "Zero items returned or parse yielded empty feed"

            db.commit()

        except Exception as e:
            logger.error(f"Error crawling source {source.name}: {e}")
            source.failure_count += 1
            source.last_error = str(e)
            if source.failure_count >= 3:
                source.health_status = "warning"
            db.commit()
            return []

        # Deduplicate and persist new items
        new_items = []
        for raw_item in items_fetched:
            content_hash = raw_item.get("content_hash") or crawler_client.calculate_hash(raw_item.get("title", "") + raw_item.get("snippet", ""))
            
            # Check if hash already exists in DB for this company
            existing = db.query(CrawledItem).filter(
                CrawledItem.company_id == source.company_id,
                CrawledItem.content_hash == content_hash
            ).first()

            if existing:
                continue

            # Check title similarity with existing items from last 7 days
            title_norm = set(raw_item.get("title", "").lower().split())
            recent_items = db.query(CrawledItem).filter(
                CrawledItem.company_id == source.company_id
            ).order_by(CrawledItem.id.desc()).limit(30).all()

            is_duplicate = False
            for prev in recent_items:
                prev_norm = set(prev.title.lower().split())
                if title_norm and prev_norm:
                    intersection = len(title_norm.intersection(prev_norm))
                    union = len(title_norm.union(prev_norm))
                    if union > 0 and (intersection / union) > 0.82:
                        is_duplicate = True
                        break

            if is_duplicate:
                continue

            crawled_obj = CrawledItem(
                source_id=source.id,
                company_id=source.company_id,
                url=raw_item.get("url", source.url),
                title=raw_item.get("title", "Untitled Signal"),
                content_hash=content_hash,
                snippet=raw_item.get("snippet", "")[:1000],
                raw_content=raw_item.get("raw_content", "")[:10000],
                publication_date=raw_item.get("publication_date") or datetime.datetime.utcnow(),
                discovery_date=datetime.datetime.utcnow()
            )
            db.add(crawled_obj)
            db.commit()
            db.refresh(crawled_obj)
            new_items.append(crawled_obj)

        logger.info(f"Persisted {len(new_items)} new unique items for source '{source.name}'")
        return new_items

    def monitor_all_company_sources(self, db: Session, company_id: int) -> List[CrawledItem]:
        sources = db.query(Source).filter(
            Source.company_id == company_id,
            Source.is_approved == True,
            Source.is_active == True
        ).all()

        total_new_items = []
        for s in sources:
            items = self.crawl_source(db, s)
            total_new_items.extend(items)
        return total_new_items

monitoring_engine = MonitoringEngine()
