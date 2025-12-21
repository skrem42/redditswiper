"""
Async Reddit client using public JSON API endpoints.
Supports rotating proxy with automatic IP rotation on rate limits.
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
    SCRAPE_DELAY_SECONDS,
    LINK_PATTERNS,
    PROXY_URL,
    PROXY_ROTATION_URL,
    RATE_LIMIT_WAIT_SECONDS,
    PROXIES,
)


class RedditClient:
    """Async client for Reddit's public JSON API with rotating proxy support."""

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
        }
        self.client: Optional[httpx.AsyncClient] = None
        self.last_request_time = 0
        self.link_patterns = [re.compile(p, re.IGNORECASE) for p in LINK_PATTERNS]
        
        # Proxy support - use configured proxy URL by default
        self.proxy = proxy or PROXY_URL
        self.worker_id = worker_id or random.randint(1000, 9999)
        
        # Fallback to legacy proxy list if no single proxy configured
        if not self.proxy and PROXIES:
            self.proxy = random.choice(PROXIES)
        
        # Track rate limit rotations
        self.rotation_count = 0
        
        # Track consecutive 403s (indicates IP block, not just single sub issue)
        self.consecutive_403s = 0
        self.max_403s_before_rotation = 2  # Rotate after 2 consecutive 403s

    async def __aenter__(self):
        # Configure proxy if available
        transport = None
        if self.proxy:
            print(f"[Worker {self.worker_id}] Using rotating proxy: {self.proxy[:40]}...")
            transport = httpx.AsyncHTTPTransport(proxy=self.proxy)
        
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

    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_request_time
        if elapsed < SCRAPE_DELAY_SECONDS:
            await asyncio.sleep(SCRAPE_DELAY_SECONDS - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()

    async def _rotate_ip(self):
        """Call the proxy rotation API to get a new IP address."""
        if not PROXY_ROTATION_URL:
            print(f"[Worker {self.worker_id}] No rotation URL configured, skipping IP rotation")
            return False
        
        try:
            # Use a separate client without proxy to call the rotation API
            async with httpx.AsyncClient(timeout=30.0) as rotation_client:
                print(f"[Worker {self.worker_id}] Rotating proxy IP via API...")
                response = await rotation_client.get(PROXY_ROTATION_URL)
                if response.status_code == 200:
                    self.rotation_count += 1
                    print(f"[Worker {self.worker_id}] ✓ IP rotated successfully (rotation #{self.rotation_count})")
                    return True
                else:
                    print(f"[Worker {self.worker_id}] ✗ IP rotation failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"[Worker {self.worker_id}] ✗ IP rotation error: {e}")
            return False

    async def _get_json(self, url: str) -> Optional[dict]:
        """Make a rate-limited GET request and return JSON."""
        await self._rate_limit()
        try:
            response = await self.client.get(url)
            
            # Handle 429 rate limit
            if response.status_code == 429:
                print(f"[Worker {self.worker_id}] Rate limited (429). Rotating IP and waiting {RATE_LIMIT_WAIT_SECONDS}s...")
                self.consecutive_403s = 0  # Reset 403 counter
                await self._rotate_ip()
                await asyncio.sleep(RATE_LIMIT_WAIT_SECONDS)
                return await self._get_json(url)
            
            # Handle 403 forbidden - Reddit IP block
            if response.status_code == 403:
                self.consecutive_403s += 1
                print(f"[Worker {self.worker_id}] 403 Forbidden (count: {self.consecutive_403s}/{self.max_403s_before_rotation})")
                
                if self.consecutive_403s >= self.max_403s_before_rotation:
                    print(f"[Worker {self.worker_id}] 🚨 IP appears blocked! Rotating IP and waiting 60s...")
                    await self._rotate_ip()
                    self.consecutive_403s = 0  # Reset counter after rotation
                    await asyncio.sleep(60)  # Wait longer after 403 block
                    return await self._get_json(url)  # Retry this request
                
                return None  # Return None for first 403, let crawler try next sub
            
            # Success - reset 403 counter
            self.consecutive_403s = 0
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                print(f"[Worker {self.worker_id}] Rate limited (429 exception). Rotating IP and waiting {RATE_LIMIT_WAIT_SECONDS}s...")
                self.consecutive_403s = 0
                await self._rotate_ip()
                await asyncio.sleep(RATE_LIMIT_WAIT_SECONDS)
                return await self._get_json(url)
            if e.response.status_code == 403:
                self.consecutive_403s += 1
                print(f"[Worker {self.worker_id}] 403 Forbidden exception (count: {self.consecutive_403s})")
                if self.consecutive_403s >= self.max_403s_before_rotation:
                    print(f"[Worker {self.worker_id}] 🚨 IP appears blocked! Rotating IP...")
                    await self._rotate_ip()
                    self.consecutive_403s = 0
                    await asyncio.sleep(60)
                    return await self._get_json(url)
                return None
            print(f"[Worker {self.worker_id}] HTTP error for {url}: {e}")
            return None
        except Exception as e:
            print(f"[Worker {self.worker_id}] Error fetching {url}: {e}")
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


