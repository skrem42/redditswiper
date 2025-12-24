#!/usr/bin/env python3
"""
Subreddit Intel Worker - JSON API Edition

Uses Reddit's JSON API with rotating proxy IPs.
Much faster and more reliable than Playwright.

Each request gets a NEW IP via unique session ID.
"""
import asyncio
import random
import string
import logging
import sys
from datetime import datetime, timezone
from typing import Optional, List
import httpx

from supabase_client import SupabaseClient
from config import CRAWLER_MIN_SUBSCRIBERS, BATCH_SIZE, CONCURRENT_SUBREDDITS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Suppress noisy httpx/httpcore logs (only show errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class SOAXRotatingProxy:
    """SOAX proxy with automatic IP rotation per request."""
    
    def __init__(self):
        self.package = "329587"
        self.base_password = "YtaNW215Z7RP5A0b"
        self.host = "proxy.soax.com"
        self.port = 5000
    
    def get_proxy_url(self) -> str:
        """Get a proxy URL with unique session ID (new IP)."""
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        username = f"package-{self.package}-sessionid-{session_id}-sessionlength-10"
        return f"http://{username}:{self.base_password}@{self.host}:{self.port}"


class JSONIntelWorker:
    """Intel worker using JSON API - faster and more reliable."""
    
    def __init__(self, worker_id: int = None):
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.supabase = SupabaseClient()
        self.proxy = SOAXRotatingProxy()
        
        self.stats = {
            "scraped": 0,
            "failed": 0,
            "with_subscribers": 0,
            "with_active_users": 0,
            "start_time": datetime.now(timezone.utc),
        }
    
    async def scrape_subreddit(self, subreddit_name: str) -> Optional[dict]:
        """Scrape a single subreddit using JSON API."""
        
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        proxy_url = self.proxy.get_proxy_url()  # New IP each time!
        
        try:
            async with httpx.AsyncClient(
                proxy=proxy_url,
                verify=False,
                timeout=15.0
            ) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                    "Accept-Language": "en-US,en;q=0.9",
                }
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    api_data = response.json().get("data", {})
                    
                    data = {
                        "subreddit_name": subreddit_name.lower(),
                        "display_name": api_data.get("display_name", subreddit_name),
                        "subscribers": api_data.get("subscribers"),
                        "accounts_active": api_data.get("accounts_active"),  # Currently online
                        "description": api_data.get("public_description", "")[:1000],
                        "allows_images": api_data.get("allow_images", True),  # Note: DB column is allows_images
                        "allows_videos": api_data.get("allow_videos", True),  # Note: DB column is allows_videos
                        "last_scraped_at": datetime.now(timezone.utc).isoformat(),
                        "scrape_status": "completed",
                    }
                    
                    # Track stats
                    if data["subscribers"]:
                        self.stats["with_subscribers"] += 1
                    if data["accounts_active"]:
                        self.stats["with_active_users"] += 1
                    
                    return data
                
                elif response.status_code == 429:
                    logger.warning(f"Rate limited on r/{subreddit_name}")
                    return None
                    
                else:
                    logger.warning(f"HTTP {response.status_code} for r/{subreddit_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error scraping r/{subreddit_name}: {type(e).__name__}")
            return None
    
    async def save_result(self, data: dict) -> bool:
        """Save result to Supabase."""
        try:
            self.supabase.client.table("nsfw_subreddit_intel") \
                .upsert(data, on_conflict="subreddit_name") \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    async def fetch_queue(self, batch_size: int = 50) -> List[str]:
        """Fetch subreddits that need scraping."""
        try:
            # Get from queue that aren't in intel table yet
            queue_resp = self.supabase.client.table("subreddit_queue") \
                .select("subreddit_name") \
                .gte("subscribers", CRAWLER_MIN_SUBSCRIBERS) \
                .order("subscribers", desc=True) \
                .limit(1000) \
                .execute()
            
            intel_resp = self.supabase.client.table("nsfw_subreddit_intel") \
                .select("subreddit_name") \
                .execute()
            
            queue_subs = {r["subreddit_name"].lower() for r in queue_resp.data}
            intel_subs = {r["subreddit_name"].lower() for r in intel_resp.data}
            
            # Return subs in queue but not in intel
            pending = list(queue_subs - intel_subs)[:batch_size]
            return pending
            
        except Exception as e:
            logger.error(f"Queue fetch error: {e}")
            return []
    
    async def process_batch(self, subreddits: List[str], concurrent: int = 10):
        """Process a batch of subreddits concurrently."""
        semaphore = asyncio.Semaphore(concurrent)
        
        async def process_one(sub: str):
            async with semaphore:
                data = await self.scrape_subreddit(sub)
                if data:
                    await self.save_result(data)
                    self.stats["scraped"] += 1
                    
                    # Log with actual data (skip accounts_active - usually null in public API)
                    subs = data.get('subscribers', 0)
                    logger.info(f"✓ r/{sub}: {subs:,} subs")
                else:
                    self.stats["failed"] += 1
                
                # Small delay between requests
                await asyncio.sleep(0.5)
        
        await asyncio.gather(*[process_one(sub) for sub in subreddits])
    
    def log_stats(self):
        """Log current statistics."""
        runtime = (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()
        rate = self.stats["scraped"] / (runtime / 3600) if runtime > 0 else 0
        
        logger.info(
            f"📊 Stats: {self.stats['scraped']} scraped, "
            f"{self.stats['failed']} failed, "
            f"Rate: {rate:.0f}/hr"
        )
    
    async def run(self):
        """Main run loop."""
        logger.info("=" * 60)
        logger.info(f"JSON Intel Worker starting (Worker {self.worker_id})")
        logger.info(f"  - Using SOAX with rotating IPs (new IP per request)")
        logger.info(f"  - Min subscribers: {CRAWLER_MIN_SUBSCRIBERS:,}")
        logger.info(f"  - Batch size: {BATCH_SIZE}")
        logger.info(f"  - Concurrent: {CONCURRENT_SUBREDDITS}")
        logger.info("=" * 60)
        
        while True:
            # Fetch batch
            subreddits = await self.fetch_queue(BATCH_SIZE)
            
            if not subreddits:
                logger.info("No pending subreddits, waiting 60s...")
                await asyncio.sleep(60)
                continue
            
            logger.info(f"Processing batch of {len(subreddits)} subreddits...")
            
            # Process batch
            await self.process_batch(subreddits, concurrent=CONCURRENT_SUBREDDITS)
            
            # Log stats
            self.log_stats()
            
            # Brief pause between batches
            await asyncio.sleep(2)


async def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="JSON Intel Worker")
    parser.add_argument("--worker-id", type=int, default=None)
    args = parser.parse_args()
    
    worker = JSONIntelWorker(worker_id=args.worker_id)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

