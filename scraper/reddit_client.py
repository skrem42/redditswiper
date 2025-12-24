"""
Async Reddit client using public JSON API endpoints.
Optimized for Brightdata residential rotating proxies - new IP per request.

For parallel processing, create multiple client instances or use the
provided helper functions for batch operations.
"""
import asyncio
import re
import random
from typing import Optional
from datetime import datetime
import httpx

from config import (
    REDDIT_BASE_URL,
    REDDIT_USER_AGENT,
    LINK_PATTERNS,
    PROXY_URL,
    BRIGHTDATA_PROXY,
    RATE_LIMIT_WAIT_SECONDS,
    MAX_CONCURRENT_REQUESTS,
)


class RedditClient:
    """
    Async client for Reddit's public JSON API.
    
    Optimized for Brightdata residential rotating proxies which provide
    a new IP per request, eliminating the need for manual rotation.
    """

    def __init__(self, proxy: str = None, worker_id: int = None):
        """
        Initialize Reddit client.
        
        Args:
            proxy: Specific proxy URL to use (e.g., "http://user:pass@host:port")
            worker_id: Worker ID for logging (auto-assigned if not provided)
        """
        self.base_url = REDDIT_BASE_URL
        self.headers = {
            "User-Agent": REDDIT_USER_AGENT,
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
        }
        self.client: Optional[httpx.AsyncClient] = None
        self.link_patterns = [re.compile(p, re.IGNORECASE) for p in LINK_PATTERNS]
        
        # Proxy support - prefer Brightdata, fallback to legacy
        self.proxy = proxy or BRIGHTDATA_PROXY or PROXY_URL
        self.worker_id = worker_id or random.randint(1000, 9999)
        self.is_brightdata = bool(BRIGHTDATA_PROXY) or (self.proxy and 'brd.superproxy.io' in self.proxy)
        
        # Stats tracking
        self.requests_made = 0
        self.requests_failed = 0
        self.consecutive_failures = 0

    async def __aenter__(self):
        """Initialize HTTP client with proxy."""
        transport = None
        if self.proxy:
            # Mask password in log
            if '@' in self.proxy:
                proxy_log = self.proxy.split('@')[0][:20] + '...@' + self.proxy.split('@')[1]
            else:
                proxy_log = self.proxy[:40]
            
            proxy_type = "Brightdata (auto-rotating)" if self.is_brightdata else "rotating"
            print(f"[Worker {self.worker_id}] ✓ Using {proxy_type} proxy: {proxy_log}")
            transport = httpx.AsyncHTTPTransport(proxy=self.proxy)
        else:
            print(f"[Worker {self.worker_id}] ⚠️ WARNING: No proxy configured!")
        
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
            transport=transport,
        )
        
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def _get_json(self, url: str, max_retries: int = 3) -> Optional[dict]:
        """
        Make a GET request and return JSON.
        
        With Brightdata, each request gets a new IP, so retries are effective
        without needing explicit rotation.
        """
        for attempt in range(max_retries):
            try:
                response = await self.client.get(url)
                self.requests_made += 1
                
                # Handle rate limit - wait briefly and retry (new IP on retry)
                if response.status_code == 429:
                    wait_time = RATE_LIMIT_WAIT_SECONDS * (attempt + 1)
                    print(f"[Worker {self.worker_id}] Rate limited (429). Waiting {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                
                # Handle 403 forbidden - retry with new IP
                if response.status_code == 403:
                    self.consecutive_failures += 1
                    if attempt < max_retries - 1:
                        print(f"[Worker {self.worker_id}] 403 Forbidden. Retrying... (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(1)
                        continue
                    return None
                
                # Success
                self.consecutive_failures = 0
                response.raise_for_status()
                
                return response.json()
                
            except httpx.HTTPStatusError as e:
                self.requests_failed += 1
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                print(f"[Worker {self.worker_id}] HTTP error for {url}: {e}")
                return None
            except Exception as e:
                self.requests_failed += 1
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                print(f"[Worker {self.worker_id}] Error fetching {url}: {e}")
                return None
        
        return None

    async def search_subreddits(self, query: str = "onlyfans", nsfw: bool = True, limit: int = 50) -> list[dict]:
        """Search for subreddits matching query."""
        subreddits = []
        after = None
        
        while len(subreddits) < limit:
            url = f"{self.base_url}/subreddits/search.json?q={query}&include_over_18={str(nsfw).lower()}&limit=25"
            if after:
                url += f"&after={after}"
            
            data = await self._get_json(url)
            if not data or "data" not in data:
                break
            
            children = data["data"].get("children", [])
            if not children:
                break
            
            for child in children:
                sub_data = child.get("data", {})
                if sub_data.get("over18", False) or not nsfw:
                    subreddits.append({
                        "name": sub_data.get("display_name", ""),
                        "display_name": sub_data.get("display_name_prefixed", ""),
                        "subscribers": sub_data.get("subscribers", 0),
                        "description": sub_data.get("public_description", ""),
                        "is_nsfw": sub_data.get("over18", False),
                    })
            
            after = data["data"].get("after")
            if not after:
                break
        
        return subreddits[:limit]

    async def get_subreddit_posts(
        self, 
        subreddit: str, 
        sort: str = "new", 
        limit: int = 100,
        time_filter: str = "all"
    ) -> list[dict]:
        """Fetch posts from a subreddit."""
        posts = []
        after = None
        
        while len(posts) < limit:
            batch_limit = min(100, limit - len(posts))
            url = f"{self.base_url}/r/{subreddit}/{sort}.json?limit={batch_limit}&t={time_filter}"
            if after:
                url += f"&after={after}"
            
            data = await self._get_json(url)
            
            if not data or "data" not in data:
                break
            
            children = data["data"].get("children", [])
            if not children:
                break
            
            for child in children:
                post_data = child.get("data", {})
                author = post_data.get("author", "[deleted]")
                
                # Skip deleted/removed posts
                if author in ("[deleted]", "[removed]", "AutoModerator"):
                    continue
                
                # Extract links from post content
                content = post_data.get("selftext", "") or ""
                title = post_data.get("title", "") or ""
                combined_text = f"{title} {content}"
                extracted_links = self._extract_links(combined_text)
                
                # Also check post URL
                post_url = post_data.get("url", "")
                extracted_links.extend(self._extract_links(post_url))
                
                # Get media URLs
                media_urls = self._extract_media_urls(post_data)
                
                posts.append({
                    "reddit_post_id": post_data.get("id", ""),
                    "subreddit_name": subreddit,
                    "author": author,
                    "title": title,
                    "content": content,
                    "url": post_url,
                    "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                    "media_urls": media_urls,
                    "upvotes": post_data.get("ups", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0),
                    "num_comments": post_data.get("num_comments", 0),
                    "is_nsfw": post_data.get("over_18", False),
                    "post_created_at": datetime.fromtimestamp(
                        post_data.get("created_utc", 0)
                    ).isoformat() if post_data.get("created_utc") else None,
                    "extracted_links": extracted_links,
                })
            
            after = data["data"].get("after")
            if not after:
                break
        
        return posts

    async def get_user_profile(self, username: str) -> Optional[dict]:
        """Fetch user profile data."""
        url = f"{self.base_url}/user/{username}/about.json"
        data = await self._get_json(url)
        
        if not data or "data" not in data:
            return None
        
        user_data = data["data"]
        
        # Extract links from user bio/description
        bio = user_data.get("subreddit", {}).get("public_description", "") or ""
        extracted_links = self._extract_links(bio)
        
        return {
            "reddit_username": username,
            "reddit_id": user_data.get("id", ""),
            "karma": user_data.get("link_karma", 0) + user_data.get("comment_karma", 0),
            "comment_karma": user_data.get("comment_karma", 0),
            "account_created_at": datetime.fromtimestamp(
                user_data.get("created_utc", 0)
            ).isoformat() if user_data.get("created_utc") else None,
            "avatar_url": user_data.get("icon_img", "").split("?")[0] if user_data.get("icon_img") else None,
            "banner_url": user_data.get("subreddit", {}).get("banner_img", "").split("?")[0] or None,
            "bio": bio,
            "extracted_links": extracted_links,
        }

    async def get_user_posts(self, username: str, limit: int = 25) -> tuple[list[dict], set[str]]:
        """
        Fetch recent posts from a user's profile.
        
        Returns:
            tuple: (list of posts, set of subreddit names user posts in)
        """
        posts = []
        discovered_subs = set()
        url = f"{self.base_url}/user/{username}/submitted.json?limit={limit}&sort=new"
        
        data = await self._get_json(url)
        if not data or "data" not in data:
            return [], set()
        
        children = data["data"].get("children", [])
        
        for child in children:
            post_data = child.get("data", {})
            
            # Skip non-posts (comments, etc.)
            if child.get("kind") != "t3":
                continue
            
            # Track subreddits user posts in (for crawler discovery)
            subreddit_name = post_data.get("subreddit", "")
            if subreddit_name:
                discovered_subs.add(subreddit_name)
            
            # Extract links from post content
            content = post_data.get("selftext", "") or ""
            title = post_data.get("title", "") or ""
            combined_text = f"{title} {content}"
            extracted_links = self._extract_links(combined_text)
            
            # Also check post URL
            post_url = post_data.get("url", "")
            extracted_links.extend(self._extract_links(post_url))
            
            # Get media URLs
            media_urls = self._extract_media_urls(post_data)
            
            posts.append({
                "reddit_post_id": post_data.get("id", ""),
                "subreddit_name": subreddit_name,
                "author": username,
                "title": title,
                "content": content,
                "url": post_url,
                "permalink": f"https://reddit.com{post_data.get('permalink', '')}",
                "media_urls": media_urls,
                "upvotes": post_data.get("ups", 0),
                "upvote_ratio": post_data.get("upvote_ratio", 0),
                "num_comments": post_data.get("num_comments", 0),
                "is_nsfw": post_data.get("over_18", False),
                "post_created_at": datetime.fromtimestamp(
                    post_data.get("created_utc", 0)
                ).isoformat() if post_data.get("created_utc") else None,
                "extracted_links": extracted_links,
            })
        
        return posts, discovered_subs

    async def get_subreddit_info(self, subreddit: str) -> Optional[dict]:
        """
        Fetch subreddit metadata including NSFW status.
        Used by crawler to determine if a discovered subreddit should be added to queue.
        """
        url = f"{self.base_url}/r/{subreddit}/about.json"
        data = await self._get_json(url)
        
        if not data or "data" not in data:
            return None
        
        sub_data = data["data"]
        return {
            "name": sub_data.get("display_name", subreddit),
            "display_name": sub_data.get("display_name_prefixed", f"r/{subreddit}"),
            "subscribers": sub_data.get("subscribers", 0),
            "is_nsfw": sub_data.get("over18", False),
            "description": sub_data.get("public_description", ""),
        }

    def _extract_links(self, text: str) -> list[str]:
        """Extract OnlyFans, Linktree, and other relevant links from text."""
        if not text:
            return []
        
        links = []
        for pattern in self.link_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # Normalize the link
                if not match.startswith("http"):
                    match = f"https://{match}"
                if match not in links:
                    links.append(match)
        return links

    def _extract_media_urls(self, post_data: dict) -> list[str]:
        """Extract media URLs from post data."""
        media_urls = []
        
        # Direct image/video URL
        url = post_data.get("url", "")
        if url and any(ext in url.lower() for ext in [".jpg", ".jpeg", ".png", ".gif", ".mp4", ".webm"]):
            media_urls.append(url)
        
        # Reddit gallery
        if post_data.get("is_gallery") and "media_metadata" in post_data:
            for media_id, media_info in post_data.get("media_metadata", {}).items():
                if media_info.get("status") == "valid":
                    # Get the highest resolution image
                    if "s" in media_info:
                        img_url = media_info["s"].get("u", "").replace("&amp;", "&")
                        if img_url:
                            media_urls.append(img_url)
        
        # Reddit video
        if "secure_media" in post_data and post_data["secure_media"]:
            reddit_video = post_data["secure_media"].get("reddit_video", {})
            if reddit_video.get("fallback_url"):
                media_urls.append(reddit_video["fallback_url"])
        
        # Preview images
        if "preview" in post_data and post_data["preview"]:
            images = post_data["preview"].get("images", [])
            for img in images[:3]:  # Limit to first 3 preview images
                source = img.get("source", {})
                if source.get("url"):
                    media_urls.append(source["url"].replace("&amp;", "&"))
        
        return media_urls

    def get_stats(self) -> dict:
        """Get client statistics."""
        return {
            "requests_made": self.requests_made,
            "requests_failed": self.requests_failed,
            "consecutive_failures": self.consecutive_failures,
        }


# =============================================================================
# Helper functions for parallel batch operations
# =============================================================================

async def fetch_subreddit_batch(
    subreddits: list[str],
    proxy: str = None,
    max_concurrent: int = None,
) -> dict[str, list[dict]]:
    """
    Fetch posts from multiple subreddits in parallel.
    
    Args:
        subreddits: List of subreddit names to fetch
        proxy: Proxy URL (uses config default if not provided)
        max_concurrent: Max concurrent requests (uses config default if not provided)
    
    Returns:
        Dict mapping subreddit name to list of posts
    """
    max_concurrent = max_concurrent or MAX_CONCURRENT_REQUESTS
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def fetch_one(sub_name: str):
        async with semaphore:
            async with RedditClient(proxy=proxy) as client:
                posts = await client.get_subreddit_posts(sub_name)
                results[sub_name] = posts
    
    await asyncio.gather(*[fetch_one(sub) for sub in subreddits])
    return results


async def fetch_user_batch(
    usernames: list[str],
    proxy: str = None,
    max_concurrent: int = None,
) -> dict[str, dict]:
    """
    Fetch profiles for multiple users in parallel.
    
    Args:
        usernames: List of Reddit usernames to fetch
        proxy: Proxy URL (uses config default if not provided)
        max_concurrent: Max concurrent requests (uses config default if not provided)
    
    Returns:
        Dict mapping username to profile data (or None if failed)
    """
    max_concurrent = max_concurrent or MAX_CONCURRENT_REQUESTS
    semaphore = asyncio.Semaphore(max_concurrent)
    results = {}
    
    async def fetch_one(username: str):
        async with semaphore:
            async with RedditClient(proxy=proxy) as client:
                profile = await client.get_user_profile(username)
                posts, discovered_subs = await client.get_user_posts(username)
                results[username] = {
                    "profile": profile,
                    "posts": posts,
                    "discovered_subs": discovered_subs,
                }
    
    await asyncio.gather(*[fetch_one(u) for u in usernames])
    return results
