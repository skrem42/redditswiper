"""
Test the enhanced LLM analyzer on r/freeuse
This is a complicated subreddit with both self-posters and content reposters.
"""
import asyncio
import sys
import json
from supabase_client import SupabaseClient
from subreddit_intel_scraper import SubredditIntelScraper
from llm_analyzer import SubredditLLMAnalyzer

async def scrape_subreddit_data(subreddit_name: str):
    """Use the actual intel scraper to get data (bypasses Reddit API blocks)."""
    supabase = SupabaseClient()
    scraper = SubredditIntelScraper(
        supabase_client=supabase,
        worker_id=999,
        proxy_url=None,
        headless=True,
        ultra_fast=False,
        enable_llm=False  # We'll run LLM separately
    )
    
    try:
        await scraper.start()
        print(f"✓ Browser started")
        
        # Scrape the subreddit
        data = await scraper.scrape_subreddit(subreddit_name)
        
        if data:
            print(f"✓ Scraped successfully")
            return data
        else:
            print(f"✗ Scraping failed")
            return None
    finally:
        await scraper.close()
        print(f"✓ Browser closed")

async def test_freeuse():
    """Test analysis on r/freeuse"""
    print("=" * 80)
    print("Testing Enhanced LLM Analyzer on r/freeuse")
    print("=" * 80)
    
    subreddit = "freeuse"
    
    print(f"\n🔍 Scraping data for r/{subreddit} (using Playwright to bypass API blocks)...")
    
    # Use the actual scraper to get data
    data = await scrape_subreddit_data(subreddit)
    
    if not data:
        print("❌ Failed to scrape subreddit data")
        return
    
    description = data.get("description", "")
    subscribers = data.get("subscribers", 0)
    
    print(f"✓ Subscribers: {subscribers:,}")
    print(f"✓ Description: {description[:100] if description else 'No description'}...")
    
    # We don't have rules from the scraper, but LLM will fetch them
    rules_data = []
    
    # Initialize analyzer
    print(f"\n🤖 Running LLM analysis WITH post checking...")
    analyzer = SubredditLLMAnalyzer()
    
    # Analyze WITH post checking
    result_with_posts = await analyzer.analyze_subreddit(
        subreddit_name=subreddit,
        description=description,
        rules=rules_data,
        subscribers=subscribers,
        check_posts=True  # Enable post checking
    )
    
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS (WITH POST CHECKING)")
    print("=" * 80)
    print(json.dumps(result_with_posts, indent=2))
    
    # Now test WITHOUT post checking for comparison
    print(f"\n\n🤖 Running LLM analysis WITHOUT post checking (for comparison)...")
    result_without_posts = await analyzer.analyze_subreddit(
        subreddit_name=subreddit,
        description=description,
        rules=rules_data,
        subscribers=subscribers,
        check_posts=False  # Disable post checking
    )
    
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS (WITHOUT POST CHECKING)")
    print("=" * 80)
    print(json.dumps(result_without_posts, indent=2))
    
    # Compare results
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print(f"Verification Required:  WITH: {result_with_posts['verification_required']}  |  WITHOUT: {result_without_posts['verification_required']}")
    print(f"Sellers Allowed:        WITH: {result_with_posts['sellers_allowed']}  |  WITHOUT: {result_without_posts['sellers_allowed']}")
    print(f"Confidence:             WITH: {result_with_posts['confidence']}  |  WITHOUT: {result_without_posts['confidence']}")
    
    if result_with_posts['sellers_allowed'] != result_without_posts['sellers_allowed']:
        print("\n✅ POST CHECKING CHANGED THE RESULT!")
        print(f"   Without posts: {result_without_posts['sellers_allowed']}")
        print(f"   With posts:    {result_with_posts['sellers_allowed']}")
    else:
        print("\n⚠️  Post checking did not change sellers_allowed result")

if __name__ == "__main__":
    asyncio.run(test_freeuse())

