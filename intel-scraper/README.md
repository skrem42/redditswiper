# Intel Scraper

Standalone Playwright-based scraper that extracts detailed subreddit intelligence data including:

- **Weekly Visitors** - Unique visitors per week
- **Weekly Contributions** - Posts and comments per week
- **Competition Score** - Ratio of contributions to visitors (lower = less competition)
- Subscriber count, rules, moderators, media permissions, etc.

## Features

- 🕵️ **Anti-detection**: User agent rotation, fingerprint spoofing, human-like delays
- 🔄 **Proxy support**: Rotating proxies with automatic IP rotation
- 📊 **Smart extraction**: Multiple fallback patterns for Reddit's dynamic UI
- 💾 **Supabase integration**: Reads from `subreddit_queue`, writes to `nsfw_subreddit_intel`

## Deployment

### Railway (Recommended)

1. Create a new Railway project
2. Connect this folder as the source
3. Set environment variables (see `.env.example`)
4. Railway will auto-detect the Dockerfile

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Test with specific subreddits
python intel_worker.py --test RealGirls gonewild

# Run continuous worker (with visible browser for debugging)
python intel_worker.py --no-headless

# Run in production mode
python intel_worker.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SUPABASE_URL` | Required | Supabase project URL |
| `SUPABASE_ANON_KEY` | Required | Supabase anon key |
| `PROXY_URL` | Optional | Proxy URL (http://user:pass@host:port) |
| `PROXY_ROTATION_URL` | Optional | URL to call for IP rotation |
| `CRAWLER_MIN_SUBSCRIBERS` | 5000 | Minimum subscribers to scrape |
| `BATCH_SIZE` | 20 | Subreddits per batch |
| `DELAY_MIN` | 5.0 | Min delay between requests (seconds) |
| `DELAY_MAX` | 10.0 | Max delay between requests (seconds) |
| `ROTATE_EVERY` | 7 | Rotate IP every N subreddits |
| `IDLE_WAIT` | 120 | Wait time when queue is empty (seconds) |
| `HEADLESS` | true | Run browser in headless mode |

## Competition Score Interpretation

| Score | Label | Opportunity |
|-------|-------|-------------|
| < 0.5% | Very Low | 🟢 Excellent |
| < 1% | Low | 🟢 Great |
| < 3% | Moderate | 🟡 Good |
| < 5% | High | 🟠 Competitive |
| > 5% | Very High | 🔴 Saturated |

