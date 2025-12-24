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

from config import PROXY_URL, PROXY_ROTATION_URL, PROXY_SERVER, PROXY_USER, PROXY_PASS, PAGE_TIMEOUT_MS
import httpx

logger = logging.getLogger(__name__)

# Pool of realistic Chrome user agents (Windows, Mac, Linux) - Updated for late 2024/early 2025
USER_AGENTS = [
    # Windows Chrome (current versions 139-143)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36",
    # Mac Chrome (current versions)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    # Linux Chrome (current versions)
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
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
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
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
        proxy_server: str = None,
        proxy_username: str = None,
        proxy_password: str = None,
        worker_id: int = None,
        headless: bool = True,
        use_fixed_fingerprint: bool = True,  # Use consistent fingerprint for session cookies
        use_session_cookies: bool = True,  # Set to False to disable hardcoded session cookies
    ):
        # Set worker_id FIRST (needed for logging)
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.headless = headless
        self.use_fixed_fingerprint = use_fixed_fingerprint
        self.use_session_cookies = use_session_cookies
        
        # Support both proxy_url format and separate server/user/pass
        if proxy_server and proxy_username and proxy_password:
            self.proxy_server = proxy_server
            self.proxy_username = proxy_username
            self.proxy_password = proxy_password
            self.proxy_url = None
        elif proxy_url:
            # Parse proxy URL to extract components
            self._parse_proxy_url(proxy_url)
        else:
            # Use default from config
            self.proxy_server = PROXY_SERVER
            self.proxy_username = PROXY_USER
            self.proxy_password = PROXY_PASS
            self.proxy_url = PROXY_URL if not (PROXY_SERVER and PROXY_USER and PROXY_PASS) else None
        
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
        
        # Resource blocking state (for data optimization)
        self.aggressive_blocking_enabled = False
    
    def _parse_proxy_url(self, proxy_url: str):
        """Parse proxy URL into components."""
        try:
            # Format: http://username:password@host:port
            import re
            match = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', proxy_url)
            if match:
                self.proxy_username = match.group(1)
                self.proxy_password = match.group(2)
                host = match.group(3)
                port = match.group(4)
                self.proxy_server = f"http://{host}:{port}"
                self.proxy_url = None
                logger.info(f"[Worker {self.worker_id}] Parsed proxy: {host}:{port}")
            else:
                # Fallback to using URL as-is
                self.proxy_server = None
                self.proxy_username = None
                self.proxy_password = None
                self.proxy_url = proxy_url
                logger.warning(f"[Worker {self.worker_id}] Could not parse proxy URL, using as-is")
        except Exception as e:
            logger.error(f"[Worker {self.worker_id}] Error parsing proxy URL: {e}")
            self.proxy_server = None
            self.proxy_username = None
            self.proxy_password = None
            self.proxy_url = proxy_url
        
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
        # Added stability flags to prevent crashes
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",  # Prevents crashes with proxies
            "--disable-dev-shm-usage",  # Prevents memory crashes in headless
            "--disable-gpu",  # Reduces crashes in headless mode
            "--disable-software-rasterizer",
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
        if self.proxy_server and self.proxy_username and self.proxy_password:
            context_options["proxy"] = {
                "server": self.proxy_server,
                "username": self.proxy_username,
                "password": self.proxy_password,
            }
            logger.info(f"[Worker {self.worker_id}] Using proxy: {self.proxy_server} (with auth)")
        elif self.proxy_url:
            # Fallback: try using URL as server (less reliable)
            context_options["proxy"] = {"server": self.proxy_url}
            logger.info(f"[Worker {self.worker_id}] Using proxy URL: {self.proxy_url[:40]}...")
        
        self.context = await self.browser.new_context(**context_options)
        
        # Create page FIRST (before patches to avoid detection)
        self.page = await self.context.new_page()
        
        # Apply minimal stealth patches (too much triggers detection)
        await self._apply_minimal_stealth_patches()
        
        # #region agent log - Set Reddit session cookies for authenticated access (OPTIONAL)
        if self.use_session_cookies:
            await self.context.add_cookies([
                # Main session cookie (expires 2026-05-08 - valid for ~1.3 years)
                {"name": "reddit_session", "value": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xcWlkcG4zZXY2IiwiZXhwIjoxNzgxNDQxNzMzLjc0MTQ4NSwiaWF0IjoxNzY1ODAzMzMzLjc0MTQ4NSwianRpIjoibGJCWmllUDRZMm5DbjllbjRmWjF5WjJiN0xHVkNnIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTc0ODY4NzA2NDY0OCwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6Mn0.zXGMEwAUYTrPLomjba0YtBSyv6gOYWCD2qEs7fsMrniSuMta6HtNxPpIWrdmEfXfO9w-SLWeHmJMwz9HEMkWY6HVuEkGCWu77KzCmegInl3s9kYd3HVjRmT59ivtLjJG-AegYPLLQ_W11iVqETlDytbzEiXqldJlYtHomj2mJjzdrZbbs-JhvGMUiiR89PJIvKGVnMoKPhm4fJtqeBorZOOhNluNXyfKLVfEFlCborNT_GVmyf6J0ncm-TZDQqlbWR4JlnJhTxAo6-eOt2cisgZGrtaUoG_pg4UYKFpX4UyH7zWnuhqVRXtWfdloqLAi5nRsO7Shv4LArp1jDqN1WQ", "domain": ".reddit.com", "path": "/", "httpOnly": True, "secure": True},
                # Auth token (refreshed Dec 23, 2024 - expires in ~24 hours, will auto-refresh on use)
                {"name": "token_v2", "value": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NTYzNTY5LjAxNzY4NywiaWF0IjoxNzY2NDc3MTY5LjAxNzY4NywianRpIjoiV2lMNWZ3NFVYWFoyZ0NuWk5FQ1BLaXhmd3pTUjJ3IiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xcWlkcG4zZXY2IiwiYWlkIjoidDJfMXFpZHBuM2V2NiIsImF0IjoxLCJsY2EiOjE3NDg2ODcwNjQ2NDgsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJOTldRUFlWUjhMUm85c1ROWXRDcHBVSVE3cWJCbGdVaUprSC1jU1VzUW5BIiwiZmxvIjoyfQ.Kfn7YF31igeXmjx5d6PzhfMQbSlmjpvuYYq6nqWITIkgBFB0v2MUUYXnvEmF6_kv5qstBLRbdxCYnG1pQBUV_06lsURz-3h7SXzf-cYiXlciOGwdVNhfLzmWA892g8cNQEzjOog3-05zIwHUuiDy6w_pOaS3AiIKgEiKNI_BVfCBmcyfmZgLRJzUSg5c88fjE7gZPNmeKV3p9uSK1N1PpftP33ZQjonGSGi66tVpXl01Rq1ZgBpjfRuRE2jeP2Q5aXlJsVZVz6wUHFpde5j9ZQiavjzm0JRp5k0_MOrwaR2TO9GsLO8LGwtgG80UW5F6kVH3I2HdgC-B_h96MHUE4w", "domain": ".reddit.com", "path": "/", "httpOnly": True, "secure": True},
                # User ID (new account)
                {"name": "loid", "value": "000000001qidpn3ev6.2.1748687064648.Z0FBQUFBQm9PdGpZb0NMZ0Z2NEFUVGZLN0hQVDBxZF84WWJ1TldhLXlFTHlUdWVSQWhXQThPdzFhODVxcllaLWZKZTk0UVRjUEI2cnBVUXNWZWpPdlhFeHY2SEVURy01OENIUkhsYzUycVJzS01mQS0ySll2SE5uZ0J2NkhnaWVnWDRnS25qbWp0ZDA", "domain": ".reddit.com", "path": "/", "secure": True},
                # Cookie consent
                {"name": "eu_cookie", "value": "{%22opted%22:true%2C%22nonessential%22:true}", "domain": "www.reddit.com", "path": "/"},
                # Theme
                {"name": "csv", "value": "2", "domain": ".reddit.com", "path": "/", "secure": True},
                {"name": "edgebucket", "value": "rlhgGhysrX0pm6bn0x", "domain": ".reddit.com", "path": "/", "secure": True},
            ])
            logger.info(f"[Worker {self.worker_id}] Set Reddit session cookies (authenticated - updated Dec 23, 2024)")
        else:
            logger.info(f"[Worker {self.worker_id}] Session cookies DISABLED - using stealth browser only")
        # #endregion
        
        # Don't set extra headers - let the browser use defaults
        # Setting too many custom headers can trigger detection
        
        # Log cookie expiration warnings
        import time
        current_time = time.time()
        for cookie in [c for c in await self.context.cookies() if c.get('name') in ('reddit_session', 'token_v2')]:
            # JWT tokens have expiration in the payload (base64 encoded)
            if cookie.get('name') == 'token_v2':
                try:
                    import base64
                    import json
                    # JWT format: header.payload.signature
                    parts = cookie['value'].split('.')
                    if len(parts) >= 2:
                        # Decode payload (add padding if needed)
                        payload_b64 = parts[1]
                        payload_b64 += '=' * (4 - len(payload_b64) % 4)
                        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                        exp_timestamp = payload.get('exp', 0)
                        if exp_timestamp and exp_timestamp < current_time:
                            logger.error(f"[Worker {self.worker_id}] ⚠️ token_v2 EXPIRED! (expired at {exp_timestamp})")
                        elif exp_timestamp and exp_timestamp - current_time < 86400:  # Less than 24 hours
                            logger.warning(f"[Worker {self.worker_id}] ⚠️ token_v2 expiring soon! ({(exp_timestamp - current_time)/3600:.1f} hours left)")
                except Exception as e:
                    logger.debug(f"[Worker {self.worker_id}] Could not check token expiration: {e}")
    
    async def _apply_minimal_stealth_patches(self):
        """Apply comprehensive stealth patches to evade bot detection."""
        # Comprehensive stealth script covering all major detection vectors
        stealth_script = """
        // 1. Hide webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // 2. Override permissions query to hide automation
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // 3. Add comprehensive chrome object (real Chrome has this)
        if (!window.chrome) {
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        }
        
        // 4. Override plugins to look real
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                },
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format"},
                    description: "Portable Document Format",
                    filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                    length: 1,
                    name: "Chrome PDF Viewer"
                },
                {
                    0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                    1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                    description: "",
                    filename: "internal-nacl-plugin",
                    length: 2,
                    name: "Native Client"
                }
            ],
        });
        
        // 5. Make languages look real
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // 6. Remove automation-specific properties
        delete navigator.__proto__.webdriver;
        
        // 7. Override toString to hide proxying
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {
            if (this === navigator.permissions.query) {
                return 'function query() { [native code] }';
            }
            return originalToString.call(this);
        };
        
        // 8. Add missing window properties
        window.chrome.runtime.connect = function() {};
        window.chrome.runtime.sendMessage = function() {};
        
        // 9. Fix navigator.connection if missing
        if (!navigator.connection) {
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    downlink: 10,
                    rtt: 50,
                    saveData: false
                }),
            });
        }
        
        // 10. Override notification permission
        if (!('Notification' in window)) {
            window.Notification = {
                permission: 'default'
            };
        }
        """
        
        await self.page.add_init_script(stealth_script)
    
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
    
    async def enable_aggressive_blocking(self):
        """
        Enable aggressive resource blocking to save data usage (up to 80% reduction).
        Blocks: images, fonts, media, stylesheets.
        Keeps: document HTML, XHR/fetch for dynamic content, essential scripts.
        """
        try:
            async def block_handler(route):
                resource_type = route.request.resource_type
                if resource_type in ["image", "font", "media", "stylesheet"]:
                    await route.abort()
                else:
                    await route.continue_()
            
            await self.page.route("**/*", block_handler)
            self.aggressive_blocking_enabled = True
            logger.info(f"[Worker {self.worker_id}] ✓ Aggressive resource blocking enabled (saves ~80% data)")
        except Exception as e:
            logger.error(f"[Worker {self.worker_id}] Failed to enable resource blocking: {e}")
            self.aggressive_blocking_enabled = False
    
    async def disable_blocking(self):
        """Disable resource blocking to allow full page rendering."""
        try:
            await self.page.unroute("**/*")
            self.aggressive_blocking_enabled = False
            logger.info(f"[Worker {self.worker_id}] ✓ Resource blocking disabled (full rendering)")
        except Exception as e:
            logger.warning(f"[Worker {self.worker_id}] Failed to disable resource blocking: {e}")
    
    async def new_context(self):
        """Create a fresh browser context with new fingerprint."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        
        self.current_fingerprint = self._generate_fingerprint()
        await self._create_context()
        self.rotation_count += 1
    
    async def enable_aggressive_blocking(self):
        """
        Enable aggressive resource blocking to save bandwidth (~80-90% savings).
        Blocks images, fonts, ads, and analytics while keeping HTML/JS needed for scraping.
        """
        async def block_resources(route):
            resource_type = route.request.resource_type
            url = route.request.url
            
            # Block images, media, fonts (biggest data consumers)
            if resource_type in ["image", "media", "font"]:
                await route.abort()
                return
            
            # Block stylesheets (we don't need styling for scraping)
            if resource_type == "stylesheet":
                await route.abort()
                return
            
            # Block ads and analytics
            ad_domains = [
                "doubleclick", "google-analytics", "googletagmanager",
                "adserver", "ads.", "analytics", "tracking",
                "pixel", "beacon", "metrics"
            ]
            if any(domain in url.lower() for domain in ad_domains):
                await route.abort()
                return
            
            # Allow everything else (HTML, scripts, XHR for data)
            await route.continue_()
        
        await self.page.route("**/*", block_resources)
        logger.info(f"[Worker {self.worker_id}] 🚫 Aggressive blocking enabled (images/fonts/ads blocked, saves ~80% data)")
    
    async def disable_blocking(self):
        """
        Disable resource blocking to load full page (fallback if Reddit detects blocking).
        """
        await self.page.unroute("**/*")
        logger.info(f"[Worker {self.worker_id}] ✅ Resource blocking disabled (full rendering)")
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
            await self.page.goto("https://www.reddit.com/login", wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
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
        max_retries: int = 5,  # Increased from 3 for better reliability
        wait_until: str = "domcontentloaded",  # Wait for DOM to load (faster than networkidle)
        timeout: int = None,  # Use config default (PAGE_TIMEOUT_MS)
        use_aggressive_blocking: bool = True,  # Enable data-saving mode by default
    ) -> bool:
        """
        Navigate to URL with exponential backoff retry logic and intelligent resource blocking.
        
        Strategy:
        1. First attempt: Use aggressive blocking (saves 80% data)
        2. If bot detection found: Disable blocking, retry with full rendering
        3. SOAX provides new IP per retry automatically
        """
        if timeout is None:
            timeout = PAGE_TIMEOUT_MS
        
        # Enable aggressive blocking before first attempt (if requested)
        if use_aggressive_blocking:
            await self.enable_aggressive_blocking()
        
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
                
                # Success case
                if response and 200 <= response.status < 400:
                    # Check if page is actually loaded (not blocked/empty)
                    try:
                        page_content = await self.page.content()
                        page_text = (await self.page.text_content("body")).lower() if await self.page.query_selector("body") else ""
                        
                        # Check for bot detection indicators
                        bot_indicators = ["blocked", "cloudflare", "automated", "captcha", "suspicious activity"]
                        is_bot_detected = any(indicator in page_text for indicator in bot_indicators)
                        is_empty = len(page_text.strip()) < 100
                        
                        if is_bot_detected or is_empty:
                            logger.warning(
                                f"[Worker {self.worker_id}] ⚠️ Bot detection or empty page "
                                f"(blocking_enabled={self.aggressive_blocking_enabled})"
                            )
                            
                            # If blocking was enabled, disable it and retry
                            if self.aggressive_blocking_enabled:
                                await self.disable_blocking()
                                logger.info(f"[Worker {self.worker_id}] Retrying with full rendering...")
                                await asyncio.sleep(3)
                                continue
                        
                        # Success!
                        self.requests_made += 1
                        self.consecutive_failures = 0
                        return True
                        
                    except Exception as e:
                        logger.warning(f"[Worker {self.worker_id}] Content check failed: {e}")
                        # Assume success if we can't check
                        self.requests_made += 1
                        self.consecutive_failures = 0
                        return True
                
                # HTTP error codes
                if response and response.status in (403, 429):
                    self.consecutive_failures += 1
                    
                    # Exponential backoff: 5s, 10s, 20s, 40s, 60s (max)
                    wait_time = min(5 * (2 ** attempt), 60)
                    
                    logger.warning(
                        f"[Worker {self.worker_id}] HTTP {response.status} on {url}, "
                        f"retrying in {wait_time}s (SOAX will rotate IP) "
                        f"[{attempt+1}/{max_retries}]"
                    )
                    
                    # If blocking was enabled on first 403, try without blocking
                    if attempt == 0 and self.aggressive_blocking_enabled:
                        await self.disable_blocking()
                        logger.info(f"[Worker {self.worker_id}] Disabled blocking, will retry with full rendering")
                    
                    await asyncio.sleep(wait_time)
                    continue
                
                return True
                
            except Exception as e:
                self.consecutive_failures += 1
                error_type = type(e).__name__
                
                # Exponential backoff: 5s, 10s, 20s, 40s, 60s (max)
                wait_time = min(5 * (2 ** attempt), 60)
                
                # Check if it's a timeout
                if "Timeout" in str(e):
                    logger.warning(
                        f"[Worker {self.worker_id}] Timeout error: {e}, "
                        f"retrying in {wait_time}s (SOAX will rotate IP) "
                        f"[{attempt+1}/{max_retries}]"
                    )
                else:
                    logger.error(
                        f"[Worker {self.worker_id}] Navigation error ({error_type}): {e}, "
                        f"retrying in {wait_time}s [{attempt+1}/{max_retries}]"
                    )
                
                await asyncio.sleep(wait_time)
        
        logger.error(f"[Worker {self.worker_id}] All retries exhausted for {url}")
        return False


class BrowserPool:
    """
    Pool of browser contexts for parallel subreddit scraping.
    
    Each browser context has its own Reddit account from the AccountManager,
    allowing safe parallel scraping without session conflicts.
    """
    
    def __init__(
        self,
        size: int = 5,
        proxy_url: str = None,
        headless: bool = True,
        worker_id: int = None,
    ):
        """
        Initialize browser pool.
        
        Args:
            size: Number of browser contexts to create
            proxy_url: Proxy URL (uses config default if not provided)
            headless: Run browsers in headless mode
            worker_id: Base worker ID for logging
        """
        from account_manager import AccountManager, get_account_manager
        
        self.size = size
        self.proxy_url = proxy_url or PROXY_URL
        self.headless = headless
        self.base_worker_id = worker_id or 1
        
        self.account_manager = get_account_manager()
        
        # Adjust pool size to available accounts
        if self.size > self.account_manager.total_accounts:
            logger.warning(
                f"BrowserPool: Requested {self.size} contexts but only "
                f"{self.account_manager.total_accounts} accounts available. "
                f"Reducing pool size."
            )
            self.size = self.account_manager.total_accounts
        
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.contexts: list[dict] = []  # {"context": BrowserContext, "page": Page, "account": RedditAccount}
        self._lock = asyncio.Lock()
        self._available = asyncio.Condition()
        
        self.stats = {
            "contexts_created": 0,
            "total_requests": 0,
            "failed_requests": 0,
        }
    
    async def start(self):
        """Initialize the browser and create contexts."""
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        
        # Browser launch args
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-software-rasterizer",
        ]
        
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=launch_args,
        )
        
        # Create browser contexts with accounts
        for i in range(self.size):
            account = await self.account_manager.acquire()
            if not account:
                logger.error(f"BrowserPool: Could not acquire account for context {i}")
                break
            
            context = await self._create_context(account, worker_id=self.base_worker_id + i)
            self.contexts.append({
                "context": context["context"],
                "page": context["page"],
                "account": account,
                "in_use": False,
                "worker_id": self.base_worker_id + i,
            })
            self.stats["contexts_created"] += 1
        
        logger.info(f"BrowserPool: Created {len(self.contexts)} browser contexts")
    
    async def _create_context(self, account, worker_id: int) -> dict:
        """Create a browser context with the given account."""
        # Use fixed fingerprint for consistency
        fp = StealthBrowser.FIXED_FINGERPRINT.copy()
        
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
        
        # Add proxy if configured
        if self.proxy_url:
            import re
            match = re.match(r'https?://([^:]+):([^@]+)@([^:]+):(\d+)', self.proxy_url)
            if match:
                context_options["proxy"] = {
                    "server": f"http://{match.group(3)}:{match.group(4)}",
                    "username": match.group(1),
                    "password": match.group(2),
                }
                logger.info(f"[Worker {worker_id}] Context using proxy: {match.group(3)}:{match.group(4)}")
        
        context = await self.browser.new_context(**context_options)
        page = await context.new_page()
        
        # Apply stealth patches
        await self._apply_stealth_patches(page)
        
        # Set account cookies
        await context.add_cookies(account.get_cookies())
        logger.info(f"[Worker {worker_id}] Set cookies for account: {account.username}")
        
        return {"context": context, "page": page}
    
    async def _apply_stealth_patches(self, page):
        """Apply stealth patches to a page."""
        stealth_script = """
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        if (!window.chrome) {
            window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
        }
        
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { 0: {type: "application/x-google-chrome-pdf"}, description: "PDF", filename: "internal-pdf-viewer", length: 1, name: "Chrome PDF Plugin" }
            ],
        });
        
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """
        await page.add_init_script(stealth_script)
    
    async def acquire(self, timeout: float = 30.0) -> Optional[dict]:
        """
        Acquire an available browser context from the pool.
        
        Args:
            timeout: Maximum seconds to wait for a context
            
        Returns:
            Dict with context, page, account, and worker_id if acquired, None if timeout
        """
        async with self._lock:
            for ctx in self.contexts:
                if not ctx["in_use"]:
                    ctx["in_use"] = True
                    logger.debug(f"BrowserPool: Acquired context {ctx['worker_id']}")
                    return ctx
        
        # Wait for available context
        try:
            async with self._available:
                await asyncio.wait_for(
                    self._wait_for_available(),
                    timeout=timeout
                )
                
                async with self._lock:
                    for ctx in self.contexts:
                        if not ctx["in_use"]:
                            ctx["in_use"] = True
                            return ctx
        except asyncio.TimeoutError:
            logger.warning("BrowserPool: Timeout waiting for available context")
            return None
        
        return None
    
    async def _wait_for_available(self):
        """Wait for a context to become available."""
        async with self._available:
            await self._available.wait()
    
    async def release(self, ctx: dict):
        """Release a browser context back to the pool."""
        async with self._lock:
            ctx["in_use"] = False
            logger.debug(f"BrowserPool: Released context {ctx['worker_id']}")
        
        async with self._available:
            self._available.notify()
    
    async def close(self):
        """Close all browser contexts and the browser."""
        # Release all accounts
        for ctx in self.contexts:
            if ctx.get("account"):
                await self.account_manager.release(ctx["account"])
            if ctx.get("page"):
                await ctx["page"].close()
            if ctx.get("context"):
                await ctx["context"].close()
        
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("BrowserPool: Closed all contexts and browser")
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def get_stats(self) -> dict:
        """Get pool statistics."""
        return {
            **self.stats,
            "pool_size": len(self.contexts),
            "available": sum(1 for c in self.contexts if not c["in_use"]),
            "in_use": sum(1 for c in self.contexts if c["in_use"]),
        }

