"""
Subreddit Intelligence Scraper

Extracts detailed metrics from subreddit pages using Playwright with stealth mode.
Captures weekly visitors, weekly contributions, rules, and other metadata.
"""
import asyncio
import re
import logging
import json
from typing import Optional
from datetime import datetime

from stealth_browser import StealthBrowser
from supabase_client import SupabaseClient
from config import DELAY_MIN, DELAY_MAX, ROTATE_EVERY

logger = logging.getLogger(__name__)

# #region agent log
DEBUG_LOG_PATH = "/Users/calummelling/Desktop/redditscraper/.cursor/debug.log"
def debug_log(hypothesis_id, location, message, data=None):
    import time
    try:
        with open(DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps({"hypothesisId": hypothesis_id, "location": location, "message": message, "data": data, "timestamp": int(time.time()*1000), "sessionId": "debug-session"}) + "\n")
    except: pass
# #endregion


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
        headless: bool = True,
    ):
        self.supabase = supabase_client
        self.worker_id = worker_id
        self.proxy_url = proxy_url
        self.headless = headless
        
        self.browser: Optional[StealthBrowser] = None
        self.stats = {
            "subreddits_scraped": 0,
            "successful": 0,
            "failed": 0,
            "ip_rotations": 0,
        }
    
    async def start(self):
        """Initialize the stealth browser."""
        self.browser = StealthBrowser(
            proxy_url=self.proxy_url,
            worker_id=self.worker_id,
            headless=self.headless,
        )
        await self.browser.start()
    
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
            
            # Handle NSFW consent dialogs
            await self.browser.handle_nsfw_consent()
            await asyncio.sleep(1)  # Wait for any transitions
            
            # #region agent log
            # Check page title and URL after consent
            page = self.browser.page
            current_url = page.url
            title = await page.title()
            debug_log("H2", "intel_scraper:post_consent", "Page state after consent", {"url": current_url, "title": title})
            # #endregion
            
            # Human-like behavior
            await self.browser.move_mouse_randomly()
            await self.browser.human_delay(2.0, 4.0)
            await self.browser.scroll_naturally(2)
            
            # #region agent log
            # Check if page has expected content structure
            body_text = await page.evaluate('() => document.body.innerText.substring(0, 2000)')
            debug_log("H3", "intel_scraper:page_text", "Page body text after scroll", {"text": body_text[:1500] if body_text else "EMPTY"})
            # #endregion
            
            # Extract data from the page
            data = {}
            
            # Extract weekly visitors
            data["weekly_visitors"] = await self._extract_weekly_visitors(page)
            
            # Extract weekly contributions  
            data["weekly_contributions"] = await self._extract_weekly_contributions(page)
            
            # Extract subscriber count
            data["subscribers"] = await self._extract_subscribers(page)
            
            # Extract description
            data["description"] = await self._extract_description(page)
            
            # Extract rules count
            data["rules_count"] = await self._count_rules(page)
            
            # Extract community icon
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
        """Extract weekly visitors from the sidebar."""
        try:
            content = await page.content()
            
            # #region agent log
            # Log a snippet of the page content around "weekly" to see actual format
            weekly_idx = content.lower().find('weekly')
            if weekly_idx > 0:
                snippet = content[max(0, weekly_idx-200):weekly_idx+300]
                debug_log("H1", "intel_scraper:weekly_visitors", "Page content around 'weekly'", {"snippet": snippet[:500], "found_at": weekly_idx})
            else:
                debug_log("H1", "intel_scraper:weekly_visitors", "No 'weekly' found in page", {"content_len": len(content), "sample": content[:1000]})
            # #endregion
            
            # Look for patterns like "559K\nWeekly visitors" or similar
            patterns = [
                r'([\d,\.]+[KMB]?)\s*(?:<[^>]*>)*\s*Weekly visitors',
                r'<strong[^>]*>(?:<[^>]*>)*([\d,\.]+[KMB]?)(?:</[^>]*>)*</strong>\s*(?:<[^>]*>)*\s*Weekly visitors',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                # #region agent log
                debug_log("H1", "intel_scraper:regex_match", f"Pattern match result", {"pattern": pattern[:50], "matched": match is not None, "groups": match.groups() if match else None})
                # #endregion
                if match:
                    value = parse_metric_value(match.group(1))
                    if value:
                        return value
            
            # Fallback: try to find strong elements near "Weekly visitors"
            elements = await page.query_selector_all('strong')
            # #region agent log
            debug_log("H4", "intel_scraper:strong_elements", f"Found strong elements", {"count": len(elements)})
            # #endregion
            for el in elements:
                text = await el.text_content()
                if text:
                    parent = await el.evaluate_handle('el => el.parentElement')
                    parent_text = await parent.evaluate('el => el.textContent')
                    if parent_text and 'weekly visitors' in parent_text.lower():
                        value = parse_metric_value(text)
                        if value:
                            return value
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting weekly visitors: {e}")
            # #region agent log
            debug_log("H1", "intel_scraper:weekly_visitors_error", str(e), {})
            # #endregion
            return None
    
    async def _extract_weekly_contributions(self, page) -> Optional[int]:
        """Extract weekly contributions from the sidebar."""
        try:
            content = await page.content()
            
            # Look for patterns like "2.2K\nWeekly contributions"
            patterns = [
                r'([\d,\.]+[KMB]?)\s*(?:<[^>]*>)*\s*Weekly contributions',
                r'<strong[^>]*>(?:<[^>]*>)*([\d,\.]+[KMB]?)(?:</[^>]*>)*</strong>\s*(?:<[^>]*>)*\s*Weekly contributions',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = parse_metric_value(match.group(1))
                    if value:
                        return value
            
            # Fallback: search in elements
            elements = await page.query_selector_all('strong')
            for el in elements:
                text = await el.text_content()
                if text:
                    parent = await el.evaluate_handle('el => el.parentElement')
                    parent_text = await parent.evaluate('el => el.textContent')
                    if parent_text and 'weekly contributions' in parent_text.lower():
                        value = parse_metric_value(text)
                        if value:
                            return value
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting weekly contributions: {e}")
            return None
    
    async def _extract_subscribers(self, page) -> Optional[int]:
        """Extract subscriber count."""
        try:
            content = await page.content()
            
            # #region agent log
            # Search for "members" text to see format
            members_idx = content.lower().find('members')
            if members_idx > 0:
                snippet = content[max(0, members_idx-150):members_idx+100]
                debug_log("H5", "intel_scraper:subscribers", "Content around 'members'", {"snippet": snippet[:300]})
            # #endregion
            
            # Look for subscriber patterns
            patterns = [
                r'([\d,\.]+[KMB]?)\s*(?:<[^>]*>)*\s*(?:members|subscribers)',
                r'"subscribers":\s*([\d]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                # #region agent log
                debug_log("H5", "intel_scraper:sub_pattern", f"Subscriber pattern", {"pattern": pattern[:40], "matched": match is not None, "value": match.group(1) if match else None})
                # #endregion
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

