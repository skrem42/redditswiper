#!/usr/bin/env python3
"""
System Health Monitor
====================

Provides consolidated view of all workers and database state.

Shows:
- Queue status (pending, processing, completed, failed)
- Intel scraper status
- LLM analyzer status
- Recent errors
- Processing rates

Usage:
    python monitor.py          # One-time snapshot
    python monitor.py --watch  # Continuous monitoring (refresh every 30s)
"""

import sys
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

# Add paths for imports
sys.path.insert(0, "scraper")
sys.path.insert(0, "intel-scraper")

from scraper.supabase_client import SupabaseClient

logging.basicConfig(level=logging.ERROR)  # Suppress debug logs
logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system health and provides status reports."""
    
    def __init__(self):
        self.supabase = SupabaseClient()
    
    def fetch_queue_stats(self) -> dict:
        """Fetch crawler queue statistics."""
        try:
            # Get counts by status
            response = self.supabase.client.table("subreddit_queue") \
                .select("status", count="exact") \
                .execute()
            
            total = response.count if hasattr(response, 'count') else 0
            
            # Count by status
            pending = len([r for r in response.data if r.get("status") == "pending"])
            processing = len([r for r in response.data if r.get("status") == "processing"])
            completed = len([r for r in response.data if r.get("status") == "complete"])
            failed = len([r for r in response.data if r.get("status") == "failed"])
            
            return {
                "total": total,
                "pending": pending,
                "processing": processing,
                "completed": completed,
                "failed": failed
            }
        except Exception as e:
            logger.error(f"Failed to fetch queue stats: {e}")
            return {}
    
    def fetch_intel_stats(self) -> dict:
        """Fetch intel scraper statistics."""
        try:
            response = self.supabase.client.table("nsfw_subreddit_intel") \
                .select("scrape_status, sellers_allowed", count="exact") \
                .execute()
            
            total = response.count if hasattr(response, 'count') else len(response.data)
            
            # Count by scrape_status
            complete = len([r for r in response.data if r.get("scrape_status") == "completed"])
            processing = len([r for r in response.data if r.get("scrape_status") == "processing"])
            failed = len([r for r in response.data if r.get("scrape_status") == "failed"])
            pending = len([r for r in response.data if r.get("scrape_status") == "pending"])
            
            # Count LLM analyzed (sellers_allowed is populated by LLM)
            with_llm = len([r for r in response.data if r.get("sellers_allowed") is not None])
            
            return {
                "total": total,
                "complete": complete,
                "processing": processing,
                "failed": failed,
                "pending": pending,
                "with_llm": with_llm
            }
        except Exception as e:
            logger.error(f"Failed to fetch intel stats: {e}")
            return {}
    
    def fetch_leads_stats(self) -> dict:
        """Fetch leads statistics."""
        try:
            response = self.supabase.client.table("reddit_leads") \
                .select("*", count="exact") \
                .execute()
            
            total = response.count if hasattr(response, 'count') else 0
            
            # Count by status
            hot = len([r for r in response.data if r.get("temperature") == "hot"])
            warm = len([r for r in response.data if r.get("temperature") == "warm"])
            cold = len([r for r in response.data if r.get("temperature") == "cold"])
            
            return {
                "total": total,
                "hot": hot,
                "warm": warm,
                "cold": cold
            }
        except Exception as e:
            logger.error(f"Failed to fetch leads stats: {e}")
            return {}
    
    def fetch_recent_activity(self) -> dict:
        """Fetch recent activity (last hour)."""
        try:
            one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
            
            # Recent completions
            queue_recent = self.supabase.client.table("subreddit_queue") \
                .select("*") \
                .eq("status", "complete") \
                .gte("updated_at", one_hour_ago) \
                .execute()
            
            intel_recent = self.supabase.client.table("nsfw_subreddit_intel") \
                .select("*") \
                .eq("scrape_status", "completed") \
                .gte("updated_at", one_hour_ago) \
                .execute()
            
            # Recent failures
            queue_failures = self.supabase.client.table("subreddit_queue") \
                .select("*") \
                .eq("status", "failed") \
                .gte("updated_at", one_hour_ago) \
                .execute()
            
            intel_failures = self.supabase.client.table("nsfw_subreddit_intel") \
                .select("*") \
                .eq("scrape_status", "failed") \
                .gte("updated_at", one_hour_ago) \
                .execute()
            
            return {
                "crawler_completed_1h": len(queue_recent.data) if queue_recent.data else 0,
                "intel_completed_1h": len(intel_recent.data) if intel_recent.data else 0,
                "crawler_failed_1h": len(queue_failures.data) if queue_failures.data else 0,
                "intel_failed_1h": len(intel_failures.data) if intel_failures.data else 0
            }
        except Exception as e:
            logger.error(f"Failed to fetch recent activity: {e}")
            return {}
    
    def print_status(self):
        """Print comprehensive system status."""
        print("\n" + "="*80)
        print(f"REDDIT SCRAPER - SYSTEM STATUS")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Crawler Queue
        queue = self.fetch_queue_stats()
        if queue:
            print(f"\n📋 CRAWLER QUEUE:")
            print(f"  Total:       {queue.get('total', 0):,}")
            print(f"  ⏳ Pending:   {queue.get('pending', 0):,}")
            print(f"  🔄 Processing: {queue.get('processing', 0):,}")
            print(f"  ✅ Completed: {queue.get('completed', 0):,}")
            print(f"  ❌ Failed:    {queue.get('failed', 0):,}")
            
            if queue.get('total', 0) > 0:
                completion = (queue.get('completed', 0) / queue.get('total', 0)) * 100
                print(f"  Progress:    {completion:.1f}%")
        
        # Intel Scraper
        intel = self.fetch_intel_stats()
        if intel:
            print(f"\n🔍 INTEL SCRAPER:")
            print(f"  Total:       {intel.get('total', 0):,}")
            print(f"  ⏳ Pending:   {intel.get('pending', 0):,}")
            print(f"  🔄 Processing: {intel.get('processing', 0):,}")
            print(f"  ✅ Completed: {intel.get('complete', 0):,}")
            print(f"  ❌ Failed:    {intel.get('failed', 0):,}")
            print(f"  🤖 With LLM:  {intel.get('with_llm', 0):,}")
            
            if intel.get('total', 0) > 0:
                completion = (intel.get('complete', 0) / intel.get('total', 0)) * 100
                llm_coverage = (intel.get('with_llm', 0) / intel.get('complete', 1)) * 100
                print(f"  Progress:    {completion:.1f}%")
                print(f"  LLM Coverage: {llm_coverage:.1f}%")
        
        # Leads
        leads = self.fetch_leads_stats()
        if leads:
            print(f"\n🎯 LEADS:")
            print(f"  Total:       {leads.get('total', 0):,}")
            print(f"  🔥 Hot:       {leads.get('hot', 0):,}")
            print(f"  🌡️ Warm:      {leads.get('warm', 0):,}")
            print(f"  ❄️ Cold:      {leads.get('cold', 0):,}")
        
        # Recent Activity (last hour)
        activity = self.fetch_recent_activity()
        if activity:
            print(f"\n⏱️ LAST HOUR:")
            print(f"  Crawler:     +{activity.get('crawler_completed_1h', 0):,} completed, "
                  f"{activity.get('crawler_failed_1h', 0):,} failed")
            print(f"  Intel:       +{activity.get('intel_completed_1h', 0):,} completed, "
                  f"{activity.get('intel_failed_1h', 0):,} failed")
            
            # Calculate rates
            crawler_rate = activity.get('crawler_completed_1h', 0)
            intel_rate = activity.get('intel_completed_1h', 0)
            print(f"  📈 Rates:     {crawler_rate}/hr (crawler), {intel_rate}/hr (intel)")
            
            # ETA calculations
            if crawler_rate > 0 and queue.get('pending', 0) > 0:
                hours_remaining = queue.get('pending', 0) / crawler_rate
                eta = datetime.now() + timedelta(hours=hours_remaining)
                print(f"  🏁 Crawler ETA: {eta.strftime('%Y-%m-%d %H:%M')} "
                      f"({hours_remaining:.1f}h remaining)")
            
            if intel_rate > 0 and intel.get('pending', 0) > 0:
                hours_remaining = intel.get('pending', 0) / intel_rate
                eta = datetime.now() + timedelta(hours=hours_remaining)
                print(f"  🏁 Intel ETA: {eta.strftime('%Y-%m-%d %H:%M')} "
                      f"({hours_remaining:.1f}h remaining)")
        
        print("\n" + "="*80 + "\n")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor Reddit scraper system health")
    parser.add_argument("--watch", action="store_true", help="Continuously monitor (refresh every 30s)")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval in seconds (default: 30)")
    
    args = parser.parse_args()
    
    monitor = SystemMonitor()
    
    try:
        if args.watch:
            print("Starting continuous monitoring (Ctrl+C to stop)...")
            while True:
                monitor.print_status()
                time.sleep(args.interval)
        else:
            monitor.print_status()
    except KeyboardInterrupt:
        print("\n\n⚠️ Monitoring stopped by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
