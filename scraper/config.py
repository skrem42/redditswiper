"""
Configuration for the Reddit scraper.
Copy this file and modify the values, or set environment variables.
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
REDDIT_USER_AGENT = os.getenv(
    "REDDIT_USER_AGENT", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Scraper Settings
SCRAPE_DELAY_SECONDS = float(os.getenv("SCRAPE_DELAY_SECONDS", "2"))
MAX_POSTS_PER_SUBREDDIT = int(os.getenv("MAX_POSTS_PER_SUBREDDIT", "100"))
MAX_SUBREDDITS = int(os.getenv("MAX_SUBREDDITS", "50"))

# =============================================================================
# SUBREDDIT SEARCH KEYWORDS
# =============================================================================
# Customize these to search for different types of subreddits
# You can set via environment variable SEARCH_KEYWORDS as JSON array
# Example: SEARCH_KEYWORDS='["fitness", "fitness models", "gym"]'
# =============================================================================
DEFAULT_SEARCH_KEYWORDS = [
    "onlyfans",
    "onlyfans promotion", 
    "onlyfans creators",
    "onlyfans free",
    "of promotion",
]

# Parse from environment or use defaults
_env_keywords = os.getenv("SEARCH_KEYWORDS", "")
if _env_keywords:
    try:
        SEARCH_KEYWORDS = json.loads(_env_keywords)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse SEARCH_KEYWORDS env var, using defaults")
        SEARCH_KEYWORDS = DEFAULT_SEARCH_KEYWORDS
else:
    SEARCH_KEYWORDS = DEFAULT_SEARCH_KEYWORDS

# =============================================================================
# SUBREDDIT NAME FILTERS
# =============================================================================
# Only include subreddits that contain one of these strings in their name
# Set via SUBREDDIT_NAME_FILTERS as JSON array, or leave empty to include all
# Example: SUBREDDIT_NAME_FILTERS='["onlyfans", "of", "nsfw"]'
# =============================================================================
DEFAULT_SUBREDDIT_FILTERS = ["onlyfans", "of"]

_env_filters = os.getenv("SUBREDDIT_NAME_FILTERS", "")
if _env_filters:
    try:
        SUBREDDIT_NAME_FILTERS = json.loads(_env_filters)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse SUBREDDIT_NAME_FILTERS env var, using defaults")
        SUBREDDIT_NAME_FILTERS = DEFAULT_SUBREDDIT_FILTERS
else:
    SUBREDDIT_NAME_FILTERS = DEFAULT_SUBREDDIT_FILTERS

# =============================================================================
# PROXY CONFIGURATION (set via environment variables)
# =============================================================================
# Brightdata Residential Rotating Proxy (RECOMMENDED - new IP per request)
# Format: http://user-zone-residential:password@brd.superproxy.io:22225
# Set BRIGHTDATA_PROXY in your .env file or Railway environment variables
# =============================================================================
BRIGHTDATA_PROXY = os.getenv("BRIGHTDATA_PROXY", "")

# Legacy: Single rotating proxy with manual IP rotation API
PROXY_HOST = os.getenv("PROXY_HOST", "")
PROXY_PORT = os.getenv("PROXY_PORT", "")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")

# Construct proxy URL - prefer Brightdata, fallback to legacy
if BRIGHTDATA_PROXY:
    PROXY_URL = BRIGHTDATA_PROXY
elif PROXY_HOST and PROXY_PORT and PROXY_USER and PROXY_PASS:
    PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
else:
    PROXY_URL = os.getenv("PROXY_URL", "")

# Rotation API URL - only needed for legacy proxies (Brightdata auto-rotates)
PROXY_ROTATION_URL = os.getenv("PROXY_ROTATION_URL", "")

# Rate limit wait time after rotating IP (seconds) - reduced for Brightdata
RATE_LIMIT_WAIT_SECONDS = int(os.getenv("RATE_LIMIT_WAIT_SECONDS", "2"))

# Legacy: comma-separated proxy list (for multiple static proxies)
_proxy_str = os.getenv("PROXIES", "")
PROXIES = [p.strip() for p in _proxy_str.split(",") if p.strip()] if _proxy_str else []

# =============================================================================
# CONCURRENCY SETTINGS (for parallel processing)
# =============================================================================
# Number of subreddits to process concurrently
CONCURRENT_SUBREDDITS = int(os.getenv("CONCURRENT_SUBREDDITS", "20"))

# Number of users to process concurrently per subreddit
CONCURRENT_USERS = int(os.getenv("CONCURRENT_USERS", "10"))

# Max concurrent HTTP requests (semaphore limit)
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "50"))

# Crawler settings
CRAWLER_MIN_SUBSCRIBERS = int(os.getenv("CRAWLER_MIN_SUBSCRIBERS", "1000"))  # Skip tiny subs

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


