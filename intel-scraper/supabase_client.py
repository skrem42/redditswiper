"""
Supabase client for Intel Scraper.
Handles reading from subreddit_queue and writing to nsfw_subreddit_intel.
"""
import logging
from datetime import datetime
from typing import Optional
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_ANON_KEY

logger = logging.getLogger(__name__)


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
        Get subreddits for intel scraping.
        Returns ANY subreddits from queue (any status) that are NOT yet in intel table.
        Uses SQL-based filtering for efficiency.
        """
        try:
            # Use RPC function to get subreddits not in intel table
            # This is much more efficient than client-side filtering
            result = self.client.rpc(
                "get_subreddits_not_in_intel",
                {
                    "p_limit": limit,
                    "p_min_subscribers": min_subscribers
                }
            ).execute()
            
            return result.data or []
            
        except Exception as e:
            # Fallback to client-side filtering if RPC fails
            logger.warning(f"RPC failed, using fallback: {e}")
            try:
                # Get ALL subreddits from queue with pagination (not just limit*20)
                all_queue_subs = []
                page_size = 1000
                offset = 0
                
                while True:
                    queue_result = self.client.table("subreddit_queue").select(
                        "subreddit_name, subscribers"
                    ).gte(
                        "subscribers", min_subscribers
                    ).order(
                        "subscribers", desc=True
                    ).range(offset, offset + page_size - 1).execute()
                    
                    if not queue_result.data or len(queue_result.data) == 0:
                        break
                    
                    all_queue_subs.extend(queue_result.data)
                    
                    if len(queue_result.data) < page_size:
                        break
                    
                    offset += page_size
                
                logger.info(f"Fetched {len(all_queue_subs)} subreddits from queue")
                
                # Get already scraped names with pagination
                all_intel_names = []
                intel_offset = 0
                
                while True:
                    intel_result = self.client.table("nsfw_subreddit_intel").select(
                        "subreddit_name"
                    ).range(intel_offset, intel_offset + page_size - 1).execute()
                    
                    if not intel_result.data or len(intel_result.data) == 0:
                        break
                    
                    all_intel_names.extend(intel_result.data)
                    
                    if len(intel_result.data) < page_size:
                        break
                    
                    intel_offset += page_size
                
                logger.info(f"Fetched {len(all_intel_names)} already-scraped subreddits from intel table")
                
                scraped_names = set(
                    row["subreddit_name"].lower() 
                    for row in all_intel_names
                )
                
                # Filter out already scraped
                pending = []
                for row in all_queue_subs:
                    if row["subreddit_name"].lower() not in scraped_names:
                        pending.append(row)
                        if len(pending) >= limit:
                            break
                
                return pending
            except Exception as e2:
                logger.error(f"Error getting pending intel scrapes: {e2}")
                return []

    async def get_intel_stats(self) -> dict:
        """Get statistics about the intel table using count queries."""
        try:
            # Use count queries instead of fetching all rows
            total_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).execute()
            
            completed_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "completed").execute()
            
            pending_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "pending").execute()
            
            failed_result = self.client.table("nsfw_subreddit_intel").select(
                "*", count="exact", head=True
            ).eq("scrape_status", "failed").execute()
            
            return {
                "total": total_result.count or 0,
                "completed": completed_result.count or 0,
                "pending": pending_result.count or 0,
                "failed": failed_result.count or 0,
            }
        except Exception as e:
            print(f"Error getting intel stats: {e}")
            return {"total": 0, "completed": 0, "pending": 0, "failed": 0}
    
    async def get_null_intel_scrapes(self, limit: int = 50) -> list[dict]:
        """
        Get subreddits that have NULL values for weekly_visitors or weekly_contributions.
        These need to be re-scraped.
        """
        try:
            # Get subreddits with NULL metrics with proper pagination
            all_results = []
            page_size = 1000
            offset = 0
            
            while len(all_results) < limit:
                result = self.client.table("nsfw_subreddit_intel").select(
                    "subreddit_name, weekly_visitors, weekly_contributions"
                ).or_(
                    "weekly_visitors.is.null,weekly_contributions.is.null"
                ).range(offset, offset + page_size - 1).execute()
                
                if not result.data or len(result.data) == 0:
                    break
                
                all_results.extend(result.data)
                
                if len(result.data) < page_size or len(all_results) >= limit:
                    break
                
                offset += page_size
            
            return all_results[:limit]
        except Exception as e:
            print(f"Error getting null intel scrapes: {e}")
            return []


