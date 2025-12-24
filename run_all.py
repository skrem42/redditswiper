#!/usr/bin/env python3
"""
Main Orchestration Script - Run All Workers
===========================================

Runs crawler, intel worker, and LLM analyzer simultaneously with monitoring.

Workers:
- Crawler: Discovers subreddits (SOAX proxy)
- Intel Worker: Scrapes subreddit details (SOAX proxy + browser pool)
- LLM Analyzer: Analyzes subreddit content (SOAX for Reddit, direct for OpenAI)

Usage:
    python run_all.py              # Run all workers
    python run_all.py --crawler    # Run only crawler
    python run_all.py --intel      # Run only intel worker
    python run_all.py --llm        # Run only LLM analyzer
"""

import asyncio
import sys
import signal
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('run_all.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class WorkerManager:
    """Manages multiple worker processes with health monitoring."""
    
    def __init__(self):
        self.processes = {}
        self.should_stop = False
        
    async def start_worker(self, name: str, cmd: list[str], cwd: str = None) -> asyncio.subprocess.Process:
        """Start a worker process."""
        try:
            logger.info(f"🚀 Starting {name}...")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            # Start output monitoring tasks
            asyncio.create_task(self._monitor_output(name, process.stdout, "INFO"))
            asyncio.create_task(self._monitor_output(name, process.stderr, "ERROR"))
            
            self.processes[name] = process
            logger.info(f"✅ {name} started (PID: {process.pid})")
            return process
            
        except Exception as e:
            logger.error(f"❌ Failed to start {name}: {e}")
            return None
    
    async def _monitor_output(self, name: str, stream, level: str):
        """Monitor and log worker output."""
        try:
            while not self.should_stop:
                line = await stream.readline()
                if not line:
                    break
                    
                line_text = line.decode().strip()
                if line_text:
                    if level == "ERROR":
                        logger.error(f"[{name}] {line_text}")
                    else:
                        logger.info(f"[{name}] {line_text}")
        except Exception as e:
            logger.error(f"Output monitoring error for {name}: {e}")
    
    async def check_health(self):
        """Check health of all workers and restart if needed."""
        while not self.should_stop:
            await asyncio.sleep(30)  # Check every 30 seconds
            
            for name, process in list(self.processes.items()):
                if process.returncode is not None:
                    logger.warning(f"⚠️ {name} exited with code {process.returncode}")
                    
                    # Restart worker
                    logger.info(f"🔄 Restarting {name}...")
                    await self._restart_worker(name)
    
    async def _restart_worker(self, name: str):
        """Restart a failed worker."""
        try:
            if name == "Crawler":
                await self.start_worker(
                    "Crawler",
                    ["python", "main.py"],
                    cwd=str(Path(__file__).parent / "scraper")
                )
            elif name == "Intel JSON":
                await self.start_worker(
                    "Intel JSON",
                    ["python", "intel_worker_json.py"],
                    cwd=str(Path(__file__).parent / "intel-scraper")
                )
            elif name == "Intel Competition":
                await self.start_worker(
                    "Intel Competition",
                    ["python", "intel_worker_hybrid.py"],
                    cwd=str(Path(__file__).parent / "intel-scraper")
                )
            elif name == "LLM Analyzer":
                await self.start_worker(
                    "LLM Analyzer",
                    ["python", "run_llm_periodic.py"],
                    cwd=str(Path(__file__).parent / "intel-scraper")
                )
        except Exception as e:
            logger.error(f"Failed to restart {name}: {e}")
    
    async def stop_all(self):
        """Stop all workers gracefully."""
        logger.info("🛑 Stopping all workers...")
        self.should_stop = True
        
        for name, process in self.processes.items():
            try:
                logger.info(f"Stopping {name}...")
                process.terminate()
                
                # Wait up to 10 seconds for graceful shutdown
                try:
                    await asyncio.wait_for(process.wait(), timeout=10.0)
                    logger.info(f"✅ {name} stopped gracefully")
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️ {name} did not stop gracefully, forcing...")
                    process.kill()
                    await process.wait()
                    logger.info(f"✅ {name} force killed")
                    
            except Exception as e:
                logger.error(f"Error stopping {name}: {e}")
    
    async def run(self, run_crawler: bool = True, run_intel: bool = True, run_llm: bool = True):
        """Run selected workers."""
        logger.info("="*80)
        logger.info("Reddit Scraper - Master Orchestrator")
        logger.info("="*80)
        logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Workers: Crawler={run_crawler}, Intel={run_intel}, LLM={run_llm}")
        logger.info("="*80)
        
        base_path = Path(__file__).parent
        
        try:
            # Start selected workers
            if run_crawler:
                await self.start_worker(
                    "Crawler",
                    ["python", "main.py"],
                    cwd=str(base_path / "scraper")
                )
                await asyncio.sleep(2)  # Stagger starts
            
            if run_intel:
                # Run both workers:
                # 1. JSON worker for fast basic data (subscribers)
                # 2. Hybrid worker for competition metrics (slower but gets weekly stats)
                await self.start_worker(
                    "Intel JSON",
                    ["python", "intel_worker_json.py"],
                    cwd=str(base_path / "intel-scraper")
                )
                await asyncio.sleep(2)
                
                await self.start_worker(
                    "Intel Competition",
                    ["python", "intel_worker_hybrid.py"],
                    cwd=str(base_path / "intel-scraper")
                )
                await asyncio.sleep(2)
            
            if run_llm:
                await self.start_worker(
                    "LLM Analyzer",
                    ["python", "run_llm_periodic.py"],
                    cwd=str(base_path / "intel-scraper")
                )
            
            # Start health monitoring
            health_task = asyncio.create_task(self.check_health())
            
            # Wait for processes
            logger.info("✅ All workers started. Press Ctrl+C to stop.")
            logger.info("="*80)
            
            # Wait for all processes to complete (or Ctrl+C)
            await asyncio.gather(
                *[p.wait() for p in self.processes.values()],
                return_exceptions=True
            )
            
        except KeyboardInterrupt:
            logger.info("\n⚠️ Keyboard interrupt received")
        except Exception as e:
            logger.error(f"❌ Error: {e}")
        finally:
            await self.stop_all()
            logger.info(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("="*80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Reddit scraper workers")
    parser.add_argument("--crawler", action="store_true", help="Run only crawler")
    parser.add_argument("--intel", action="store_true", help="Run only intel worker")
    parser.add_argument("--llm", action="store_true", help="Run only LLM analyzer")
    
    args = parser.parse_args()
    
    # If no specific workers selected, run all
    if not any([args.crawler, args.intel, args.llm]):
        run_crawler = run_intel = run_llm = True
    else:
        run_crawler = args.crawler
        run_intel = args.intel
        run_llm = args.llm
    
    # Setup signal handlers
    manager = WorkerManager()
    
    def signal_handler(sig, frame):
        logger.info(f"\n⚠️ Signal {sig} received")
        asyncio.create_task(manager.stop_all())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run
    try:
        asyncio.run(manager.run(run_crawler, run_intel, run_llm))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
