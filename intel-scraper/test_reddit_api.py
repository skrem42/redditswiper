import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            'https://www.reddit.com/r/freeuse/about.json',
            headers={'User-Agent': 'Mozilla/5.0'},
            follow_redirects=True
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(json.dumps(data, indent=2)[:1000])
        else:
            print(resp.text[:500])

asyncio.run(test())

