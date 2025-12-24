#!/usr/bin/env python3
"""
Subreddit Intel Worker - Hybrid Edition

Strategy:
1. Fast pass: JSON API for basic data (subscribers, description) 
2. Slow pass: Playwright for competition metrics (weekly visitors, contributions)

Uses separate IPs for each request via SOAX session rotation.
"""
import asyncio
import random
import string
import logging
import sys
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict
import httpx
from playwright.async_api import async_playwright

from supabase_client import SupabaseClient
from config import (
    CRAWLER_MIN_SUBSCRIBERS, 
    BATCH_SIZE, 
    CONCURRENT_SUBREDDITS,
    PROXY_SERVER,
    PROXY_USER,
    PROXY_PASS,
    REDDIT_ACCOUNTS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Suppress noisy httpx/httpcore logs (only show errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class SOAXRotatingProxy:
    """SOAX proxy with automatic IP rotation per request."""
    
    def __init__(self):
        self.package = "329587"
        self.base_password = "YtaNW215Z7RP5A0b"
        self.host = "proxy.soax.com"
        self.port = 5000
    
    def get_proxy_url(self) -> str:
        """Get a proxy URL with unique session ID (new IP)."""
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        username = f"package-{self.package}-sessionid-{session_id}-sessionlength-10"
        return f"http://{username}:{self.base_password}@{self.host}:{self.port}"
    
    def get_playwright_proxy(self) -> dict:
        """Get proxy config for Playwright with longer session for page load."""
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        return {
            "server": f"http://{self.host}:{self.port}",
            "username": f"package-{self.package}-sessionid-{session_id}-sessionlength-180",
            "password": self.base_password,
        }


class HybridIntelWorker:
    """
    Hybrid worker: JSON API + Playwright for complete data.
    """
    
    def __init__(self, worker_id: int = None):
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.supabase = SupabaseClient()
        self.proxy = SOAXRotatingProxy()
        self.accounts = REDDIT_ACCOUNTS
        
        self.stats = {
            "scraped": 0,
            "with_competition": 0,
            "failed": 0,
            "start_time": datetime.now(timezone.utc),
        }
    
    async def scrape_json(self, subreddit_name: str) -> Optional[dict]:
        """Fast scrape via JSON API."""
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        proxy_url = self.proxy.get_proxy_url()
        
        try:
            async with httpx.AsyncClient(proxy=proxy_url, verify=False, timeout=15.0) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                }
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    api_data = response.json().get("data", {})
                    
                    return {
                        "subreddit_name": subreddit_name.lower(),
                        "display_name": api_data.get("display_name", subreddit_name),
                        "subscribers": api_data.get("subscribers"),
                        "accounts_active": api_data.get("accounts_active"),
                        "description": api_data.get("public_description", "")[:1000],
                        "allows_images": api_data.get("allow_images", True),
                        "allows_videos": api_data.get("allow_videos", True),
                    }
        except Exception as e:
            logger.warning(f"JSON failed for r/{subreddit_name}: {type(e).__name__}")
        
        return None
    
    async def scrape_competition_metrics(self, subreddit_name: str, page) -> dict:
        """
        Scrape competition metrics from Reddit page.
        Returns dict with weekly_visitors, weekly_contributions.
        
        Uses 90s timeout - page loads slowly through proxy but data is there.
        """
        metrics = {}
        
        url = f"https://www.reddit.com/r/{subreddit_name}"
        
        try:
            # Start navigation - use 'commit' to not wait for full load
            await page.goto(url, wait_until="commit", timeout=90000)
            
            # Handle NSFW consent / age verification
            await asyncio.sleep(2)
            
            # Handle birthday verification dialog (UK law) - just click "Not Now"
            for attempt in range(3):
                try:
                    not_now = await page.query_selector('button:has-text("Not Now")')
                    if not_now:
                        await not_now.click()
                        logger.info(f"  Clicked 'Not Now' on birthday dialog")
                        await asyncio.sleep(1)
                        break
                except:
                    pass
                await asyncio.sleep(1)
            
            # Try simple consent buttons
            for selector in ['button:has-text("Yes")', 'button:has-text("Continue")', 'button:has-text("I am 18")']:
                try:
                    await page.click(selector, timeout=2000)
                    await asyncio.sleep(1)
                    break
                except:
                    pass
            
            # Poll for the competition data (it loads in the sidebar)
            # Data appears in: <span slot="weekly-active-users-count">8.3M</span>
            for attempt in range(20):  # Poll for up to 40 seconds
                await asyncio.sleep(2)
                
                content = await page.content()
                
                # Check for weekly active users
                # Pattern: <span slot="weekly-active-users-count">8.3M</span>
                visitors_match = re.search(r'slot="weekly-active-users-count"[^>]*>([^<]+)<', content)
                
                # Check for weekly contributions  
                # Pattern: <span slot="weekly-contributions-count">125K</span>
                contrib_match = re.search(r'slot="weekly-contributions-count"[^>]*>([^<]+)<', content)
                
                if visitors_match:
                    metrics["weekly_visitors"] = self._parse_metric(visitors_match.group(1))
                    logger.info(f"  Found weekly visitors: {visitors_match.group(1)}")
                
                if contrib_match:
                    metrics["weekly_contributions"] = self._parse_metric(contrib_match.group(1))
                    logger.info(f"  Found weekly contributions: {contrib_match.group(1)}")
                
                # If we have both, we're done!
                if metrics.get("weekly_visitors") and metrics.get("weekly_contributions"):
                    break
                
                # Also check for subscribers count
                subs_match = re.search(r'slot="subscriber-count"[^>]*>([^<]+)<', content)
                if subs_match and "subscribers" not in metrics:
                    metrics["subscribers"] = self._parse_metric(subs_match.group(1))
            
            # Calculate competition score if we have both metrics
            if metrics.get("weekly_visitors") and metrics.get("weekly_contributions"):
                metrics["competition_score"] = round(
                    metrics["weekly_contributions"] / metrics["weekly_visitors"], 6
                )
                logger.info(f"  Competition score: {metrics['competition_score']:.4%}")
            
        except Exception as e:
            logger.warning(f"Playwright failed for r/{subreddit_name}: {type(e).__name__}: {e}")
        
        return metrics
    
    def _parse_metric(self, text: str) -> Optional[int]:
        """Parse metric like '1.2K' or '1,234' to integer."""
        if not text:
            return None
        
        text = text.strip().replace(',', '')
        
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
        
        for suffix, mult in multipliers.items():
            if suffix in text.upper():
                try:
                    num = float(text.upper().replace(suffix, ''))
                    return int(num * mult)
                except:
                    pass
        
        try:
            return int(float(text))
        except:
            return None
    
    async def save_result(self, data: dict) -> bool:
        """Save result to Supabase."""
        try:
            # Add metadata
            data["last_scraped_at"] = datetime.now(timezone.utc).isoformat()
            data["scrape_status"] = "completed"
            
            self.supabase.client.table("nsfw_subreddit_intel") \
                .upsert(data, on_conflict="subreddit_name") \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    async def fetch_queue(self, batch_size: int = 50) -> List[str]:
        """Fetch subreddits that need scraping."""
        try:
            # Get subs without competition metrics
            response = self.supabase.client.table("nsfw_subreddit_intel") \
                .select("subreddit_name") \
                .is_("weekly_visitors", "null") \
                .gte("subscribers", CRAWLER_MIN_SUBSCRIBERS) \
                .order("subscribers", desc=True) \
                .limit(batch_size) \
                .execute()
            
            return [r["subreddit_name"] for r in response.data]
        except Exception as e:
            logger.error(f"Queue fetch error: {e}")
            return []
    
    async def process_batch_playwright(self, subreddits: List[str], concurrent: int = 3):
        """Process batch with Playwright for competition metrics."""
        
        semaphore = asyncio.Semaphore(concurrent)
        
        async def process_one(sub: str, browser):
            async with semaphore:
                # Get account for cookies
                account = random.choice(self.accounts)
                
                # Create new context with fresh proxy IP
                proxy_config = self.proxy.get_playwright_proxy()
                
                context = await browser.new_context(
                    proxy=proxy_config,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                )
                
                # Set cookies
                cookies = [
                    {"name": "reddit_session", "value": account.get("reddit_session", ""), "domain": ".reddit.com", "path": "/"},
                    {"name": "token_v2", "value": account.get("token_v2", ""), "domain": ".reddit.com", "path": "/"},
                    {"name": "loid", "value": account.get("loid", ""), "domain": ".reddit.com", "path": "/"},
                ]
                await context.add_cookies([c for c in cookies if c["value"]])
                
                page = await context.new_page()
                
                try:
                    # Scrape competition metrics
                    metrics = await self.scrape_competition_metrics(sub, page)
                    
                    if metrics:
                        await self.save_result({"subreddit_name": sub.lower(), **metrics})
                        self.stats["with_competition"] += 1
                        
                        wv = metrics.get('weekly_visitors', 'N/A')
                        wc = metrics.get('weekly_contributions', 'N/A')
                        logger.info(f"✓ r/{sub}: {wv} visitors/wk, {wc} posts/wk")
                    else:
                        logger.info(f"- r/{sub}: No competition data found")
                    
                    self.stats["scraped"] += 1
                    
                except Exception as e:
                    logger.error(f"Error on r/{sub}: {e}")
                    self.stats["failed"] += 1
                
                finally:
                    await context.close()
                
                # Delay between requests
                await asyncio.sleep(2)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                await asyncio.gather(*[process_one(sub, browser) for sub in subreddits])
            finally:
                await browser.close()
    
    def log_stats(self):
        """Log current statistics."""
        runtime = (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()
        rate = self.stats["scraped"] / (runtime / 3600) if runtime > 0 else 0
        
        logger.info(
            f"📊 Stats: {self.stats['scraped']} scraped, "
            f"{self.stats['with_competition']} with competition data, "
            f"{self.stats['failed']} failed, "
            f"Rate: {rate:.0f}/hr"
        )
    
    async def run(self):
        """Main run loop - focuses on getting competition metrics."""
        logger.info("=" * 60)
        logger.info(f"Hybrid Intel Worker starting (Worker {self.worker_id})")
        logger.info(f"  - Phase: Competition metrics (Playwright)")
        logger.info(f"  - Using SOAX with rotating IPs")
        logger.info(f"  - Accounts: {len(self.accounts)}")
        logger.info(f"  - Concurrent: 3 browsers")
        logger.info("=" * 60)
        
        while True:
            # Fetch subs that need competition metrics
            subreddits = await self.fetch_queue(batch_size=10)
            
            if not subreddits:
                logger.info("No subs need competition data, waiting 60s...")
                await asyncio.sleep(60)
                continue
            
            logger.info(f"Processing {len(subreddits)} subs for competition metrics...")
            
            # Process with Playwright (slower but gets competition data)
            await self.process_batch_playwright(subreddits, concurrent=3)
            
            # Log stats
            self.log_stats()
            
            # Pause between batches
            await asyncio.sleep(5)


async def main():
    """Entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hybrid Intel Worker")
    parser.add_argument("--worker-id", type=int, default=None)
    args = parser.parse_args()
    
    worker = HybridIntelWorker(worker_id=args.worker_id)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())

