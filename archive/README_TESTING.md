# Intel Scraper Testing with SA Reddit Accounts

## ✅ What's Been Set Up

1. **Proxy Configuration**: Updated `config.py` to support country-specific proxies (South Africa)
2. **Reddit Accounts**: Converted your 10 SA Reddit accounts to Playwright cookie format
3. **Test Configuration**: Created `test_accounts_config.sh` with 2 accounts for initial testing

## 🚀 How to Test

### 1. Add Your Brightdata Proxy Credentials

Edit `test_accounts_config.sh` and uncomment/update this line:

```bash
export BRIGHTDATA_PROXY=http://brd-customer-hl_xxxxx-zone-residential:password@brd.superproxy.io:22225
```

Replace with your actual Brightdata credentials.

### 2. Load the Test Configuration

```bash
cd /Users/calummelling/Desktop/redditscraper/intel-scraper
source test_accounts_config.sh
```

This will set:
- `PROXY_COUNTRY=sa` (routes through South Africa)
- `REDDIT_ACCOUNTS` (2 accounts with full session cookies)
- `BROWSER_POOL_SIZE=2` (2 parallel browsers)
- Other settings (Supabase, delays, etc.)

### 3. Run the Intel Scraper

```bash
python intel_worker.py
```

## 🔍 What Will Happen

- The scraper will initialize 2 browser instances
- Each browser will load one of your SA Reddit accounts' cookies
- Proxies will route through South Africa (matching your account IPs)
- Browsers will scrape subreddits in parallel with NSFW access

## 📊 Expected Behavior

✅ **Success indicators:**
- Browser instances start without SSL errors
- NSFW age gates are bypassed (session cookies work)
- Multiple subreddits processed simultaneously  
- Proxy routes through SA

⚠️ **Potential issues:**
- `402 Residential Failed` errors: Check your Brightdata credit/settings
- NSFW blocked: Cookies may have expired (re-export from browser)
- Slow performance: Increase `BROWSER_POOL_SIZE` and `CONCURRENT_SUBREDDITS`

## 📝 Configuration Details

### Current Settings (test_accounts_config.sh):
- **Accounts**: 2 of 10 (for initial testing)
- **Browser Pool**: 2 parallel browsers
- **Concurrent Subreddits**: 2 at a time
- **Proxy Country**: SA (South Africa)
- **Delays**: 1-3 seconds between requests

### To Scale Up:

1. **Add more accounts**: Edit `REDDIT_ACCOUNTS` JSON in `test_accounts_config.sh`
2. **Increase parallelism**: 
   ```bash
   export BROWSER_POOL_SIZE=5
   export CONCURRENT_SUBREDDITS=10
   ```
3. **Run on Railway**: Set all these as environment variables

## 🛠️ Troubleshooting

### SSL Certificate Errors
Fixed! The crawler now uses `verify=False` for Brightdata MITM proxies.

### NSFW Age Gate Still Appearing
Your cookies might have expired. To refresh:
1. Log into Reddit in a browser
2. Export cookies again (using EditThisCookie or similar)
3. Run `python convert_cookies.py` to convert them
4. Update `REDDIT_ACCOUNTS` in your config

### 402 Proxy Errors
- Check Brightdata dashboard for:
  - Account balance/credits
  - Zone configuration (residential enabled?)
  - Country availability (SA supported?)

### Slow Scraping
Increase parallelism gradually:
```bash
export BROWSER_POOL_SIZE=5  # 5 browsers
export CONCURRENT_SUBREDDITS=10  # 10 subreddits at once
```

## 📌 Next Steps

1. ✅ Test with 2 accounts (done - use `test_accounts_config.sh`)
2. ⏳ Add remaining 8 accounts to config
3. ⏳ Set up Brightdata proxy credentials
4. ⏳ Deploy to Railway with all environment variables
5. ⏳ Monitor performance and adjust `BROWSER_POOL_SIZE`/`CONCURRENT_SUBREDDITS`

## 🎯 Files Created/Modified

- `config.py`: Added `PROXY_COUNTRY` support
- `test_accounts_config.sh`: Test configuration with 2 accounts
- `convert_cookies.py`: Tool to convert browser cookies to Playwright format
- `reddit_accounts.json`: Output from cookie conversion

## 💡 Tips

- Start small (2-3 browsers) and scale up
- Monitor Brightdata costs ($10/GB for residential)
- SA proxies ensure cookies work (same geolocation)
- Each browser gets its own Reddit account (no session conflicts)

