# System Audit & Action Plan
**Date**: December 24, 2025

## ✅ Cleanup Completed

### Archived Files
Moved to `archive/` folder:
- **Old worker versions**: `intel_worker_fast.py`, `intel_worker_ultra.py`
- **Debug files**: All `debug_*.html/png` screenshots
- **Old configs**: `config_fast.py`, `config_ultra.py`, `config_proxyempire.sh`, `test_accounts_config.sh`
- **Test scripts**: `test_403_fix.py`, `test_freeuse.py`, `test_llm_analysis.py`, `test_llm_enhanced.py`, `test_reddit_api.py`
- **Utilities**: `convert_cookies.py`, `setup_accounts.py`, `reanalyze_all.py`, `force_rotate.py`
- **Old data**: `reddit_accounts.json`, `similarprofiles.json`, `profile_viewer.html`
- **Old docs**: `README_TESTING.md`, `INTEL_WORKER_FIXES.md`, `HARDCORE_CLASSIFIER_README.md`, `SETUP_HARDCORE_CLASSIFIER.md`, `PROXY_FIX_README.md`, `BRIGHTDATA_402_ERRORS.md`

### Current File Structure (Clean)
```
redditscraper/
├── scraper/              # Crawler worker (Brightdata proxy)
│   ├── config.py         # Hardcoded Brightdata config
│   ├── main.py
│   ├── crawler.py
│   ├── reddit_client.py
│   └── supabase_client.py
│
├── intel-scraper/        # Intel + LLM workers (SOAX + ProxyEmpire)
│   ├── config.py         # Hardcoded SOAX + ProxyEmpire config
│   ├── intel_worker.py   # Browser-based scraper
│   ├── llm_analyzer.py
│   ├── run_llm_analysis.py
│   ├── stealth_browser.py
│   ├── account_manager.py
│   └── supabase_client.py
│
├── frontend/             # Next.js dashboard (optional)
├── archive/              # Old files
└── README.md
```

---

## 📊 Current Database State

### 1. Subreddit Queue (`subreddit_queue`)
```
Total: 10,307 subreddits
├── ✅ Completed:  224 (2%)
├── ⏳ Pending:    9,732 (94%)
├── 🔄 Processing: 20
└── ❌ Failed:     331 (3%)
```

**Problem**: 94% of subreddits still pending - crawler not keeping up!

### 2. Intel Table (`nsfw_subreddit_intel`)
```
Total: 2,179 subreddits
├── ✅ With basic metrics:   2,176 (99%)
├── ✅ With content rating:  2,087 (95%)
├── ✅ With LLM analysis:    639 (29%)
└── ⚠️  Missing LLM:         1,540 (71%)
```

**Problem**: Most subreddits have basic intel but 71% still need LLM analysis!

### 3. Leads (`reddit_leads`)
```
Total: 7,565 OnlyFans creator profiles
```

### 4. Recent Errors
Most common error: **"No posts returned - subreddit may be empty or private"**
- These are likely banned/private subreddits that should be marked as failed

### 5. Top Subreddits (by subscribers)
1. r/gonewild: 5.2M | Verification required | Sellers allowed
2. r/nsfw: 4.4M | No verification | Sellers not allowed
3. r/cumsluts: 4.1M | No verification | Sellers allowed
4. r/hentai: 4.1M | No verification | Sellers allowed
5. r/realgirls: 4.1M | No verification | Sellers allowed

---

## 🔥 Current Problems

### 1. **Queue Bottleneck**
- **9,732 pending subreddits** not being processed
- Crawler is adding faster than intel worker can scrape
- You're constantly babysitting because workers aren't keeping up

### 2. **LLM Analysis Lagging**
- **1,540 subreddits (71%)** need LLM analysis
- This is the final enrichment step that's not keeping up

### 3. **Proxy Chaos**
- 3 different proxy providers (Brightdata, SOAX, ProxyEmpire)
- Different failure modes for each
- Hard to debug which proxy is causing issues

### 4. **Intel Worker Issues**
- Only 2 Reddit accounts configured (need 10 for full parallelism)
- SOAX proxy might be timing out
- Browser pool not fully utilized

### 5. **Failed Subreddits Not Retried**
- 331 failed subreddits just sitting there
- No automatic retry mechanism

---

## 🎯 Recommended Action Plan

### Immediate Actions (Today)

#### 1. **Add 8 More Reddit Accounts**
```bash
# Edit intel-scraper/config.py
# Add accounts 3-10 to REDDIT_ACCOUNTS list
```
**Impact**: 5x faster intel scraping (2 accounts → 10 accounts)

#### 2. **Test SOAX Proxy**
```bash
cd intel-scraper
python intel_worker.py
# Watch for timeouts - if many, SOAX might be blocked
```

#### 3. **Run LLM Analyzer on Backlog**
```bash
cd intel-scraper
python run_llm_analysis.py --limit 1000 --batch-size 20
# This will catch up on the 1,540 missing analyses
```

### Short Term (This Week)

#### 4. **Simplify to One Good Proxy**
**Option A**: Use SOAX for everything (if it's reliable)
- Change crawler to use SOAX
- Change LLM to use SOAX
- Drop Brightdata + ProxyEmpire

**Option B**: Use ProxyEmpire for everything
- Most reliable for mobile IPs
- Single provider = easier debugging

#### 5. **Add Auto-Retry for Failed Subreddits**
Create `retry_failed.py`:
```python
# Mark all "failed" as "pending" to retry
sb.client.table('subreddit_queue').update({'status': 'pending'}).eq('status', 'failed').execute()
```

#### 6. **Scale Up Workers**
Run multiple instances:
```bash
# Terminal 1: Crawler worker 1
cd scraper && python main.py --crawl --worker-id 1

# Terminal 2: Crawler worker 2
cd scraper && python main.py --crawl --worker-id 2

# Terminal 3: Intel worker
cd intel-scraper && python intel_worker.py

# Terminal 4: LLM analyzer (run periodically)
cd intel-scraper && python run_llm_analysis.py --limit 500
```

### Long Term

#### 7. **Deploy to Railway/Cloud**
- Auto-scaling workers
- No more local babysitting
- Set up monitoring/alerts

#### 8. **Database Cleanup**
- Delete truly failed subreddits (banned/private)
- Archive old data
- Optimize queries

---

## 📈 Success Metrics

### Current State
- Queue completion: **2%**
- Intel coverage: **21%** (2,179 / 10,307)
- LLM analysis: **6%** (639 / 10,307)
- Active workers: **1-2** (manual)

### Target State
- Queue completion: **>90%**
- Intel coverage: **>80%**
- LLM analysis: **>70%**
- Active workers: **5-10** (automated)

---

## 🚀 Quick Start Commands

### Check System Health
```bash
cd intel-scraper
python << 'EOF'
from supabase_client import SupabaseClient
sb = SupabaseClient()
pending = sb.client.table('subreddit_queue').select('id', count='exact').eq('status', 'pending').execute()
intel = sb.client.table('nsfw_subreddit_intel').select('id', count='exact').not_.is_('verification_required', 'null').execute()
print(f"Pending: {pending.count:,} | With LLM: {intel.count:,}")
EOF
```

### Process Queue
```bash
# Crawler (find new subreddits)
cd scraper && python main.py --crawl --workers 3

# Intel worker (scrape subreddit details)
cd intel-scraper && python intel_worker.py

# LLM analyzer (enrich with GPT analysis)
cd intel-scraper && python run_llm_analysis.py --limit 100
```

### Retry Failed Subreddits
```bash
cd intel-scraper
python << 'EOF'
from supabase_client import SupabaseClient
sb = SupabaseClient()
result = sb.client.table('subreddit_queue').update({'status': 'pending', 'error_message': None}).eq('status', 'failed').execute()
print(f"Marked {len(result.data)} failed subreddits for retry")
EOF
```

---

## 💡 Key Insight

**The real problem isn't the code - it's the workflow**:
1. Queue fills up faster than it's processed
2. Multiple proxies with different failure modes
3. Manual monitoring instead of automation
4. No retry logic for failures

**Fix**: Pick ONE reliable proxy, add more Reddit accounts, automate everything, deploy to cloud.

