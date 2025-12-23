"""
ULTRA-FAST Subreddit Intel Worker

Runs MANY concurrent scraping tasks with smart error handling.
Auto-rotates IP and browser when rate limited or blocked.

Usage:
    python intel_worker_ultra.py [--concurrency N] [--test subreddit1 subreddit2 ...]
"""
import asyncio
import argparse
import logging
import sys
from datetime import datetime
from typing import List, Optional
import random

from supabase_client import SupabaseClient
from subreddit_intel_scraper import SubredditIntelScraper
import httpx

# Try to use ultra config, fall back to fast config
try:
    from config_ultra import (
        PROXY_CONFIG,
        PROXY_ROTATION_URL,
        CRAWLER_MIN_SUBSCRIBERS,
        HEADLESS,
        NUM_WORKERS,
        DELAY_MIN,
        DELAY_MAX,
        ROTATE_IP_EVERY,
    )
    USING_ULTRA_CONFIG = True
except ImportError:
    from config_fast import (
        PROXY_POOL,
        CRAWLER_MIN_SUBSCRIBERS,
        HEADLESS,
    )
    PROXY_CONFIG = None
    PROXY_ROTATION_URL = ""
    NUM_WORKERS = 10
    DELAY_MIN = 0.5
    DELAY_MAX = 1.0
    ROTATE_IP_EVERY = 999999
    USING_ULTRA_CONFIG = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


class UltraFastScraper:
    """
    Ultra-fast scraper that runs MANY concurrent tasks.
    
    - No artificial delays (proxies auto-rotate!)
    - Smart retry on rate limits
    - Recreates browser on failures
    - Scales to 10-20+ concurrent tasks
    """
    
    def __init__(
        self,
        concurrency: int = 3,
        headless: bool = True,
        min_subscribers: int = 5000,
    ):
        self.concurrency = concurrency
        self.headless = headless
        self.min_subscribers = min_subscribers
        
        self.supabase = SupabaseClient()
        
        # Use single proxy if ultra config, otherwise use pool
        if USING_ULTRA_CONFIG and PROXY_CONFIG:
            self.single_proxy = PROXY_CONFIG
            self.proxy_pool = [PROXY_CONFIG]
            self.using_single_proxy = True
            logger.info(f"Using SINGLE unlimited proxy: {PROXY_CONFIG['name']}")
        else:
            self.single_proxy = None
            self.proxy_pool = PROXY_POOL.copy()
            self.using_single_proxy = False
            logger.info(f"Using POOL of {len(PROXY_POOL)} proxies")
        
        self.stats = {
            "total_scraped": 0,
            "total_failed": 0,
            "total_retries": 0,
            "rate_limits": 0,
            "ip_rotations": 0,
            "start_time": datetime.now(),
        }
        
        # Semaphore to limit concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
    
    def _get_proxy_for_worker(self, worker_id: int) -> dict:
        """Get a proxy from the pool (round-robin)."""
        return self.proxy_pool[worker_id % len(self.proxy_pool)]
    
    async def rotate_ip_if_needed(self, scrapes_since_rotation: int):
        """Manually rotate IP using rotation API if available."""
        if USING_ULTRA_CONFIG and PROXY_ROTATION_URL and scrapes_since_rotation >= ROTATE_IP_EVERY:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info("🔄 Calling proxy rotation API...")
                    response = await client.get(PROXY_ROTATION_URL)
                    if response.status_code == 200:
                        self.stats["ip_rotations"] += 1
                        logger.info(f"✓ IP rotated successfully (#{self.stats['ip_rotations']})")
                        await asyncio.sleep(3)  # Brief pause after rotation
                        return True
                    else:
                        logger.warning(f"IP rotation failed: {response.status_code}")
            except Exception as e:
                logger.error(f"IP rotation error: {e}")
        return False
    
    async def scrape_single(
        self, 
        subreddit_name: str, 
        worker_id: int,
        retry_count: int = 0,
        max_retries: int = 2,  # Only retry twice (some subs don't display metrics)
    ) -> Optional[dict]:
        """
        Scrape a single subreddit with smart retry logic.
        Browser is ALWAYS closed after each scrape (fresh every time).
        
        Returns scraped data or None if failed after retries.
        """
        async with self.semaphore:  # Limit concurrency
            proxy_config = self._get_proxy_for_worker(worker_id)
            
            try:
                # Create a FRESH scraper for this subreddit (always new browser)
                # Always use ultra_fast=True to skip mouse movements (causes issues in concurrent mode)
                scraper = SubredditIntelScraper(
                    supabase_client=self.supabase,
                    worker_id=worker_id,
                    proxy_url=proxy_config["url"],
                    headless=self.headless,
                    ultra_fast=True,  # Skip mouse movements (they cause crashes in concurrent mode)
                    enable_llm=True,  # Enable LLM analysis after scraping
                )
                
                try:
                    await scraper.start()
                    
                    # Scrape the subreddit
                    data = await scraper.scrape_subreddit(subreddit_name)
                    
                except Exception as scrape_error:
                    # Ensure cleanup happens even on error
                    try:
                        await scraper.close()
                    except:
                        pass
                    raise scrape_error
                finally:
                    # ALWAYS close browser after scraping (fresh browser next time)
                    try:
                        await scraper.close()
                    except Exception as close_error:
                        logger.debug(f"Browser close error (already closed?): {close_error}")
                
                if data:
                    # Check if data is valid (page rendered properly)
                    has_visitors = data.get("weekly_visitors") is not None
                    has_contributions = data.get("weekly_contributions") is not None
                    
                    # ONLY save if we have at least ONE metric
                    if has_visitors or has_contributions:
                        # Save the data (even if partial)
                        await self.supabase.upsert_subreddit_intel(data)
                        self.stats["total_scraped"] += 1
                        
                        if has_visitors and has_contributions:
                            # Perfect! Both metrics
                            logger.info(
                                f"[Worker {worker_id}] ✓ r/{subreddit_name}: "
                                f"{data.get('weekly_visitors'):,} visitors, "
                                f"{data.get('weekly_contributions'):,} contributions"
                            )
                        else:
                            # Partial data (some subs don't show all metrics)
                            logger.info(
                                f"[Worker {worker_id}] ✓ r/{subreddit_name}: "
                                f"visitors={data.get('weekly_visitors', 'N/A')}, "
                                f"contributions={data.get('weekly_contributions', 'N/A')} "
                                f"(partial data - sub may not display all metrics)"
                            )
                        
                        # Add small delay after successful scrape (if using ultra config)
                        if USING_ULTRA_CONFIG:
                            delay = random.uniform(DELAY_MIN, DELAY_MAX)
                            await asyncio.sleep(delay)
                        
                        return data
                    else:
                        # Both are NULL - page didn't render or sub doesn't show metrics
                        # Only retry if it's likely a rendering issue (not just missing data)
                        if retry_count == 0:
                            # First attempt - might be rendering issue, try once more
                            logger.warning(
                                f"[Worker {worker_id}] ⚠ r/{subreddit_name}: "
                                f"No metrics found - retrying once (may not display metrics)"
                            )
                            raise Exception("No metrics found - retry once")
                        else:
                            # Second attempt failed - sub probably doesn't display metrics
                            # Save with NULLs and mark as scraped (don't keep retrying)
                            logger.info(
                                f"[Worker {worker_id}] ℹ r/{subreddit_name}: "
                                f"No metrics available (sub may not display them) - saving anyway"
                            )
                            await self.supabase.upsert_subreddit_intel(data)
                            self.stats["total_scraped"] += 1
                            return data
                else:
                    raise Exception("Scrape returned None")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[Worker {worker_id}] ✗ r/{subreddit_name}: {error_msg[:100]}")
                
                # Check if it's a rate limit or block
                is_rate_limit = "403" in error_msg or "429" in error_msg or "blocked" in error_msg.lower()
                
                if is_rate_limit:
                    self.stats["rate_limits"] += 1
                    logger.warning(f"[Worker {worker_id}] 🛑 Rate limited! Waiting 10s...")
                    await asyncio.sleep(10)  # Back off on rate limits
                
                # Retry with a different proxy/worker ID (new IP!)
                if retry_count < max_retries:
                    self.stats["total_retries"] += 1
                    new_worker_id = worker_id + 1000  # Use different proxy
                    logger.info(
                        f"[Worker {worker_id}] 🔄 Retry {retry_count + 1}/{max_retries} "
                        f"for r/{subreddit_name} (switching IP)"
                    )
                    await asyncio.sleep(2)  # Brief pause before retry
                    return await self.scrape_single(
                        subreddit_name, 
                        new_worker_id, 
                        retry_count + 1,
                        max_retries
                    )
                else:
                    # Max retries reached
                    self.stats["total_failed"] += 1
                    await self.supabase.mark_intel_failed(
                        subreddit_name,
                        f"Failed after {max_retries} retries: {error_msg[:200]}"
                    )
                    return None
    
    async def scrape_batch(self, subreddits: List[str], scrapes_since_rotation: int = 0) -> tuple[List[dict], int]:
        """
        Scrape a batch of subreddits CONCURRENTLY.
        
        Returns tuple of (successfully scraped data, new rotation counter).
        """
        logger.info(f"🚀 Starting batch of {len(subreddits)} subreddits with {self.concurrency} concurrent workers")
        
        # Rotate IP before batch if needed
        if await self.rotate_ip_if_needed(scrapes_since_rotation):
            scrapes_since_rotation = 0
        
        # Create concurrent tasks
        tasks = [
            self.scrape_single(sub, worker_id=i)
            for i, sub in enumerate(subreddits)
        ]
        
        # Run ALL tasks concurrently!
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None and exceptions
        successful = [r for r in results if r and not isinstance(r, Exception)]
        
        # Update rotation counter
        scrapes_since_rotation += len(successful)
        
        return successful, scrapes_since_rotation
    
    async def run_continuous(self, batch_size: int = 50, idle_wait: int = 60):
        """
        Continuous scraping mode - keeps pulling from queue.
        """
        logger.info("=" * 60)
        if USING_ULTRA_CONFIG:
            logger.info("⚡ ULTRA-FAST INTEL SCRAPER - CONSERVATIVE MODE")
            logger.info(f"   Concurrency: {self.concurrency} simultaneous scrapes")
            logger.info(f"   Batch size: {batch_size} subreddits per round")
            logger.info(f"   Proxy: Single unlimited proxy")
            logger.info(f"   Delays: {DELAY_MIN}-{DELAY_MAX}s between scrapes")
            logger.info(f"   IP Rotation: Every {ROTATE_IP_EVERY} successful scrapes")
            logger.info(f"   Browser: Fresh for EVERY subreddit")
        else:
            logger.info("⚡ ULTRA-FAST INTEL SCRAPER")
            logger.info(f"   Concurrency: {self.concurrency} simultaneous scrapes")
            logger.info(f"   Batch size: {batch_size} subreddits per round")
            logger.info(f"   Proxies: {len(self.proxy_pool)} auto-rotating")
            logger.info(f"   Mode: NO DELAYS - full speed!")
        logger.info("=" * 60)
        
        scrapes_since_rotation = 0
        while True:
            try:
                # FIRST: Get pending subreddits (normal queue - prioritize new ones)
                pending = await self.supabase.get_pending_intel_scrapes(
                    limit=batch_size,
                    min_subscribers=self.min_subscribers,
                )
                
                if pending:
                    subreddits = [s["subreddit_name"] for s in pending]
                else:
                    # If no new pending, check for NULL entries that need retry
                    null_entries = await self.supabase.get_null_intel_scrapes(limit=batch_size)
                    
                    if null_entries:
                        logger.info(f"🔄 No new pending subs - found {len(null_entries)} with NULL data to retry")
                        subreddits = [s["subreddit_name"] for s in null_entries]
                    else:
                        logger.info(f"No pending subreddits. Waiting {idle_wait}s...")
                        self._log_stats()
                        await asyncio.sleep(idle_wait)
                        continue
                
                logger.info(f"\n📦 Processing batch of {len(subreddits)} subreddits...")
                
                # Scrape the batch concurrently
                start_time = datetime.now()
                results, scrapes_since_rotation = await self.scrape_batch(subreddits, scrapes_since_rotation)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # Log batch stats
                rate = len(results) / elapsed if elapsed > 0 else 0
                logger.info(
                    f"✓ Batch complete: {len(results)}/{len(subreddits)} successful "
                    f"in {elapsed:.1f}s ({rate:.2f} subs/sec)"
                )
                if USING_ULTRA_CONFIG:
                    logger.info(f"   📊 Scrapes since IP rotation: {scrapes_since_rotation}/{ROTATE_IP_EVERY}")
                
                self._log_stats()
                
                # Very brief pause between batches
                await asyncio.sleep(2)
                
            except KeyboardInterrupt:
                logger.info("Stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(30)
    
    def _log_stats(self):
        """Log current statistics."""
        runtime = (datetime.now() - self.stats["start_time"]).total_seconds()
        hours = runtime / 3600
        
        rate = self.stats["total_scraped"] / hours if hours > 0 else 0
        
        stats_msg = (
            f"📊 Total: {self.stats['total_scraped']} scraped, "
            f"{self.stats['total_failed']} failed, "
            f"{self.stats['total_retries']} retries, "
            f"{self.stats['rate_limits']} rate limits"
        )
        
        if USING_ULTRA_CONFIG:
            stats_msg += f", {self.stats['ip_rotations']} IP rotations"
        
        stats_msg += f", {rate:.1f}/hour"
        
        logger.info(stats_msg)


async def run_test(subreddits: List[str], concurrency: int = 3, headless: bool = True):
    """Test mode - scrape specific subreddits."""
    scraper = UltraFastScraper(
        concurrency=concurrency,
        headless=headless,
    )
    
    logger.info("=" * 60)
    logger.info("🧪 TEST MODE - Ultra-fast concurrent scraping")
    logger.info(f"   Testing {len(subreddits)} subreddits")
    logger.info(f"   Concurrency: {concurrency}")
    if USING_ULTRA_CONFIG:
        logger.info(f"   Using: Single unlimited proxy")
        logger.info(f"   Delays: {DELAY_MIN}-{DELAY_MAX}s")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    results, _ = await scraper.scrape_batch(subreddits)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"Results ({len(results)}/{len(subreddits)} successful in {elapsed:.1f}s)")
    print(f"{'='*60}")
    
    for result in results:
        comp = result.get('competition_score')
        comp_str = f"{comp*100:.2f}%" if comp else "N/A"
        print(f"\nr/{result['subreddit_name']}:")
        if result.get('subscribers'):
            print(f"  Subscribers:     {result['subscribers']:,}")
        if result.get('weekly_visitors'):
            print(f"  Weekly visitors: {result['weekly_visitors']:,}")
        if result.get('weekly_contributions'):
            print(f"  Weekly posts:    {result['weekly_contributions']:,}")
        print(f"  Competition:     {comp_str}")
    
    print(f"\n{'='*60}")
    scraper._log_stats()


def main():
    parser = argparse.ArgumentParser(description="Ultra-Fast Subreddit Intel Worker")
    parser.add_argument(
        "--concurrency",
        type=int,
        default=None,
        help=f"Number of concurrent scraping tasks (default: {NUM_WORKERS if USING_ULTRA_CONFIG else 10})"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of subreddits per batch (default: 50)"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with visible window (for debugging)"
    )
    parser.add_argument(
        "--min-subscribers",
        type=int,
        default=CRAWLER_MIN_SUBSCRIBERS,
        help=f"Minimum subscriber count filter (default: {CRAWLER_MIN_SUBSCRIBERS})"
    )
    parser.add_argument(
        "--test",
        nargs="+",
        help="Test mode: scrape specific subreddits"
    )
    parser.add_argument(
        "--retry-nulls",
        action="store_true",
        help="Retry all subreddits with NULL data (one-time run)"
    )
    parser.add_argument(
        "--idle-wait",
        type=int,
        default=60,
        help="Seconds to wait when queue is empty (default: 60)"
    )
    
    args = parser.parse_args()
    
    # Use config defaults if not specified
    concurrency = args.concurrency if args.concurrency is not None else (NUM_WORKERS if USING_ULTRA_CONFIG else 10)
    
    # Determine headless mode
    if args.no_headless:
        headless = False
    elif args.headless:
        headless = True
    else:
        headless = HEADLESS
    
    if args.test:
        # Test mode
        asyncio.run(run_test(
            args.test,
            concurrency=concurrency,
            headless=headless,
        ))
    elif args.retry_nulls:
        # Retry NULL entries mode
        async def retry_nulls():
            scraper = UltraFastScraper(
                concurrency=concurrency,
                headless=headless,
                min_subscribers=args.min_subscribers,
            )
            
            logger.info("=" * 60)
            logger.info("🔄 RETRY NULL ENTRIES MODE")
            logger.info(f"   Concurrency: {args.concurrency}")
            logger.info("=" * 60)
            
            # Get all NULL entries
            null_entries = await scraper.supabase.get_null_intel_scrapes(limit=1000)
            
            if not null_entries:
                logger.info("✓ No NULL entries found! All subreddits have complete data.")
                return
            
            logger.info(f"Found {len(null_entries)} subreddits with NULL data")
            subreddits = [s["subreddit_name"] for s in null_entries]
            
            # Scrape them all
            start_time = datetime.now()
            results, _ = await scraper.scrape_batch(subreddits)
            elapsed = (datetime.now() - start_time).total_seconds()
            
            logger.info(
                f"\n✓ Retry complete: {len(results)}/{len(subreddits)} fixed "
                f"in {elapsed:.1f}s"
            )
            scraper._log_stats()
        
        asyncio.run(retry_nulls())
    else:
        # Production mode: continuous ultra-fast scraping
        scraper = UltraFastScraper(
            concurrency=concurrency,
            headless=headless,
            min_subscribers=args.min_subscribers,
        )
        asyncio.run(scraper.run_continuous(
            batch_size=args.batch_size,
            idle_wait=args.idle_wait,
        ))


if __name__ == "__main__":
    main()

