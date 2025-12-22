"""
Supabase client for Intel Scraper.
Handles reading from subreddit_queue and writing to nsfw_subreddit_intel.
"""
from datetime import datetime
from typing import Optional
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_ANON_KEY


class SupabaseClient:
    """Supabase client for intel scraper operations."""
    
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    
    # ==================== Subreddit Intel ====================

    async def upsert_subreddit_intel(self, data: dict) -> Optional[dict]:
        """Insert or update subreddit intelligence data."""
        try:
            intel_data = {
                "subreddit_name": data["subreddit_name"].lower(),
                "display_name": data.get("display_name"),
                "subscribers": data.get("subscribers"),
                "weekly_visitors": data.get("weekly_visitors"),
                "weekly_contributions": data.get("weekly_contributions"),
                "competition_score": data.get("competition_score"),
                "description": data.get("description"),
                "rules_count": data.get("rules_count", 0),
                "created_utc": data.get("created_utc"),
                "is_verified": data.get("is_verified", False),
                "allows_images": data.get("allows_images", True),
                "allows_videos": data.get("allows_videos", True),
                "allows_polls": data.get("allows_polls", True),
                "post_requirements": data.get("post_requirements", {}),
                "moderator_count": data.get("moderator_count", 0),
                "community_icon_url": data.get("community_icon_url"),
                "banner_url": data.get("banner_url"),
                "last_scraped_at": data.get("last_scraped_at", datetime.utcnow().isoformat()),
                "scrape_status": data.get("scrape_status", "completed"),
                "error_message": data.get("error_message"),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            result = self.client.table("nsfw_subreddit_intel").upsert(
                intel_data,
                on_conflict="subreddit_name"
            ).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error upserting subreddit intel {data.get('subreddit_name')}: {e}")
            return None

    async def mark_intel_failed(self, subreddit_name: str, error_message: str) -> bool:
        """Mark a subreddit intel scrape as failed."""
        try:
            self.client.table("nsfw_subreddit_intel").upsert({
                "subreddit_name": subreddit_name.lower(),
                "scrape_status": "failed",
                "error_message": error_message,
                "updated_at": datetime.utcnow().isoformat(),
            }, on_conflict="subreddit_name").execute()
            return True
        except Exception as e:
            print(f"Error marking intel failed {subreddit_name}: {e}")
            return False

    async def get_pending_intel_scrapes(self, limit: int = 50, min_subscribers: int = 5000) -> list[dict]:
        """
        Get subreddits that need intel scraping.
        Pulls from subreddit_queue where status=completed (already crawled)
        and not yet in nsfw_subreddit_intel or needs refresh.
        """
        try:
            # Get all subreddits from intel table
            intel_result = self.client.table("nsfw_subreddit_intel").select(
                "subreddit_name"
            ).execute()
            
            scraped_names = set(
                row["subreddit_name"].lower() 
                for row in (intel_result.data or [])
            )
            
            # Get completed subreddits from queue that haven't been scraped
            queue_result = self.client.table("subreddit_queue").select(
                "subreddit_name, subscribers"
            ).eq(
                "status", "completed"
            ).gte(
                "subscribers", min_subscribers
            ).order(
                "subscribers", desc=True
            ).limit(limit * 3).execute()  # Fetch extra to filter
            
            # Filter out already scraped
            pending = []
            for row in (queue_result.data or []):
                if row["subreddit_name"].lower() not in scraped_names:
                    pending.append(row)
                    if len(pending) >= limit:
                        break
            
            return pending
        except Exception as e:
            print(f"Error getting pending intel scrapes: {e}")
            return []

    async def get_intel_stats(self) -> dict:
        """Get statistics about the intel table."""
        try:
            result = self.client.table("nsfw_subreddit_intel").select(
                "scrape_status"
            ).execute()
            
            data = result.data or []
            
            return {
                "total": len(data),
                "completed": len([d for d in data if d.get("scrape_status") == "completed"]),
                "pending": len([d for d in data if d.get("scrape_status") == "pending"]),
                "failed": len([d for d in data if d.get("scrape_status") == "failed"]),
            }
        except Exception as e:
            print(f"Error getting intel stats: {e}")
            return {"total": 0, "completed": 0, "pending": 0, "failed": 0}


