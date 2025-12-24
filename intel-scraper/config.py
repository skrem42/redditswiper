"""
Configuration for the Intel Scraper Worker.
Set environment variables for production deployment.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jmchmbwhnmlednaycxqh.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU")

# =============================================================================
# PROXY CONFIGURATION
# =============================================================================
# Brightdata Residential Rotating Proxy (RECOMMENDED - new IP per request)
# Format: http://user-zone-residential:password@brd.superproxy.io:22225
BRIGHTDATA_PROXY = os.getenv("BRIGHTDATA_PROXY", "")

# Legacy: Single rotating proxy with manual IP rotation API
PROXY_HOST = os.getenv("PROXY_HOST", "")
PROXY_PORT = os.getenv("PROXY_PORT", "")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")

# Construct proxy server URL (without auth for Playwright)
if BRIGHTDATA_PROXY:
    # Parse Brightdata URL for Playwright (needs server separate from auth)
    import re
    _bd_match = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', BRIGHTDATA_PROXY)
    if _bd_match:
        PROXY_USER = _bd_match.group(1)
        PROXY_PASS = _bd_match.group(2)
        PROXY_SERVER = f"http://{_bd_match.group(3)}:{_bd_match.group(4)}"
    else:
        PROXY_SERVER = BRIGHTDATA_PROXY
elif PROXY_HOST and PROXY_PORT:
    PROXY_SERVER = f"http://{PROXY_HOST}:{PROXY_PORT}"
else:
    PROXY_SERVER = ""

# Full proxy URL with auth embedded
if BRIGHTDATA_PROXY:
    PROXY_URL = BRIGHTDATA_PROXY
elif PROXY_HOST and PROXY_PORT and PROXY_USER and PROXY_PASS:
    PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
else:
    PROXY_URL = os.getenv("PROXY_URL", "")

# Rotation API URL - only needed for legacy proxies (Brightdata auto-rotates)
PROXY_ROTATION_URL = os.getenv("PROXY_ROTATION_URL", "")

# =============================================================================
# REDDIT ACCOUNTS (for NSFW access with parallel scraping)
# =============================================================================
# Multiple accounts for parallel browser pool
# Format: JSON array of account objects with cookies
# Example: REDDIT_ACCOUNTS='[{"username": "user1", "reddit_session": "...", "token_v2": "...", "loid": "..."}]'
_reddit_accounts_str = os.getenv("REDDIT_ACCOUNTS", "")
if _reddit_accounts_str:
    try:
        REDDIT_ACCOUNTS = json.loads(_reddit_accounts_str)
    except json.JSONDecodeError:
        print("Warning: Could not parse REDDIT_ACCOUNTS env var")
        REDDIT_ACCOUNTS = []
else:
    REDDIT_ACCOUNTS = []

# Legacy single account (fallback if REDDIT_ACCOUNTS not set)
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "petitebbyxoxod")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "KyvNzPv@NRYy2@y")

# =============================================================================
# BROWSER POOL SETTINGS (for parallel scraping)
# =============================================================================
# Number of browser contexts to run in parallel
BROWSER_POOL_SIZE = int(os.getenv("BROWSER_POOL_SIZE", "5"))

# Number of subreddits to process concurrently
CONCURRENT_SUBREDDITS = int(os.getenv("CONCURRENT_SUBREDDITS", "5"))

# =============================================================================
# SCRAPER SETTINGS
# =============================================================================
# Minimum subscribers to scrape a subreddit
CRAWLER_MIN_SUBSCRIBERS = int(os.getenv("CRAWLER_MIN_SUBSCRIBERS", "5000"))

# Batch size per worker cycle
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))

# Delay between requests (seconds) - reduced for parallel processing
DELAY_MIN = float(os.getenv("DELAY_MIN", "1.0"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "3.0"))

# Rotate IP every N subreddits - less important with Brightdata auto-rotation
ROTATE_EVERY = int(os.getenv("ROTATE_EVERY", "20"))

# Wait time when queue is empty (seconds)
IDLE_WAIT = int(os.getenv("IDLE_WAIT", "120"))

# Run browser in headless mode
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

