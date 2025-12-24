"""
NSFW Subreddit Crawler - Parallel Edition

Continuously discovers and crawls NSFW subreddits by following user cross-posts.
Optimized for Brightdata residential rotating proxies with parallel processing.

When a user is found in one subreddit, we check what other subreddits they post in
and add those NSFW subreddits to the crawl queue.
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Optional

from reddit_client import RedditClient
from supabase_client import SupabaseClient
from config import (
    MAX_POSTS_PER_SUBREDDIT, 
    CRAWLER_MIN_SUBSCRIBERS,
    CONCURRENT_SUBREDDITS,
    CONCURRENT_USERS,
    MAX_CONCURRENT_REQUESTS,
    PROXY_URL,
    BRIGHTDATA_PROXY,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ParallelSubredditCrawler:
    """
    High-performance parallel crawler for NSFW subreddits.
    
    Discovery works by:
    1. Claim multiple subreddits from queue (CONCURRENT_SUBREDDITS at a time)
    2. For each subreddit in parallel: scrape posts
    3. For each unique user in parallel: fetch profile and recent posts
    4. Check discovered subreddits in parallel for NSFW status
    5. Add new NSFW subreddits to the queue
    6. Repeat
    
    Optimized for Brightdata residential rotating proxies - each request gets
    a fresh IP automatically, so we can safely run many concurrent requests.
    """

    def __init__(
        self, 
        supabase_client: SupabaseClient,
        worker_id: int = None,
        min_subscribers: int = None,
        concurrent_subs: int = None,
        concurrent_users: int = None,
    ):
        self.supabase = supabase_client
        self.worker_id = worker_id or 1
        self.min_subscribers = min_subscribers if min_subscribers is not None else CRAWLER_MIN_SUBSCRIBERS
        self.concurrent_subs = concurrent_subs or CONCURRENT_SUBREDDITS
        self.concurrent_users = concurrent_users or CONCURRENT_USERS
        
        # Semaphores for rate limiting
        self.request_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        self.user_semaphore = asyncio.Semaphore(self.concurrent_users)
        
        # Use Brightdata if available, otherwise legacy proxy
        self.proxy = BRIGHTDATA_PROXY or PROXY_URL
        
        self.stats = {
            "subreddits_crawled": 0,
            "users_processed": 0,
            "leads_saved": 0,
            "posts_saved": 0,
            "new_subs_discovered": 0,
            "subs_skipped_small": 0,
            "batches_completed": 0,
        }

    async def run(self, idle_wait: int = 60):
        """
        Main crawler loop - runs indefinitely processing batches in parallel.
        
        Args:
            idle_wait: Seconds to wait when queue is empty
        """
        logger.info(f"[Worker {self.worker_id}] ========================================")
        logger.info(f"[Worker {self.worker_id}] Starting Parallel NSFW Subreddit Crawler")
        logger.info(f"[Worker {self.worker_id}] Concurrent subreddits: {self.concurrent_subs}")
        logger.info(f"[Worker {self.worker_id}] Concurrent users: {self.concurrent_users}")
        logger.info(f"[Worker {self.worker_id}] Min subscribers: {self.min_subscribers}")
        logger.info(f"[Worker {self.worker_id}] Proxy: {'Brightdata' if BRIGHTDATA_PROXY else 'Legacy' if self.proxy else 'None'}")
        logger.info(f"[Worker {self.worker_id}] ========================================")
        
        # Reset any stale processing entries from crashed runs
        reset_count = await self.supabase.reset_stale_processing(minutes=30)
        if reset_count > 0:
            logger.info(f"[Worker {self.worker_id}] Reset {reset_count} stale processing entries")
        
        while True:
            try:
                # Claim a batch of subreddits
                batch = await self._claim_batch()
                
                if not batch:
                    queue_stats = await self.supabase.get_queue_stats()
                    logger.info(
                        f"[Worker {self.worker_id}] Queue empty. Stats: {queue_stats['completed']} completed, "
                        f"{queue_stats['failed']} failed. Waiting {idle_wait}s..."
                    )
                    await asyncio.sleep(idle_wait)
                    continue
                
                logger.info(f"[Worker {self.worker_id}] Processing batch of {len(batch)} subreddits...")
                
                # Process all subreddits in parallel
                await asyncio.gather(*[
                    self._crawl_subreddit_safe(sub_entry)
                    for sub_entry in batch
                ])
                
                self.stats["batches_completed"] += 1
                self._log_stats()
                    
            except KeyboardInterrupt:
                logger.info(f"[Worker {self.worker_id}] Crawler stopped by user")
                break
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] Error in crawler loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(30)

    async def _claim_batch(self) -> list[dict]:
        """Claim multiple subreddits from the queue for parallel processing."""
        batch = []
        for _ in range(self.concurrent_subs):
            sub_entry = await self.supabase.claim_next_subreddit(
                min_subscribers=self.min_subscribers
            )
            if sub_entry:
                batch.append(sub_entry)
            else:
                break  # No more available
        return batch

    async def _crawl_subreddit_safe(self, sub_entry: dict):
        """Wrapper to catch exceptions per-subreddit without failing the batch."""
        try:
            await self._crawl_subreddit(sub_entry)
        except Exception as e:
            logger.error(f"Error crawling r/{sub_entry['subreddit_name']}: {e}")
            await self.supabase.fail_subreddit_crawl(sub_entry["id"], str(e))

    async def _crawl_subreddit(self, sub_entry: dict):
        """
        Crawl a single subreddit and discover new ones from user cross-posts.
        Uses parallel user processing for speed.
        """
        sub_name = sub_entry["subreddit_name"]
        queue_id = sub_entry["id"]
        
        logger.info(f"[Worker {self.worker_id}] Crawling r/{sub_name}...")
        
        # Fetch posts from the subreddit
        async with self.request_semaphore:
            async with RedditClient(proxy=self.proxy, worker_id=self.worker_id) as client:
                posts = await client.get_subreddit_posts(
                    sub_name,
                    sort="new",
                    limit=MAX_POSTS_PER_SUBREDDIT,
                )
        
        if not posts:
            logger.warning(f"[Worker {self.worker_id}] No posts from r/{sub_name} (empty or private)")
            await self.supabase.fail_subreddit_crawl(
                queue_id, 
                "No posts returned - subreddit may be empty or private"
            )
            return
        
        logger.info(f"[Worker {self.worker_id}]   r/{sub_name}: {len(posts)} posts")
        
        # Group posts by user
        user_posts = self._group_posts_by_user(posts)
        logger.info(f"[Worker {self.worker_id}]   r/{sub_name}: {len(user_posts)} unique users")
        
        # Process users in parallel (with concurrency limit)
        all_discovered_subs = set()
        
        async def process_user_wrapper(username: str, user_post_list: list[dict]):
            async with self.user_semaphore:
                discovered = await self._process_user(
                    username=username,
                    subreddit_posts=user_post_list,
                    source_subreddit=sub_name,
                )
                return discovered or set()
        
        user_tasks = [
            process_user_wrapper(username, user_post_list)
            for username, user_post_list in user_posts.items()
        ]
        
        results = await asyncio.gather(*user_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, set):
                all_discovered_subs.update(result)
            elif isinstance(result, Exception):
                logger.debug(f"User processing error: {result}")
        
        # Check discovered subreddits in parallel
        if all_discovered_subs:
            await self._check_subreddits_parallel(
                list(all_discovered_subs),
                discovered_from=sub_name,
            )
        
        # Mark subreddit as crawled
        await self.supabase.complete_subreddit_crawl(queue_id)
        self.stats["subreddits_crawled"] += 1
        
        logger.info(f"[Worker {self.worker_id}]   ✓ Completed r/{sub_name}")

    async def _process_user(
        self, 
        username: str, 
        subreddit_posts: list[dict],
        source_subreddit: str,
    ) -> set[str]:
        """
        Process a single user: fetch profile, save lead, and return discovered subreddits.
        """
        discovered_subs = set()
        
        try:
            async with self.request_semaphore:
                async with RedditClient(proxy=self.proxy, worker_id=self.worker_id) as client:
                    # Fetch user profile
                    profile = await client.get_user_profile(username)
                    if not profile:
                        return discovered_subs
                    
                    # Fetch user's recent posts
                    user_posts, discovered = await client.get_user_posts(username, limit=25)
                    discovered_subs.update(discovered)
            
            # Combine subreddit posts with profile posts (deduplicate)
            combined_posts = list({
                p.get("reddit_post_id"): p 
                for p in (subreddit_posts + user_posts)
            }.values())
            
            # Calculate posting frequency
            posting_frequency = self._calculate_posting_frequency(combined_posts)
            
            # Merge extracted links
            all_links = set()
            for link in profile.get("extracted_links", []):
                all_links.add(link)
            for post in combined_posts:
                for link in post.get("extracted_links", []):
                    all_links.add(link)
            
            # Prepare and save lead
            lead_data = {
                **profile,
                "reddit_username": username,
                "total_posts": len(combined_posts),
                "posting_frequency": posting_frequency,
                "extracted_links": list(all_links),
            }
            
            saved_lead = await self.supabase.upsert_lead(lead_data)
            
            if saved_lead:
                self.stats["leads_saved"] += 1
                lead_id = saved_lead["id"]
                
                # Save posts (batch for efficiency)
                for post in combined_posts:
                    saved_post = await self.supabase.upsert_post(post, lead_id=lead_id)
                    if saved_post:
                        self.stats["posts_saved"] += 1
            
            self.stats["users_processed"] += 1
            
        except Exception as e:
            logger.debug(f"Error processing user u/{username}: {e}")
        
        return discovered_subs

    async def _check_subreddits_parallel(
        self, 
        sub_names: list[str],
        discovered_from: str = None,
    ):
        """Check multiple subreddits for NSFW status in parallel."""
        
        async def check_one(sub_name: str):
            try:
                async with self.request_semaphore:
                    async with RedditClient(proxy=self.proxy, worker_id=self.worker_id) as client:
                        info = await client.get_subreddit_info(sub_name)
                
                if not info:
                    return
                
                if not info.get("is_nsfw"):
                    return  # Skip non-NSFW
                
                subscribers = info.get("subscribers", 0)
                
                # Skip very small subreddits
                if subscribers < 500:
                    self.stats["subs_skipped_small"] += 1
                    return
                
                # Try to add to queue
                added = await self.supabase.enqueue_subreddit(
                    name=sub_name,
                    discovered_from=discovered_from,
                    subscribers=subscribers,
                    is_nsfw=True,
                )
                
                if added:
                    self.stats["new_subs_discovered"] += 1
                    logger.info(f"[Worker {self.worker_id}]     📡 Discovered: r/{sub_name} ({subscribers:,} subs)")
                    
            except Exception as e:
                logger.debug(f"Error checking r/{sub_name}: {e}")
        
        await asyncio.gather(*[check_one(sub) for sub in sub_names])

    def _group_posts_by_user(self, posts: list[dict]) -> dict[str, list[dict]]:
        """Group posts by author username."""
        user_posts = defaultdict(list)
        
        for post in posts:
            author = post.get("author")
            if author and author not in ("[deleted]", "[removed]", "AutoModerator"):
                user_posts[author].append(post)
        
        return dict(user_posts)

    def _calculate_posting_frequency(self, posts: list[dict]) -> Optional[float]:
        """Calculate posts per day based on post timestamps."""
        if len(posts) < 2:
            return None
        
        timestamps = []
        for post in posts:
            created_at = post.get("post_created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    else:
                        dt = created_at
                    timestamps.append(dt)
                except:
                    pass
        
        if len(timestamps) < 2:
            return None
        
        timestamps.sort()
        time_span = (timestamps[-1] - timestamps[0]).total_seconds()
        
        if time_span <= 0:
            return None
        
        days = time_span / 86400
        if days < 1:
            days = 1
        
        return round(len(posts) / days, 4)

    def _log_stats(self):
        """Log current crawler statistics."""
        logger.info(
            f"[Worker {self.worker_id}] 📊 Stats: "
            f"{self.stats['batches_completed']} batches, "
            f"{self.stats['subreddits_crawled']} subs, "
            f"{self.stats['users_processed']} users, "
            f"{self.stats['leads_saved']} leads, "
            f"{self.stats['new_subs_discovered']} new subs"
        )

    def get_stats(self) -> dict:
        """Get current crawler statistics."""
        return self.stats.copy()


# Legacy class for backwards compatibility
class SubredditCrawler(ParallelSubredditCrawler):
    """Legacy crawler class - now uses parallel processing."""
    
    def __init__(
        self, 
        reddit_client: RedditClient, 
        supabase_client: SupabaseClient,
        worker_id: int = None,
        min_subscribers: int = None,
    ):
        # Ignore the passed-in reddit_client, we create our own for parallel processing
        super().__init__(
            supabase_client=supabase_client,
            worker_id=worker_id or getattr(reddit_client, 'worker_id', 1),
            min_subscribers=min_subscribers,
        )


async def seed_queue_from_keywords(supabase: SupabaseClient, proxy: str = None):
    """
    Seed the crawler queue with subreddits discovered from search keywords.
    Used when the queue is empty to bootstrap the crawler.
    """
    from subreddit_discovery import SubredditDiscovery
    
    proxy = proxy or BRIGHTDATA_PROXY or PROXY_URL
    
    logger.info("Seeding crawler queue from search keywords...")
    
    async with RedditClient(proxy=proxy) as reddit:
        discovery = SubredditDiscovery(reddit, supabase)
        subreddits = await discovery.discover_subreddits(max_subreddits=50)
    
    added_count = 0
    for sub in subreddits:
        added = await supabase.enqueue_subreddit(
            name=sub["name"],
            discovered_from="seed_keywords",
            subscribers=sub.get("subscribers", 0),
            is_nsfw=sub.get("is_nsfw", True),
        )
        if added:
            added_count += 1
    
    logger.info(f"Seeded queue with {added_count} subreddits")
    return added_count
