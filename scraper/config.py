"""
Configuration for the Reddit scraper.
Hardcoded settings for production use.
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Supabase Configuration (set via environment variables)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Reddit API Configuration
REDDIT_BASE_URL = "https://www.reddit.com"
REDDIT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Scraper Settings
SCRAPE_DELAY_SECONDS = 2.0
MAX_POSTS_PER_SUBREDDIT = 100
MAX_SUBREDDITS = 50

# =============================================================================
# SUBREDDIT SEARCH KEYWORDS
# =============================================================================
SEARCH_KEYWORDS = [
    "onlyfans",
    "onlyfans promotion", 
    "onlyfans creators",
    "onlyfans free",
    "of promotion",
]

# =============================================================================
# SUBREDDIT NAME FILTERS
# =============================================================================
SUBREDDIT_NAME_FILTERS = ["onlyfans", "of"]

# =============================================================================
# PROXY CONFIGURATION - SOAX (new IP per request)
# =============================================================================
PROXY_URL = "http://package-329587-sessionid-dCA64Iso3jw8VBw0-sessionlength-300:YtaNW215Z7RP5A0b@proxy.soax.com:5000"

# =============================================================================
# CONCURRENCY SETTINGS
# =============================================================================
# Number of subreddits to process concurrently
CONCURRENT_SUBREDDITS = 20

# Number of users to process concurrently per subreddit
CONCURRENT_USERS = 10

# Max concurrent HTTP requests (semaphore limit)
MAX_CONCURRENT_REQUESTS = 50

# Error handling settings
RATE_LIMIT_WAIT_SECONDS = 2
MAX_402_RETRIES = 2  # Max retries for Brightdata 402 errors

# Crawler settings
CRAWLER_MIN_SUBSCRIBERS = 1000  # Skip tiny subs

# Link patterns to extract (OnlyFans, Linktree, etc.)
LINK_PATTERNS = [
    r'onlyfans\.com/[\w\-\.]+',
    r'linktr\.ee/[\w\-\.]+',
    r'linktree\.com/[\w\-\.]+',
    r'allmylinks\.com/[\w\-\.]+',
    r'beacons\.ai/[\w\-\.]+',
    r'linkr\.bio/[\w\-\.]+',
    r'solo\.to/[\w\-\.]+',
    r'fanfix\.io/[\w\-\.]+',
    r'fansly\.com/[\w\-\.]+',
    r'patreon\.com/[\w\-\.]+',
    r'ko-fi\.com/[\w\-\.]+',
    r'cashapp\.com/[\w\-\.]+',
    r'venmo\.com/[\w\-\.]+',
]
