"""
FAST Subreddit Intel Worker

Uses multiple parallel workers with auto-rotating proxies for maximum speed.
Each worker uses a dedicated proxy that rotates IP on every request.

Usage:
    python intel_worker_fast.py [--headless] [--batch-size N] [--test subreddit1 subreddit2 ...]
"""
import asyncio
import argparse
import logging
import random
import sys
from datetime import datetime
from typing import List

from supabase_client import SupabaseClient
from subreddit_intel_scraper import SubredditIntelScraper
from config_fast import (
    PROXY_POOL,
    CRAWLER_MIN_SUBSCRIBERS,
    BATCH_SIZE,
    IDLE_WAIT,
    HEADLESS,
    DELAY_MIN,
    DELAY_MAX,
    NUM_WORKERS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)


class FastIntelWorker:
    """
    Fast worker that runs multiple parallel scrapers with auto-rotating proxies.
    
    Each worker gets its own proxy from the pool and scrapes subreddits concurrently.
    Since proxies rotate on every request, we can run MUCH faster with minimal delays.
    """
    
    def __init__(
        self,
        worker_id: int,
        proxy_config: dict,
        batch_size: int = None,
        headless: bool = None,
        min_subscribers: int = None,
    ):
        self.worker_id = worker_id
        self.proxy_config = proxy_config
        self.batch_size = batch_size or BATCH_SIZE
        self.headless = headless if headless is not None else HEADLESS
        self.min_subscribers = min_subscribers or CRAWLER_MIN_SUBSCRIBERS
        
        self.supabase = SupabaseClient()
        self.scraper: SubredditIntelScraper = None
        
        self.stats = {
            "batches_completed": 0,
            "total_scraped": 0,
            "total_failed": 0,
            "start_time": None,
        }
    
    async def run(self, idle_wait: int = None):
        """
        Main worker loop - runs continuously.
        
        Args:
            idle_wait: Seconds to wait when no work is available
        """
        idle_wait = idle_wait or IDLE_WAIT
        self.stats["start_time"] = datetime.utcnow()
        
        logger.info(f"[Worker {self.worker_id}] ========================================")
        logger.info(f"[Worker {self.worker_id}] FAST Intel Worker starting...")
        logger.info(f"[Worker {self.worker_id}] Proxy: {self.proxy_config['name']}")
        logger.info(f"[Worker {self.worker_id}] Batch size: {self.batch_size}")
        logger.info(f"[Worker {self.worker_id}] Min subscribers: {self.min_subscribers}")
        logger.info(f"[Worker {self.worker_id}] Delays: {DELAY_MIN}-{DELAY_MAX}s (FAST mode)")
        logger.info(f"[Worker {self.worker_id}] ========================================")
        
        while True:
            try:
                # Get pending subreddits to scrape
                pending = await self.supabase.get_pending_intel_scrapes(
                    limit=self.batch_size,
                    min_subscribers=self.min_subscribers,
                )
                
                if not pending:
                    logger.info(
                        f"[Worker {self.worker_id}] No pending subreddits. "
                        f"Waiting {idle_wait}s..."
                    )
                    await asyncio.sleep(idle_wait)
                    continue
                
                subreddits = [s["subreddit_name"] for s in pending]
                
                logger.info(
                    f"[Worker {self.worker_id}] Processing batch of "
                    f"{len(subreddits)} subreddits..."
                )
                
                # Create scraper and process batch
                async with SubredditIntelScraper(
                    supabase_client=self.supabase,
                    worker_id=self.worker_id,
                    proxy_url=self.proxy_config["url"],
                    headless=self.headless,
                ) as scraper:
                    self.scraper = scraper
                    
                    results = await scraper.scrape_batch(
                        subreddits=subreddits,
                        delay_min=DELAY_MIN,
                        delay_max=DELAY_MAX,
                        rotate_every=999999,  # Never rotate - proxy does it automatically
                    )
                    
                    # Update stats
                    scraper_stats = scraper.get_stats()
                    self.stats["total_scraped"] += scraper_stats["successful"]
                    self.stats["total_failed"] += scraper_stats["failed"]
                    self.stats["batches_completed"] += 1
                
                self._log_stats()
                
                # Brief pause between batches
                await asyncio.sleep(random.uniform(2, 5))
                
            except KeyboardInterrupt:
                logger.info(f"[Worker {self.worker_id}] Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] Error in worker loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(30)  # Wait before retrying
    
    def _log_stats(self):
        """Log current worker statistics."""
        runtime = datetime.utcnow() - self.stats["start_time"]
        hours = runtime.total_seconds() / 3600
        
        rate = self.stats["total_scraped"] / hours if hours > 0 else 0
        
        logger.info(
            f"[Worker {self.worker_id}] 📊 Stats: "
            f"{self.stats['batches_completed']} batches, "
            f"{self.stats['total_scraped']} scraped, "
            f"{self.stats['total_failed']} failed, "
            f"{rate:.1f}/hour"
        )


async def run_parallel_workers(
    num_workers: int = None,
    batch_size: int = None,
    headless: bool = None,
    min_subscribers: int = None,
    idle_wait: int = None,
):
    """
    Run multiple workers in parallel, each with its own proxy.
    
    This is the FAST mode - all workers run simultaneously!
    """
    num_workers = num_workers or NUM_WORKERS
    
    logger.info("=" * 60)
    logger.info("🚀 FAST INTEL SCRAPER - PARALLEL MODE")
    logger.info(f"   Running {num_workers} workers in parallel")
    logger.info(f"   Each worker uses a dedicated auto-rotating proxy")
    logger.info(f"   Delays: {DELAY_MIN}-{DELAY_MAX}s (MUCH faster than normal mode)")
    logger.info("=" * 60)
    
    # Create workers, one per proxy
    workers = []
    for i in range(num_workers):
        proxy_config = PROXY_POOL[i % len(PROXY_POOL)]
        
        worker = FastIntelWorker(
            worker_id=i + 1,
            proxy_config=proxy_config,
            batch_size=batch_size,
            headless=headless,
            min_subscribers=min_subscribers,
        )
        workers.append(worker)
    
    # Run all workers in parallel
    tasks = [worker.run(idle_wait=idle_wait) for worker in workers]
    await asyncio.gather(*tasks)


async def run_single_batch_fast(subreddits: List[str], headless: bool = True):
    """Run a single batch in FAST mode for testing."""
    supabase = SupabaseClient()
    
    logger.info("=" * 60)
    logger.info("🧪 TEST MODE - Single batch with FAST settings")
    logger.info(f"   Testing {len(subreddits)} subreddits")
    logger.info(f"   Using proxy: {PROXY_POOL[0]['name']}")
    logger.info("=" * 60)
    
    async with SubredditIntelScraper(
        supabase_client=supabase,
        worker_id=9999,
        proxy_url=PROXY_POOL[0]["url"],
        headless=headless,
    ) as scraper:
        results = await scraper.scrape_batch(
            subreddits=subreddits,
            delay_min=DELAY_MIN,
            delay_max=DELAY_MAX,
            rotate_every=999999,
        )
        
        print(f"\n{'='*50}")
        print(f"Results ({len(results)}/{len(subreddits)} successful)")
        print(f"{'='*50}")
        
        for result in results:
            comp = result.get('competition_score')
            comp_str = f"{comp*100:.2f}%" if comp else "N/A"
            print(f"\nr/{result['subreddit_name']}:")
            print(f"  Subscribers:     {result.get('subscribers', 'N/A'):,}" if result.get('subscribers') else "  Subscribers:     N/A")
            print(f"  Weekly visitors: {result.get('weekly_visitors', 'N/A'):,}" if result.get('weekly_visitors') else "  Weekly visitors: N/A")
            print(f"  Weekly posts:    {result.get('weekly_contributions', 'N/A'):,}" if result.get('weekly_contributions') else "  Weekly posts:    N/A")
            print(f"  Competition:     {comp_str}")
        
        print(f"\n{'='*50}")
        print(f"Scraper Stats: {scraper.get_stats()}")


def main():
    parser = argparse.ArgumentParser(description="FAST Subreddit Intel Worker")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Number of parallel workers (default: {NUM_WORKERS})"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=None,
        help=f"Number of subreddits per batch (default: {BATCH_SIZE})"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
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
        default=None,
        help=f"Minimum subscriber count filter (default: {CRAWLER_MIN_SUBSCRIBERS})"
    )
    parser.add_argument(
        "--test",
        nargs="+",
        help="Test mode: scrape specific subreddits"
    )
    parser.add_argument(
        "--idle-wait",
        type=int,
        default=None,
        help=f"Seconds to wait when queue is empty (default: {IDLE_WAIT})"
    )
    
    args = parser.parse_args()
    
    # Determine headless mode
    if args.no_headless:
        headless = False
    elif args.headless:
        headless = True
    else:
        headless = None  # Use config default
    
    if args.test:
        # Test mode: scrape specific subreddits
        asyncio.run(run_single_batch_fast(
            args.test, 
            headless=headless if headless is not None else True
        ))
    else:
        # Production mode: continuous parallel workers
        asyncio.run(run_parallel_workers(
            num_workers=args.workers,
            batch_size=args.batch_size,
            headless=headless,
            min_subscribers=args.min_subscribers,
            idle_wait=args.idle_wait,
        ))


if __name__ == "__main__":
    main()

