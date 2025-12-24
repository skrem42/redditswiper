#!/usr/bin/env python3
"""
Visual test to debug Intel Worker
Run with: python test_visual.py
"""
import asyncio
import re
from playwright.async_api import async_playwright
from config import PROXY_URL, PROXY_USER, PROXY_PASS, PROXY_SERVER, REDDIT_ACCOUNTS

async def test_visual():
    print("=" * 60)
    print("VISUAL TEST - Intel Worker Debug")
    print("=" * 60)
    print()
    
    # Use first account
    account = REDDIT_ACCOUNTS[0]
    print(f"Using account: {account.get('username', 'unknown')}")
    print(f"Proxy: {PROXY_SERVER}")
    print()
    
    async with async_playwright() as p:
        # Launch browser NON-headless
        browser = await p.chromium.launch(
            headless=False,  # VISUAL MODE
            slow_mo=500,  # Slow down for visibility
        )
        
        # Create context with proxy
        context = await browser.new_context(
            proxy={
                "server": PROXY_SERVER,
                "username": PROXY_USER,
                "password": PROXY_PASS,
            },
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        
        # Set cookies for authentication
        cookies = [
            {"name": "reddit_session", "value": account.get("reddit_session", ""), "domain": ".reddit.com", "path": "/"},
            {"name": "token_v2", "value": account.get("token_v2", ""), "domain": ".reddit.com", "path": "/"},
            {"name": "loid", "value": account.get("loid", ""), "domain": ".reddit.com", "path": "/"},
        ]
        await context.add_cookies([c for c in cookies if c["value"]])
        
        page = await context.new_page()
        
        # Test subreddit
        test_subs = ["gonewild", "onlyfans101", "RealGirls"]
        
        for sub in test_subs:
            print(f"\n{'='*60}")
            print(f"Testing r/{sub}")
            print("="*60)
            
            url = f"https://www.reddit.com/r/{sub}"
            print(f"Navigating to: {url}")
            
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print(f"Response status: {response.status if response else 'None'}")
                
                # Handle NSFW consent
                consent_selectors = [
                    'button:has-text("Yes")',
                    'button:has-text("I am 18")',
                    '[data-testid="over-18-button"]',
                ]
                for selector in consent_selectors:
                    try:
                        btn = await page.wait_for_selector(selector, timeout=2000)
                        if btn:
                            await btn.click()
                            print(f"Clicked consent button: {selector}")
                            await asyncio.sleep(1)
                            break
                    except:
                        pass
                
                # Wait and scroll
                await asyncio.sleep(2)
                await page.evaluate('window.scrollTo(0, 500)')
                await asyncio.sleep(1)
                
                # Get page content
                content = await page.content()
                
                # Check for traffic stats
                print("\nSearching for traffic stats in page HTML...")
                
                # Weekly visitors
                slot_match = re.search(r'slot="weekly-active-users-count"[^>]*>([^<]+)<', content)
                if slot_match:
                    print(f"✅ Found weekly visitors: {slot_match.group(1)}")
                else:
                    print("❌ No weekly-active-users-count slot found")
                
                # Weekly contributions
                for slot_pattern in [
                    r'slot="weekly-posts-count"[^>]*>([^<]+)<',
                    r'slot="weekly-contributions-count"[^>]*>([^<]+)<',
                ]:
                    slot_match = re.search(slot_pattern, content)
                    if slot_match:
                        print(f"✅ Found weekly posts/contributions: {slot_match.group(1)}")
                        break
                else:
                    print("❌ No weekly-posts-count or weekly-contributions-count slot found")
                
                # Check for subscriber count
                sub_match = re.search(r'(\d[\d,]*)\s*members', content, re.IGNORECASE)
                if sub_match:
                    print(f"✅ Found members: {sub_match.group(1)}")
                else:
                    print("❌ No members count found in HTML")
                
                # Save screenshot
                screenshot_path = f"/tmp/reddit_{sub}.png"
                await page.screenshot(path=screenshot_path)
                print(f"📸 Screenshot saved: {screenshot_path}")
                
                # Pause to let you see
                print("\n⏸️  Pausing 5 seconds to view...")
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"❌ Error: {type(e).__name__}: {e}")
        
        print("\n" + "="*60)
        print("Test complete! Check screenshots in /tmp/")
        print("="*60)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_visual())

