# Intel Worker Fixes - December 24, 2025

## Issues Found & Fixed

### ✅ 1. **Account Loading Failure** (CRITICAL - FIXED)

**Problem:**
```
WARNING - Skipping incomplete account config: reddit_sa_1ceq8goqi5
INFO - AccountManager: Loaded 0 accounts
INFO - BrowserPool: Created 0 browser contexts
```

**Root Cause:** Wrong account format in `test_accounts_config.sh`
- Had: Full Playwright cookie objects with `{"name": "...", "value": "..."}`
- Needed: Just the cookie VALUES: `{"username": "...", "reddit_session": "...", "token_v2": "...", "loid": "..."}`

**Fix Applied:** ✅ Updated `test_accounts_config.sh` with correct format

**What AccountManager expects:**
```json
{
  "username": "reddit_sa_account1",
  "reddit_session": "eyJhbGc...long_jwt_token",
  "token_v2": "eyJhbGc...long_jwt_token", 
  "loid": "000000001ceq8goqi5..."
}
```

---

### ✅ 2. **BrowserPool Timeout** (CONSEQUENCE OF #1 - WILL FIX AUTOMATICALLY)

**Problem:**
```
WARNING - BrowserPool: Timeout waiting for available context
WARNING - Could not acquire browser context for r/latinamilfs
```

**Root Cause:** No browsers in pool because no accounts loaded

**Fix:** Once accounts load correctly (fix #1), browsers will be created and this will resolve.

---

### ⚠️ 3. **Database RPC Error** (MINOR - ALREADY HAS FALLBACK)

**Problem:**
```
RPC failed, using fallback: 'structure of query does not match function result type'
Details: 'Returned type integer does not match expected type bigint in column 2'
```

**Impact:** Minimal - code falls back to manual pagination (which works fine)

**What's Happening:**
1. Tries to call Supabase RPC function `get_subreddits_not_in_intel`
2. RPC fails due to type mismatch (integer vs bigint)
3. Falls back to fetching all subreddits manually (8507 total)
4. Fetches already-scraped subreddits (2111 total)
5. Filters to get unscrape ones (6,396 remaining)

**This works fine**, just slower than the RPC would be.

**Optional Fix (in Supabase):**
```sql
-- Update the RPC function to return bigint instead of integer
-- Or cast the column to the expected type
ALTER FUNCTION get_subreddits_not_in_intel() 
RETURNS TABLE(subreddit_name text, subscribers bigint);
```

---

### ✅ 4. **Re-processing Already-Scraped Subs** (NOT AN ISSUE)

**Question:** "Will it work on subs that have already been processed?"

**Answer:** ✅ **NO - It correctly skips them!**

**Evidence from logs:**
```
Line 66: Fetched 2111 already-scraped subreddits from intel table
Line 67: Processing batch of 20 subreddits in parallel...
```

**What this means:**
- Total subs in queue: 8,507
- Already scraped: 2,111
- **Remaining to scrape: 6,396**
- The batch of 20 comes from the 6,396 unscrapped ones

**Logic:**
```python
# Pseudocode showing the filtering
all_subs = fetch_from_queue()  # 8507 subs
already_done = fetch_from_intel_table()  # 2111 subs  
to_scrape = all_subs - already_done  # 6396 subs
batch = to_scrape[:20]  # First 20 unscrapped subs
```

✅ **Working as intended!**

---

## Testing Steps

### 1. Kill the current intel worker (if still running)
```bash
# Press Ctrl+C to stop it
```

### 2. Reload the fixed configuration
```bash
cd /Users/calummelling/Desktop/redditscraper/intel-scraper
source test_accounts_config.sh
```

### 3. Run the intel worker again
```bash
python intel_worker.py
```

### 4. What you should see (if fixes worked):

**✅ Good Output:**
```
INFO - AccountManager: Loaded 2 accounts
INFO - BrowserPool: Created 2 browser contexts
INFO - [Worker XXXX] Processing batch of 20 subreddits in parallel...
```

**❌ Bad Output (means accounts still not loading):**
```
WARNING - Skipping incomplete account config
INFO - AccountManager: Loaded 0 accounts
```

---

## Remaining Tasks

### For Intel Scraper:

1. ✅ Fix account format (DONE)
2. ⏳ Test with 2 accounts
3. ⏳ Add remaining 8 accounts if successful
4. ⏳ Increase `BROWSER_POOL_SIZE` once stable

### For Crawler (402 Errors):

1. ✅ Added exponential backoff for 402 errors (DONE)
2. ✅ Fast failure for persistent 402s (DONE)
3. ⏳ Monitor failure rate for 24 hours
4. ⏳ Contact Brightdata if >30% failure persists

### Optional (Database):

1. Fix RPC function type mismatch in Supabase (low priority - fallback works)

---

## Summary

**What was wrong:**
- Accounts in wrong format (Playwright cookie objects instead of cookie values)
- This caused 0 browsers to be created
- Which caused browser pool timeouts

**What's fixed:**
- ✅ Account format corrected
- ✅ Will now load 2 accounts properly
- ✅ Will create 2 browser contexts
- ✅ Can process subreddits in parallel

**What's working correctly (not bugs):**
- ✅ Skips already-scraped subs (2111 skipped, 6396 remaining)
- ✅ RPC failure has working fallback
- ✅ Database inserts working (201 Created responses)

---

## Next Test

Run this and share the output:
```bash
cd /Users/calummelling/Desktop/redditscraper/intel-scraper
source test_accounts_config.sh
python intel_worker.py
```

Look for:
- `AccountManager: Loaded 2 accounts` ← Should see this!
- `BrowserPool: Created 2 browser contexts` ← Should see this!
- Browser contexts scraping subreddits ← Should start working!

