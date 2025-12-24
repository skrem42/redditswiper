"""
Run LLM analysis on subreddits and save to database.
"""
import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

# Load from scraper/.env
load_dotenv("/Users/calummelling/Desktop/redditscraper/scraper/.env")

from supabase_client import SupabaseClient
from llm_analyzer import SubredditLLMAnalyzer
from config import LLM_REDDIT_PROXY, OPENAI_API_KEY

async def fetch_subreddit_rules(subreddit_name: str, proxy_url: str = None) -> list:
    """Fetch subreddit rules from Reddit API."""
    try:
        url = f"https://www.reddit.com/r/{subreddit_name}/about/rules.json"
        client_kwargs = {"timeout": 30.0}
        if proxy_url:
            client_kwargs["proxy"] = proxy_url  # Fixed: use "proxy" not "proxies"
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("rules", [])
    except Exception as e:
        print(f"Could not fetch rules for r/{subreddit_name}: {e}")
    return []

async def fetch_subreddit_about(subreddit_name: str, proxy_url: str = None) -> dict:
    """Fetch subreddit about data from Reddit API."""
    try:
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        client_kwargs = {"timeout": 30.0}
        if proxy_url:
            client_kwargs["proxy"] = proxy_url  # Fixed: use "proxy" not "proxies"
        
        async with httpx.AsyncClient(**client_kwargs) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
    except Exception as e:
        print(f"Could not fetch about data for r/{subreddit_name}: {e}")
    return {}

async def process_subreddit(
    subreddit_data: dict,
    analyzer: SubredditLLMAnalyzer,
    supabase: SupabaseClient,
    index: int,
    total: int,
    reddit_proxy: str = None
) -> tuple[bool, float]:
    """Process a single subreddit with LLM analysis."""
    subreddit_name = subreddit_data["subreddit_name"]
    subreddit_id = subreddit_data["id"]
    subscribers = subreddit_data.get("subscribers") or 0
    
    print(f"[{index}/{total}] Analyzing r/{subreddit_name} ({subscribers:,} subscribers)...")
    
    try:
        # Fetch rules and description in parallel
        rules_task = fetch_subreddit_rules(subreddit_name, reddit_proxy)
        about_task = fetch_subreddit_about(subreddit_name, reddit_proxy)
        
        rules, about_data = await asyncio.gather(rules_task, about_task)
        description = about_data.get("public_description", "")
        
        # Analyze with LLM
        analysis = await analyzer.analyze_subreddit(
            subreddit_name=subreddit_name,
            description=description,
            rules=rules,
            subscribers=subscribers
        )
        
        # Estimate cost
        estimated_cost = (500 * 0.150 / 1_000_000) + (200 * 0.600 / 1_000_000)
        
        # Save to database
        update_data = {
            "verification_required": analysis["verification_required"],
            "sellers_allowed": analysis["sellers_allowed"],
            "niche_categories": analysis["niche_categories"],
            "llm_analysis_confidence": analysis["confidence"],
            "llm_analysis_reasoning": analysis["reasoning"]
        }
        
        supabase.client.table("nsfw_subreddit_intel").update(
            update_data
        ).eq("id", subreddit_id).execute()
        
        # Display results
        print(f"   ✅ r/{subreddit_name}: {analysis['sellers_allowed']} sellers, {analysis['verification_required']} verification, [{', '.join(analysis['niche_categories'][:3])}]")
        
        return True, estimated_cost
        
    except Exception as e:
        print(f"   ❌ r/{subreddit_name}: {e}")
        return False, 0.0

async def run_llm_analysis(limit: int = 10, skip_existing: bool = True, batch_size: int = 10):
    """Run LLM analysis on subreddits and save to database."""
    
    # Check for OpenAI API key
    api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set!")
        print("   Set it in config.py or environment variable")
        return
    
    print("🔍 Fetching subreddits from database...")
    supabase = SupabaseClient()
    
    # Build query
    query = supabase.client.table("nsfw_subreddit_intel").select(
        "id, subreddit_name, subscribers, verification_required"
    ).order("subscribers", desc=True)
    
    # Skip ones that already have LLM analysis
    if skip_existing:
        query = query.is_("verification_required", "null")
    
    result = query.limit(limit).execute()
    subreddits = result.data or []
    
    if not subreddits:
        print("❌ No subreddits found (all already analyzed or none in DB)!")
        return
    
    print(f"✓ Found {len(subreddits)} subreddits to analyze")
    print(f"⚡ Processing in batches of {batch_size}")
    print(f"🌐 Reddit API proxy: ProxyEmpire ({LLM_REDDIT_PROXY.split('@')[1]})")
    print(f"🌐 OpenAI API: Direct connection (no proxy)")
    print("=" * 80)
    
    # Initialize LLM analyzer - uses hardcoded proxies from config
    analyzer = SubredditLLMAnalyzer()
    
    total_cost = 0.0
    successful = 0
    failed = 0
    
    # Process in batches
    for batch_start in range(0, len(subreddits), batch_size):
        batch_end = min(batch_start + batch_size, len(subreddits))
        batch = subreddits[batch_start:batch_end]
        
        print(f"\n🔄 Batch {batch_start//batch_size + 1}/{(len(subreddits) + batch_size - 1)//batch_size}")
        print("-" * 80)
        
        # Process batch in parallel
        tasks = [
            process_subreddit(sub_data, analyzer, supabase, batch_start + i + 1, len(subreddits), LLM_REDDIT_PROXY)
            for i, sub_data in enumerate(batch)
        ]
        
        results = await asyncio.gather(*tasks)
        
        for success, cost in results:
            if success:
                successful += 1
                total_cost += cost
            else:
                failed += 1
        
        # Small delay between batches to avoid rate limits
        if batch_end < len(subreddits):
            await asyncio.sleep(2)
    
    print("\n" + "=" * 80)
    print(f"✅ Analysis complete!")
    print(f"📊 Successful: {successful}")
    print(f"📊 Failed: {failed}")
    print(f"📊 Total cost: ${total_cost:.4f}")
    print(f"📊 Average per subreddit: ${total_cost/successful if successful > 0 else 0:.6f}")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run LLM analysis on subreddits")
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Number of subreddits to analyze (default: 50)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of concurrent requests per batch (default: 10)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all subreddits, even ones already analyzed"
    )
    args = parser.parse_args()
    
    await run_llm_analysis(limit=args.limit, skip_existing=not args.all, batch_size=args.batch_size)

if __name__ == "__main__":
    asyncio.run(main())
