"""
Stealth Browser Configuration for Anti-Bot Evasion

Provides a fully configured Playwright browser with comprehensive anti-detection
measures including fingerprint spoofing, proxy support, and human-like behavior.
"""
import asyncio
import random
import logging
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

try:
    from playwright_stealth import stealth_async
except ImportError:
    stealth_async = None

from config import PROXY_URL, PROXY_ROTATION_URL, PROXY_SERVER, PROXY_USER, PROXY_PASS
import httpx

logger = logging.getLogger(__name__)

# Pool of realistic Chrome user agents (Windows, Mac, Linux)
USER_AGENTS = [
    # Windows Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Mac Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# WebGL renderer/vendor combinations (real GPU fingerprints)
WEBGL_CONFIGS = [
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (NVIDIA)", "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (AMD)", "renderer": "ANGLE (AMD, AMD Radeon RX 580 Series Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Intel)", "renderer": "ANGLE (Intel, Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0, D3D11)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)"},
    {"vendor": "Google Inc. (Apple)", "renderer": "ANGLE (Apple, Apple M2, OpenGL 4.1)"},
    {"vendor": "Intel Inc.", "renderer": "Intel Iris Pro OpenGL Engine"},
    {"vendor": "NVIDIA Corporation", "renderer": "NVIDIA GeForce GTX 1660 Ti/PCIe/SSE2"},
]

# Viewport sizes (common desktop resolutions)
VIEWPORT_SIZES = [
    {"width": 1920, "height": 1080},
    {"width": 1536, "height": 864},
    {"width": 1440, "height": 900},
    {"width": 1366, "height": 768},
    {"width": 1280, "height": 720},
    {"width": 1600, "height": 900},
    {"width": 1680, "height": 1050},
    {"width": 2560, "height": 1440},
]

# Timezone IDs
TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "America/Phoenix",
    "Europe/London",
    "Europe/Paris",
    "Australia/Sydney",
]

# Languages
LANGUAGES = ["en-US", "en-GB", "en-CA", "en-AU"]


class StealthBrowser:
    """
    A stealth Playwright browser with comprehensive anti-detection measures.
    
    Features:
    - Consistent fingerprint when using session cookies
    - WebGL fingerprint spoofing
    - Proxy support with rotation
    - Human-like behavior simulation
    - NSFW consent handling
    - Cookie extraction and refresh
    """
    
    # Fixed fingerprint for session cookie consistency (matches the session's original browser)
    FIXED_FINGERPRINT = {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "viewport": {"width": 1920, "height": 1080},
        "webgl_vendor": "Google Inc. (NVIDIA)",
        "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "timezone": "America/New_York",
        "language": "en-US",
        "platform": "Win32",
        "screen": {"width": 1920, "height": 1080, "availWidth": 1920, "availHeight": 1040, "colorDepth": 24, "pixelDepth": 24},
    }
    
    def __init__(
        self,
        proxy_url: str = None,
        worker_id: int = None,
        headless: bool = True,
        use_fixed_fingerprint: bool = True,  # Use consistent fingerprint for session cookies
    ):
        self.proxy_url = proxy_url or PROXY_URL
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.headless = headless
        self.use_fixed_fingerprint = use_fixed_fingerprint
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Track stats
        self.requests_made = 0
        self.rotation_count = 0
        self.consecutive_failures = 0
        
        # Current fingerprint
        self.current_fingerprint = None
        
        # Extracted cookies (to be saved/refreshed)
        self.extracted_cookies = None
        
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _generate_fingerprint(self) -> dict:
        """Generate a browser fingerprint. Uses fixed fingerprint when session cookies are used for consistency."""
        # Use fixed fingerprint for session cookie consistency
        if self.use_fixed_fingerprint:
            logger.info(f"[Worker {self.worker_id}] Using FIXED fingerprint for session cookie consistency")
            return self.FIXED_FINGERPRINT.copy()
        
        # Random fingerprint for non-session use
        user_agent = random.choice(USER_AGENTS)
        viewport = random.choice(VIEWPORT_SIZES)
        webgl = random.choice(WEBGL_CONFIGS)
        timezone = random.choice(TIMEZONES)
        language = random.choice(LANGUAGES)
        
        # Determine platform from user agent
        if "Windows" in user_agent:
            platform = "Win32"
        elif "Macintosh" in user_agent:
            platform = "MacIntel"
        else:
            platform = "Linux x86_64"
        
        return {
            "user_agent": user_agent,
            "viewport": viewport,
            "webgl_vendor": webgl["vendor"],
            "webgl_renderer": webgl["renderer"],
            "timezone": timezone,
            "language": language,
            "platform": platform,
            "screen": {
                "width": viewport["width"],
                "height": viewport["height"],
                "availWidth": viewport["width"],
                "availHeight": viewport["height"] - 40,  # Account for taskbar
                "colorDepth": 24,
                "pixelDepth": 24,
            },
        }
    
    async def start(self):
        """Start the browser with stealth configuration."""
        self.current_fingerprint = self._generate_fingerprint()
        fp = self.current_fingerprint
        
        self.playwright = await async_playwright().start()
        
        # Browser launch args - keep it minimal (too many args trigger detection)
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
        ]
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )
        
        await self._create_context()
        
        logger.info(f"[Worker {self.worker_id}] Stealth browser started")
        logger.info(f"[Worker {self.worker_id}] UA: {fp['user_agent'][:60]}...")
        logger.info(f"[Worker {self.worker_id}] Viewport: {fp['viewport']['width']}x{fp['viewport']['height']}")
        
    async def _create_context(self):
        """Create a new browser context with fingerprint and proxy."""
        fp = self.current_fingerprint
        
        context_options = {
            "viewport": fp["viewport"],
            "user_agent": fp["user_agent"],
            "locale": fp["language"],
            "timezone_id": fp["timezone"],
            "permissions": ["geolocation"],
            "color_scheme": "dark",
            "device_scale_factor": 1,
            "is_mobile": False,
            "has_touch": False,
            "java_script_enabled": True,
            "accept_downloads": False,
            "ignore_https_errors": True,
        }
        
        # Add proxy if configured - Playwright needs auth as separate fields
        if PROXY_SERVER and PROXY_USER and PROXY_PASS:
            context_options["proxy"] = {
                "server": PROXY_SERVER,
                "username": PROXY_USER,
                "password": PROXY_PASS,
            }
            logger.info(f"[Worker {self.worker_id}] Using proxy: {PROXY_SERVER} (with auth)")
        elif self.proxy_url:
            # Fallback: try parsing auth from URL
            context_options["proxy"] = {"server": self.proxy_url}
            logger.info(f"[Worker {self.worker_id}] Using proxy URL: {self.proxy_url[:40]}...")
        
        self.context = await self.browser.new_context(**context_options)
        
        # Create page FIRST (before patches to avoid detection)
        self.page = await self.context.new_page()
        
        # Apply minimal stealth patches (too much triggers detection)
        await self._apply_minimal_stealth_patches()
        
        # #region agent log - Set Reddit session cookies for authenticated access
        await self.context.add_cookies([
            # Main session cookie
            {"name": "reddit_session", "value": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xYW10dDVhcWF5IiwiZXhwIjoxNzgxMDM4MTU0LjcwNjg2NiwiaWF0IjoxNzY1Mzk5NzU0LjcwNjg2NiwianRpIjoidE1SamJDMUxxTmlIZXVpNUhqUUc0WEMwSU12N0FBIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTcyODY2NDcwNjIwMCwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6MywiYW1yIjpbInNzbyJdfQ.Vt-6-jjxJl24-zFC6CJNcg5UWyRXIH1dIeyaMwFah-Bo2oRznhydO3fe05A8bsov_SBGNetlHsg0M3NkQy7uECc1zBzSwsoCdOWqXlBU-k4b9mU1BtImqMYb4tjvQQP9v0TclRszAhtbmNXfVmihW4VybA8t0_IUHkNrjend_Qj8HghqrcO2OLhNa6Ve5kN49SiYgyHDHGW1oI7P03Tw4-Ylb2GiYMx_Lb8pUfZ9GDLNPeDEPksPde8CldRlHTcBHfOWuMmSJy1GAW1piWGk1dipQeS3KmcpauZ4mVJmBQ0RdGeYJNxb9DjPo1iZNvak-SA-njh9ZlvJ4diwfoTD_Q", "domain": ".reddit.com", "path": "/", "httpOnly": True, "secure": True},
            # Auth token
            {"name": "token_v2", "value": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NDMzMjU4Ljk2NzQzOSwiaWF0IjoxNzY2MzQ2ODU4Ljk2NzQzOSwianRpIjoiVGhfLURxcG1sbzFfQ2xiQjlGTFNFU2l2MkMwMHJRIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xYW10dDVhcWF5IiwiYWlkIjoidDJfMWFtdHQ1YXFheSIsImF0IjoxLCJsY2EiOjE3Mjg2NjQ3MDYyMDAsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJVa1N4YzFpYUd4U2kyWXpib18tTGEyekJiNkxUbnpfWldQZmJtSGduRENVIiwiZmxvIjoyfQ.HCWGETGXDzhHNBak87WxdsHCweLACSY0A_U4GwDkstCfuid8vz_9k90f-Gr3Zzj_jKrc0iZXE63y94hpFO4JazxGoTfaQnPGSsawoSvgms5ODHLB89fA4KYb7cBZerOQaM_hVXqlWs3ybf8Z2toC4Cohw1ui7Gc1lDIRqF5IsRWEFYbfb5VKVC9Pxxc--gc4M4V2dgN2Tid4afdO7PgAe-MAidp1e-fyJqbW8hZDfquLpQy4jbIWU9wQAHctl7eMueRuId37LtLDnxB5njPcQAk_c5WOM3ipqU9-bsO6DvYtvW08l3ZS8pLwTnsJcnp4qe6bW7pRmHG6ZE_gD2c6yw", "domain": ".reddit.com", "path": "/", "httpOnly": True, "secure": True},
            # User ID
            {"name": "loid", "value": "000000001amtt5aqay.2.1728664706200.Z0FBQUFBQnBKaTJIcktBVVlHSFVxd2RwYW5iYVhTN2NtNnE4OGlwUGwxMlo5NVN4a3d6MFdlRFlNV0liX3VrazNMTlllYUxFMUdDVnFjdWtiN0pGdEg5RHNsRTRaSGNTWlhvWklhQlBWSkJweDQtb3h1dnp0ZHlKR01YUGFMR29HQlRGZ0VCa3l3aUI", "domain": ".reddit.com", "path": "/", "secure": True},
            # Cookie consent
            {"name": "eu_cookie", "value": "{%22opted%22:true%2C%22nonessential%22:true}", "domain": "www.reddit.com", "path": "/"},
            # Theme
            {"name": "csv", "value": "2", "domain": ".reddit.com", "path": "/", "secure": True},
            {"name": "edgebucket", "value": "kAjS9mooWgcUQWtVE5", "domain": ".reddit.com", "path": "/", "secure": True},
        ])
        logger.info(f"[Worker {self.worker_id}] Set Reddit session cookies (authenticated)")
        # #endregion
        
        # Don't set extra headers - let the browser use defaults
        # Setting too many custom headers can trigger detection
    
    async def _apply_minimal_stealth_patches(self):
        """Apply minimal JavaScript patches - too much triggers detection!"""
        # MINIMAL patching - Reddit detects excessive modifications
        minimal_script = """
        // Only hide webdriver property - nothing else!
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Add minimal chrome object
        if (!window.chrome) {
            window.chrome = { runtime: {} };
        }
        """
        
        await self.page.add_init_script(minimal_script)
    
    async def rotate_ip(self):
        """Rotate the proxy IP address."""
        if PROXY_ROTATION_URL:
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    logger.info(f"[Worker {self.worker_id}] Rotating proxy IP...")
                    response = await client.get(PROXY_ROTATION_URL)
                    if response.status_code == 200:
                        self.rotation_count += 1
                        logger.info(f"[Worker {self.worker_id}] ✓ IP rotated (#{self.rotation_count})")
                        return True
                    else:
                        logger.warning(f"[Worker {self.worker_id}] IP rotation failed: {response.status_code}")
            except Exception as e:
                logger.error(f"[Worker {self.worker_id}] IP rotation error: {e}")
        
        # Fallback: recreate context with new fingerprint
        logger.info(f"[Worker {self.worker_id}] Recreating browser context...")
        await self.new_context()
        return True
    
    async def new_context(self):
        """Create a fresh browser context with new fingerprint."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        
        self.current_fingerprint = self._generate_fingerprint()
        await self._create_context()
        self.rotation_count += 1
        logger.info(f"[Worker {self.worker_id}] ✓ New context created (#{self.rotation_count})")
    
    async def close(self):
        """Close the browser."""
        # Extract cookies before closing for future sessions
        await self.extract_cookies()
        
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info(f"[Worker {self.worker_id}] Browser closed")
    
    async def extract_cookies(self) -> list:
        """Extract current cookies from the browser context for future sessions."""
        if not self.context:
            return []
        try:
            cookies = await self.context.cookies()
            # Filter for important Reddit cookies
            important_cookies = [c for c in cookies if c.get('domain', '').endswith('reddit.com')]
            self.extracted_cookies = important_cookies
            logger.info(f"[Worker {self.worker_id}] Extracted {len(important_cookies)} Reddit cookies")
            return important_cookies
        except Exception as e:
            logger.warning(f"[Worker {self.worker_id}] Failed to extract cookies: {e}")
            return []
    
    async def verify_logged_in(self) -> bool:
        """Verify that we're actually logged in to Reddit."""
        if not self.page:
            return False
        try:
            # Check for logged-in indicators
            logged_in_selectors = [
                '[data-testid="user-drawer-button"]',  # User menu button
                'button[aria-label*="profile"]',
                '[id*="USER_DROPDOWN"]',
                'a[href*="/user/"]',
            ]
            for selector in logged_in_selectors:
                el = await self.page.query_selector(selector)
                if el:
                    logger.info(f"[Worker {self.worker_id}] ✓ Logged in (found {selector})")
                    return True
            
            # Also check page content for username
            content = await self.page.content()
            if 'data-testid="user-drawer-button"' in content or 'petitebbyxoxod' in content.lower():
                logger.info(f"[Worker {self.worker_id}] ✓ Logged in (found in content)")
                return True
            
            logger.warning(f"[Worker {self.worker_id}] ⚠ Could not verify login status")
            return False
        except Exception as e:
            logger.warning(f"[Worker {self.worker_id}] Login verification failed: {e}")
            return False
    
    # ==================== Human-Like Behavior ====================
    
    async def human_delay(self, min_sec: float = 3.0, max_sec: float = 8.0):
        """Add a random human-like delay."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
    
    async def scroll_naturally(self, scroll_count: int = None):
        """Simulate natural scrolling behavior."""
        count = scroll_count or random.randint(2, 4)
        for _ in range(count):
            scroll_amount = random.randint(200, 500)
            await self.page.mouse.wheel(0, scroll_amount)
            await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def move_mouse_randomly(self):
        """Move mouse to random positions."""
        for _ in range(random.randint(1, 3)):
            x = random.randint(100, self.current_fingerprint["viewport"]["width"] - 100)
            y = random.randint(100, self.current_fingerprint["viewport"]["height"] - 100)
            await self.page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def login_reddit(self, username: str, password: str) -> bool:
        """Log in to Reddit to bypass NSFW age gates."""
        try:
            logger.info(f"[Worker {self.worker_id}] Logging in to Reddit...")
            
            # Go to login page
            await self.page.goto("https://www.reddit.com/login", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            # Fill username
            username_input = await self.page.wait_for_selector('input[name="username"], #loginUsername', timeout=10000)
            await username_input.fill(username)
            await asyncio.sleep(0.5)
            
            # Fill password
            password_input = await self.page.wait_for_selector('input[name="password"], #loginPassword', timeout=5000)
            await password_input.fill(password)
            await asyncio.sleep(0.5)
            
            # Click login button
            login_button = await self.page.wait_for_selector('button[type="submit"], button:has-text("Log In")', timeout=5000)
            await login_button.click()
            
            # Wait for login to complete
            await asyncio.sleep(5)
            
            # Check if logged in by looking for user menu or logged-in indicators
            current_url = self.page.url
            if "login" not in current_url.lower():
                logger.info(f"[Worker {self.worker_id}] ✓ Reddit login successful")
                return True
            else:
                logger.warning(f"[Worker {self.worker_id}] Login may have failed - still on login page")
                return False
                
        except Exception as e:
            logger.error(f"[Worker {self.worker_id}] Reddit login failed: {e}")
            return False
    
    async def handle_nsfw_consent(self):
        """Click through NSFW/age verification dialogs."""
        consent_selectors = [
            # New Reddit age gate buttons
            'button:has-text("Yes, I\'m over 18")',
            'button:has-text("I\'m 18 or older")',
            'button:has-text("I am 18 or older")',
            '[data-testid="over-18-button"]',
            '[data-testid="mature-content-confirm"]',
            # Legacy selectors
            'button:has-text("Yes")',
            'button:has-text("Continue")',
            'button:has-text("I am over 18")',
            'button:has-text("Enter")',
            '[data-testid="age-gate-continue"]',
            'button:has-text("View NSFW content")',
            'button:has-text("Click to see nsfw")',
        ]
        
        for selector in consent_selectors:
            try:
                await self.page.click(selector, timeout=2000)
                logger.info(f"[Worker {self.worker_id}] Clicked consent: {selector}")
                await asyncio.sleep(0.5)
            except Exception:
                pass  # Button not found, continue
    
    async def goto_with_retry(
        self, 
        url: str, 
        max_retries: int = 3,
        wait_until: str = "domcontentloaded",  # Wait for DOM to load (faster than networkidle)
        timeout: int = 30000,  # 30 second timeout
    ) -> bool:
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"[Worker {self.worker_id}] Navigating to {url} (attempt {attempt + 1}/{max_retries})")
                response = await self.page.goto(
                    url, 
                    wait_until=wait_until,
                    timeout=timeout,
                )
                
                status = response.status if response else 0
                logger.info(f"[Worker {self.worker_id}] Response status: {status}")
                
                if response and response.status == 200:
                    self.requests_made += 1
                    self.consecutive_failures = 0
                    return True
                
                # Also accept other success codes
                if response and 200 <= response.status < 400:
                    self.requests_made += 1
                    self.consecutive_failures = 0
                    return True
                
                if response and response.status in (403, 429):
                    self.consecutive_failures += 1
                    logger.warning(
                        f"[Worker {self.worker_id}] {response.status} on {url} "
                        f"(failures: {self.consecutive_failures})"
                    )
                    
                    if self.consecutive_failures >= 3:
                        await self.rotate_ip()
                        await asyncio.sleep(60)
                        self.consecutive_failures = 0
                    else:
                        await asyncio.sleep(30 * (attempt + 1))
                    continue
                
                return True
                
            except Exception as e:
                self.consecutive_failures += 1
                error_type = type(e).__name__
                logger.error(f"[Worker {self.worker_id}] Navigation error ({error_type}): {e}")
                
                # If it's a timeout, it might be a proxy issue
                if "Timeout" in str(e):
                    logger.warning(f"[Worker {self.worker_id}] Timeout - proxy might be slow or blocked")
                
                if self.consecutive_failures >= 3:
                    logger.info(f"[Worker {self.worker_id}] 3 consecutive failures, rotating context...")
                    await self.rotate_ip()
                    self.consecutive_failures = 0
                
                wait_time = 10 * (attempt + 1)
                logger.info(f"[Worker {self.worker_id}] Waiting {wait_time}s before retry...")
                await asyncio.sleep(wait_time)
        
        logger.error(f"[Worker {self.worker_id}] All retries exhausted for {url}")
        return False

