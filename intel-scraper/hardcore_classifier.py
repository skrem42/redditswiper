"""
Hardcore/Softcore Classifier for Subreddits

Fetches subreddit data from Reddit's JSON API and uses ChatGPT to classify
whether a subreddit is "hardcore" or "softcore" NSFW content.

- Hardcore: Explicit sexual acts (porn, hardcore, deepthroat, anal, etc.)
  Not appropriate for OF creator promotion
- Softcore: Suggestive/sexy content without explicit acts (legalteens, fitgirls, etc.)
  Appropriate for OF creator promotion

Usage:
    python hardcore_classifier.py [--batch-size N] [--test subreddit1 subreddit2 ...]
"""
import asyncio
import argparse
import logging
import sys
import os
import json
from datetime import datetime
from typing import Optional, List
import httpx
from openai import AsyncOpenAI
from dotenv import load_dotenv

from supabase_client import SupabaseClient

# Load environment variables
load_dotenv("/Users/calummelling/Desktop/redditscraper/scraper/.env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class HardcoreClassifier:
    """Classifies subreddits as hardcore or softcore using ChatGPT."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        # Using GPT-4o-mini: Fast and cheap
        self.model = "gpt-4o-mini"
        
        self.supabase = SupabaseClient()
        
        self.stats = {
            "total_classified": 0,
            "hardcore": 0,
            "softcore": 0,
            "uncertain": 0,
            "failed": 0,
            "start_time": datetime.now(),
        }
        
        logger.info("Hardcore Classifier initialized")
    
    async def _fetch_subreddit_json(self, subreddit_name: str) -> Optional[dict]:
        """Fetch subreddit data from Reddit's JSON API."""
        url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        sub_data = data.get("data", {})
                        
                        return {
                            "name": sub_data.get("display_name", subreddit_name),
                            "display_name": sub_data.get("display_name_prefixed", f"r/{subreddit_name}"),
                            "subscribers": sub_data.get("subscribers", 0),
                            "public_description": sub_data.get("public_description", ""),
                            "description": sub_data.get("description", ""),
                            "title": sub_data.get("title", ""),
                            "over18": sub_data.get("over18", False),
                            "subreddit_type": sub_data.get("subreddit_type", ""),
                        }
                    
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited fetching r/{subreddit_name} (attempt {attempt+1}/{max_retries})")
                        await asyncio.sleep(5 * (attempt + 1))
                    
                    elif response.status_code == 404:
                        logger.warning(f"Subreddit r/{subreddit_name} not found (404)")
                        return None
                    
                    else:
                        logger.warning(f"Reddit API returned {response.status_code} for r/{subreddit_name}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                        else:
                            return None
                            
            except Exception as e:
                logger.warning(f"Could not fetch r/{subreddit_name} (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    async def classify_subreddit(self, subreddit_name: str, reddit_data: dict) -> dict:
        """
        Use ChatGPT to classify if a subreddit is hardcore or softcore.
        
        Returns dict with:
        - content_rating: 'hardcore', 'softcore', or 'uncertain'
        - confidence: 'high', 'medium', or 'low'
        - reasoning: str
        """
        try:
            # Build classification prompt
            prompt = self._build_prompt(subreddit_name, reddit_data)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing NSFW subreddit content to classify it as hardcore or softcore. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Low temperature for consistent classification
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            logger.info(
                f"Classified r/{subreddit_name} as {result.get('content_rating', 'unknown')} "
                f"(confidence: {result.get('confidence', 'unknown')})"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Classification error for r/{subreddit_name}: {e}")
            return {
                "content_rating": "uncertain",
                "confidence": "low",
                "reasoning": f"Classification failed: {str(e)}"
            }
    
    def _build_prompt(self, subreddit_name: str, reddit_data: dict) -> str:
        """Build the classification prompt for ChatGPT."""
        
        return f"""Classify this NSFW subreddit as either "hardcore" or "softcore" based on its content type:

**Subreddit:** r/{subreddit_name}
**Title:** {reddit_data.get('title', 'N/A')}
**Subscribers:** {reddit_data.get('subscribers', 0):,}
**Public Description:** {reddit_data.get('public_description', 'N/A')}
**Full Description:** {reddit_data.get('description', 'N/A')[:500]}

**CLASSIFICATION CRITERIA:**

**SOFTCORE** (appropriate for OnlyFans creator promotion):
- Suggestive/sexy content without explicit sexual acts
- Bikini/lingerie photos, poses, modeling
- Body appreciation (fit girls, petite, curves, body parts like legs/feet)
- Teasing/flirting content
- Amateur selfies/photos that are sexy but not explicit
- Examples: legalteens, xsmallgirls, fitgirls, bikinis, gonewild (poses), petite, curvy

**HARDCORE** (NOT appropriate for OnlyFans promotion):
- Explicit sexual acts clearly visible
- Pornographic content (penetration, oral sex, etc.)
- Graphic sexual content
- Content focused on explicit acts rather than just nudity/poses
- Examples: nsfwhardcore, porn, deepthroat, anal, blowjobs, cumsluts, latinchickswhitedicks

**KEY DISTINCTION:**
- Softcore = Sexy/nude poses and teasing (showing body)
- Hardcore = Explicit sexual acts in progress (doing sexual acts)

**EDGE CASES:**
- If subreddit name or description is ambiguous, lean toward "softcore" by default
- If it's clearly about nude modeling/posing (even if fully nude), classify as "softcore"
- Only classify as "hardcore" if there's clear indication of explicit sexual acts

Return a JSON object:
{{
  "content_rating": "hardcore" or "softcore" or "uncertain",
  "confidence": "high" or "medium" or "low",
  "reasoning": "Brief 1-2 sentence explanation"
}}"""
    
    async def classify_and_update(self, subreddit_name: str) -> bool:
        """Fetch subreddit data, classify it, and update the database."""
        try:
            # Fetch from Reddit API
            reddit_data = await self._fetch_subreddit_json(subreddit_name)
            
            if not reddit_data:
                logger.warning(f"Could not fetch data for r/{subreddit_name}")
                self.stats["failed"] += 1
                return False
            
            # Classify using ChatGPT
            classification = await self.classify_subreddit(subreddit_name, reddit_data)
            
            # Update database
            rating = classification.get("content_rating", "uncertain")
            
            update_data = {
                "subreddit_name": subreddit_name.lower(),
                "content_rating": rating,
                "content_rating_confidence": classification.get("confidence", "low"),
                "content_rating_reasoning": classification.get("reasoning", ""),
                "updated_at": datetime.now().isoformat(),
            }
            
            self.supabase.client.table("nsfw_subreddit_intel").upsert(
                update_data,
                on_conflict="subreddit_name"
            ).execute()
            
            # Update stats
            self.stats["total_classified"] += 1
            if rating == "hardcore":
                self.stats["hardcore"] += 1
            elif rating == "softcore":
                self.stats["softcore"] += 1
            else:
                self.stats["uncertain"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error classifying r/{subreddit_name}: {e}")
            self.stats["failed"] += 1
            return False
    
    async def classify_batch(self, subreddits: List[str], concurrency: int = 5) -> dict:
        """Classify a batch of subreddits with rate limiting."""
        logger.info(f"Starting batch of {len(subreddits)} subreddits (concurrency: {concurrency})")
        
        semaphore = asyncio.Semaphore(concurrency)
        
        async def classify_with_semaphore(sub_name: str):
            async with semaphore:
                result = await self.classify_and_update(sub_name)
                # Small delay to avoid rate limits
                await asyncio.sleep(1)
                return result
        
        tasks = [classify_with_semaphore(sub) for sub in subreddits]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in results if r is True)
        
        logger.info(f"Batch complete: {successful}/{len(subreddits)} successful")
        
        return {
            "total": len(subreddits),
            "successful": successful,
            "failed": len(subreddits) - successful,
        }
    
    async def run_continuous(self, batch_size: int = 50, concurrency: int = 5):
        """Continuous classification mode - processes all unclassified subreddits."""
        logger.info("=" * 60)
        logger.info("🔍 HARDCORE/SOFTCORE CLASSIFIER")
        logger.info(f"   Batch size: {batch_size}")
        logger.info(f"   Concurrency: {concurrency}")
        logger.info("=" * 60)
        
        while True:
            try:
                # Get subreddits that need classification (content_rating is NULL)
                result = self.supabase.client.table("nsfw_subreddit_intel").select(
                    "subreddit_name"
                ).is_(
                    "content_rating", "null"
                ).eq(
                    "scrape_status", "completed"
                ).limit(batch_size).execute()
                
                if not result.data or len(result.data) == 0:
                    logger.info("✓ All subreddits classified! Waiting for new ones...")
                    self._log_stats()
                    await asyncio.sleep(300)  # Wait 5 minutes
                    continue
                
                subreddits = [row["subreddit_name"] for row in result.data]
                
                logger.info(f"\n📦 Processing batch of {len(subreddits)} unclassified subreddits...")
                
                start_time = datetime.now()
                await self.classify_batch(subreddits, concurrency=concurrency)
                elapsed = (datetime.now() - start_time).total_seconds()
                
                rate = len(subreddits) / elapsed if elapsed > 0 else 0
                logger.info(f"✓ Batch complete in {elapsed:.1f}s ({rate:.2f} subs/sec)")
                
                self._log_stats()
                
                # Brief pause between batches
                await asyncio.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(30)
    
    def _log_stats(self):
        """Log current statistics."""
        runtime = (datetime.now() - self.stats["start_time"]).total_seconds()
        hours = runtime / 3600
        
        rate = self.stats["total_classified"] / hours if hours > 0 else 0
        
        logger.info(
            f"📊 Total: {self.stats['total_classified']} classified "
            f"({self.stats['hardcore']} hardcore, {self.stats['softcore']} softcore, "
            f"{self.stats['uncertain']} uncertain, {self.stats['failed']} failed) "
            f"- {rate:.1f}/hour"
        )


async def run_test(subreddits: List[str]):
    """Test mode - classify specific subreddits."""
    classifier = HardcoreClassifier()
    
    logger.info("=" * 60)
    logger.info("🧪 TEST MODE - Hardcore/Softcore Classification")
    logger.info(f"   Testing {len(subreddits)} subreddits")
    logger.info("=" * 60)
    
    for sub in subreddits:
        await classifier.classify_and_update(sub)
        print()
    
    classifier._log_stats()


def main():
    parser = argparse.ArgumentParser(description="Hardcore/Softcore Subreddit Classifier")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of subreddits per batch (default: 50)"
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent API calls (default: 5)"
    )
    parser.add_argument(
        "--test",
        nargs="+",
        help="Test mode: classify specific subreddits"
    )
    
    args = parser.parse_args()
    
    if args.test:
        # Test mode
        asyncio.run(run_test(args.test))
    else:
        # Production mode: continuous classification
        classifier = HardcoreClassifier()
        asyncio.run(classifier.run_continuous(
            batch_size=args.batch_size,
            concurrency=args.concurrency,
        ))


if __name__ == "__main__":
    main()

