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

from config import PROXY_URL, PROXY_ROTATION_URL
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
    - Random user agent rotation
    - WebGL fingerprint spoofing
    - Viewport randomization
    - Proxy support with rotation
    - Human-like behavior simulation
    - NSFW consent handling
    """
    
    def __init__(
        self,
        proxy_url: str = None,
        worker_id: int = None,
        headless: bool = True,
    ):
        self.proxy_url = proxy_url or PROXY_URL
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.headless = headless
        
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
        
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _generate_fingerprint(self) -> dict:
        """Generate a random but consistent browser fingerprint."""
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
        
        # Browser launch args for stealth
        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--disable-dev-shm-usage",
            "--disable-browser-side-navigation",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            f"--window-size={fp['viewport']['width']},{fp['viewport']['height']}",
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
        
        # Add proxy if configured
        if self.proxy_url:
            context_options["proxy"] = {"server": self.proxy_url}
            logger.info(f"[Worker {self.worker_id}] Using proxy: {self.proxy_url[:40]}...")
        
        self.context = await self.browser.new_context(**context_options)
        
        # Apply stealth patches
        await self._apply_stealth_patches()
        
        # Create page
        self.page = await self.context.new_page()
        
        # Apply stealth to page if playwright_stealth is available
        if stealth_async:
            await stealth_async(self.page)
        
        # Set extra headers
        await self.page.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": f"{fp['language']},en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Sec-CH-UA": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{fp["platform"]}"',
        })
    
    async def _apply_stealth_patches(self):
        """Apply JavaScript patches to evade detection."""
        fp = self.current_fingerprint
        
        # Comprehensive stealth script
        stealth_script = f"""
        // Override webdriver detection
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
        }});
        
        // Override chrome automation detection
        window.chrome = {{
            runtime: {{}},
            loadTimes: function() {{}},
            csi: function() {{}},
            app: {{}},
        }};
        
        // Override plugins (make it look like real Chrome)
        Object.defineProperty(navigator, 'plugins', {{
            get: () => [
                {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }},
            ],
        }});
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {{
            get: () => ['{fp["language"]}', 'en'],
        }});
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{fp["platform"]}',
        }});
        
        // Override hardware concurrency (realistic values)
        Object.defineProperty(navigator, 'hardwareConcurrency', {{
            get: () => {random.choice([4, 6, 8, 12, 16])},
        }});
        
        // Override device memory
        Object.defineProperty(navigator, 'deviceMemory', {{
            get: () => {random.choice([4, 8, 16, 32])},
        }});
        
        // Override WebGL
        const getParameterProxy = new Proxy(WebGLRenderingContext.prototype.getParameter, {{
            apply: function(target, thisArg, args) {{
                if (args[0] === 37445) {{ // UNMASKED_VENDOR_WEBGL
                    return '{fp["webgl_vendor"]}';
                }}
                if (args[0] === 37446) {{ // UNMASKED_RENDERER_WEBGL
                    return '{fp["webgl_renderer"]}';
                }}
                return Reflect.apply(target, thisArg, args);
            }}
        }});
        WebGLRenderingContext.prototype.getParameter = getParameterProxy;
        
        // Also patch WebGL2
        if (typeof WebGL2RenderingContext !== 'undefined') {{
            WebGL2RenderingContext.prototype.getParameter = getParameterProxy;
        }}
        
        // Override permissions API
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // Override screen properties
        Object.defineProperty(screen, 'width', {{ get: () => {fp['screen']['width']} }});
        Object.defineProperty(screen, 'height', {{ get: () => {fp['screen']['height']} }});
        Object.defineProperty(screen, 'availWidth', {{ get: () => {fp['screen']['availWidth']} }});
        Object.defineProperty(screen, 'availHeight', {{ get: () => {fp['screen']['availHeight']} }});
        Object.defineProperty(screen, 'colorDepth', {{ get: () => {fp['screen']['colorDepth']} }});
        Object.defineProperty(screen, 'pixelDepth', {{ get: () => {fp['screen']['pixelDepth']} }});
        
        // Add slight canvas noise for fingerprint randomization
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function(type) {{
            if (type === 'image/png' && this.width > 16 && this.height > 16) {{
                const context = this.getContext('2d');
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = imageData.data[i] + (Math.random() * 0.1 - 0.05);
                }}
                context.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.apply(this, arguments);
        }};
        """
        
        await self.context.add_init_script(stealth_script)
    
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
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info(f"[Worker {self.worker_id}] Browser closed")
    
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
    
    async def handle_nsfw_consent(self):
        """Click through NSFW/age verification dialogs."""
        consent_selectors = [
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
                logger.debug(f"[Worker {self.worker_id}] Clicked consent: {selector}")
                await asyncio.sleep(0.5)
            except Exception:
                pass  # Button not found, continue
    
    async def goto_with_retry(
        self, 
        url: str, 
        max_retries: int = 3,
        wait_until: str = "domcontentloaded",
    ) -> bool:
        """Navigate to URL with retry logic."""
        for attempt in range(max_retries):
            try:
                response = await self.page.goto(
                    url, 
                    wait_until=wait_until,
                    timeout=30000,
                )
                
                if response and response.status == 200:
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
                logger.error(f"[Worker {self.worker_id}] Navigation error: {e}")
                
                if self.consecutive_failures >= 3:
                    await self.rotate_ip()
                    self.consecutive_failures = 0
                
                await asyncio.sleep(10 * (attempt + 1))
        
        return False

