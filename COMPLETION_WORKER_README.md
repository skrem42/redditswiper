# Completion Worker

A slow, synchronous worker that ensures **every** subreddit in your database has complete data.

## What It Does

The Completion Worker systematically goes through your `nsfw_subreddit_intel` table and fills in any missing:

1. **Subscribers** - Via Reddit JSON API
2. **Competition Metrics** - Weekly visitors and contributions via Playwright
3. **LLM Analysis** - Verification requirements, seller policies, and niche categories

## Features

- ✅ **Slow & Steady** - 10 second delay between subreddits (configurable)
- ✅ **Synchronous** - Processes one subreddit at a time
- ✅ **Resumable** - Always picks up where it left off
- ✅ **ProxyEmpire Mobile Proxy** - Uses your ProxyEmpire mobile proxy for maximum reliability
- ✅ **Smart Priority** - Processes most popular subreddits first
- ✅ **Detailed Logging** - Shows exactly what's being added
- ✅ **Progress Stats** - Checkpoints every 50 subreddits

## Setup

### 1. Configure ProxyEmpire

The completion worker is already configured with your ProxyEmpire credentials:

```python
PROXYEMPIRE_HOST = "mobdedi.proxyempire.io"
PROXYEMPIRE_PORT = 9000
PROXYEMPIRE_USERNAME = "2ed80b8624"
PROXYEMPIRE_PASSWORD = "570abb9a59"
```

It also uses your single Reddit account session. No further configuration needed!

### 2. (Optional) Adjust Settings

You can modify these settings in the file:

```python
DELAY_BETWEEN_SUBS = 10  # Seconds between each subreddit (increase for slower)
BATCH_SIZE = 10  # How many to check at once
CHECKPOINT_EVERY = 50  # Log progress every N subreddits
```

## Running the Worker

### Option 1: Using the Shell Script (Recommended)

```bash
chmod +x run_completion_worker.sh
./run_completion_worker.sh
```

This will:
- Activate your virtual environment
- Run the worker
- Log output to `completion_worker.log` and console

### Option 2: Running Directly

```bash
source venv/bin/activate
python intel-scraper/completion_worker.py
```

### Option 3: Running in Background

```bash
nohup ./run_completion_worker.sh > completion_worker.log 2>&1 &
echo $! > completion_worker.pid

# To stop:
kill $(cat completion_worker.pid)
```

## What You'll See

```
================================================================================
COMPLETION WORKER STARTING
  Proxy: ProxyEmpire (mobdedi.proxyempire.io:9000)
  Account: Reddit account (t2_1qidpn3ev6)
  Delay: 10s between subreddits
================================================================================

📋 Processing batch of 10 incomplete subreddits...

Processing r/gonewild...
  Fetching subscribers...
  ✓ Subscribers: 4,123,456
  Fetching competition metrics...
  ✓ Competition: 125,000 visitors, 850 posts
  Running LLM analysis...
  ✓ LLM: verification=True, sellers=False
✅ r/gonewild updated with 7 fields
⏳ Waiting 10s...

Processing r/OnlyFans101...
  Fetching subscribers...
  ✓ Subscribers: 523,000
...
```

### Progress Checkpoints

Every 50 subreddits, you'll see:

```
================================================================================
📊 COMPLETION STATS
  Processed:        50
  Subscribers:      +12
  Competition:      +18
  LLM Analysis:     +25
  Errors:           2
  Runtime:          1.2h
  Rate:             41.7 subs/hr
================================================================================
```

## How It Works

1. **Query Database** - Fetches 10 subreddits missing any data (prioritized by subscriber count)
2. **Check Each Field** - For each subreddit, checks what's missing:
   - If subscribers missing → Fetch via JSON API
   - If competition metrics missing → Scrape via Playwright
   - If LLM analysis missing → Analyze with GPT-4
3. **Save Updates** - Saves all collected data to database
4. **Wait & Repeat** - Waits 10 seconds, then moves to next subreddit
5. **Complete** - When all subreddits have complete data, worker stops automatically

## Monitoring

### Check Current Status

While the worker is running in another terminal:

```bash
tail -f completion_worker.log
```

### Check Database Progress

```bash
python check_status.py
```

This shows how many subreddits are "fully ready" with all data.

## Error Handling

- **HTTP 403/429** - Worker automatically rotates accounts and continues
- **Timeout** - Skips the problematic field and continues
- **Missing Data** - Will retry on next batch
- **Subreddit Deleted** - Marks as complete with null values

## Performance

At **10 seconds per subreddit**:
- ~6 subreddits per minute
- ~360 subreddits per hour
- ~8,640 subreddits per day

To process faster, reduce `DELAY_BETWEEN_SUBS` in the config (not recommended if using free proxies).

## Stopping the Worker

Press `Ctrl+C` in the terminal, or if running in background:

```bash
pkill -f completion_worker.py
```

The worker is **resumable** - it will pick up exactly where it left off when you restart it.

## Tips

1. **Run Overnight** - Let it run for hours/days in the background
2. **Monitor Logs** - Check `completion_worker.log` periodically
3. **Check Database** - Use `check_status.py` to see progress
4. **Adjust Speed** - Increase `DELAY_BETWEEN_SUBS` if you get rate limited
5. **Parallel Workers** - Can run alongside your main scrapers

## Troubleshooting

### "Please configure ProxyEmpire credentials"

The worker is already pre-configured with your ProxyEmpire credentials.

### Rate Limited (HTTP 429)

Increase `DELAY_BETWEEN_SUBS` to 15-20 seconds.

### Connection Errors

Check that your ProxyEmpire proxy is working:

```bash
curl -x http://2ed80b8624:570abb9a59@mobdedi.proxyempire.io:9000 https://ipinfo.io
```

### Worker Stops with Errors

Check `completion_worker.log` for details. Worker automatically retries on next run.

## Integration with Main Scrapers

The Completion Worker is designed to run **alongside** your main scrapers:

- **Main Scrapers** - Fast, high-volume, fills in new subreddits
- **Completion Worker** - Slow, thorough, fills in gaps and missing data

They work together to ensure 100% data completeness.

