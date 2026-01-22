#!/usr/bin/env python3
"""
Completion Worker - Slow, Synchronous Intel Collector

This worker slowly goes through the nsfw_subreddit_intel table and ensures
EVERY subreddit has complete data:
- Subscribers (Intel JSON)
- Competition metrics (weekly visitors/contributions)  
- LLM analysis (verification/sellers/niche)

Uses Proxidize mobile proxy for maximum reliability.
Designed to run in the background for hours/days until everything is complete.
"""
import sys
import asyncio
import random
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))

from supabase_client import SupabaseClient
from playwright.async_api import async_playwright
from llm_analyzer import SubredditLLMAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [COMPLETION] %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# =============================================================================
# PROXYEMPIRE CONFIGURATION
# =============================================================================
PROXYEMPIRE_HOST = "mobdedi.proxyempire.io"
PROXYEMPIRE_PORT = 9000
PROXYEMPIRE_USERNAME = "2ed80b8624"
PROXYEMPIRE_PASSWORD = "570abb9a59"

PROXYEMPIRE_URL = f"http://{PROXYEMPIRE_USERNAME}:{PROXYEMPIRE_PASSWORD}@{PROXYEMPIRE_HOST}:{PROXYEMPIRE_PORT}"
PROXYEMPIRE_ROTATION_URL = f"https://panel.proxyempire.io/dedicated-mobile/{PROXYEMPIRE_USERNAME}/get-new-ip-by-username"

# Completion worker settings
DELAY_BETWEEN_SUBS = 10  # seconds between each subreddit
BATCH_SIZE = 10  # Check 10 subreddits at a time
CHECKPOINT_EVERY = 50  # Log progress every 50 subreddits


class CompletionWorker:
    """Slow, methodical worker that ensures every subreddit has complete data."""
    
    def __init__(self):
        self.supabase = SupabaseClient()
        self.account = self._load_account()
        self.llm_analyzer = None  # Initialize when needed
        
        self.stats = {
            "processed": 0,
            "subscribers_added": 0,
            "competition_added": 0,
            "llm_added": 0,
            "errors": 0,
            "start_time": datetime.now(timezone.utc),
        }
    
    def _load_account(self) -> dict:
        """Load the single Reddit account from cookies."""
        # Single account from user's browser cookies
        account = {
            "loid": "000000001qidpn3ev6.2.1748687064648.Z0FBQUFBQm9PdGpZb0NMZ0Z2NEFUVGZLN0hQVDBxZF84WWJ1TldhLXlFTHlUdWVSQWhXQThPdzFhODVxcllaLWZKZTk0UVRjUEI2cnBVUXNWZWpPdlhFeHY2SEVURy01OENIUkhsYzUycVJzS01mQS0ySll2SE5uZ0J2NkhnaWVnWDRnS25qbWp0ZDA",
            "csv": "2",
            "edgebucket": "rlhgGhysrX0pm6bn0x",
            "reddit_session": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xcWlkcG4zZXY2IiwiZXhwIjoxNzgxNDQxNzMzLjc0MTQ4NSwiaWF0IjoxNzY1ODAzMzMzLjc0MTQ4NSwianRpIjoibGJCWmllUDRZMm5DbjllbjRmWjF5WjJiN0xHVkNnIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTc0ODY4NzA2NDY0OCwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6Mn0.zXGMEwAUYTrPLomjba0YtBSyv6gOYWCD2qEs7fsMrniSuMta6HtNxPpIWrdmEfXfO9w-SLWeHmJMwz9HEMkWY6HVuEkGCWu77KzCmegInl3s9kYd3HVjRmT59ivtLjJG-AegYPLLQ_W11iVqETlDytbzEiXqldJlYtHomj2mJjzdrZbbs-JhvGMUiiR89PJIvKGVnMoKPhm4fJtqeBorZOOhNluNXyfKLVfEFlCborNT_GVmyf6J0ncm-TZDQqlbWR4JlnJhTxAo6-eOt2cisgZGrtaUoG_pg4UYKFpX4UyH7zWnuhqVRXtWfdloqLAi5nRsO7Shv4LArp1jDqN1WQ",
            "token_v2": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NjUzNTg3LjQ1OTU5NSwiaWF0IjoxNzY2NTY3MTg3LjQ1OTU5NSwianRpIjoiVDdoSjAtSHJFdTFqTGhnX09tX1kwU1Rhc2k3WWpnIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xcWlkcG4zZXY2IiwiYWlkIjoidDJfMXFpZHBuM2V2NiIsImF0IjoxLCJsY2EiOjE3NDg2ODcwNjQ2NDgsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJOTldRUFlWUjhMUm85c1ROWXRDcHBVSVE3cWJCbGdVaUprSC1jU1VzUW5BIiwiZmxvIjoyfQ.fkq5wwn72yab9idn7Hh6-CsfnvVvn5pFz03aK-O9tF-Rb0PdmCPZZFC3CqVzCVlweP-Mm08_TF225zQ3LPedzSy3_xjSFr5sMn0aGBwyp5tCbduhzQidzmHmGZyCCFyT3ZmtQsTAjBA9l66EQzX2gQP3nOO8TsDs_W_rxgg7ny4Sp45mZfSkAPaijaLfvkIe6r3pwW5W27hYAzK8tRTFSObyM7ZqB5HYqYLKvdKWvHGspZls-VsWBNPTqNMeZJoOliDOtHSw2OMYs1WbLZkcOn6RgRZ1Z3IBAqcj9oFyzpUbtyIRDTOY2YMC23hiEXYw1HDbOX81f6rFOCsC9dg0XA",
        }
        
        logger.info(f"Loaded Reddit account (t2_1qidpn3ev6)")
        return account
    
    def _get_cookie_header(self) -> str:
        """Get account cookies as Cookie header."""
        cookies = []
        for key in ["reddit_session", "token_v2", "loid", "edgebucket", "csv"]:
            if self.account.get(key):
                cookies.append(f"{key}={self.account[key]}")
        return "; ".join(cookies) if cookies else ""
    
    async def rotate_ip(self):
        """Rotate ProxyEmpire IP."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(PROXYEMPIRE_ROTATION_URL)
                if response.status_code == 200:
                    logger.info("🔄 ProxyEmpire IP rotated")
                else:
                    logger.warning(f"Failed to rotate IP: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"Error rotating IP: {e}")
    
    async def get_incomplete_subreddits(self, limit: int = BATCH_SIZE) -> list[dict]:
        """
        Get subreddits that are missing any data.
        Returns subreddits sorted by priority (most popular first).
        """
        try:
            # Get subreddits missing ANY required field, include description for LLM
            result = self.supabase.client.table("nsfw_subreddit_intel").select(
                "subreddit_name, subscribers, weekly_visitors, weekly_contributions, "
                "verification_required, sellers_allowed, description"
            ).or_(
                "subscribers.is.null,"
                "weekly_visitors.is.null,"
                "weekly_contributions.is.null,"
                "verification_required.is.null,"
                "sellers_allowed.is.null"
            ).order(
                "subscribers", desc=True, nullsfirst=False
            ).limit(limit).execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"Error fetching incomplete subreddits: {e}")
            return []
    
    async def fetch_subscribers(self, subreddit_name: str) -> Optional[int]:
        """Fetch subscriber count via JSON API."""
        import httpx
        
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        cookie_header = self._get_cookie_header()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Cookie": cookie_header,
        }
        
        try:
            async with httpx.AsyncClient(
                proxy=PROXYEMPIRE_URL,
                verify=False,
                timeout=30.0
            ) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json().get("data", {})
                    return data.get("subscribers")
                else:
                    logger.warning(f"HTTP {response.status_code} for r/{subreddit_name}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching subscribers for r/{subreddit_name}: {e}")
            return None
    
    async def fetch_competition_metrics(self, subreddit_name: str, page) -> Optional[dict]:
        """Fetch competition metrics via Playwright."""
        url = f"https://www.reddit.com/r/{subreddit_name}"
        
        try:
            await page.goto(url, wait_until="commit", timeout=90000)
            await asyncio.sleep(3)
            
            # Handle age verification
            try:
                not_now = await page.query_selector('button:has-text("Not Now")')
                if not_now:
                    await not_now.click()
                    await asyncio.sleep(1)
            except:
                pass
            
            # Poll for competition data
            for _ in range(15):
                await asyncio.sleep(2)
                content = await page.content()
                
                import re
                visitors_match = re.search(r'slot="weekly-active-users-count"[^>]*>([^<]+)<', content)
                contrib_match = re.search(r'slot="weekly-contributions-count"[^>]*>([^<]+)<', content)
                
                if visitors_match and contrib_match:
                    return {
                        "weekly_visitors": self._parse_metric(visitors_match.group(1)),
                        "weekly_contributions": self._parse_metric(contrib_match.group(1)),
                    }
            
            return None
        except Exception as e:
            logger.error(f"Error fetching competition for r/{subreddit_name}: {e}")
            return None
    
    def _parse_metric(self, text: str) -> Optional[int]:
        """Parse metrics like '1.2K' to integer."""
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
            return int(text)
        except:
            return None
    
    async def process_subreddit(self, sub_data: dict, browser) -> dict:
        """Process one subreddit and fill in missing data."""
        subreddit_name = sub_data["subreddit_name"]
        updates = {}
        
        logger.info(f"Processing r/{subreddit_name}...")
        
        # 1. Get subscribers if missing
        if sub_data.get("subscribers") is None:
            logger.info(f"  Fetching subscribers...")
            subs = await self.fetch_subscribers(subreddit_name)
            if subs:
                updates["subscribers"] = subs
                self.stats["subscribers_added"] += 1
                logger.info(f"  ✓ Subscribers: {subs:,}")
            await asyncio.sleep(2)
        
        # 2. Get competition metrics if missing
        if sub_data.get("weekly_visitors") is None or sub_data.get("weekly_contributions") is None:
            logger.info(f"  Fetching competition metrics...")
            
            # Create new page for this request
            context = await browser.new_context(
                proxy={
                    "server": f"http://{PROXYEMPIRE_HOST}:{PROXYEMPIRE_PORT}",
                    "username": PROXYEMPIRE_USERNAME,
                    "password": PROXYEMPIRE_PASSWORD,
                },
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            
            # Set cookies
            cookies = []
            for key in ["reddit_session", "token_v2", "loid", "edgebucket", "csv"]:
                if self.account.get(key):
                    cookies.append({
                        "name": key,
                        "value": self.account[key],
                        "domain": ".reddit.com",
                        "path": "/"
                    })
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            try:
                metrics = await self.fetch_competition_metrics(subreddit_name, page)
                if metrics:
                    updates.update(metrics)
                    self.stats["competition_added"] += 1
                    logger.info(f"  ✓ Competition: {metrics['weekly_visitors']:,} visitors, {metrics['weekly_contributions']:,} posts")
                await asyncio.sleep(3)
            finally:
                await context.close()
        
        # 3. Get LLM analysis if missing
        if sub_data.get("verification_required") is None or sub_data.get("sellers_allowed") is None:
            # Check if we have description (rules will be fetched by LLM analyzer if needed)
            description = sub_data.get("description")
            
            if description:
                logger.info(f"  Running LLM analysis...")
                
                # Initialize LLM analyzer if needed
                if not self.llm_analyzer:
                    self.llm_analyzer = SubredditLLMAnalyzer(reddit_proxy=PROXYEMPIRE_URL)
                
                try:
                    # LLM analyzer will fetch rules from Reddit if needed
                    llm_result = await self.llm_analyzer.analyze_subreddit(
                        subreddit_name=subreddit_name,
                        description=description,
                        rules=[],  # Empty rules - analyzer will fetch if needed
                        subscribers=sub_data.get("subscribers", 0),
                        check_posts=True
                    )
                    
                    if llm_result:
                        updates.update({
                            "verification_required": llm_result.get("verification_required"),
                            "sellers_allowed": llm_result.get("sellers_allowed"),
                            "niche_categories": llm_result.get("niche_categories"),
                            "llm_analysis_confidence": llm_result.get("confidence"),
                            "llm_analysis_reasoning": llm_result.get("reasoning"),
                        })
                        self.stats["llm_added"] += 1
                        logger.info(f"  ✓ LLM: verification={llm_result.get('verification_required')}, sellers={llm_result.get('sellers_allowed')}")
                    
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"  LLM analysis failed: {e}")
            else:
                logger.warning(f"  ⚠️  Missing description for LLM analysis - skipping")
        
        # Save updates if we have any
        if updates:
            try:
                updates["subreddit_name"] = subreddit_name
                updates["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                self.supabase.client.table("nsfw_subreddit_intel").upsert(
                    updates,
                    on_conflict="subreddit_name"
                ).execute()
                
                logger.info(f"✅ r/{subreddit_name} updated with {len(updates)} fields")
                return True  # Return True if we made updates
            except Exception as e:
                logger.error(f"Error saving updates for r/{subreddit_name}: {e}")
                self.stats["errors"] += 1
                return False
        else:
            logger.info(f"ℹ️  r/{subreddit_name} already complete (skipping wait)")
            return False  # Return False if no updates
    
    async def run(self):
        """Main loop - process all incomplete subreddits."""
        logger.info("=" * 80)
        logger.info("COMPLETION WORKER STARTING")
        logger.info(f"  Proxy: ProxyEmpire ({PROXYEMPIRE_HOST}:{PROXYEMPIRE_PORT})")
        logger.info(f"  Account: Reddit account (t2_1qidpn3ev6)")
        logger.info(f"  Delay: {DELAY_BETWEEN_SUBS}s between subreddits")
        logger.info("=" * 80)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            try:
                while True:
                    # Fetch batch of incomplete subreddits
                    incomplete = await self.get_incomplete_subreddits(BATCH_SIZE)
                    
                    if not incomplete:
                        logger.info("🎉 ALL SUBREDDITS COMPLETE! No more work to do.")
                        break
                    
                    logger.info(f"\n📋 Processing batch of {len(incomplete)} incomplete subreddits...")
                    
                    for sub_data in incomplete:
                        try:
                            made_updates = await self.process_subreddit(sub_data, browser)
                            self.stats["processed"] += 1
                            
                            # Rotate IP every 25 subreddits
                            if self.stats["processed"] % 25 == 0:
                                await self.rotate_ip()
                                await asyncio.sleep(3)
                            
                            # Log checkpoint
                            if self.stats["processed"] % CHECKPOINT_EVERY == 0:
                                self.log_stats()
                            
                            # Only wait if we made updates
                            if made_updates:
                                logger.info(f"⏳ Waiting {DELAY_BETWEEN_SUBS}s...\n")
                                await asyncio.sleep(DELAY_BETWEEN_SUBS)
                            else:
                                # Just a brief pause between checks
                                await asyncio.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Error processing subreddit: {e}")
                            self.stats["errors"] += 1
                            await asyncio.sleep(5)
                    
                    logger.info(f"✅ Batch complete. Fetching next batch...\n")
                    await asyncio.sleep(5)
                    
            finally:
                await browser.close()
                self.log_stats()
                logger.info("Completion worker stopped.")
    
    def log_stats(self):
        """Log current statistics."""
        runtime = (datetime.now(timezone.utc) - self.stats["start_time"]).total_seconds()
        hours = runtime / 3600
        
        logger.info("=" * 80)
        logger.info("📊 COMPLETION STATS")
        logger.info(f"  Processed:        {self.stats['processed']}")
        logger.info(f"  Subscribers:      +{self.stats['subscribers_added']}")
        logger.info(f"  Competition:      +{self.stats['competition_added']}")
        logger.info(f"  LLM Analysis:     +{self.stats['llm_added']}")
        logger.info(f"  Errors:           {self.stats['errors']}")
        logger.info(f"  Runtime:          {hours:.1f}h")
        logger.info(f"  Rate:             {self.stats['processed']/hours:.1f} subs/hr")
        logger.info("=" * 80)


def main():
    """Entry point."""
    logger.info("Starting Completion Worker with ProxyEmpire...")
    worker = CompletionWorker()
    asyncio.run(worker.run())


if __name__ == "__main__":
    main()

