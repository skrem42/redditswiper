"""
Subreddit Intel Worker

Entry point for Railway deployment. Continuously scrapes subreddit intelligence
data using Playwright with stealth anti-detection measures.

Usage:
    python intel_worker.py [--worker-id N] [--headless] [--batch-size N]
"""
import asyncio
import argparse
import logging
import random
import sys
from datetime import datetime

from supabase_client import SupabaseClient
from subreddit_intel_scraper import SubredditIntelScraper
from config import (
    PROXY_URL, 
    CRAWLER_MIN_SUBSCRIBERS, 
    BATCH_SIZE, 
    IDLE_WAIT,
    HEADLESS,
    DELAY_MIN,
    DELAY_MAX,
    ROTATE_EVERY,
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


class IntelWorker:
    """
    Worker that continuously scrapes subreddit intelligence data.
    
    Pulls subreddits from the queue (those already crawled) and
    extracts detailed metrics like weekly visitors and contributions.
    """
    
    def __init__(
        self,
        worker_id: int = None,
        batch_size: int = None,
        headless: bool = None,
        min_subscribers: int = None,
    ):
        self.worker_id = worker_id or random.randint(1000, 9999)
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
        logger.info(f"[Worker {self.worker_id}] Intel Worker starting...")
        logger.info(f"[Worker {self.worker_id}] Batch size: {self.batch_size}")
        logger.info(f"[Worker {self.worker_id}] Min subscribers: {self.min_subscribers}")
        logger.info(f"[Worker {self.worker_id}] Headless: {self.headless}")
        logger.info(f"[Worker {self.worker_id}] Proxy: {'Yes' if PROXY_URL else 'No'}")
        logger.info(f"[Worker {self.worker_id}] Delay: {DELAY_MIN}-{DELAY_MAX}s")
        logger.info(f"[Worker {self.worker_id}] Rotate every: {ROTATE_EVERY} subs")
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
                    proxy_url=PROXY_URL,
                    headless=self.headless,
                ) as scraper:
                    self.scraper = scraper
                    
                    results = await scraper.scrape_batch(
                        subreddits=subreddits,
                        delay_min=DELAY_MIN,
                        delay_max=DELAY_MAX,
                        rotate_every=ROTATE_EVERY,
                    )
                    
                    # Update stats
                    scraper_stats = scraper.get_stats()
                    self.stats["total_scraped"] += scraper_stats["successful"]
                    self.stats["total_failed"] += scraper_stats["failed"]
                    self.stats["batches_completed"] += 1
                
                self._log_stats()
                
                # Brief pause between batches
                await asyncio.sleep(random.uniform(10, 20))
                
            except KeyboardInterrupt:
                logger.info(f"[Worker {self.worker_id}] Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] Error in worker loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)  # Wait before retrying
    
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


async def run_single_batch(subreddits: list[str], headless: bool = True):
    """Run a single batch for testing."""
    supabase = SupabaseClient()
    
    async with SubredditIntelScraper(
        supabase_client=supabase,
        headless=headless,
    ) as scraper:
        results = await scraper.scrape_batch(subreddits)
        
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
    parser = argparse.ArgumentParser(description="Subreddit Intel Worker")
    parser.add_argument(
        "--worker-id", 
        type=int, 
        default=None,
        help="Worker ID for logging"
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
        asyncio.run(run_single_batch(args.test, headless=headless if headless is not None else True))
    else:
        # Production mode: continuous worker
        worker = IntelWorker(
            worker_id=args.worker_id,
            batch_size=args.batch_size,
            headless=headless,
            min_subscribers=args.min_subscribers,
        )
        asyncio.run(worker.run(idle_wait=args.idle_wait))


if __name__ == "__main__":
    main()


