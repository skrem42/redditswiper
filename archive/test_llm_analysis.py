"""
Test LLM-based subreddit analysis on existing scraped subreddits.
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

async def fetch_subreddit_rules(subreddit_name: str) -> list:
    """Fetch subreddit rules from Reddit API."""
    try:
        url = f"https://www.reddit.com/r/{subreddit_name}/about/rules.json"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("rules", [])
    except Exception as e:
        print(f"Could not fetch rules for r/{subreddit_name}: {e}")
    return []

async def fetch_subreddit_about(subreddit_name: str) -> dict:
    """Fetch subreddit about data from Reddit API."""
    try:
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {})
    except Exception as e:
        print(f"Could not fetch about data for r/{subreddit_name}: {e}")
    return {}

async def test_llm_analysis(limit: int = 10):
    """Test LLM analysis on subreddits from database."""
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    print("🔍 Fetching subreddits from database...")
    supabase = SupabaseClient()
    
    # Get scraped subreddits
    result = supabase.client.table("nsfw_subreddit_intel").select(
        "subreddit_name, subscribers"
    ).order(
        "subscribers", desc=True
    ).limit(limit).execute()
    
    subreddits = result.data or []
    
    if not subreddits:
        print("❌ No subreddits found in database!")
        return
    
    print(f"✓ Found {len(subreddits)} subreddits\n")
    print("=" * 80)
    
    # Initialize LLM analyzer
    analyzer = SubredditLLMAnalyzer()
    
    total_cost = 0.0
    
    for i, sub_data in enumerate(subreddits, 1):
        subreddit_name = sub_data["subreddit_name"]
        subscribers = sub_data.get("subscribers", 0)
        
        print(f"\n[{i}/{len(subreddits)}] Analyzing r/{subreddit_name} ({subscribers:,} subscribers)...")
        
        # Fetch rules and description
        print("   Fetching rules and description...")
        rules = await fetch_subreddit_rules(subreddit_name)
        about_data = await fetch_subreddit_about(subreddit_name)
        description = about_data.get("public_description", "")
        
        # Analyze with LLM
        print("   Analyzing with LLM...")
        analysis = await analyzer.analyze_subreddit(
            subreddit_name=subreddit_name,
            description=description,
            rules=rules,
            subscribers=subscribers
        )
        
        # Estimate cost (rough approximation)
        # Average ~500 tokens input, ~200 tokens output
        # GPT-4o-mini: $0.150/1M input, $0.600/1M output
        estimated_cost = (500 * 0.150 / 1_000_000) + (200 * 0.600 / 1_000_000)
        total_cost += estimated_cost
        
        # Display results
        print(f"\n   ✓ Analysis complete!")
        print(f"   Verification Required: {analysis['verification_required']}")
        print(f"   Sellers Allowed: {analysis['sellers_allowed']}")
        print(f"   Niche Categories: {', '.join(analysis['niche_categories'])}")
        print(f"   Confidence: {analysis['confidence']}")
        print(f"   Reasoning: {analysis['reasoning']}")
        print(f"   Estimated cost: ${estimated_cost:.6f}")
        
        print("-" * 80)
        
        # Small delay to avoid rate limits
        await asyncio.sleep(1)
    
    print("\n" + "=" * 80)
    print(f"✓ Analysis complete!")
    print(f"📊 Total estimated cost: ${total_cost:.4f}")
    print(f"📊 Average per subreddit: ${total_cost/len(subreddits):.6f}")
    print(f"\n💡 To analyze all 7,234 subreddits: ~${7234 * (total_cost/len(subreddits)):.2f}")

async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Test LLM subreddit analysis")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of subreddits to analyze (default: 10)"
    )
    args = parser.parse_args()
    
    await test_llm_analysis(limit=args.limit)

if __name__ == "__main__":
    asyncio.run(main())

