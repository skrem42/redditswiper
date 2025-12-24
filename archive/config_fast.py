"""
Configuration for the FAST Intel Scraper Worker.
Uses rotating proxies that change IP on every request - no manual rotation needed!
"""
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jmchmbwhnmlednaycxqh.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImptY2htYndobm1sZWRuYXljeHFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjMzODI4MzYsImV4cCI6MjA3ODk1ODgzNn0.Ux8SqBEj1isHUGIiGh4I-MM54dUb3sd0D7VsRjRKDuU")

# =============================================================================
# FAST ROTATING PROXY POOL
# =============================================================================
# These proxies rotate IP on EVERY request - no manual rotation needed!
PROXY_POOL = [
    {
        "name": "Mobile Proxy 1",
        "host": "v2.proxyempire.io",
        "port": "5000",
        "username": "m_08c80bbb9f",
        "password": "a5e85ac6e3",
    },
    {
        "name": "Residential Proxy 2",
        "host": "v2.proxyempire.io",
        "port": "5000", 
        "username": "r_8491573ae7",
        "password": "b8d76316bb",
    },
]

# Build proxy URLs
for proxy in PROXY_POOL:
    proxy["url"] = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
    proxy["server"] = f"http://{proxy['host']}:{proxy['port']}"

# =============================================================================
# REDDIT LOGIN (for NSFW access)
# =============================================================================
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "petitebbyxoxod")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "KyvNzPv@NRYy2@y")

# =============================================================================
# FAST SCRAPER SETTINGS
# =============================================================================
# Minimum subscribers to scrape a subreddit
CRAWLER_MIN_SUBSCRIBERS = int(os.getenv("CRAWLER_MIN_SUBSCRIBERS", "5000"))

# Number of parallel workers (one per proxy)
NUM_WORKERS = len(PROXY_POOL)

# Batch size per worker
BATCH_SIZE = int(os.getenv("BATCH_SIZE_FAST", "10"))  # Smaller batches, more parallel

# Minimal delays since proxies auto-rotate
DELAY_MIN = float(os.getenv("DELAY_MIN_FAST", "1.0"))  # Much faster!
DELAY_MAX = float(os.getenv("DELAY_MAX_FAST", "2.0"))

# No manual rotation needed - proxies rotate on every request
ROTATE_EVERY = 999999  # Effectively never

# Wait time when queue is empty (seconds)
IDLE_WAIT = int(os.getenv("IDLE_WAIT", "60"))

# Run browser in headless mode
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

