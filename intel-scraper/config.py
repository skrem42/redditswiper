"""
Configuration for the Intel Scraper Worker.
Set environment variables for production deployment.
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
# PROXY CONFIGURATION
# =============================================================================
# Single rotating proxy with IP rotation API
PROXY_HOST = os.getenv("PROXY_HOST", "")
PROXY_PORT = os.getenv("PROXY_PORT", "")
PROXY_USER = os.getenv("PROXY_USER", "")
PROXY_PASS = os.getenv("PROXY_PASS", "")

# Construct proxy server URL (without auth for Playwright)
if PROXY_HOST and PROXY_PORT:
    PROXY_SERVER = f"http://{PROXY_HOST}:{PROXY_PORT}"
else:
    PROXY_SERVER = ""

# Legacy: Full proxy URL with auth embedded
if PROXY_HOST and PROXY_PORT and PROXY_USER and PROXY_PASS:
    PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
else:
    PROXY_URL = os.getenv("PROXY_URL", "")

# Rotation API URL - called to get a new IP
PROXY_ROTATION_URL = os.getenv("PROXY_ROTATION_URL", "")

# =============================================================================
# REDDIT LOGIN (for NSFW access)
# =============================================================================
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "petitebbyxoxod")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "KyvNzPv@NRYy2@y")

# =============================================================================
# SCRAPER SETTINGS
# =============================================================================
# Minimum subscribers to scrape a subreddit
CRAWLER_MIN_SUBSCRIBERS = int(os.getenv("CRAWLER_MIN_SUBSCRIBERS", "5000"))

# Batch size per worker cycle
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))

# Delay between requests (seconds)
DELAY_MIN = float(os.getenv("DELAY_MIN", "5.0"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "10.0"))

# Rotate IP every N subreddits
ROTATE_EVERY = int(os.getenv("ROTATE_EVERY", "7"))

# Wait time when queue is empty (seconds)
IDLE_WAIT = int(os.getenv("IDLE_WAIT", "120"))

# Run browser in headless mode
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

