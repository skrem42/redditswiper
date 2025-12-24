"""
Re-analyze ALL subreddits in intel table with enhanced LLM
Uses proxy to avoid rate limits, rotates IP when needed.
"""
import asyncio
import os
import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv("/Users/calummelling/Desktop/redditscraper/scraper/.env")

from llm_analyzer import SubredditLLMAnalyzer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProxyRotatingAnalyzer:
    """LLM analyzer with proxy support and IP rotation."""
    
    def __init__(self):
        # Supabase
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Proxy config
        self.proxy_host = os.getenv("PROXY_HOST")
        self.proxy_port = os.getenv("PROXY_PORT")
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")
        self.proxy_rotation_url = os.getenv("PROXY_ROTATION_URL")
        self.rate_limit_wait = int(os.getenv("RATE_LIMIT_WAIT_SECONDS", "10"))
        
        # Build proxy URL
        self.proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
        
        # LLM analyzer with proxy and rotation callback
        self.llm = SubredditLLMAnalyzer(
            proxy_url=self.proxy_url,
            rotation_callback=self.rotate_ip
        )
        
        # Stats
        self.stats = {
            "total": 0,
            "analyzed": 0,
            "failed": 0,
            "skipped": 0,
            "cached_data_used": 0,
            "ip_rotations": 0,
            "rate_limits": 0,
            "start_time": datetime.now()
        }
        
        logger.info(f"✓ Proxy: {self.proxy_host}:{self.proxy_port}")
        logger.info(f"✓ IP Rotation URL: {self.proxy_rotation_url}")
    
    async def rotate_ip(self):
        """Rotate proxy IP."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.proxy_rotation_url)
                if response.status_code == 200:
                    self.stats["ip_rotations"] += 1
                    logger.info(f"✓ IP rotated (#{self.stats['ip_rotations']})")
                    await asyncio.sleep(5)  # Wait for IP to switch
                    return True
                else:
                    logger.warning(f"IP rotation failed: {response.status_code}")
        except Exception as e:
            logger.error(f"IP rotation error: {e}")
        return False
    
    async def fetch_with_proxy(self, url: str, retry_on_429: bool = True) -> Optional[dict]:
        """Fetch URL with proxy, handle rate limits."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # httpx uses 'proxy' (singular) for a single proxy string
                async with httpx.AsyncClient(
                    proxy=self.proxy_url,
                    timeout=30.0,
                    follow_redirects=True
                ) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 429:
                        self.stats["rate_limits"] += 1
                        if retry_on_429 and attempt < max_retries - 1:
                            logger.warning(f"Rate limited! Rotating IP and retrying... (attempt {attempt+1}/{max_retries})")
                            await self.rotate_ip()
                            await asyncio.sleep(self.rate_limit_wait)
                        else:
                            logger.error(f"Rate limited after {max_retries} attempts")
                            return None
                    elif response.status_code == 403:
                        logger.warning(f"Blocked (403) - rotating IP...")
                        await self.rotate_ip()
                        await asyncio.sleep(5)
                    else:
                        logger.warning(f"HTTP {response.status_code} for {url}")
                        return None
            except Exception as e:
                logger.warning(f"Fetch error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
        
        return None
    
    async def get_subreddit_data(self, subreddit_name: str) -> tuple[str, list]:
        """Fetch subreddit description and rules."""
        # Fetch about data
        about_url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        about_data = await self.fetch_with_proxy(about_url)
        
        description = ""
        if about_data and "data" in about_data:
            description = about_data["data"].get("public_description", "")
        
        # Fetch rules
        rules_url = f"https://www.reddit.com/r/{subreddit_name}/about/rules.json"
        rules_data = await self.fetch_with_proxy(rules_url)
        
        rules = []
        if rules_data and "rules" in rules_data:
            rules = rules_data["rules"]
        
        return description, rules
    
    async def reanalyze_subreddit(self, sub_data: dict):
        """Re-analyze a single subreddit."""
        subreddit_name = sub_data["subreddit_name"]
        sub_id = sub_data["id"]
        subscribers = sub_data.get("subscribers", 0)
        
        logger.info(f"\n[{self.stats['analyzed']+1}/{self.stats['total']}] Analyzing r/{subreddit_name} ({subscribers:,} subs)...")
        
        try:
            # Use cached description from DB if available
            description = sub_data.get("description", "")
            rules = []
            
            # Always fetch rules from Reddit (they're not cached in DB)
            # Only fetch description if missing
            if not description:
                logger.info(f"  ℹ️  Fetching data from Reddit...")
                fetched_description, rules = await self.get_subreddit_data(subreddit_name)
                if fetched_description:
                    description = fetched_description
                
                # Need at least SOMETHING to analyze (description OR rules)
                if not description and not rules:
                    logger.warning(f"  ⚠️  No data available for r/{subreddit_name} - skipping")
                    self.stats["failed"] += 1
                    return
            else:
                # We have description cached, just fetch rules
                logger.info(f"  ✓ Using cached description from DB")
                self.stats["cached_data_used"] += 1
                _, rules = await self.get_subreddit_data(subreddit_name)
            
            # Log what data we have for transparency
            logger.info(f"     Description: {len(description)} chars, Rules: {len(rules)} items")
            
            # Run LLM analysis with post checking
            result = await self.llm.analyze_subreddit(
                subreddit_name=subreddit_name,
                description=description,
                rules=rules,
                subscribers=subscribers,
                check_posts=True  # Enable post checking for unclear cases
            )
            
            # Update database
            update_data = {
                "verification_required": result["verification_required"],
                "sellers_allowed": result["sellers_allowed"],
                "niche_categories": result["niche_categories"],
                "llm_analysis_confidence": result["confidence"],
                "llm_analysis_reasoning": result["reasoning"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            self.supabase.table("nsfw_subreddit_intel").update(
                update_data
            ).eq("id", sub_id).execute()
            
            self.stats["analyzed"] += 1
            
            logger.info(f"  ✅ {result['sellers_allowed']:12} sellers | {result['verification_required']} verify | {result['confidence']} confidence")
            logger.info(f"     Niches: {', '.join(result['niche_categories'][:3])}")
            
            # Small delay to avoid hammering (increased from 1s to 2s)
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"  ❌ Error: {e}")
            self.stats["failed"] += 1
    
    async def run(self, limit: Optional[int] = None, force_reanalyze: bool = False):
        """Re-analyze all subreddits in intel table."""
        logger.info("=" * 80)
        logger.info("🔄 RE-ANALYZING ALL SUBREDDITS WITH ENHANCED LLM")
        logger.info("=" * 80)
        
        # Fetch subreddits to analyze (include existing data to avoid re-fetching)
        query = self.supabase.table("nsfw_subreddit_intel").select(
            "id, subreddit_name, subscribers, description, llm_analysis_confidence"
        ).order("subscribers", desc=True)
        
        if not force_reanalyze:
            # Only re-analyze ones with 'unknown' or NULL sellers_allowed
            # Exclude high-confidence "unknown" results (they've been thoroughly analyzed)
            query = query.or_(
                "sellers_allowed.is.null,"
                "and(sellers_allowed.eq.unknown,or(llm_analysis_confidence.is.null,llm_analysis_confidence.neq.high))"
            )
        
        if limit:
            query = query.limit(limit)
        else:
            query = query.limit(10000)  # Fetch in batches
        
        result = query.execute()
        subreddits = result.data or []
        
        if not subreddits:
            logger.info("✓ No subreddits need re-analysis!")
            return
        
        self.stats["total"] = len(subreddits)
        
        logger.info(f"✓ Found {len(subreddits)} subreddits to re-analyze")
        logger.info(f"✓ Force reanalyze: {force_reanalyze}")
        logger.info("=" * 80)
        
        # Process in batches with IP rotation every 50
        for i, sub_data in enumerate(subreddits):
            # Rotate IP every 50 subs proactively
            if i > 0 and i % 50 == 0:
                logger.info(f"\n🔄 Proactive IP rotation at {i} subreddits...")
                await self.rotate_ip()
            
            await self.reanalyze_subreddit(sub_data)
        
        # Final stats
        elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
        logger.info("\n" + "=" * 80)
        logger.info("✅ RE-ANALYSIS COMPLETE!")
        logger.info("=" * 80)
        logger.info(f"📊 Total: {self.stats['total']}")
        logger.info(f"📊 Analyzed: {self.stats['analyzed']}")
        logger.info(f"📊 Failed: {self.stats['failed']}")
        logger.info(f"📊 Cached Data Used: {self.stats['cached_data_used']}")
        logger.info(f"📊 IP Rotations: {self.stats['ip_rotations']}")
        logger.info(f"📊 Rate Limits: {self.stats['rate_limits']}")
        logger.info(f"📊 Time: {elapsed/60:.1f} minutes")
        if elapsed > 0:
            logger.info(f"📊 Rate: {self.stats['analyzed']/(elapsed/3600):.1f} subs/hour")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Re-analyze subreddits with enhanced LLM")
    parser.add_argument("--limit", type=int, help="Limit number of subreddits to analyze")
    parser.add_argument("--force", action="store_true", help="Force re-analyze ALL subs (not just unknown)")
    args = parser.parse_args()
    
    analyzer = ProxyRotatingAnalyzer()
    await analyzer.run(limit=args.limit, force_reanalyze=args.force)


if __name__ == "__main__":
    asyncio.run(main())

