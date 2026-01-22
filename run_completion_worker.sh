#!/bin/bash
# Run the Completion Worker
# This worker slowly fills in all missing data for subreddits

cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Run completion worker
echo "Starting Completion Worker..."
echo "This will run slowly and carefully fill in all missing subreddit data."
echo "Press Ctrl+C to stop."
echo ""

python intel-scraper/completion_worker.py 2>&1 | tee completion_worker.log







