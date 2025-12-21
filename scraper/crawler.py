"""
NSFW Subreddit Crawler

Continuously discovers and crawls NSFW subreddits by following user cross-posts.
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
from config import MAX_POSTS_PER_SUBREDDIT, CRAWLER_MIN_SUBSCRIBERS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SubredditCrawler:
    """
    Continuously discovers and crawls NSFW subreddits.
    
    Discovery works by:
    1. Scraping posts from a subreddit
    2. For each unique user, fetching their profile and recent posts
    3. Checking which OTHER subreddits they post in
    4. Adding any new NSFW subreddits to the queue
    5. Repeat with the next subreddit in the queue
    
    Supports multiple workers running in parallel - each claims subreddits atomically.
    """

    def __init__(
        self, 
        reddit_client: RedditClient, 
        supabase_client: SupabaseClient,
        worker_id: int = None,
        min_subscribers: int = None,
    ):
        self.reddit = reddit_client
        self.supabase = supabase_client
        self.worker_id = worker_id or getattr(reddit_client, 'worker_id', 1)
        self.min_subscribers = min_subscribers if min_subscribers is not None else CRAWLER_MIN_SUBSCRIBERS
        self.stats = {
            "subreddits_crawled": 0,
            "users_processed": 0,
            "leads_saved": 0,
            "posts_saved": 0,
            "new_subs_discovered": 0,
            "subs_skipped_small": 0,
        }

    async def run(self, idle_wait: int = 60):
        """
        Main crawler loop - runs indefinitely.
        
        Args:
            idle_wait: Seconds to wait when queue is empty
        """
        logger.info(f"[Worker {self.worker_id}] Starting NSFW Subreddit Crawler...")
        logger.info(f"[Worker {self.worker_id}] Min subscribers filter: {self.min_subscribers}")
        logger.info(f"[Worker {self.worker_id}] Press Ctrl+C to stop")
        
        # Reset any stale processing entries from crashed runs (only first worker should do this)
        reset_count = await self.supabase.reset_stale_processing(minutes=30)
        if reset_count > 0:
            logger.info(f"[Worker {self.worker_id}] Reset {reset_count} stale processing entries")
        
        while True:
            try:
                # Get next subreddit from queue (prioritized by subscriber count)
                sub_entry = await self.supabase.claim_next_subreddit(
                    min_subscribers=self.min_subscribers
                )
                
                if not sub_entry:
                    queue_stats = await self.supabase.get_queue_stats()
                    logger.info(
                        f"[Worker {self.worker_id}] Queue empty. Stats: {queue_stats['completed']} completed, "
                        f"{queue_stats['failed']} failed. Waiting {idle_wait}s..."
                    )
                    await asyncio.sleep(idle_wait)
                    continue
                
                # Crawl the subreddit
                await self.crawl_subreddit(sub_entry)
                
                # Log progress periodically
                if self.stats["subreddits_crawled"] % 5 == 0:
                    self._log_stats()
                    
            except KeyboardInterrupt:
                logger.info(f"[Worker {self.worker_id}] Crawler stopped by user")
                break
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] Error in crawler loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying

    async def crawl_subreddit(self, sub_entry: dict):
        """
        Crawl a single subreddit and discover new ones from user cross-posts.
        """
        sub_name = sub_entry["subreddit_name"]
        queue_id = sub_entry["id"]
        
        logger.info(f"Crawling r/{sub_name}...")
        
        try:
            # Fetch posts from the subreddit
            posts = await self.reddit.get_subreddit_posts(
                sub_name,
                sort="new",
                limit=MAX_POSTS_PER_SUBREDDIT,
            )
            
            if not posts:
                logger.warning(f"No posts found in r/{sub_name} (403 blocked or empty)")
                # Mark as failed so it can be retried later when proxy is fixed
                await self.supabase.fail_subreddit_crawl(
                    queue_id, 
                    "No posts returned - likely 403 blocked or empty subreddit"
                )
                return
            
            logger.info(f"  Found {len(posts)} posts")
            
            # Group posts by user
            user_posts = self._group_posts_by_user(posts)
            logger.info(f"  Found {len(user_posts)} unique users")
            
            # Process each user
            # Note: We pass None for subreddit_id because queue_id is from subreddit_queue,
            # not the subreddits table. Posts will still have subreddit_name set.
            for username, user_post_list in user_posts.items():
                await self._process_user(
                    username=username,
                    subreddit_posts=user_post_list,
                    source_subreddit=sub_name,
                    subreddit_id=None,  # Don't link to subreddits table from crawler
                )
            
            # Mark subreddit as crawled
            await self.supabase.complete_subreddit_crawl(queue_id)
            self.stats["subreddits_crawled"] += 1
            
            logger.info(f"  ✓ Completed r/{sub_name}")
            
        except Exception as e:
            logger.error(f"Error crawling r/{sub_name}: {e}")
            await self.supabase.fail_subreddit_crawl(queue_id, str(e))

    async def _process_user(
        self, 
        username: str, 
        subreddit_posts: list[dict],
        source_subreddit: str,
        subreddit_id: str = None,
    ):
        """
        Process a single user: fetch profile, save lead, and discover new subreddits.
        """
        try:
            # Fetch user profile
            profile = await self.reddit.get_user_profile(username)
            if not profile:
                return
            
            # Fetch user's recent posts (returns posts + discovered subs)
            user_posts, discovered_subs = await self.reddit.get_user_posts(username, limit=25)
            
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
                
                # Save posts
                for post in combined_posts:
                    saved_post = await self.supabase.upsert_post(
                        post, 
                        lead_id=lead_id, 
                        subreddit_id=subreddit_id
                    )
                    if saved_post:
                        self.stats["posts_saved"] += 1
            
            # Discover new subreddits from this user's posts
            for new_sub in discovered_subs:
                await self._maybe_enqueue_subreddit(
                    new_sub,
                    discovered_from=source_subreddit,
                    discovered_via_user=username,
                )
            
            self.stats["users_processed"] += 1
            
        except Exception as e:
            logger.error(f"Error processing user u/{username}: {e}")

    async def _maybe_enqueue_subreddit(
        self, 
        sub_name: str,
        discovered_from: str = None,
        discovered_via_user: str = None,
    ):
        """
        Check if a subreddit is NSFW and add to queue if new.
        Skips subreddits that are too small (likely rabbit holes).
        """
        try:
            # Get subreddit info to check if NSFW
            info = await self.reddit.get_subreddit_info(sub_name)
            
            if not info:
                return  # Subreddit not accessible
            
            if not info.get("is_nsfw"):
                return  # Skip non-NSFW subreddits
            
            subscribers = info.get("subscribers", 0)
            
            # Skip very small subreddits to avoid rabbit holes
            # (they can still be added via frontend keywords if needed)
            if subscribers < 500:
                self.stats["subs_skipped_small"] += 1
                return
            
            # Try to add to queue
            added = await self.supabase.enqueue_subreddit(
                name=sub_name,
                discovered_from=discovered_from,
                discovered_via_user=discovered_via_user,
                subscribers=subscribers,
                is_nsfw=True,
            )
            
            if added:
                self.stats["new_subs_discovered"] += 1
                logger.info(
                    f"    📡 Discovered: r/{sub_name} ({subscribers:,} subs) "
                    f"via u/{discovered_via_user}"
                )
                
        except Exception as e:
            logger.error(f"Error checking subreddit r/{sub_name}: {e}")

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
        
        days = time_span / 86400  # seconds per day
        if days < 1:
            days = 1
        
        return round(len(posts) / days, 4)

    def _log_stats(self):
        """Log current crawler statistics."""
        logger.info(
            f"📊 Stats: {self.stats['subreddits_crawled']} subs crawled, "
            f"{self.stats['users_processed']} users, "
            f"{self.stats['leads_saved']} leads, "
            f"{self.stats['posts_saved']} posts, "
            f"{self.stats['new_subs_discovered']} new subs discovered"
        )

    def get_stats(self) -> dict:
        """Get current crawler statistics."""
        return self.stats.copy()


async def seed_queue_from_keywords(reddit: RedditClient, supabase: SupabaseClient):
    """
    Seed the crawler queue with subreddits discovered from search keywords.
    Used when the queue is empty to bootstrap the crawler.
    """
    from subreddit_discovery import SubredditDiscovery
    
    logger.info("Seeding crawler queue from search keywords...")
    
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

