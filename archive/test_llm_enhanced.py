"""
Test the enhanced LLM analyzer on multiple subreddits
Shows how post checking improves accuracy when rules are unclear.
"""
import asyncio
import json
from llm_analyzer import SubredditLLMAnalyzer

async def test_subreddit(analyzer, subreddit_name: str, check_posts: bool = True):
    """Test a single subreddit."""
    print(f"\n{'='*80}")
    print(f"Testing: r/{subreddit_name}")
    print(f"Post checking: {'ENABLED' if check_posts else 'DISABLED'}")
    print('='*80)
    
    result = await analyzer.analyze_subreddit(
        subreddit_name=subreddit_name,
        description=f"Analyzing r/{subreddit_name}",
        rules=[],  # No rules to force post checking
        subscribers=100000,
        check_posts=check_posts
    )
    
    print(json.dumps(result, indent=2))
    return result

async def main():
    """Test on multiple subreddits."""
    print("\n" + "="*80)
    print("ENHANCED LLM ANALYZER TEST")
    print("Testing subreddits with unclear rules to show post-checking improvement")
    print("="*80)
    
    analyzer = SubredditLLMAnalyzer()
    
    # Test subreddits that might have unclear rules but clear posting patterns
    test_subs = [
        "freeuse",        # Mixed: both self-posters and reposters
        "RealGirls",      # Verification required, no sellers
        "OnlyFans101",    # Obviously allows sellers
        "BigBootyGoTHICCgf",  # Amateur sub, unclear rules
    ]
    
    for sub in test_subs:
        # Test WITH post checking
        with_posts = await test_subreddit(analyzer, sub, check_posts=True)
        
        await asyncio.sleep(2)  # Rate limit prevention
        
        # Test WITHOUT post checking (for comparison)
        without_posts = await test_subreddit(analyzer, sub, check_posts=False)
        
        # Compare
        print(f"\n📊 COMPARISON for r/{sub}:")
        print(f"   Sellers:    WITH posts = {with_posts['sellers_allowed']:12} | WITHOUT posts = {without_posts['sellers_allowed']}")
        print(f"   Confidence: WITH posts = {with_posts['confidence']:12} | WITHOUT posts = {without_posts['confidence']}")
        
        if with_posts['sellers_allowed'] != without_posts['sellers_allowed']:
            print(f"   ✅ POST CHECKING CHANGED THE RESULT!")
        
        await asyncio.sleep(2)  # Rate limit prevention
    
    print("\n" + "="*80)
    print("✓ Test complete!")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())

