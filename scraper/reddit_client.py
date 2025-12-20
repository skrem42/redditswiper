"""
Async Reddit client using public JSON API endpoints.
"""
import asyncio
import re
from typing import Optional
from datetime import datetime
import httpx

from config import (
    REDDIT_BASE_URL,
    REDDIT_USER_AGENT,
    SCRAPE_DELAY_SECONDS,
    LINK_PATTERNS,
)


class RedditClient:
    """Async client for Reddit's public JSON API."""

    def __init__(self):
        self.base_url = REDDIT_BASE_URL
        self.headers = {
            "User-Agent": REDDIT_USER_AGENT,
            "Accept": "application/json",
        }
        self.client: Optional[httpx.AsyncClient] = None
        self.last_request_time = 0
        self.link_patterns = [re.compile(p, re.IGNORECASE) for p in LINK_PATTERNS]

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
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

    async def _get_json(self, url: str) -> Optional[dict]:
        """Make a rate-limited GET request and return JSON."""
        await self._rate_limit()
        try:
            response = await self.client.get(url)
            if response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                await asyncio.sleep(retry_after)
                return await self._get_json(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error for {url}: {e}")
            return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
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

    async def get_user_posts(self, username: str, limit: int = 25) -> list[dict]:
        """Fetch recent posts from a user's profile."""
        posts = []
        url = f"{self.base_url}/user/{username}/submitted.json?limit={limit}&sort=new"
        
        data = await self._get_json(url)
        if not data or "data" not in data:
            return []
        
        children = data["data"].get("children", [])
        
        for child in children:
            post_data = child.get("data", {})
            
            # Skip non-posts (comments, etc.)
            if child.get("kind") != "t3":
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
                "subreddit_name": post_data.get("subreddit", ""),
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
        
        return posts

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


