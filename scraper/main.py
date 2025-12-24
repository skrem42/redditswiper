#!/usr/bin/env python3
"""
Reddit Lead Scraper - Main Entry Point

Usage:
    python main.py              # Full scrape: discover subs + scrape posts
    python main.py --discover   # Only discover new subreddits
    python main.py --scrape     # Only scrape posts from known subreddits
    python main.py --stats      # Show scraping statistics
    python main.py --jobs       # Process pending jobs from the queue (frontend-triggered)
    python main.py --watch      # Watch for new jobs and process continuously
    python main.py --crawl      # Run as continuous crawler (discovers subs via user cross-posts)
    
    # Custom keywords:
    python main.py --keywords "fitness,gym,workout"
    python main.py --keywords "cosplay,cosplayers" --filters "cosplay,nsfw"
"""
import asyncio
import argparse
from datetime import datetime

from config import MAX_POSTS_PER_SUBREDDIT, MAX_SUBREDDITS, SEARCH_KEYWORDS, SUBREDDIT_NAME_FILTERS
from reddit_client import RedditClient
from supabase_client import SupabaseClient
from subreddit_discovery import SubredditDiscovery
from user_aggregator import UserAggregator


async def discover_subreddits(
    reddit: RedditClient, 
    supabase: SupabaseClient,
    keywords: list[str] = None,
    filters: list[str] = None
) -> list[dict]:
    """Discover and save new subreddits."""
    discovery = SubredditDiscovery(reddit, supabase)
    subreddits = await discovery.discover_subreddits(
        MAX_SUBREDDITS, 
        search_keywords=keywords,
        name_filters=filters
    )
    return await discovery.save_subreddits(subreddits)


async def scrape_subreddits(
    reddit: RedditClient, 
    supabase: SupabaseClient,
    subreddits: list[dict]
) -> dict:
    """Scrape posts from subreddits and aggregate by user."""
    aggregator = UserAggregator(reddit, supabase)
    
    total_stats = {
        "subreddits_scraped": 0,
        "posts_processed": 0,
        "unique_users": 0,
        "users_saved": 0,
        "posts_saved": 0,
    }
    
    for i, sub in enumerate(subreddits, 1):
        sub_name = sub.get("name")
        sub_id = sub.get("id")
        
        print(f"\n[{i}/{len(subreddits)}] Scraping r/{sub_name}...")
        
        try:
            # Fetch posts from subreddit
            posts = await reddit.get_subreddit_posts(
                sub_name,
                sort="new",
                limit=MAX_POSTS_PER_SUBREDDIT,
            )
            
            if not posts:
                print(f"  No posts found in r/{sub_name}")
                continue
            
            print(f"  Fetched {len(posts)} posts")
            
            # Process and save users/posts
            stats = await aggregator.process_and_save_users(posts, subreddit_id=sub_id)
            
            # Update subreddit last_scraped
            if sub_id:
                await supabase.update_subreddit_last_scraped(sub_id)
            
            # Accumulate stats
            total_stats["subreddits_scraped"] += 1
            total_stats["posts_processed"] += stats["posts_processed"]
            total_stats["unique_users"] += stats["unique_users"]
            total_stats["users_saved"] += stats["users_saved"]
            total_stats["posts_saved"] += stats["posts_saved"]
            
            print(f"  Saved {stats['users_saved']} users, {stats['posts_saved']} posts")
            
        except Exception as e:
            print(f"  Error scraping r/{sub_name}: {e}")
            continue
    
    return total_stats


async def show_stats(supabase: SupabaseClient):
    """Display current scraping statistics."""
    stats = await supabase.get_stats()
    
    print("\n" + "=" * 50)
    print("REDDIT LEAD SCRAPER STATISTICS")
    print("=" * 50)
    print(f"Total Subreddits:  {stats.get('total_subreddits', 0)}")
    print(f"Total Leads:       {stats.get('total_leads', 0)}")
    print(f"Total Posts:       {stats.get('total_posts', 0)}")
    print("-" * 50)
    print(f"Pending Leads:     {stats.get('pending_leads', 0)}")
    print(f"Approved Leads:    {stats.get('approved_leads', 0)}")
    print(f"Rejected Leads:    {stats.get('rejected_leads', 0)}")
    print("=" * 50)


async def process_single_job(
    reddit: RedditClient, 
    supabase: SupabaseClient, 
    job: dict
) -> dict:
    """Process a single scrape job."""
    job_id = job["id"]
    keyword = job["keyword"]
    keyword_id = job.get("keyword_id")
    
    print(f"\n🚀 Processing job: '{keyword}' (priority: {job['priority']})")
    
    # Claim the job
    claimed = await supabase.claim_job(job_id)
    if not claimed:
        print(f"  ⚠️ Could not claim job (may already be processing)")
        return {"success": False, "reason": "claim_failed"}
    
    try:
        # Discover subreddits for this keyword
        print(f"  📡 Discovering subreddits for '{keyword}'...")
        discovery = SubredditDiscovery(reddit, supabase)
        subreddits = await discovery.discover_subreddits(
            MAX_SUBREDDITS,
            search_keywords=[keyword],
            name_filters=[]  # No filter - include all results for custom keywords
        )
        saved_subs = await discovery.save_subreddits(subreddits)
        print(f"  ✓ Found {len(saved_subs)} subreddits")
        
        if not saved_subs:
            await supabase.complete_job(job_id, 0, 0, 0)
            if keyword_id:
                await supabase.update_keyword_scraped(keyword_id)
            return {"success": True, "subreddits": 0, "leads": 0, "posts": 0}
        
        # Scrape posts from discovered subreddits
        print(f"  🔍 Scraping posts...")
        stats = await scrape_subreddits(reddit, supabase, saved_subs)
        
        # Complete the job
        await supabase.complete_job(
            job_id,
            subreddits_found=len(saved_subs),
            leads_found=stats["users_saved"],
            posts_found=stats["posts_saved"]
        )
        
        # Update keyword stats if linked
        if keyword_id:
            await supabase.update_keyword_scraped(keyword_id)
        
        print(f"  ✓ Complete: {len(saved_subs)} subs, {stats['users_saved']} leads, {stats['posts_saved']} posts")
        
        return {
            "success": True,
            "subreddits": len(saved_subs),
            "leads": stats["users_saved"],
            "posts": stats["posts_saved"]
        }
        
    except Exception as e:
        print(f"  ❌ Job failed: {e}")
        await supabase.fail_job(job_id, str(e))
        return {"success": False, "reason": str(e)}


async def process_job_queue(supabase: SupabaseClient, reddit: RedditClient, once: bool = True):
    """Process pending jobs from the queue."""
    print("\n" + "=" * 50)
    print("JOB QUEUE PROCESSOR")
    print("=" * 50)
    
    while True:
        # Get pending jobs
        jobs = await supabase.get_pending_jobs(limit=5)
        
        if not jobs:
            if once:
                print("No pending jobs in queue.")
                break
            else:
                print("No jobs. Waiting 10 seconds...")
                await asyncio.sleep(10)
                continue
        
        print(f"Found {len(jobs)} pending job(s)")
        
        for job in jobs:
            await process_single_job(reddit, supabase, job)
        
        if once:
            break
    
    print("\n✓ Job queue processing complete")


async def main():
    parser = argparse.ArgumentParser(
        description="Reddit Lead Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Full scrape with default keywords
  python main.py --discover                         # Only discover new subreddits
  python main.py --scrape                           # Only scrape posts from known subreddits
  python main.py --keywords "fitness,gym,models"    # Custom search keywords
  python main.py --keywords "cosplay" --filters ""  # No name filter (include all results)
  python main.py --show-config                      # Show current configuration
  python main.py --crawl                            # Run continuous crawler
  python main.py --crawl-stats                      # Show crawler queue stats
  python main.py --retry-failed                     # Retry failed subreddits (after fixing proxy)
        """
    )
    parser.add_argument(
        "--discover", 
        action="store_true",
        help="Only discover new subreddits"
    )
    parser.add_argument(
        "--scrape", 
        action="store_true",
        help="Only scrape posts from known subreddits"
    )
    parser.add_argument(
        "--stats", 
        action="store_true",
        help="Show scraping statistics"
    )
    parser.add_argument(
        "--keywords",
        type=str,
        help="Comma-separated search keywords (e.g., 'fitness,gym,models')"
    )
    parser.add_argument(
        "--filters",
        type=str,
        help="Comma-separated name filters for subreddits (e.g., 'onlyfans,of'). Use empty string '' to disable."
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="Show current configuration and exit"
    )
    parser.add_argument(
        "--jobs",
        action="store_true",
        help="Process pending jobs from the queue (added via frontend)"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for new jobs and process them continuously"
    )
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Run as continuous crawler (discovers new NSFW subs via user cross-posts)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of crawler workers to run in parallel (default: 1)"
    )
    parser.add_argument(
        "--worker-id",
        type=int,
        help="Specific worker ID (for running separate processes)"
    )
    parser.add_argument(
        "--min-subs",
        type=int,
        help="Minimum subscribers for subreddits to crawl (default: from config)"
    )
    parser.add_argument(
        "--crawl-stats",
        action="store_true",
        help="Show crawler queue statistics"
    )
    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Reset failed subreddits back to pending (for retrying after fixing proxy/issues)"
    )
    
    args = parser.parse_args()
    
    # Parse keywords and filters
    keywords = None
    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    
    filters = None
    if args.filters is not None:
        if args.filters == "":
            filters = []  # Empty list = no filtering
        else:
            filters = [f.strip() for f in args.filters.split(",") if f.strip()]
    
    # Show config mode
    if args.show_config:
        print("\n" + "=" * 50)
        print("CURRENT CONFIGURATION")
        print("=" * 50)
        print(f"Search Keywords:     {keywords or SEARCH_KEYWORDS}")
        print(f"Subreddit Filters:   {filters if filters is not None else SUBREDDIT_NAME_FILTERS}")
        print(f"Max Subreddits:      {MAX_SUBREDDITS}")
        print(f"Max Posts/Subreddit: {MAX_POSTS_PER_SUBREDDIT}")
        print("=" * 50)
        print("\nTo change defaults, edit config.py or set environment variables:")
        print('  SEARCH_KEYWORDS=\'["fitness", "gym"]\' python main.py')
        print('  SUBREDDIT_NAME_FILTERS=\'["nsfw", "models"]\' python main.py')
        return
    
    # Initialize clients
    supabase = SupabaseClient()
    
    # Stats only mode
    if args.stats:
        await show_stats(supabase)
        return
    
    # Crawler stats mode
    if args.crawl_stats:
        print("\n📊 Crawler Queue Statistics")
        print("=" * 50)
        stats = await supabase.get_queue_stats()
        print(f"Total:      {stats.get('total', 0)}")
        print(f"Pending:    {stats.get('pending', 0)}")
        print(f"Processing: {stats.get('processing', 0)}")
        print(f"Completed:  {stats.get('completed', 0)}")
        print(f"Failed:     {stats.get('failed', 0)}")
        print("=" * 50)
        return
    
    # Retry failed subreddits mode
    if args.retry_failed:
        print("\n🔄 Retrying Failed/Blocked Subreddits...")
        print("-" * 50)
        
        # Get count of explicitly failed subreddits
        failed_count = await supabase.get_queue_count(status="failed")
        print(f"Found {failed_count} explicitly failed subreddits")
        
        # For completed with no posts, we need to check manually
        # Get all completed subs and check if they have posts
        print("Checking completed subs... (finding ones with no posts)")
        completed_result = supabase.client.table("subreddit_queue").select(
            "id, subreddit_name"
        ).eq("status", "completed").execute()
        
        completed_subs = completed_result.data or []
        print(f"  Checking {len(completed_subs)} completed subreddits...")
        
        # Get all subreddit names that have posts
        posts_result = supabase.client.table("reddit_posts").select(
            "subreddit_name"
        ).not_.is_("subreddit_name", "null").execute()
        
        subs_with_posts = set(p["subreddit_name"] for p in (posts_result.data or []))
        
        # Find completed subs with no posts
        empty_completed_ids = [
            sub["id"] for sub in completed_subs 
            if sub["subreddit_name"] not in subs_with_posts
        ]
        
        empty_count = len(empty_completed_ids)
        print(f"Found {empty_count} completed subs with no posts (likely 403 blocked)")
        
        total = failed_count + empty_count
        if total == 0:
            print("✅ No failed subreddits to retry!")
            return
        
        print(f"\n📝 Total to retry: {total} subreddits")
        print("-" * 50)
        
        # Reset explicitly failed ones
        if failed_count > 0:
            result1 = supabase.client.table("subreddit_queue").update({
                "status": "pending",
                "error_message": None,
            }).eq("status", "failed").execute()
            reset1 = len(result1.data) if result1.data else 0
            print(f"✓ Reset {reset1} failed → pending")
        
        # Reset completed ones with no posts (batch update)
        if empty_count > 0:
            # Update in chunks of 100 to avoid query limits
            chunk_size = 100
            total_reset = 0
            for i in range(0, len(empty_completed_ids), chunk_size):
                chunk = empty_completed_ids[i:i+chunk_size]
                result2 = supabase.client.table("subreddit_queue").update({
                    "status": "pending",
                    "error_message": "Retrying - previously marked completed with no posts",
                }).in_("id", chunk).execute()
                total_reset += len(result2.data) if result2.data else 0
            print(f"✓ Reset {total_reset} empty completed → pending")
        
        print("\n✅ All subreddits reset! The crawler will retry them once the proxy is working.")
        return
    
    # Jobs mode - process queue from frontend
    if args.jobs or args.watch:
        async with RedditClient() as reddit:
            await process_job_queue(supabase, reddit, once=not args.watch)
            await show_stats(supabase)
        return
    
    # Crawler mode - continuous discovery via user cross-posts
    if args.crawl:
        from crawler import ParallelSubredditCrawler, seed_queue_from_keywords
        
        # Check if queue has any pending items (seed if empty)
        queue_count = await supabase.get_queue_count(status="pending")
        if queue_count == 0:
            print("Crawler queue is empty. Seeding with initial subreddits...")
            await seed_queue_from_keywords(supabase)
        
        # Use parallel crawler (processes multiple subreddits concurrently)
        worker_id = args.worker_id or 1
        crawler = ParallelSubredditCrawler(
            supabase_client=supabase,
            worker_id=worker_id,
            min_subscribers=args.min_subs,
        )
        await crawler.run()
        
        return
    
    # Crawler stats mode
    if args.crawl_stats:
        queue_stats = await supabase.get_queue_stats()
        print("\n" + "=" * 50)
        print("CRAWLER QUEUE STATISTICS")
        print("=" * 50)
        print(f"Total in Queue:    {queue_stats['total']}")
        print(f"Pending:           {queue_stats['pending']}")
        print(f"Processing:        {queue_stats['processing']}")
        print(f"Completed:         {queue_stats['completed']}")
        print(f"Failed:            {queue_stats['failed']}")
        print("=" * 50)
        return
    
    async with RedditClient() as reddit:
        start_time = datetime.now()
        print(f"\n{'=' * 50}")
        print(f"REDDIT LEAD SCRAPER - Started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 50}")
        
        subreddits = []
        
        # Discover subreddits
        if not args.scrape:  # Either --discover only or full run
            print("\n📡 PHASE 1: Discovering Subreddits")
            print("-" * 50)
            subreddits = await discover_subreddits(reddit, supabase, keywords, filters)
        
        # Scrape posts
        if not args.discover:  # Either --scrape only or full run
            print("\n🔍 PHASE 2: Scraping Posts")
            print("-" * 50)
            
            # If scrape-only mode, get subreddits from database
            if args.scrape or not subreddits:
                subreddits = await supabase.get_subreddits()
            
            if not subreddits:
                print("No subreddits to scrape. Run with --discover first.")
                return
            
            stats = await scrape_subreddits(reddit, supabase, subreddits)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n{'=' * 50}")
            print("SCRAPING COMPLETE")
            print(f"{'=' * 50}")
            print(f"Duration:           {duration:.1f} seconds")
            print(f"Subreddits Scraped: {stats['subreddits_scraped']}")
            print(f"Posts Processed:    {stats['posts_processed']}")
            print(f"Unique Users:       {stats['unique_users']}")
            print(f"Users Saved:        {stats['users_saved']}")
            print(f"Posts Saved:        {stats['posts_saved']}")
            print(f"{'=' * 50}")
        
        # Show final stats
        await show_stats(supabase)


if __name__ == "__main__":
    asyncio.run(main())


