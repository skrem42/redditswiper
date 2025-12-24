#!/usr/bin/env python3
"""
Periodic LLM Analyzer Runner

Runs LLM analysis in batches every 30 minutes to process the backlog
of subreddits that have been scraped but not yet analyzed.

Features:
- Runs in background
- Automatic batching (200 subreddits per run, 20 concurrent)
- Skips already-analyzed subreddits
- Error handling and auto-retry
- Status reporting
"""
import asyncio
import subprocess
import sys
import signal
from datetime import datetime
from pathlib import Path

class LLMPeriodicRunner:
    """Manages periodic LLM analysis runs."""
    
    def __init__(
        self, 
        interval_minutes: int = 30,
        batch_limit: int = 200,
        concurrent: int = 20
    ):
        self.interval_minutes = interval_minutes
        self.batch_limit = batch_limit
        self.concurrent = concurrent
        self.project_root = Path(__file__).parent
        self.intel_dir = self.project_root / "intel-scraper"
        self.running = True
        self.run_count = 0
        self.total_analyzed = 0
    
    async def run_batch(self):
        """Run a single LLM analysis batch."""
        self.run_count += 1
        start_time = datetime.now()
        
        print()
        print("=" * 70)
        print(f"🧠 LLM ANALYSIS BATCH #{self.run_count}")
        print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        print()
        print(f"  Limit: {self.batch_limit} subreddits")
        print(f"  Concurrent: {self.concurrent} at a time")
        print(f"  Proxy: SOAX (for Reddit API calls)")
        print()
        
        try:
            # Run the LLM analysis script
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "run_llm_analysis.py",
                "--limit", str(self.batch_limit),
                "--batch-size", str(self.concurrent),
                "--skip-existing",  # Only analyze new subreddits
                cwd=self.intel_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )
            
            # Stream output
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                print(line.decode('utf-8', errors='replace').rstrip())
            
            # Wait for completion
            await process.wait()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print()
            print("=" * 70)
            
            if process.returncode == 0:
                print(f"✅ LLM Batch #{self.run_count} completed successfully")
                print(f"   Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
            else:
                print(f"⚠️  LLM Batch #{self.run_count} failed")
                print(f"   Exit code: {process.returncode}")
                print(f"   Duration: {duration:.1f}s")
            
            print("=" * 70)
            print()
            
            return process.returncode == 0
            
        except Exception as e:
            print()
            print(f"❌ Error running LLM batch: {e}")
            print()
            return False
    
    async def run_forever(self):
        """Run LLM analysis batches periodically."""
        print("=" * 70)
        print("PERIODIC LLM ANALYZER")
        print("=" * 70)
        print()
        print(f"Interval: Every {self.interval_minutes} minutes")
        print(f"Batch size: {self.batch_limit} subreddits")
        print(f"Concurrency: {self.concurrent} simultaneous")
        print()
        print("💡 Press Ctrl+C to stop")
        print()
        
        while self.running:
            # Run a batch
            success = await self.run_batch()
            
            if not success:
                print("⚠️  Batch failed, will retry next interval")
            
            # Wait for next interval
            next_run = datetime.now()
            next_run = next_run.replace(
                minute=(next_run.minute + self.interval_minutes) % 60,
                second=0,
                microsecond=0
            )
            
            wait_seconds = (next_run - datetime.now()).total_seconds()
            if wait_seconds < 0:
                wait_seconds = self.interval_minutes * 60
            
            print(f"⏳ Next LLM batch in {wait_seconds/60:.1f} minutes "
                  f"(at {next_run.strftime('%H:%M')})")
            print()
            
            # Sleep with periodic checks for shutdown
            slept = 0
            while slept < wait_seconds and self.running:
                await asyncio.sleep(min(10, wait_seconds - slept))
                slept += 10
    
    def stop(self):
        """Stop the periodic runner."""
        self.running = False
        print()
        print("🛑 Stopping periodic LLM analyzer...")


async def main():
    """Main entry point."""
    # Parse command line args
    import argparse
    parser = argparse.ArgumentParser(description="Periodic LLM Analysis Runner")
    parser.add_argument("--interval", type=int, default=30,
                       help="Minutes between batches (default: 30)")
    parser.add_argument("--limit", type=int, default=200,
                       help="Subreddits per batch (default: 200)")
    parser.add_argument("--concurrent", type=int, default=20,
                       help="Concurrent analyses (default: 20)")
    args = parser.parse_args()
    
    # Create runner
    runner = LLMPeriodicRunner(
        interval_minutes=args.interval,
        batch_limit=args.limit,
        concurrent=args.concurrent
    )
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        print()
        print(f"⚠️  Received signal {signum}")
        runner.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await runner.run_forever()
    except KeyboardInterrupt:
        print()
        print("⚠️  Keyboard interrupt")
    finally:
        runner.stop()
        print()
        print("=" * 70)
        print("✅ PERIODIC LLM ANALYZER STOPPED")
        print("=" * 70)
        print(f"Total batches run: {runner.run_count}")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print()
        print("👋 Goodbye!")
        sys.exit(0)

