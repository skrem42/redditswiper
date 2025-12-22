"""Quick test script to verify proxy connectivity."""
import httpx
import asyncio

async def test_proxy():
    proxy_url = "http://2ed80b8624:570abb9a59@mobdedi.proxyempire.io:9000"
    
    print("Testing proxy connection...")
    print(f"Proxy: mobdedi.proxyempire.io:9000")
    print(f"User: 2ed80b8624")
    print("-" * 50)
    
    try:
        async with httpx.AsyncClient(proxy=proxy_url, timeout=30.0) as client:
            print("Attempting to fetch https://api.ipify.org (to see proxy IP)...")
            response = await client.get("https://api.ipify.org?format=json")
            print(f"✓ Proxy works! IP: {response.json()['ip']}")
            print(f"✓ Status: {response.status_code}")
            
            print("\nTesting Reddit access through proxy...")
            response = await client.get("https://www.reddit.com/", follow_redirects=True)
            print(f"✓ Reddit accessible! Status: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Proxy connection failed: {e}")
        print("\nPossible issues:")
        print("  1. Proxy not activated in ProxyEmpire panel")
        print("  2. Wrong credentials or port")
        print("  3. Proxy service is down")

if __name__ == "__main__":
    asyncio.run(test_proxy())

