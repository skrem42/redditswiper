# Reddit Scraper - Quick Start Guide

## 🚀 Getting Started

This system consists of 3 main workers that run simultaneously:

1. **Crawler** (3 instances) - Discovers NSFW subreddits via Reddit JSON API
2. **Intel Worker** (1 instance) - Scrapes detailed metrics using browser automation
3. **LLM Analyzer** (periodic) - Analyzes subreddits using GPT-4o-mini

All workers use **SOAX rotating proxies** (new IP per request).

---

## 📋 Prerequisites

### 1. Install Dependencies

```bash
# Python packages
pip install -r requirements.txt

# Playwright browsers (for intel worker)
playwright install chromium
```

### 2. Setup Reddit Accounts (for Intel Worker)

The intel worker needs Reddit account cookies to bypass NSFW age gates.

**You have 2 accounts configured. To add the remaining 8:**

1. Open browser, log into Reddit account
2. Go to Settings → Confirm you're 18+
3. Export cookies (use browser extension or DevTools)
4. Save cookies to `intel-scraper/redditaccounts.json`
5. Run the parser:

```bash
cd intel-scraper
python parse_accounts.py
```

6. Copy the output to `intel-scraper/config.py` → `REDDIT_ACCOUNTS` list

**Current status:**
- ✅ 2 accounts configured
- ⏳ 8 more accounts needed (recommended: 10 total for best performance)

---

## 🧪 Test SOAX Proxy

Before running the full system, verify SOAX proxy works:

```bash
python test_soax_proxy.py
```

This will test:
- ✅ Crawler (Reddit JSON API)
- ✅ LLM Analyzer (Reddit API)
- ✅ Intel Worker (Playwright browser)
- ✅ IP Rotation (verifies new IPs)

**Expected result:** All tests pass ✅

**If tests fail:**
- Check SOAX credentials in `scraper/config.py` and `intel-scraper/config.py`
- Verify SOAX account has sufficient balance
- Check network connection

---

## 🏃 Running the System

### Option 1: Run Everything Together (Recommended)

Start all workers with auto-restart and monitoring:

```bash
python run_all.py
```

This starts:
- **Crawler-1, Crawler-2, Crawler-3** (discover subreddits)
- **Intel-Worker** (scrape metrics)

**Features:**
- ✅ Auto-restart on crashes
- ✅ Consolidated logging
- ✅ Graceful shutdown (Ctrl+C)
- ✅ Status updates every 5 minutes

### Option 2: Run Workers Individually

**Crawler (Railway-compatible):**
```bash
cd scraper
python main.py --worker-id 1
```

**Intel Worker (local only):**
```bash
cd intel-scraper
python intel_worker.py
```

**LLM Analyzer (periodic batches):**
```bash
python run_llm_periodic.py --interval 30
```
- Runs every 30 minutes
- Processes 200 subreddits per batch
- 20 concurrent analyses

---

## 📊 Monitoring

### Quick Health Check

```bash
python monitor.py
```

Shows:
- 📋 Queue status (pending/completed/failed)
- 🔍 Intel scraper progress
- 🧠 LLM analysis backlog
- 👥 Leads count

### Continuous Monitoring

```bash
python monitor.py --watch
```

Updates every 30 seconds.

### Check Database Directly

```bash
cd intel-scraper
python supabase_client.py
```

---

## 💰 Data Usage Optimization

The system includes aggressive bandwidth optimization:

### Crawler
- Uses JSON API only (~1KB per subreddit)
- **Cost:** ~$1 per 10,000 subreddits

### Intel Worker (Optimized!)
- Tries JSON API first (free)
- Uses browser with resource blocking (blocks images/fonts/ads)
- Falls back to full rendering if needed
- **Cost:** ~$50 per 10,000 subreddits (80% savings!)

### LLM Analyzer  
- Uses JSON API only (~2KB per subreddit)
- **Cost:** ~$1 per 10,000 subreddits (proxy) + OpenAI API costs

### Total Expected Cost
- **10,000 subreddits:** ~$50-60 (SOAX) + ~$5-10 (OpenAI)
- **Compare to before:** ~$200+ (would have been without optimization)

---

## 🎯 Workflow

Here's how everything works together:

```
1. Crawlers discover NSFW subreddits
   ↓
2. Subreddits added to queue (Supabase)
   ↓
3. Intel worker scrapes metrics
   - Uses JSON API first (free)
   - Uses browser if needed (with blocking)
   - Saves to subreddit_intel table
   ↓
4. LLM analyzer runs periodically
   - Fetches recent posts (JSON API via SOAX)
   - Analyzes with GPT-4o-mini
   - Updates subreddit_intel with keywords/quality
   ↓
5. Qualified creators → reddit_leads table
```

---

## 🔧 Configuration

### Proxy Settings

All proxies are hardcoded in `config.py` files (no env vars needed):

**Crawler:** `scraper/config.py`
```python
PROXY_URL = "http://package-329587-..."  # SOAX
```

**Intel Worker:** `intel-scraper/config.py`
```python
PROXY_URL = "http://package-329587-..."  # SOAX
```

**LLM Analyzer:** `intel-scraper/config.py`
```python
LLM_REDDIT_PROXY = "http://package-329587-..."  # SOAX
```

### Concurrency Settings

**Crawler:** `scraper/config.py`
```python
CONCURRENT_SUBREDDITS = 20  # Process 20 subs in parallel
MAX_CONCURRENT_REQUESTS = 10  # Max HTTP requests at once
```

**Intel Worker:** `intel-scraper/config.py`
```python
BROWSER_POOL_SIZE = 10  # 10 browser contexts
CONCURRENT_SUBREDDITS = 10  # Process 10 subs in parallel
```

### Retry Settings

Both workers use exponential backoff:
- Max retries: 5
- Backoff: 2s, 4s, 8s, 16s, 30s
- Handles: 429, 403, 502, 503, 504, timeouts

---

## 🚨 Troubleshooting

### "No accounts loaded" (Intel Worker)

**Problem:** Intel worker can't find Reddit accounts

**Solution:**
1. Check `intel-scraper/redditaccounts.json` exists and has data
2. Run `cd intel-scraper && python parse_accounts.py`
3. Copy output to `intel-scraper/config.py`

### "Timeout 30000ms exceeded" (Intel Worker)

**Problem:** SOAX proxy is slow or blocked

**Solution:**
1. Increase timeout in `intel-scraper/config.py`:
   ```python
   PAGE_TIMEOUT_MS = 60000  # 60 seconds
   ```
2. Check SOAX balance/status
3. Retry - SOAX rotates IPs automatically

### "HTTP 429 Rate Limited"

**Problem:** Reddit is rate limiting

**Solution:**
- System will auto-retry with exponential backoff
- New IP will be used automatically (SOAX rotation)
- If persistent, reduce concurrency

### High Data Usage

**Problem:** SOAX charges are higher than expected

**Solution:**
1. Verify resource blocking is working:
   - Check logs for "🚫 Aggressive blocking enabled"
2. Reduce browser pool size:
   ```python
   BROWSER_POOL_SIZE = 5  # Use fewer browsers
   ```
3. Skip intel scraper for non-priority subs

---

## 📈 Performance Expectations

With current setup (SOAX + optimizations):

| Worker | Speed | Daily Capacity |
|--------|-------|----------------|
| Crawler (3x) | ~500-1000/hour | ~10,000-15,000 |
| Intel Worker | ~50-100/hour | ~1,000-2,000 |
| LLM Analyzer | ~100-200/hour | ~2,000-4,000 |

**Bottleneck:** Intel worker (browser-based, slower)

**To speed up Intel Worker:**
- Add more Reddit accounts (up to 10)
- Increase `BROWSER_POOL_SIZE` (if you have accounts)
- Use multiple machines (run locally on each)

---

## 🎬 Ready to Run?

1. ✅ Test proxy: `python test_soax_proxy.py`
2. ✅ Add Reddit accounts (optional but recommended)
3. 🚀 Start system: `python run_all.py`
4. 📊 Monitor: `python monitor.py --watch`

**Let it run overnight!**

The system will:
- Auto-restart on crashes
- Rotate IPs automatically
- Optimize bandwidth usage
- Save data to Supabase

Check back in the morning and run `python monitor.py` to see progress!

---

## 📞 Need Help?

- **Logs:** Workers print detailed logs (look for ⚠️ or ❌)
- **Database:** Run `monitor.py` to check queue/intel/leads
- **Errors:** All errors include retry logic - most resolve automatically

**Common Issues:**
- **Slow scraping:** Check SOAX balance, reduce concurrency
- **High costs:** Verify resource blocking is enabled
- **No progress:** Check if workers are running (`ps aux | grep python`)

