# Reddit Scraper - Simplified

Three independent workers for scraping Reddit NSFW subreddits and creator profiles.

## 🚀 Quick Start

```bash
# Run all workers simultaneously
python run_all.py

# Monitor system health (live)
python monitor.py --watch

# Run individual workers
python run_all.py --crawler
python run_all.py --intel
python run_all.py --llm
```

## System Architecture

```
┌─────────────┐         ┌──────────────┐         ┌──────────────┐
│   Crawler   │────────▶│ Supabase DB  │────────▶│ Intel Worker │
│ (Brightdata)│         │    Queue     │         │    (SOAX)    │
└─────────────┘         └──────────────┘         └──────────────┘
                               │                         │
                               │                         ▼
                               │                  ┌──────────────┐
                               └─────────────────▶│ LLM Analyzer │
                                                  │(ProxyEmpire) │
                                                  └──────────────┘
```

## Workers

### 1. Crawler (`scraper/`)
Discovers NSFW subreddits and extracts OnlyFans creator links.
- **Proxy**: Brightdata residential rotating
- **Concurrency**: 20 subreddits + 10 users in parallel
- **Output**: Adds subreddits to Supabase queue, extracts creator profiles

**Run**:
```bash
cd scraper
python main.py --crawl --workers 3
```

### 2. Intel Worker (`intel-scraper/`)
Scrapes detailed subreddit intelligence using headless browser.
- **Proxy**: SOAX rotating mobile
- **Accounts**: 10 Reddit accounts for parallel scraping
- **Concurrency**: 10 browser contexts in parallel
- **Output**: Subreddit metrics (subscribers, rules, activity)

**Run**:
```bash
cd intel-scraper
python intel_worker.py
```

### 3. LLM Analyzer (`intel-scraper/`)
Analyzes subreddit rules and metadata with GPT-4o-mini.
- **Reddit API Proxy**: ProxyEmpire mobile
- **OpenAI API**: Direct connection (no proxy)
- **Concurrency**: 10 subreddits per batch
- **Output**: Structured analysis (verification, niche, seller policies)

**Run**:
```bash
cd intel-scraper
python run_llm_analysis.py --limit 100
```

## Configuration

All proxies are hardcoded in config files:
- **Crawler**: `scraper/config.py`
- **Intel/LLM**: `intel-scraper/config.py`

### Adding Reddit Accounts

Edit `intel-scraper/config.py` and add accounts to `REDDIT_ACCOUNTS` list:

```python
REDDIT_ACCOUNTS = [
    {
        "username": "reddit_account_1",
        "reddit_session": "eyJ...",  # JWT from browser
        "token_v2": "eyJ...",         # Auth token from browser
        "loid": "00000..."            # User ID from browser
    },
    # Add 9 more accounts...
]
```

**To extract cookies**:
1. Log into Reddit in browser
2. Open DevTools → Application → Cookies
3. Copy values for: `reddit_session`, `token_v2`, `loid`

### Environment Variables

Only required for sensitive keys:
```bash
export OPENAI_API_KEY="sk-..."  # For LLM analyzer
export SUPABASE_URL="https://..."
export SUPABASE_ANON_KEY="eyJ..."
```

## File Structure

```
redditscraper/
├── scraper/              # Crawler worker
│   ├── config.py         # Brightdata proxy config
│   ├── main.py           # Entry point
│   ├── crawler.py        # Subreddit discovery
│   ├── reddit_client.py  # HTTP client
│   └── supabase_client.py
│
├── intel-scraper/        # Intel + LLM workers
│   ├── config.py         # SOAX + ProxyEmpire config
│   ├── intel_worker.py   # Browser-based scraper
│   ├── llm_analyzer.py   # GPT-4o-mini analyzer
│   ├── run_llm_analysis.py # LLM worker entry
│   ├── stealth_browser.py
│   ├── account_manager.py # Reddit account pool
│   └── supabase_client.py
│
└── archive/              # Old config/test files
```

## Monitoring & Utilities

### Check System Status
```bash
python check_status.py
```
Shows queue state, intel coverage, and health status.

### Retry Failed Subreddits
```bash
python retry_failed.py
```
Marks failed subreddits as pending for retry.

### Full System Audit
See `SYSTEM_AUDIT.md` for detailed database analysis and action plan.

## Notes

- **Intel Worker**: Currently configured with 2 accounts, expand to 10 for full parallelism
- **Proxy Costs**: Brightdata ~$10/GB, SOAX session-based, ProxyEmpire mobile ~$X/GB
- **LLM Costs**: ~$0.0002 per subreddit analysis with GPT-4o-mini
- **No env files needed**: All proxies hardcoded for simplicity

## Archived Files

Old test scripts and alternative configs moved to `archive/`:
- `test_*.py` - Test scripts
- `config_*.py/sh` - Alternative configurations
- `convert_cookies.py` - Cookie conversion utilities
