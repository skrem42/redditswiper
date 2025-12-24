#!/usr/bin/env python3
"""
Quick status check for the Reddit scraper system.
Run this anytime to see what's happening.
"""
import sys
import os

# Add intel-scraper to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'intel-scraper'))

from supabase_client import SupabaseClient

def main():
    sb = SupabaseClient()
    
    print("🔍 REDDIT SCRAPER STATUS CHECK")
    print("=" * 60)
    
    # Queue stats
    total = sb.client.table('subreddit_queue').select('id', count='exact').execute()
    pending = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'pending').execute()
    processing = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'processing').execute()
    completed = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'completed').execute()
    failed = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'failed').execute()
    
    print(f"\n📊 QUEUE")
    print(f"  Total:      {total.count:,}")
    print(f"  Pending:    {pending.count:,} ({pending.count*100//total.count if total.count else 0}%)")
    print(f"  Processing: {processing.count:,}")
    print(f"  Completed:  {completed.count:,} ({completed.count*100//total.count if total.count else 0}%)")
    print(f"  Failed:     {failed.count:,} ({failed.count*100//total.count if total.count else 0}%)")
    
    # Intel stats
    intel_total = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').execute()
    intel_with_llm = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').not_.is_('verification_required', 'null').execute()
    
    print(f"\n📊 INTEL")
    print(f"  Scraped:   {intel_total.count:,}")
    print(f"  With LLM:  {intel_with_llm.count:,} ({intel_with_llm.count*100//intel_total.count if intel_total.count else 0}%)")
    print(f"  Need LLM:  {intel_total.count - intel_with_llm.count:,}")
    
    # Leads
    leads = sb.client.table('reddit_leads').select('id', count='exact').execute()
    print(f"\n📊 LEADS")
    print(f"  Total:     {leads.count:,}")
    
    # Health check
    print(f"\n🏥 HEALTH")
    backlog = pending.count
    failure_rate = (failed.count * 100 // total.count) if total.count else 0
    
    if backlog > 5000 and failure_rate > 5:
        print(f"  ❌ CRITICAL: {backlog:,} pending + {failure_rate}% failures")
    elif backlog > 5000:
        print(f"  ⚠️  WARNING: {backlog:,} pending subreddits")
    elif failure_rate > 5:
        print(f"  ⚠️  WARNING: {failure_rate}% failure rate")
    else:
        print(f"  ✅ HEALTHY")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

