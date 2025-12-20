"""
Aggregate posts by user and fetch comprehensive user data.
"""
from collections import defaultdict
from datetime import datetime
from typing import Optional

from reddit_client import RedditClient
from supabase_client import SupabaseClient


class UserAggregator:
    """Aggregate posts by user and enrich with profile data."""

    def __init__(self, reddit_client: RedditClient, supabase_client: SupabaseClient):
        self.reddit = reddit_client
        self.supabase = supabase_client

    async def aggregate_posts_by_user(self, posts: list[dict]) -> dict[str, list[dict]]:
        """
        Group posts by author username.
        Returns dict mapping username -> list of posts.
        """
        user_posts = defaultdict(list)
        
        for post in posts:
            author = post.get("author")
            if author and author not in ("[deleted]", "[removed]", "AutoModerator"):
                user_posts[author].append(post)
        
        return dict(user_posts)

    async def fetch_user_profiles(self, usernames: list[str], fetch_posts: bool = True) -> dict[str, dict]:
        """
        Fetch profile data and recent posts for multiple users.
        Returns dict mapping username -> profile data (with posts).
        """
        profiles = {}
        total = len(usernames)
        
        for i, username in enumerate(usernames, 1):
            print(f"  Fetching profile {i}/{total}: u/{username}")
            profile = await self.reddit.get_user_profile(username)
            if profile:
                # Also fetch recent posts from user profile for better metrics
                if fetch_posts:
                    user_posts = await self.reddit.get_user_posts(username, limit=25)
                    profile["user_posts"] = user_posts
                    print(f"    -> Found {len(user_posts)} posts from profile")
                profiles[username] = profile
        
        return profiles

    def calculate_posting_frequency(self, posts: list[dict]) -> Optional[float]:
        """Calculate posts per day based on post timestamps."""
        if len(posts) < 2:
            return None
        
        timestamps = []
        for post in posts:
            created_at = post.get("post_created_at")
            if created_at:
                try:
                    if isinstance(created_at, str):
                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    else:
                        dt = created_at
                    timestamps.append(dt)
                except:
                    pass
        
        if len(timestamps) < 2:
            return None
        
        timestamps.sort()
        time_span = (timestamps[-1] - timestamps[0]).total_seconds()
        
        if time_span <= 0:
            return None
        
        days = time_span / 86400  # seconds per day
        if days < 1:
            days = 1
        
        return round(len(posts) / days, 4)

    def merge_extracted_links(self, posts: list[dict], profile: dict) -> list[str]:
        """Merge all extracted links from posts and profile."""
        all_links = set()
        
        # Links from profile
        for link in profile.get("extracted_links", []):
            all_links.add(link)
        
        # Links from posts
        for post in posts:
            for link in post.get("extracted_links", []):
                all_links.add(link)
        
        return list(all_links)

    async def process_and_save_users(
        self, 
        posts: list[dict], 
        subreddit_id: str = None
    ) -> dict:
        """
        Process posts, aggregate by user, fetch profiles, and save to database.
        Returns stats about the processing.
        """
        stats = {
            "posts_processed": len(posts),
            "unique_users": 0,
            "users_saved": 0,
            "posts_saved": 0,
        }
        
        if not posts:
            return stats
        
        # Group posts by user
        user_posts = await self.aggregate_posts_by_user(posts)
        stats["unique_users"] = len(user_posts)
        
        if not user_posts:
            return stats
        
        print(f"  Found {len(user_posts)} unique users from {len(posts)} posts")
        
        # Fetch user profiles (including their recent posts)
        profiles = await self.fetch_user_profiles(list(user_posts.keys()), fetch_posts=True)
        
        # Process each user
        for username, subreddit_posts in user_posts.items():
            profile = profiles.get(username, {"reddit_username": username})
            
            # Use posts from user profile if available (more accurate), otherwise use subreddit posts
            profile_posts = profile.get("user_posts", [])
            all_posts = profile_posts if profile_posts else subreddit_posts
            
            # Merge both sets for links and media, but use profile posts for metrics
            combined_posts = list({p.get("reddit_post_id"): p for p in (subreddit_posts + profile_posts)}.values())
            
            # Calculate posting frequency from profile posts (more accurate)
            posting_frequency = self.calculate_posting_frequency(all_posts)
            
            # Merge all extracted links from both sources
            extracted_links = self.merge_extracted_links(combined_posts, profile)
            
            # Prepare lead data
            lead_data = {
                **profile,
                "reddit_username": username,
                "total_posts": len(all_posts),
                "posting_frequency": posting_frequency,
                "extracted_links": extracted_links,
            }
            # Remove user_posts from lead_data (it's used for calculation, not storage)
            lead_data.pop("user_posts", None)
            
            # Save lead to database
            saved_lead = await self.supabase.upsert_lead(lead_data)
            
            if saved_lead:
                stats["users_saved"] += 1
                lead_id = saved_lead["id"]
                
                # Save all combined posts for this user (from both subreddit and profile)
                for post in combined_posts:
                    saved_post = await self.supabase.upsert_post(
                        post, 
                        lead_id=lead_id, 
                        subreddit_id=subreddit_id
                    )
                    if saved_post:
                        stats["posts_saved"] += 1
        
        return stats


