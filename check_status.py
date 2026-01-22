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
    print("=" * 80)
    
    # Queue stats
    total = sb.client.table('subreddit_queue').select('id', count='exact').execute()
    pending = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'pending').execute()
    processing = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'processing').execute()
    completed = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'completed').execute()
    failed = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'failed').execute()
    
    print(f"\n📊 QUEUE (Crawler)")
    print(f"  Total:      {total.count:,}")
    print(f"  Pending:    {pending.count:,} ({pending.count*100//total.count if total.count else 0}%)")
    print(f"  Processing: {processing.count:,}")
    print(f"  Completed:  {completed.count:,} ({completed.count*100//total.count if total.count else 0}%)")
    print(f"  Failed:     {failed.count:,} ({failed.count*100//total.count if total.count else 0}%)")
    
    # Intel stats - DETAILED BREAKDOWN
    intel_total = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').execute()
    
    # Individual components
    with_subs = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').not_.is_('subscribers', 'null').execute()
    with_competition = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').not_.is_('weekly_visitors', 'null').not_.is_('weekly_contributions', 'null').execute()
    with_llm = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').not_.is_('verification_required', 'null').not_.is_('sellers_allowed', 'null').execute()
    
    # FULLY READY = has all required fields for frontend
    fully_ready = sb.client.table('nsfw_subreddit_intel').select('id', count='exact')\
        .not_.is_('subscribers', 'null')\
        .not_.is_('weekly_visitors', 'null')\
        .not_.is_('weekly_contributions', 'null')\
        .not_.is_('verification_required', 'null')\
        .not_.is_('sellers_allowed', 'null').execute()
    
    print(f"\n📊 INTEL (nsfw_subreddit_intel)")
    print(f"  Total subreddits:              {intel_total.count:,}")
    print(f"\n  Component Status:")
    print(f"    ✓ Subscribers (Intel JSON):  {with_subs.count:,} ({with_subs.count*100//intel_total.count if intel_total.count else 0}%)")
    print(f"    ✓ Competition (Intel Comp):  {with_competition.count:,} ({with_competition.count*100//intel_total.count if intel_total.count else 0}%)")
    print(f"    ✓ LLM Analysis (LLM):        {with_llm.count:,} ({with_llm.count*100//intel_total.count if intel_total.count else 0}%)")
    print(f"\n  ✨ FULLY READY (all fields):   {fully_ready.count:,} ({fully_ready.count*100//intel_total.count if intel_total.count else 0}%) ✨")
    
    # Missing data
    need_subs = intel_total.count - with_subs.count
    need_competition = intel_total.count - with_competition.count
    need_llm = intel_total.count - with_llm.count
    
    print(f"\n  ⏳ Still Needed:")
    print(f"    Need subscribers:            {need_subs:,}")
    print(f"    Need competition metrics:    {need_competition:,}")
    print(f"    Need LLM analysis:           {need_llm:,}")
    
    # Leads
    leads = sb.client.table('reddit_leads').select('id', count='exact').execute()
    pending_leads = sb.client.table('reddit_leads').select('id', count='exact').eq('status', 'pending').execute()
    approved_leads = sb.client.table('reddit_leads').select('id', count='exact').eq('status', 'approved').execute()
    
    print(f"\n📊 LEADS")
    print(f"  Total:     {leads.count:,}")
    print(f"  Pending:   {pending_leads.count:,}")
    print(f"  Approved:  {approved_leads.count:,}")
    
    # Health check
    print(f"\n🏥 SYSTEM HEALTH")
    backlog = pending.count
    failure_rate = (failed.count * 100 // total.count) if total.count else 0
    intel_completion = (fully_ready.count * 100 // intel_total.count) if intel_total.count else 0
    
    if backlog > 5000 and failure_rate > 5:
        print(f"  ❌ CRITICAL: {backlog:,} pending + {failure_rate}% failures")
    elif backlog > 5000:
        print(f"  ⚠️  WARNING: {backlog:,} pending subreddits")
    elif failure_rate > 5:
        print(f"  ⚠️  WARNING: {failure_rate}% failure rate")
    else:
        print(f"  ✅ HEALTHY: {intel_completion}% of intel fully populated")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()

