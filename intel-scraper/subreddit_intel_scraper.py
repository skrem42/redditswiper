"""
Subreddit Intelligence Scraper

Extracts detailed metrics from subreddit pages using Playwright with stealth mode.
Captures weekly visitors, weekly contributions, rules, and other metadata.
"""
import asyncio
import re
import logging
from typing import Optional
from datetime import datetime
import httpx

from stealth_browser import StealthBrowser
from supabase_client import SupabaseClient
from config import DELAY_MIN, DELAY_MAX, ROTATE_EVERY

logger = logging.getLogger(__name__)

# Import LLM analyzer for optional analysis
try:
    from llm_analyzer import SubredditLLMAnalyzer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM analyzer not available - install openai package to enable")


def parse_metric_value(text: str) -> Optional[int]:
    """
    Parse Reddit's formatted metric values (e.g., '559K', '2.2M', '1,234').
    Returns the numeric value or None if parsing fails.
    """
    if not text:
        return None
    
    text = text.strip().upper().replace(",", "")
    
    try:
        # Handle K (thousands)
        if "K" in text:
            num = float(text.replace("K", ""))
            return int(num * 1000)
        # Handle M (millions)
        elif "M" in text:
            num = float(text.replace("M", ""))
            return int(num * 1000000)
        # Handle B (billions)
        elif "B" in text:
            num = float(text.replace("B", ""))
            return int(num * 1000000000)
        else:
            return int(float(text))
    except (ValueError, TypeError):
        return None


class SubredditIntelScraper:
    """
    Scrapes detailed intelligence data from subreddit pages.
    
    Extracts:
    - Weekly visitors and contributions (new Reddit metrics)
    - Subscriber count
    - Community rules and requirements
    - Moderator count
    - Media permissions (images, videos, polls)
    - Community age
    """
    
    def __init__(
        self,
        supabase_client: SupabaseClient,
        worker_id: int = None,
        proxy_url: str = None,
        headless: bool = False,
        ultra_fast: bool = False,  # Skip artificial delays for max speed
        enable_llm: bool = True,  # Enable LLM analysis after scraping
        use_session_cookies: bool = True,  # Use hardcoded Reddit session cookies
    ):
        self.supabase = supabase_client
        self.worker_id = worker_id
        self.proxy_url = proxy_url
        self.headless = headless
        self.ultra_fast = ultra_fast
        self.enable_llm = enable_llm and LLM_AVAILABLE
        self.use_session_cookies = use_session_cookies
        
        self.browser: Optional[StealthBrowser] = None
        
        # Initialize LLM analyzer if available and enabled
        if self.enable_llm:
            self.llm_analyzer = SubredditLLMAnalyzer()
            logger.info(f"[Worker {worker_id}] LLM analysis enabled")
        else:
            self.llm_analyzer = None
            if enable_llm and not LLM_AVAILABLE:
                logger.warning(f"[Worker {worker_id}] LLM requested but not available")
        
        self.stats = {
            "subreddits_scraped": 0,
            "successful": 0,
            "failed": 0,
            "ip_rotations": 0,
            "llm_analyzed": 0,
        }
    
    async def start(self):
        """Initialize the stealth browser and login to Reddit."""
        self.browser = StealthBrowser(
            proxy_url=self.proxy_url,
            worker_id=self.worker_id,
            headless=self.headless,
            use_session_cookies=self.use_session_cookies,
        )
        await self.browser.start()
        
        # Session cookies are set in stealth_browser.py - no login needed
        logger.info(f"[Worker {self.worker_id}] Using Reddit session cookies")
    
    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def scrape_subreddit(self, subreddit_name: str) -> Optional[dict]:
        """
        Scrape intelligence data from a single subreddit.
        
        Args:
            subreddit_name: Name of the subreddit (without r/)
            
        Returns:
            Dict with scraped data or None if failed
        """
        url = f"https://www.reddit.com/r/{subreddit_name}"
        logger.info(f"[Worker {self.worker_id}] Scraping r/{subreddit_name}...")
        
        try:
            # Navigate with retry logic
            success = await self.browser.goto_with_retry(url)
            if not success:
                logger.error(f"[Worker {self.worker_id}] Failed to load r/{subreddit_name}")
                return None
            
            page = self.browser.page
            
            # Handle NSFW consent dialogs
            await self.browser.handle_nsfw_consent()
            
            if not self.ultra_fast:
                # Human-like behavior (skipped in ultra-fast mode)
                try:
                    await asyncio.sleep(1)
                    await self.browser.move_mouse_randomly()
                    await self.browser.human_delay(2.0, 3.0)
                except Exception as e:
                    logger.debug(f"Mouse movement skipped: {e}")
            
            # Wait for content to hydrate
            content_selectors = [
                'shreddit-post',
                '[data-testid="post-container"]',
                'article',
            ]
            for sel in content_selectors:
                try:
                    timeout = 5000 if self.ultra_fast else 10000
                    await page.wait_for_selector(sel, timeout=timeout)
                    break
                except:
                    continue
            
            # Scroll to trigger lazy loading
            await page.evaluate('window.scrollTo(0, 500)')
            if not self.ultra_fast:
                await asyncio.sleep(2)
            else:
                await asyncio.sleep(0.5)  # Minimal wait for lazy load
            await page.evaluate('window.scrollTo(0, 0)')
            if not self.ultra_fast:
                await asyncio.sleep(3)
            else:
                await asyncio.sleep(1)  # Just wait for content to settle
            
            # Debug: Check what HTML we're getting
            html_content = await page.content()
            html_length = len(html_content)
            has_shreddit = "shreddit" in html_content.lower()
            has_posts = "shreddit-post" in html_content.lower()
            has_sidebar = "subreddit-sidebar" in html_content.lower()
            logger.info(
                f"[Worker {self.worker_id}] Page content: {html_length} chars, "
                f"has_shreddit={has_shreddit}, has_posts={has_posts}, has_sidebar={has_sidebar}"
            )
            
            # Save screenshot and HTML for debugging (only when not headless)
            if not self.headless:
                try:
                    screenshot_path = f"/Users/calummelling/Desktop/redditscraper/intel-scraper/debug_{subreddit_name}.png"
                    html_path = f"/Users/calummelling/Desktop/redditscraper/intel-scraper/debug_{subreddit_name}.html"
                    await page.screenshot(path=screenshot_path, full_page=True)
                    with open(html_path, "w") as f:
                        f.write(html_content)
                    logger.info(f"[Worker {self.worker_id}] Debug files saved: {screenshot_path}, {html_path}")
                except Exception as e:
                    logger.debug(f"Debug save failed: {e}")
            
            # Extract data from the page
            data = {}
            
            # Get subscriber count from JSON API (reliable method)
            try:
                json_url = f"https://www.reddit.com/r/{subreddit_name}/about.json"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.get(json_url, headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    })
                    if resp.status_code == 200:
                        json_data = resp.json()
                        if json_data and "data" in json_data:
                            sub_data = json_data["data"]
                            if sub_data.get("subscribers"):
                                data["subscribers"] = sub_data["subscribers"]
            except Exception as e:
                logger.debug(f"JSON API fetch failed: {e}")
            
            # Extract weekly visitors and contributions
            data["weekly_visitors"] = await self._extract_weekly_visitors(page)
            data["weekly_contributions"] = await self._extract_weekly_contributions(page)
            
            # Extract subscriber count from page if JSON API failed
            if not data.get("subscribers"):
                data["subscribers"] = await self._extract_subscribers(page)
            
            # Extract additional metadata
            data["description"] = await self._extract_description(page)
            data["rules_count"] = await self._count_rules(page)
            data["community_icon_url"] = await self._extract_community_icon(page)
            
            # Calculate competition score
            if data["weekly_visitors"] and data["weekly_contributions"]:
                data["competition_score"] = round(
                    data["weekly_contributions"] / data["weekly_visitors"], 
                    6
                )
            else:
                data["competition_score"] = None
            
            # Add metadata
            data["subreddit_name"] = subreddit_name.lower()
            data["display_name"] = f"r/{subreddit_name}"
            data["last_scraped_at"] = datetime.utcnow().isoformat()
            data["scrape_status"] = "completed"
            
            logger.info(
                f"[Worker {self.worker_id}] ✓ r/{subreddit_name}: "
                f"{data.get('weekly_visitors', 'N/A')} visitors, "
                f"{data.get('weekly_contributions', 'N/A')} contributions"
            )
            
            self.stats["subreddits_scraped"] += 1
            self.stats["successful"] += 1
            
            return data
            
        except Exception as e:
            logger.error(f"[Worker {self.worker_id}] Error scraping r/{subreddit_name}: {e}")
            self.stats["failed"] += 1
            return None
    
    async def _extract_weekly_visitors(self, page) -> Optional[int]:
        """Extract weekly visitors from slot elements."""
        try:
            # Method 1: Try Playwright selector for slot element (primary method)
            try:
                slot_el = await page.query_selector('[slot="weekly-active-users-count"]')
                if slot_el:
                    text = await slot_el.text_content()
                    value = parse_metric_value(text)
                    if value:
                        return value
            except:
                pass
            
            # Method 2: Regex fallback on page content
            content = await page.content()
            slot_match = re.search(r'slot="weekly-active-users-count"[^>]*>([^<]+)<', content)
            if slot_match:
                value = parse_metric_value(slot_match.group(1))
                if value:
                    return value
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting weekly visitors: {e}")
            return None
    
    async def _extract_weekly_contributions(self, page) -> Optional[int]:
        """Extract weekly contributions from slot elements."""
        try:
            # Method 1: Try Playwright selectors for slot elements (primary method)
            slot_selectors = [
                '[slot="weekly-posts-count"]',
                '[slot="weekly-contributions-count"]',
                '[slot="weekly-content-count"]',
            ]
            for selector in slot_selectors:
                try:
                    slot_el = await page.query_selector(selector)
                    if slot_el:
                        text = await slot_el.text_content()
                        value = parse_metric_value(text)
                        if value:
                            return value
                except:
                    pass
            
            # Method 2: Regex fallback on page content
            content = await page.content()
            slot_patterns = [
                r'slot="weekly-posts-count"[^>]*>([^<]+)<',
                r'slot="weekly-contributions-count"[^>]*>([^<]+)<',
                r'slot="weekly-content-count"[^>]*>([^<]+)<',
            ]
            for slot_pattern in slot_patterns:
                slot_match = re.search(slot_pattern, content)
                if slot_match:
                    value = parse_metric_value(slot_match.group(1))
                    if value:
                        return value
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting weekly contributions: {e}")
            return None
    
    async def _extract_subscribers(self, page) -> Optional[int]:
        """Extract subscriber count from page content."""
        try:
            content = await page.content()
            
            # Look for subscriber patterns
            patterns = [
                r'([\d,\.]+[KMB]?)\s*(?:<[^>]*>)*\s*(?:members|subscribers)',
                r'"subscribers":\s*([\d]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = parse_metric_value(match.group(1))
                    if value:
                        return value
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting subscribers: {e}")
            return None
    
    async def _extract_description(self, page) -> Optional[str]:
        """Extract the subreddit description."""
        try:
            # Try common selectors for description
            selectors = [
                '[data-testid="subreddit-sidebar"] p',
                '.md p:first-of-type',
                '[class*="sidebar"] [class*="description"]',
            ]
            
            for selector in selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        text = await el.text_content()
                        if text and len(text) > 10:
                            return text.strip()[:1000]  # Limit length
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting description: {e}")
            return None
    
    async def _count_rules(self, page) -> int:
        """Count the number of subreddit rules."""
        try:
            content = await page.content()
            
            # Count rule headings (usually numbered)
            rule_patterns = [
                r'<h\d[^>]*>.*?Rule\s*\d+',
                r'"R\d+[-\s]',  # Like "R1-NO SPAM"
                r'>\s*\d+\.\s*[A-Z]',  # Numbered rules
            ]
            
            max_count = 0
            for pattern in rule_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                max_count = max(max_count, len(matches))
            
            # Also try to find rule section and count items
            rule_elements = await page.query_selector_all('[class*="rule"], [data-testid*="rule"]')
            if rule_elements:
                max_count = max(max_count, len(rule_elements))
            
            return max_count
            
        except Exception as e:
            logger.debug(f"Error counting rules: {e}")
            return 0
    
    async def _extract_community_icon(self, page) -> Optional[str]:
        """Extract the community icon URL."""
        try:
            selectors = [
                'img[alt*="icon" i]',
                'img[class*="community" i][class*="icon" i]',
                '[data-testid="community-icon"] img',
            ]
            
            for selector in selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        src = await el.get_attribute('src')
                        if src and 'reddit' in src:
                            return src.split('?')[0]  # Remove query params
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting community icon: {e}")
            return None
    
    async def _fetch_subreddit_rules(self, subreddit_name: str) -> list:
        """Fetch subreddit rules from Reddit API for LLM analysis."""
        try:
            url = f"https://www.reddit.com/r/{subreddit_name}/about/rules.json"
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("rules", [])
        except Exception as e:
            logger.debug(f"Could not fetch rules for r/{subreddit_name}: {e}")
        return []
    
    async def scrape_batch(
        self,
        subreddits: list[str],
        delay_min: float = None,
        delay_max: float = None,
        rotate_every: int = None,
    ) -> list[dict]:
        """
        Scrape a batch of subreddits with rate limiting and IP rotation.
        
        Args:
            subreddits: List of subreddit names to scrape
            delay_min: Minimum delay between requests
            delay_max: Maximum delay between requests
            rotate_every: Rotate IP after this many subreddits
            
        Returns:
            List of successfully scraped data dicts
        """
        delay_min = delay_min or DELAY_MIN
        delay_max = delay_max or DELAY_MAX
        rotate_every = rotate_every or ROTATE_EVERY
        
        results = []
        
        for i, subreddit in enumerate(subreddits):
            # Proactive IP rotation
            if i > 0 and i % rotate_every == 0:
                logger.info(f"[Worker {self.worker_id}] Proactive IP rotation...")
                await self.browser.rotate_ip()
                self.stats["ip_rotations"] += 1
                await asyncio.sleep(5)
            
            # Scrape the subreddit
            data = await self.scrape_subreddit(subreddit)
            
            if data:
                # Run LLM analysis if enabled
                if self.enable_llm and self.llm_analyzer:
                    try:
                        logger.info(f"[Worker {self.worker_id}] Running LLM analysis for r/{subreddit}...")
                        
                        # Fetch rules and description for LLM
                        rules_data = await self._fetch_subreddit_rules(subreddit)
                        
                        # Use description from scraped data if available
                        description = data.get("description", "")
                        subscribers = data.get("subscribers", 0)
                        
                        # Analyze with LLM
                        llm_result = await self.llm_analyzer.analyze_subreddit(
                            subreddit_name=subreddit,
                            description=description,
                            rules=rules_data,
                            subscribers=subscribers
                        )
                        
                        # Add LLM results to data
                        data["verification_required"] = llm_result["verification_required"]
                        data["sellers_allowed"] = llm_result["sellers_allowed"]
                        data["niche_categories"] = llm_result["niche_categories"]
                        data["llm_analysis_confidence"] = llm_result["confidence"]
                        data["llm_analysis_reasoning"] = llm_result["reasoning"]
                        
                        self.stats["llm_analyzed"] += 1
                        logger.info(f"[Worker {self.worker_id}] ✓ LLM: {llm_result['sellers_allowed']} sellers, {llm_result['verification_required']} verification")
                    except Exception as e:
                        logger.warning(f"[Worker {self.worker_id}] LLM analysis failed: {e}")
                
                results.append(data)
                # Save to database
                await self.supabase.upsert_subreddit_intel(data)
            else:
                # Mark as failed in database
                await self.supabase.mark_intel_failed(
                    subreddit, 
                    "Scrape failed after retries"
                )
            
            # Random delay before next request
            await self.browser.human_delay(delay_min, delay_max)
        
        return results
    
    def get_stats(self) -> dict:
        """Get scraping statistics."""
        stats = self.stats.copy()
        if self.browser:
            stats["requests_made"] = self.browser.requests_made
            stats["browser_rotations"] = self.browser.rotation_count
        return stats

