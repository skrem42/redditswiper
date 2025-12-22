"""Test Playwright with the proxy."""
import asyncio
from playwright.async_api import async_playwright

async def test_playwright_proxy():
    print("Testing Playwright with proxy...")
    print("-" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        # Test with proxy
        context = await browser.new_context(
            proxy={
                "server": "http://mobdedi.proxyempire.io:9000",
                "username": "2ed80b8624",
                "password": "570abb9a59",
            }
        )
        
        page = await context.new_page()
        
        try:
            print("Navigating to https://api.ipify.org...")
            await page.goto("https://api.ipify.org", wait_until="domcontentloaded", timeout=30000)
            content = await page.content()
            print(f"✓ Page loaded! Content: {content[:200]}")
            
            print("\nNavigating to https://www.reddit.com...")
            await page.goto("https://www.reddit.com", wait_until="domcontentloaded", timeout=30000)
            print(f"✓ Reddit loaded! Title: {await page.title()}")
            
        except Exception as e:
            print(f"✗ Error: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_playwright_proxy())

