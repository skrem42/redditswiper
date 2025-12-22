"""
Configuration for ULTRA Intel Scraper - Conservative with single unlimited proxy.
Uses ONE dedicated mobile proxy with smart refresh strategy.
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
# UNLIMITED DEDICATED MOBILE PROXY
# =============================================================================
# Single unlimited proxy
PROXY_HOST = os.getenv("PROXY_HOST_ULTRA", "mobdedi.proxyempire.io")
PROXY_PORT = os.getenv("PROXY_PORT_ULTRA", "9000")  # Correct port
PROXY_USER = os.getenv("PROXY_USER_ULTRA", "2ed80b8624")
PROXY_PASS = os.getenv("PROXY_PASS_ULTRA", "570abb9a59")

# Build single proxy config
PROXY_CONFIG = {
    "name": "Unlimited Dedicated Mobile",
    "host": PROXY_HOST,
    "port": PROXY_PORT,
    "username": PROXY_USER,
    "password": PROXY_PASS,
    "url": f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}",
    "server": f"http://{PROXY_HOST}:{PROXY_PORT}",
}

# Proxy rotation URL (to manually refresh IP when needed)
PROXY_ROTATION_URL = os.getenv("PROXY_ROTATION_URL_ULTRA", "https://panel.proxyempire.io/dedicated-mobile/2ed80b8624/get-new-ip-by-username")

# =============================================================================
# REDDIT LOGIN (for NSFW access)
# =============================================================================
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "petitebbyxoxod")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "KyvNzPv@NRYy2@y")

# =============================================================================
# ULTRA CONSERVATIVE SCRAPER SETTINGS
# =============================================================================
# Minimum subscribers to scrape a subreddit
CRAWLER_MIN_SUBSCRIBERS = int(os.getenv("CRAWLER_MIN_SUBSCRIBERS", "5000"))

# Optimal concurrency for single mobile proxy (tested up to 4 successfully)
NUM_WORKERS = int(os.getenv("NUM_WORKERS_ULTRA", "4"))

# Batch size per round
BATCH_SIZE = int(os.getenv("BATCH_SIZE_ULTRA", "10"))

# Small delays to be nice to the proxy (1-2 seconds between scrapes)
DELAY_MIN = float(os.getenv("DELAY_MIN_ULTRA", "1.0"))
DELAY_MAX = float(os.getenv("DELAY_MAX_ULTRA", "2.0"))

# Refresh browser between every subreddit (prevents accumulation of issues)
REFRESH_EVERY = 1  # Every 1 subreddit

# Call rotation API every N subreddits (manual IP refresh)
ROTATE_IP_EVERY = int(os.getenv("ROTATE_IP_EVERY_ULTRA", "10"))

# Wait time when queue is empty (seconds)
IDLE_WAIT = int(os.getenv("IDLE_WAIT", "60"))

# Run browser in headless mode
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

