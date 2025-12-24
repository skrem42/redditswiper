"""
Subreddit Intel Worker - Parallel Edition

Entry point for Railway deployment. Continuously scrapes subreddit intelligence
data using Playwright with parallel browser contexts and stealth anti-detection.

Usage:
    python intel_worker.py [--worker-id N] [--headless] [--batch-size N] [--parallel N]
"""
import asyncio
import argparse
import logging
import random
import sys
from datetime import datetime, timezone

from supabase_client import SupabaseClient
from subreddit_intel_scraper import SubredditIntelScraper
from stealth_browser import BrowserPool
from config import (
    PROXY_URL,
    CRAWLER_MIN_SUBSCRIBERS, 
    BATCH_SIZE, 
    IDLE_WAIT,
    HEADLESS,
    DELAY_MIN,
    DELAY_MAX,
    ROTATE_EVERY,
    BROWSER_POOL_SIZE,
    CONCURRENT_SUBREDDITS,
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


class ParallelIntelWorker:
    """
    High-performance parallel worker for subreddit intelligence scraping.
    
    Uses a pool of browser contexts to scrape multiple subreddits simultaneously.
    Each browser context has its own Reddit account for authenticated access.
    """
    
    def __init__(
        self,
        worker_id: int = None,
        batch_size: int = None,
        pool_size: int = None,
        headless: bool = None,
        min_subscribers: int = None,
    ):
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.batch_size = batch_size or BATCH_SIZE
        self.pool_size = pool_size or BROWSER_POOL_SIZE
        self.headless = headless if headless is not None else HEADLESS
        self.min_subscribers = min_subscribers or CRAWLER_MIN_SUBSCRIBERS
        
        self.supabase = SupabaseClient()
        self.browser_pool: BrowserPool = None
        
        # Use SOAX proxy
        self.proxy = PROXY_URL
        
        self.stats = {
            "batches_completed": 0,
            "total_scraped": 0,
            "total_failed": 0,
            "start_time": None,
        }
    
    async def run(self, idle_wait: int = None):
        """
        Main worker loop - runs continuously with parallel processing.
        
        Args:
            idle_wait: Seconds to wait when no work is available
        """
        idle_wait = idle_wait or IDLE_WAIT
        self.stats["start_time"] = datetime.now(timezone.utc)
        
        logger.info(f"[Worker {self.worker_id}] ========================================")
        logger.info(f"[Worker {self.worker_id}] Parallel Intel Worker starting...")
        logger.info(f"[Worker {self.worker_id}] Batch size: {self.batch_size}")
        logger.info(f"[Worker {self.worker_id}] Browser pool size: {self.pool_size}")
        logger.info(f"[Worker {self.worker_id}] Concurrent subreddits: {CONCURRENT_SUBREDDITS}")
        logger.info(f"[Worker {self.worker_id}] Min subscribers: {self.min_subscribers}")
        logger.info(f"[Worker {self.worker_id}] Headless: {self.headless}")
        logger.info(f"[Worker {self.worker_id}] Proxy: {'SOAX' if self.proxy else 'None'}")
        logger.info(f"[Worker {self.worker_id}] ========================================")
        
        # Initialize browser pool
        async with BrowserPool(
            size=self.pool_size,
            proxy_url=self.proxy,
            headless=self.headless,
            worker_id=self.worker_id,
        ) as pool:
            self.browser_pool = pool
            
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
                        f"{len(subreddits)} subreddits in parallel..."
                    )
                    
                    # Process subreddits in parallel using browser pool
                    results = await self._process_batch_parallel(subreddits)
                    
                    # Update stats
                    self.stats["total_scraped"] += len([r for r in results if r])
                    self.stats["total_failed"] += len([r for r in results if not r])
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
                    await asyncio.sleep(60)
    
    async def _process_batch_parallel(self, subreddits: list[str]) -> list[dict]:
        """
        Process a batch of subreddits in parallel using the browser pool.
        
        Args:
            subreddits: List of subreddit names to scrape
            
        Returns:
            List of results (dict for success, None for failure)
        """
        # Create semaphore to limit concurrent scrapes
        semaphore = asyncio.Semaphore(CONCURRENT_SUBREDDITS)
        
        async def scrape_one(subreddit_name: str) -> dict:
            async with semaphore:
                # Acquire a browser context from the pool
                ctx = await self.browser_pool.acquire(timeout=60.0)
                if not ctx:
                    logger.warning(f"Could not acquire browser context for r/{subreddit_name}")
                    await self.supabase.mark_intel_failed(subreddit_name, "No browser context available")
                    return None
                
                try:
                    # Create a single-use scraper with the borrowed page
                    result = await self._scrape_subreddit(
                        subreddit_name=subreddit_name,
                        page=ctx["page"],
                        worker_id=ctx["worker_id"],
                    )
                    
                    if result:
                        await self.supabase.upsert_subreddit_intel(result)
                        return result
                    else:
                        await self.supabase.mark_intel_failed(subreddit_name, "Scrape failed")
                        return None
                        
                except Exception as e:
                    logger.error(f"[Worker {ctx['worker_id']}] Error scraping r/{subreddit_name}: {e}")
                    await self.supabase.mark_intel_failed(subreddit_name, str(e))
                    return None
                finally:
                    # Release context back to pool
                    await self.browser_pool.release(ctx)
        
        # Run all scrapes in parallel
        results = await asyncio.gather(*[scrape_one(sub) for sub in subreddits])
        return results
    
    async def _scrape_subreddit(self, subreddit_name: str, page, worker_id: int) -> dict:
        """
        Scrape a single subreddit using a borrowed page from the pool.
        
        This is a simplified version of SubredditIntelScraper.scrape_subreddit
        that works with an existing page.
        """
        import re
        import httpx
        from subreddit_intel_scraper import parse_metric_value
        
        url = f"https://www.reddit.com/r/{subreddit_name}"
        logger.info(f"[Worker {worker_id}] Scraping r/{subreddit_name}...")
        
        try:
            # Navigate to subreddit
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if not response or response.status != 200:
                logger.warning(f"[Worker {worker_id}] Failed to load r/{subreddit_name}: {response.status if response else 'No response'}")
                return None
            
            # Handle NSFW consent dialogs
            consent_selectors = [
                'button:has-text("Yes, I\'m over 18")',
                'button:has-text("I am 18 or older")',
                '[data-testid="over-18-button"]',
            ]
            for selector in consent_selectors:
                try:
                    await page.click(selector, timeout=2000)
                    await asyncio.sleep(0.5)
                except:
                    pass
            
            # Wait for content
            await asyncio.sleep(1)
            
            # Scroll to trigger lazy loading
            await page.evaluate('window.scrollTo(0, 500)')
            await asyncio.sleep(0.5)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(1)
            
            # Extract data
            data = {"subreddit_name": subreddit_name.lower()}
            
            # Get subscriber count from JSON API
            try:
                json_url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.get(json_url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    })
                    if resp.status_code == 200:
                        json_data = resp.json()
                        if json_data and "data" in json_data:
                            sub_data = json_data["data"]
                            if sub_data.get("subscribers"):
                                data["subscribers"] = sub_data["subscribers"]
            except:
                pass
            
            # Extract weekly visitors and contributions from page
            content = await page.content()
            
            # Weekly visitors
            slot_match = re.search(r'slot="weekly-active-users-count"[^>]*>([^<]+)<', content)
            if slot_match:
                data["weekly_visitors"] = parse_metric_value(slot_match.group(1))
            
            # Weekly contributions
            for slot_pattern in [
                r'slot="weekly-posts-count"[^>]*>([^<]+)<',
                r'slot="weekly-contributions-count"[^>]*>([^<]+)<',
            ]:
                slot_match = re.search(slot_pattern, content)
                if slot_match:
                    data["weekly_contributions"] = parse_metric_value(slot_match.group(1))
                    break
            
            # Calculate competition score
            if data.get("weekly_visitors") and data.get("weekly_contributions"):
                data["competition_score"] = round(
                    data["weekly_contributions"] / data["weekly_visitors"], 6
                )
            
            # Add metadata
            data["display_name"] = f"r/{subreddit_name}"
            data["last_scraped_at"] = datetime.now(timezone.utc).isoformat()
            data["scrape_status"] = "completed"
            
            logger.info(
                f"[Worker {worker_id}] ✓ r/{subreddit_name}: "
                f"{data.get('weekly_visitors', 'N/A')} visitors, "
                f"{data.get('weekly_contributions', 'N/A')} contributions"
            )
            
            return data
            
        except Exception as e:
            logger.error(f"[Worker {worker_id}] Error scraping r/{subreddit_name}: {e}")
            return None
    
    def _log_stats(self):
        """Log current worker statistics."""
        runtime = datetime.now(timezone.utc) - self.stats["start_time"]
        hours = runtime.total_seconds() / 3600
        
        rate = self.stats["total_scraped"] / hours if hours > 0 else 0
        
        pool_stats = self.browser_pool.get_stats() if self.browser_pool else {}
        
        logger.info(
            f"[Worker {self.worker_id}] 📊 Stats: "
            f"{self.stats['batches_completed']} batches, "
            f"{self.stats['total_scraped']} scraped, "
            f"{self.stats['total_failed']} failed, "
            f"{rate:.1f}/hour, "
            f"pool: {pool_stats.get('available', '?')}/{pool_stats.get('pool_size', '?')} available"
        )


# Legacy worker for backwards compatibility
class IntelWorker:
    """
    Legacy worker that uses single browser.
    For parallel processing, use ParallelIntelWorker.
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
        """Main worker loop - runs continuously."""
        idle_wait = idle_wait or IDLE_WAIT
        self.stats["start_time"] = datetime.now(timezone.utc)
        
        proxy = PROXY_URL
        
        logger.info(f"[Worker {self.worker_id}] ========================================")
        logger.info(f"[Worker {self.worker_id}] Intel Worker starting (legacy mode)...")
        logger.info(f"[Worker {self.worker_id}] Batch size: {self.batch_size}")
        logger.info(f"[Worker {self.worker_id}] Min subscribers: {self.min_subscribers}")
        logger.info(f"[Worker {self.worker_id}] Headless: {self.headless}")
        logger.info(f"[Worker {self.worker_id}] Proxy: {'Yes' if proxy else 'No'}")
        logger.info(f"[Worker {self.worker_id}] ========================================")
        
        while True:
            try:
                pending = await self.supabase.get_pending_intel_scrapes(
                    limit=self.batch_size,
                    min_subscribers=self.min_subscribers,
                )
                
                if not pending:
                    logger.info(f"[Worker {self.worker_id}] No pending. Waiting {idle_wait}s...")
                    await asyncio.sleep(idle_wait)
                    continue
                
                subreddits = [s["subreddit_name"] for s in pending]
                logger.info(f"[Worker {self.worker_id}] Processing {len(subreddits)} subreddits...")
                
                async with SubredditIntelScraper(
                    supabase_client=self.supabase,
                    worker_id=self.worker_id,
                    proxy_url=proxy,
                    headless=self.headless,
                ) as scraper:
                    self.scraper = scraper
                    results = await scraper.scrape_batch(
                        subreddits=subreddits,
                        delay_min=DELAY_MIN,
                        delay_max=DELAY_MAX,
                        rotate_every=ROTATE_EVERY,
                    )
                    
                    scraper_stats = scraper.get_stats()
                    self.stats["total_scraped"] += scraper_stats["successful"]
                    self.stats["total_failed"] += scraper_stats["failed"]
                    self.stats["batches_completed"] += 1
                
                self._log_stats()
                await asyncio.sleep(random.uniform(5, 10))
                
            except KeyboardInterrupt:
                logger.info(f"[Worker {self.worker_id}] Worker stopped by user")
                break
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] Error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)
    
    def _log_stats(self):
        runtime = datetime.now(timezone.utc) - self.stats["start_time"]
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
    proxy = PROXY_URL
    
    async with SubredditIntelScraper(
        supabase_client=supabase,
        headless=headless,
        proxy_url=proxy,
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
        "--pool-size",
        type=int,
        default=None,
        help=f"Number of browser contexts in pool (default: {BROWSER_POOL_SIZE})"
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
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Use legacy single-browser mode instead of parallel"
    )
    
    args = parser.parse_args()
    
    # Determine headless mode
    if args.no_headless:
        headless = False
    elif args.headless:
        headless = True
    else:
        headless = None
    
    if args.test:
        # Test mode
        asyncio.run(run_single_batch(args.test, headless=headless if headless is not None else True))
    elif args.legacy:
        # Legacy single-browser mode
        worker = IntelWorker(
            worker_id=args.worker_id,
            batch_size=args.batch_size,
            headless=headless,
            min_subscribers=args.min_subscribers,
        )
        asyncio.run(worker.run(idle_wait=args.idle_wait))
    else:
        # Parallel mode (default)
        worker = ParallelIntelWorker(
            worker_id=args.worker_id,
            batch_size=args.batch_size,
            pool_size=args.pool_size,
            headless=headless,
            min_subscribers=args.min_subscribers,
        )
        asyncio.run(worker.run(idle_wait=args.idle_wait))


if __name__ == "__main__":
    main()
