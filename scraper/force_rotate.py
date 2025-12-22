#!/usr/bin/env python3
"""
Force rotate proxy IP and test.
"""
import asyncio
import httpx
import time
from config import PROXY_ROTATION_URL, PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS

async def force_rotate_and_test():
    print("=" * 60)
    print("FORCE ROTATING PROXY IP")
    print("=" * 60)
    
    proxy_url = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    
    # Try to rotate
    print(f"\nRotation URL: {PROXY_ROTATION_URL}")
    print("Attempting rotation...")
    
    rotation_success = False
    for attempt in range(10):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(PROXY_ROTATION_URL)
                print(f"Attempt {attempt + 1}: Status {response.status_code}")
                print(f"Response: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 200:
                        print("✓ IP ROTATION SUCCESSFUL!")
                        rotation_success = True
                        break
                    elif data.get("status") == 429:
                        print(f"⏳ Cooldown active. Waiting 30 seconds...")
                        await asyncio.sleep(30)
                    else:
                        print(f"⚠️ Unexpected response: {data}")
                        break
        except Exception as e:
            print(f"✗ Error: {e}")
            break
    
    if not rotation_success:
        print("\n⚠️ Could not rotate IP. Testing with current IP anyway...")
    else:
        print("\n✓ Waiting 5 seconds for new IP to take effect...")
        await asyncio.sleep(5)
    
    # Test Reddit
    print("\n" + "=" * 60)
    print("TESTING REDDIT WITH (POSSIBLY) NEW IP")
    print("=" * 60)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    # Try multiple subreddits
    test_subs = ["boobs", "asianhotties", "nsfw", "gonewild"]
    
    for sub in test_subs:
        print(f"\n--- Testing r/{sub} ---")
        async with httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(proxy=proxy_url),
            headers=headers,
            timeout=30.0,
            follow_redirects=True
        ) as client:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=5"
            try:
                response = await client.get(url)
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    children = data.get("data", {}).get("children", [])
                    print(f"Posts returned: {len(children)}")
                    if children:
                        print(f"✓ SUCCESS! r/{sub} returned posts!")
                        post = children[0].get("data", {})
                        print(f"  Example: u/{post.get('author')}: {post.get('title', '')[:60]}")
                        return True
                    else:
                        print(f"✗ Still empty")
                else:
                    print(f"✗ Failed with status {response.status_code}")
            except Exception as e:
                print(f"✗ Error: {e}")
            
            await asyncio.sleep(2)  # Rate limit between requests
    
    print("\n" + "=" * 60)
    print("❌ ALL TESTS FAILED - Proxy IP appears to be blocked")
    print("=" * 60)
    print("\nPossible issues:")
    print("1. ProxyEmpire mobile proxy IPs may be flagged by Reddit")
    print("2. Need residential proxies instead of mobile/datacenter")
    print("3. May need to add authentication cookies or session handling")
    return False

if __name__ == "__main__":
    asyncio.run(force_rotate_and_test())

