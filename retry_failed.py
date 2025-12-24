#!/usr/bin/env python3
"""
Retry failed subreddits by marking them as pending again.
"""
import sys
import os

# Add intel-scraper to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'intel-scraper'))

from supabase_client import SupabaseClient

def main():
    sb = SupabaseClient()
    
    print("🔄 RETRY FAILED SUBREDDITS")
    print("=" * 60)
    
    # Check how many failed
    failed = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'failed').execute()
    print(f"\nFound {failed.count:,} failed subreddits")
    
    if failed.count == 0:
        print("✅ No failed subreddits to retry!")
        return
    
    # Show sample of errors
    sample = sb.client.table('subreddit_queue').select('subreddit_name, error_message').eq('status', 'failed').limit(5).execute()
    print("\nSample errors:")
    for s in sample.data:
        error = (s['error_message'] or 'No message')[:60]
        print(f"  - r/{s['subreddit_name']}: {error}")
    
    # Ask for confirmation
    response = input(f"\n⚠️  Mark all {failed.count:,} failed subreddits as pending for retry? (yes/no): ")
    
    if response.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    # Retry all failed
    result = sb.client.table('subreddit_queue').update({
        'status': 'pending',
        'error_message': None
    }).eq('status', 'failed').execute()
    
    print(f"\n✅ Marked {len(result.data)} subreddits for retry!")
    print("\nNext: Run the intel worker to process them:")
    print("  cd intel-scraper && python intel_worker.py")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()

