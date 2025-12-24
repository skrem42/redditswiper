#!/usr/bin/env python3
"""
Periodic LLM Analysis Runner
============================

Runs LLM analysis in periodic batches to process the backlog efficiently.

Strategy:
- Every 30 minutes, fetch batch of subreddits needing LLM analysis
- Process batch concurrently (10 at a time to avoid rate limits)
- Uses SOAX proxy for Reddit API, direct connection for OpenAI
- Continuous loop with health monitoring

Usage:
    python run_llm_periodic.py
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Optional

from llm_analyzer import SubredditLLMAnalyzer
from supabase_client import SupabaseClient
from config import LLM_REDDIT_PROXY, OPENAI_API_KEY

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('llm_periodic.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Suppress noisy httpx/httpcore logs (only show errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configuration
BATCH_SIZE = 50  # Process 50 subreddits per batch
CONCURRENT_LLM = 10  # Analyze 10 subreddits concurrently
BATCH_INTERVAL_MINUTES = 30  # Run every 30 minutes
MAX_RETRIES = 3  # Retry failed analyses


class PeriodicLLMRunner:
    """Runs LLM analysis in periodic batches."""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.analyzer = SubredditLLMAnalyzer(reddit_proxy=LLM_REDDIT_PROXY)
        self.should_stop = False
        self.batches_processed = 0
        self.subreddits_analyzed = 0
        self.failures = 0
        
    async def fetch_batch(self) -> List[dict]:
        """Fetch batch of subreddits needing LLM analysis."""
        try:
            # Fetch subreddits that haven't been LLM analyzed yet
            # sellers_allowed is null means LLM hasn't analyzed it
            response = self.supabase.client.table("nsfw_subreddit_intel") \
                .select("subreddit_name, subscribers, description") \
                .is_("sellers_allowed", "null") \
                .order("subscribers", desc=True) \
                .limit(BATCH_SIZE) \
                .execute()
            
            if response.data:
                logger.info(f"📦 Fetched batch of {len(response.data)} subreddits for LLM analysis")
                return response.data
            else:
                logger.info("✅ No subreddits need LLM analysis at this time")
                return []
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch batch: {e}")
            return []
    
    async def analyze_subreddit(self, subreddit_data: dict, semaphore: asyncio.Semaphore) -> bool:
        """Analyze a single subreddit with rate limiting."""
        async with semaphore:
            subreddit_name = subreddit_data.get("subreddit_name")
            
            try:
                logger.info(f"🤖 Analyzing r/{subreddit_name}...")
                
                # Extract parameters from subreddit_data
                # Note: rules are not stored in DB, pass empty list
                result = await self.analyzer.analyze_subreddit(
                    subreddit_name=subreddit_name,
                    description=subreddit_data.get("description") or "",
                    rules=[],  # Rules not stored in DB
                    subscribers=subreddit_data.get("subscribers", 0),
                    check_posts=True
                )
                
                if result:
                    self.subreddits_analyzed += 1
                    logger.info(f"✅ r/{subreddit_name} analyzed successfully")
                    return True
                else:
                    self.failures += 1
                    logger.warning(f"⚠️ r/{subreddit_name} analysis returned no result")
                    return False
                    
            except Exception as e:
                self.failures += 1
                logger.error(f"❌ r/{subreddit_name} analysis failed: {e}")
                return False
    
    async def process_batch(self, batch: List[dict]) -> int:
        """Process a batch of subreddits concurrently."""
        if not batch:
            return 0
        
        logger.info(f"🔄 Processing batch of {len(batch)} subreddits...")
        start_time = datetime.now()
        
        # Create semaphore for concurrent processing
        semaphore = asyncio.Semaphore(CONCURRENT_LLM)
        
        # Process all subreddits concurrently
        tasks = [
            self.analyze_subreddit(sub_data, semaphore)
            for sub_data in batch
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes
        successes = sum(1 for r in results if r is True)
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Batch complete: {successes}/{len(batch)} analyzed in {duration:.1f}s")
        
        return successes
    
    async def run(self):
        """Main loop: fetch and process batches periodically."""
        logger.info("="*80)
        logger.info("Periodic LLM Analysis Runner")
        logger.info("="*80)
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Batch size: {BATCH_SIZE}")
        logger.info(f"Concurrent: {CONCURRENT_LLM}")
        logger.info(f"Interval: {BATCH_INTERVAL_MINUTES} minutes")
        logger.info("="*80)
        
        try:
            while not self.should_stop:
                batch_start = datetime.now()
                
                # Fetch batch
                batch = await self.fetch_batch()
                
                if batch:
                    # Process batch
                    self.batches_processed += 1
                    await self.process_batch(batch)
                    
                    # Log stats
                    logger.info("="*80)
                    logger.info(f"📊 Statistics:")
                    logger.info(f"  Batches processed: {self.batches_processed}")
                    logger.info(f"  Total analyzed: {self.subreddits_analyzed}")
                    logger.info(f"  Total failures: {self.failures}")
                    logger.info(f"  Success rate: {self.subreddits_analyzed / (self.subreddits_analyzed + self.failures) * 100:.1f}%" if (self.subreddits_analyzed + self.failures) > 0 else "  Success rate: N/A")
                    logger.info("="*80)
                else:
                    logger.info(f"💤 No work to do, waiting {BATCH_INTERVAL_MINUTES} minutes...")
                
                # Calculate sleep time
                batch_duration = (datetime.now() - batch_start).total_seconds()
                sleep_time = max(0, BATCH_INTERVAL_MINUTES * 60 - batch_duration)
                
                if sleep_time > 0:
                    next_run = datetime.now().timestamp() + sleep_time
                    next_run_str = datetime.fromtimestamp(next_run).strftime('%H:%M:%S')
                    logger.info(f"⏰ Next batch at {next_run_str}")
                    await asyncio.sleep(sleep_time)
                    
        except KeyboardInterrupt:
            logger.info("\n⚠️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)
    
    def stop(self):
        """Signal the runner to stop."""
        self.should_stop = True


async def main():
    """Main entry point."""
    runner = PeriodicLLMRunner()
    
    try:
        await runner.run()
    except KeyboardInterrupt:
        runner.stop()


if __name__ == "__main__":
    asyncio.run(main())

