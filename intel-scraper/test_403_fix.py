"""
Test script to diagnose and fix 403 errors.

Tests both with and without session cookies to identify the issue.
"""
import asyncio
import logging
import sys

from subreddit_intel_scraper import SubredditIntelScraper
from supabase_client import SupabaseClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

async def test_with_cookies():
    """Test with hardcoded session cookies (current behavior)."""
    logger.info("=" * 60)
    logger.info("TEST 1: WITH session cookies (expired token_v2?)")
    logger.info("=" * 60)
    
    supabase = SupabaseClient()
    scraper = SubredditIntelScraper(
        supabase_client=supabase,
        worker_id=9999,
        headless=True,
        ultra_fast=True,
        enable_llm=False,
        use_session_cookies=True,  # Use hardcoded cookies
    )
    
    try:
        await scraper.start()
        result = await scraper.scrape_subreddit("realgirls")
        
        if result:
            logger.info("✓ SUCCESS with session cookies!")
            logger.info(f"   Visitors: {result.get('weekly_visitors')}")
            logger.info(f"   Contributions: {result.get('weekly_contributions')}")
            return True
        else:
            logger.error("✗ FAILED with session cookies")
            return False
    except Exception as e:
        logger.error(f"✗ ERROR with session cookies: {e}")
        return False
    finally:
        await scraper.close()

async def test_without_cookies():
    """Test WITHOUT session cookies (pure stealth browser)."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: WITHOUT session cookies (stealth only)")
    logger.info("=" * 60)
    
    supabase = SupabaseClient()
    scraper = SubredditIntelScraper(
        supabase_client=supabase,
        worker_id=9998,
        headless=True,
        ultra_fast=True,
        enable_llm=False,
        use_session_cookies=False,  # Disable hardcoded cookies
    )
    
    try:
        await scraper.start()
        result = await scraper.scrape_subreddit("realgirls")
        
        if result:
            logger.info("✓ SUCCESS without session cookies!")
            logger.info(f"   Visitors: {result.get('weekly_visitors')}")
            logger.info(f"   Contributions: {result.get('weekly_contributions')}")
            return True
        else:
            logger.error("✗ FAILED without session cookies")
            return False
    except Exception as e:
        logger.error(f"✗ ERROR without session cookies: {e}")
        return False
    finally:
        await scraper.close()

async def main():
    logger.info("🔍 Testing 403 Fix - Checking Session Cookies\n")
    
    # Test with cookies first
    with_cookies_ok = await test_with_cookies()
    
    # Small pause between tests
    await asyncio.sleep(5)
    
    # Test without cookies
    without_cookies_ok = await test_without_cookies()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)
    logger.info(f"With session cookies:    {'✓ PASS' if with_cookies_ok else '✗ FAIL'}")
    logger.info(f"Without session cookies: {'✓ PASS' if without_cookies_ok else '✗ FAIL'}")
    
    if not with_cookies_ok and without_cookies_ok:
        logger.info("\n🎯 DIAGNOSIS: Session cookies are EXPIRED/INVALID!")
        logger.info("   Solution: Disable session cookies or get fresh ones")
        logger.info("   To disable: use use_session_cookies=False")
    elif with_cookies_ok:
        logger.info("\n✓ Session cookies are working fine")
    elif not with_cookies_ok and not without_cookies_ok:
        logger.info("\n⚠️ Both failed - might be IP/proxy issue")
    
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

