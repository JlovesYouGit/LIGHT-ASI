"""
ingester.py — Light-ASI LLM Gateway Phase 2
Background world-net ingestion daemon.

Runs a persistent daemon thread that:
  1. Fetches from all feed sources on a configurable interval
  2. Hashes items into the SemanticMap (10^48 space)
  3. Pipes new text into the NodeGraph index
  4. Tracks ingestion metrics and health

The NodeGraph's `_semantic_map_size` is kept in sync so the
ASI emergence checklist can track progress toward 10^9.

Ruleset reference: LLM_GATEWAY_RULESET.md § 6.1
  Pipeline: raw_traffic → hash → node_select → semantic_index → available_for_query
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from engine.world.feeds import fetch_all, FeedItem
from engine.world.semantic_map import SemanticMap

logger = logging.getLogger("light-asi.ingester")

# Default ingestion interval (seconds)
DEFAULT_INTERVAL   = 120   # 2 minutes between full sweeps
MIN_INTERVAL       = 30    # safety floor
BATCH_SLEEP        = 0.1   # sleep between items during a batch
MAX_CRAWL_DEPTH    = 2     # Global phase default
MAX_LINKS_PER_PAGE = 5     # Avoid link explosion
DOMAIN_DELAY       = 1.0   # 1s delay per domain crawl


@dataclass
class IngestionMetrics:
    total_fetched:  int = 0
    total_indexed:  int = 0
    total_errors:   int = 0
    last_run_at:    float = 0.0
    last_run_items: int = 0
    runs:           int = 0
    sources_seen:   dict = field(default_factory=dict)
    visited_urls:   set = field(default_factory=set) # Deduplication cache

    def record_run(self, items: list[FeedItem], errors: int = 0) -> None:
        self.runs += 1
        self.last_run_at = time.time()
        self.last_run_items = len(items)
        self.total_fetched += len(items)
        self.total_errors  += errors
        for item in items:
            self.sources_seen[item.source] = self.sources_seen.get(item.source, 0) + 1

    def to_dict(self) -> dict:
        return {
            "total_fetched":  self.total_fetched,
            "total_indexed":  self.total_indexed,
            "total_errors":   self.total_errors,
            "runs":           self.runs,
            "last_run_items": self.last_run_items,
            "last_run_ago_s": round(time.time() - self.last_run_at, 1) if self.last_run_at else None,
            "sources":        self.sources_seen,
        }


class WorldIngester:
    """
    Background daemon that continuously ingests world-net data into the
    SemanticMap and NodeGraph.

    Usage:
        ingester = WorldIngester(semantic_map, graph)
        ingester.start()   # starts background thread
        ingester.stop()    # signals graceful shutdown
    """

    def __init__(
        self,
        semantic_map: SemanticMap,
        graph,                          # NodeGraph (avoid circular import)
        interval: int = DEFAULT_INTERVAL,
        on_ingest: Optional[Callable[[list[FeedItem]], None]] = None,
    ):
        if interval < MIN_INTERVAL:
            interval = MIN_INTERVAL
            logger.warning(f"Interval clamped to minimum {MIN_INTERVAL}s")

        self.semantic_map  = semantic_map
        self.graph         = graph
        self.interval      = interval
        self.on_ingest     = on_ingest
        self.metrics       = IngestionMetrics()

        self._stop_event   = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._running      = False

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background ingestion daemon thread."""
        if self._running:
            logger.warning("Ingester already running.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="world-ingester",
            daemon=True,
        )
        self._thread.start()
        self._running = True
        logger.info(f"WorldIngester started (interval={self.interval}s)")

    def stop(self) -> None:
        """Signal the daemon to stop after its current cycle."""
        self._stop_event.set()
        self._running = False
        logger.info("WorldIngester stop signal sent.")

    def is_running(self) -> bool:
        return self._running and (self._thread is not None) and self._thread.is_alive()

    # ── Immediate single-run (blocking, for terminal use) ──────────────────

    def run_once(self) -> dict:
        """
        Perform a single ingestion cycle synchronously.
        Returns a summary dict.
        """
        return self._ingest_cycle()

    # ── Internal loop ──────────────────────────────────────────────────────

    def _loop(self) -> None:
        logger.info("WorldIngester daemon entering main loop.")
        while not self._stop_event.is_set():
            try:
                self._ingest_cycle()
            except Exception as e:
                logger.error(f"Ingestion cycle error: {e}", exc_info=True)
                self.metrics.total_errors += 1
            # Wait for next interval, but wake up immediately on stop
            self._stop_event.wait(timeout=self.interval)
        logger.info("WorldIngester daemon exited.")

    def _extract_links(self, html: str, base_url: str) -> list[str]:
        """Extracts valid absolute URLs from HTML content."""
        import re
        from urllib.parse import urljoin, urlparse
        
        links = re.findall(r'href=["\'](https?://[^"\']+)["\']', html)
        if not links:
            # Try relative links
            rel_links = re.findall(r'href=["\'](/[^"\']+)["\']', html)
            links = [urljoin(base_url, l) for l in rel_links]
            
        # Filter: same domain or high-authority extensions
        valid = []
        base_domain = urlparse(base_url).netloc
        for link in links[:50]: # limit scan
            if urlparse(link).netloc == base_domain or any(ext in link for ext in ['.gov', '.edu', '.org']):
                valid.append(link)
        return list(set(valid))

    def _recursive_crawl(self, url: str, depth: int) -> int:
        """Recursively fetches and indexes a URL up to depth."""
        if depth < 0 or url in self.metrics.visited_urls or len(self.metrics.visited_urls) > 5000:
            return 0
        
        self.metrics.visited_urls.add(url)
        logger.info(f"Recursive Crawl (depth={depth}): {url}")
        
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Light-ASI/1.0 (WorldNet; Ingester)"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode('utf-8', errors='ignore')
            
            # Index this page
            title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
            title = title_match.group(1) if title_match else url
            
            item = FeedItem(
                title=title,
                url=url,
                summary=content[:500],
                source="WorldNet-Crawler",
                timestamp=time.time(),
                tags=["recursive", f"depth-{depth}"]
            )
            
            self.semantic_map.ingest(item)
            self.graph.index_text(content, metadata=item.__dict__)
            
            count = 1
            if depth > 0:
                links = self._extract_links(content, url)
                for link in links[:MAX_LINKS_PER_PAGE]:
                    if self._stop_event.is_set(): break
                    time.sleep(DOMAIN_DELAY)
                    count += self._recursive_crawl(link, depth - 1)
            return count
            
        except Exception as e:
            logger.warning(f"Crawl error at {url}: {e}")
            return 0

    def _ingest_cycle(self) -> dict:
        """
        One full fetch → hash → index cycle.
        Ruleset § 6.1 pipeline:
          raw_traffic → hash → node_select → semantic_index → available_for_query
        """
        t_start = time.perf_counter()
        logger.info("World-net ingestion cycle starting…")

        # Step 1: Fetch from all sources
        try:
            items = fetch_all(hn_limit=10, wiki_count=10, arxiv=True, rss=True)
            # Add some seed recursion for Phase 2
            recursive_seeds = [
                "https://en.wikipedia.org/wiki/Artificial_general_intelligence",
                "https://news.ycombinator.com",
                "https://arxiv.org/list/cs.AI/recent"
            ]
        except Exception as e:
            logger.error(f"Fetch error: {e}")
            items = []
            recursive_seeds = []

        errors = 0
        indexed_this_cycle = 0

        for item in items:
            if self._stop_event.is_set():
                break
            try:
                # Step 2: Hash into semantic map (10^48 space)
                self.semantic_map.ingest(item)

                # Step 3: Index into node graph (feeds the node hash pipeline)
                text = item.full_text()
                if text:
                    self.graph.index_text(
                        text,
                        metadata={
                            "source":     item.source,
                            "title":      item.title[:80],
                            "url":        item.url,
                            "tags":       item.tags,
                            "world_net":  True,
                        },
                    )
                    indexed_this_cycle += 1

                # Step 4: Fire optional callback (e.g. terminal notification)
                if self.on_ingest:
                    self.on_ingest([item])

                time.sleep(BATCH_SLEEP)  # be respectful

            except Exception as e:
                logger.warning(f"Item ingestion error: {e}")
                errors += 1

        self.metrics.record_run(items, errors)
        self.metrics.total_indexed += indexed_this_cycle

        # Step 5: Execute Recursive Phase
        for seed in recursive_seeds:
            if self._stop_event.is_set(): break
            indexed_this_cycle += self._recursive_crawl(seed, MAX_CRAWL_DEPTH)
            
        self.metrics.total_indexed += (indexed_this_cycle - indexed_this_cycle) # already added in crawl

        elapsed = (time.perf_counter() - t_start) * 1000
        summary = {
            "items_fetched":   len(items),
            "items_indexed":   indexed_this_cycle,
            "errors":          errors,
            "elapsed_ms":      round(elapsed, 1),
            "semantic_map_size": self.semantic_map.size,
        }
        logger.info(
            f"Cycle complete: {len(items)} fetched, {indexed_this_cycle} indexed, "
            f"{errors} errors, {elapsed:.0f}ms"
        )
        return summary

    # ── Status ─────────────────────────────────────────────────────────────

    def status(self) -> dict:
        return {
            "running":       self.is_running(),
            "interval_s":    self.interval,
            "metrics":       self.metrics.to_dict(),
            "semantic_map":  repr(self.semantic_map),
        }

    def __repr__(self) -> str:
        return (
            f"WorldIngester(running={self.is_running()}, "
            f"interval={self.interval}s, "
            f"fetched={self.metrics.total_fetched})"
        )
