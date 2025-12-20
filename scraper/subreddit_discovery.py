"""
Discover NSFW subreddits based on configurable search keywords.
"""
from typing import Optional
from reddit_client import RedditClient
from supabase_client import SupabaseClient
from config import SEARCH_KEYWORDS, SUBREDDIT_NAME_FILTERS


class SubredditDiscovery:
    """Discover and manage NSFW subreddits based on search keywords."""

    def __init__(self, reddit_client: RedditClient, supabase_client: SupabaseClient):
        self.reddit = reddit_client
        self.supabase = supabase_client

    async def discover_subreddits(
        self, 
        max_subreddits: int = 50,
        search_keywords: list[str] = None,
        name_filters: list[str] = None
    ) -> list[dict]:
        """
        Search for NSFW subreddits using configurable search keywords.
        
        Args:
            max_subreddits: Maximum number of subreddits to return
            search_keywords: List of search terms (defaults to config.SEARCH_KEYWORDS)
            name_filters: Only include subs containing these strings (defaults to config.SUBREDDIT_NAME_FILTERS)
        
        Returns list of subreddit data dicts.
        """
        keywords = search_keywords or SEARCH_KEYWORDS
        filters = name_filters or SUBREDDIT_NAME_FILTERS
        
        print(f"Discovering NSFW subreddits...")
        print(f"  Search keywords: {keywords}")
        print(f"  Name filters: {filters if filters else 'None (include all)'}")
        
        all_subreddits = {}
        
        for term in keywords:
            print(f"  Searching for: {term}")
            subs = await self.reddit.search_subreddits(
                query=term,
                nsfw=True,
                limit=max_subreddits,
            )
            
            for sub in subs:
                name = sub["name"].lower()
                
                # Apply name filters if specified
                if filters:
                    matches_filter = any(
                        f.lower() in name or f.lower() in name.split() 
                        for f in filters
                    )
                    if not matches_filter:
                        continue
                
                if name not in all_subreddits:
                    all_subreddits[name] = sub
        
        subreddits = list(all_subreddits.values())[:max_subreddits]
        print(f"  Found {len(subreddits)} unique subreddits")
        
        return subreddits

    async def save_subreddits(self, subreddits: list[dict]) -> list[dict]:
        """Save discovered subreddits to database and return with IDs."""
        saved = []
        for sub in subreddits:
            result = await self.supabase.upsert_subreddit(sub)
            if result:
                saved.append(result)
        print(f"  Saved {len(saved)} subreddits to database")
        return saved

    async def get_stored_subreddits(self) -> list[dict]:
        """Get all subreddits from database."""
        return await self.supabase.get_subreddits()

    async def discover_and_save(self, max_subreddits: int = 50) -> list[dict]:
        """Discover new subreddits and save to database."""
        subreddits = await self.discover_subreddits(max_subreddits)
        return await self.save_subreddits(subreddits)


