"""
Supabase client for storing scraped Reddit data.
"""
from typing import Optional
from datetime import datetime
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_ANON_KEY


class SupabaseClient:
    """Client for interacting with Supabase database."""

    def __init__(self):
        if not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_ANON_KEY environment variable is required")
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    # ==================== Subreddits ====================

    async def upsert_subreddit(self, subreddit: dict) -> Optional[dict]:
        """Insert or update a subreddit."""
        try:
            data = {
                "name": subreddit["name"],
                "display_name": subreddit.get("display_name"),
                "subscribers": subreddit.get("subscribers", 0),
                "description": subreddit.get("description"),
                "is_nsfw": subreddit.get("is_nsfw", True),
                "updated_at": datetime.utcnow().isoformat(),
            }
            
            result = self.client.table("subreddits").upsert(
                data,
                on_conflict="name"
            ).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error upserting subreddit {subreddit.get('name')}: {e}")
            return None

    async def get_subreddits(self) -> list[dict]:
        """Get all subreddits."""
        try:
            result = self.client.table("subreddits").select("*").execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching subreddits: {e}")
            return []

    async def update_subreddit_last_scraped(self, subreddit_id: str) -> None:
        """Update the last_scraped timestamp for a subreddit."""
        try:
            self.client.table("subreddits").update({
                "last_scraped": datetime.utcnow().isoformat()
            }).eq("id", subreddit_id).execute()
        except Exception as e:
            print(f"Error updating subreddit last_scraped: {e}")

    # ==================== Reddit Leads ====================

    async def upsert_lead(self, lead: dict) -> Optional[dict]:
        """Insert or update a Reddit lead (user)."""
        try:
            # Check if lead exists
            existing = self.client.table("reddit_leads").select("id, extracted_links, total_posts, first_seen").eq(
                "reddit_username", lead["reddit_username"]
            ).execute()
            
            now = datetime.utcnow().isoformat()
            
            if existing.data:
                # Update existing lead
                existing_lead = existing.data[0]
                existing_links = existing_lead.get("extracted_links", []) or []
                new_links = lead.get("extracted_links", []) or []
                
                # Merge links, avoiding duplicates
                merged_links = list(set(existing_links + new_links))
                
                data = {
                    "reddit_id": lead.get("reddit_id"),
                    "karma": lead.get("karma", 0),
                    "comment_karma": lead.get("comment_karma", 0),
                    "account_created_at": lead.get("account_created_at"),
                    "avatar_url": lead.get("avatar_url"),
                    "banner_url": lead.get("banner_url"),
                    "total_posts": lead.get("total_posts", existing_lead.get("total_posts", 0)),
                    "posting_frequency": lead.get("posting_frequency"),
                    "last_seen": now,
                    "extracted_links": merged_links,
                    "bio": lead.get("bio"),
                    "updated_at": now,
                }
                
                result = self.client.table("reddit_leads").update(data).eq(
                    "id", existing_lead["id"]
                ).execute()
                
                return result.data[0] if result.data else None
            else:
                # Insert new lead
                data = {
                    "reddit_username": lead["reddit_username"],
                    "reddit_id": lead.get("reddit_id"),
                    "karma": lead.get("karma", 0),
                    "comment_karma": lead.get("comment_karma", 0),
                    "account_created_at": lead.get("account_created_at"),
                    "avatar_url": lead.get("avatar_url"),
                    "banner_url": lead.get("banner_url"),
                    "total_posts": lead.get("total_posts", 0),
                    "posting_frequency": lead.get("posting_frequency"),
                    "first_seen": now,
                    "last_seen": now,
                    "extracted_links": lead.get("extracted_links", []),
                    "bio": lead.get("bio"),
                    "status": "pending",
                }
                
                result = self.client.table("reddit_leads").insert(data).execute()
                return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error upserting lead {lead.get('reddit_username')}: {e}")
            return None

    async def get_lead_by_username(self, username: str) -> Optional[dict]:
        """Get a lead by Reddit username."""
        try:
            result = self.client.table("reddit_leads").select("*").eq(
                "reddit_username", username
            ).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error fetching lead {username}: {e}")
            return None

    async def get_pending_leads(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Get pending leads for review."""
        try:
            result = self.client.table("reddit_leads").select(
                "*, reddit_posts(*)"
            ).eq("status", "pending").order(
                "karma", desc=True
            ).range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching pending leads: {e}")
            return []

    async def update_lead_status(self, lead_id: str, status: str, notes: str = None) -> bool:
        """Update lead status and create decision record."""
        try:
            # Update lead status
            self.client.table("reddit_leads").update({
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", lead_id).execute()
            
            # Create decision record
            decision = "approved" if status == "approved" else "rejected"
            self.client.table("lead_decisions").insert({
                "lead_id": lead_id,
                "decision": decision,
                "notes": notes,
            }).execute()
            
            return True
        except Exception as e:
            print(f"Error updating lead status: {e}")
            return False

    # ==================== Reddit Posts ====================

    async def upsert_post(self, post: dict, lead_id: str, subreddit_id: str = None) -> Optional[dict]:
        """Insert or update a Reddit post."""
        try:
            data = {
                "reddit_post_id": post["reddit_post_id"],
                "lead_id": lead_id,
                "subreddit_id": subreddit_id,
                "subreddit_name": post.get("subreddit_name"),
                "title": post.get("title"),
                "content": post.get("content"),
                "url": post.get("url"),
                "permalink": post.get("permalink"),
                "media_urls": post.get("media_urls", []),
                "upvotes": post.get("upvotes", 0),
                "upvote_ratio": post.get("upvote_ratio"),
                "num_comments": post.get("num_comments", 0),
                "is_nsfw": post.get("is_nsfw", True),
                "post_created_at": post.get("post_created_at"),
            }
            
            result = self.client.table("reddit_posts").upsert(
                data,
                on_conflict="reddit_post_id"
            ).execute()
            
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error upserting post {post.get('reddit_post_id')}: {e}")
            return None

    async def get_posts_for_lead(self, lead_id: str) -> list[dict]:
        """Get all posts for a lead."""
        try:
            result = self.client.table("reddit_posts").select("*").eq(
                "lead_id", lead_id
            ).order("post_created_at", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching posts for lead {lead_id}: {e}")
            return []

    # ==================== Statistics ====================

    async def get_stats(self) -> dict:
        """Get scraping statistics."""
        try:
            leads = self.client.table("reddit_leads").select("id, status", count="exact").execute()
            posts = self.client.table("reddit_posts").select("id", count="exact").execute()
            subreddits = self.client.table("subreddits").select("id", count="exact").execute()
            
            # Count by status
            pending = len([l for l in (leads.data or []) if l.get("status") == "pending"])
            approved = len([l for l in (leads.data or []) if l.get("status") == "approved"])
            rejected = len([l for l in (leads.data or []) if l.get("status") == "rejected"])
            
            return {
                "total_leads": leads.count or 0,
                "total_posts": posts.count or 0,
                "total_subreddits": subreddits.count or 0,
                "pending_leads": pending,
                "approved_leads": approved,
                "rejected_leads": rejected,
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            return {}

    # ==================== Scrape Jobs ====================

    async def get_pending_jobs(self, limit: int = 10) -> list[dict]:
        """Get pending scrape jobs ordered by priority."""
        try:
            result = self.client.table("scrape_jobs").select("*").eq(
                "status", "pending"
            ).order(
                "priority", desc=True
            ).order(
                "created_at", desc=False
            ).limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching pending jobs: {e}")
            return []

    async def claim_job(self, job_id: str) -> bool:
        """Claim a job for processing (set status to processing)."""
        try:
            result = self.client.table("scrape_jobs").update({
                "status": "processing",
                "started_at": datetime.utcnow().isoformat(),
            }).eq("id", job_id).eq("status", "pending").execute()
            return bool(result.data)
        except Exception as e:
            print(f"Error claiming job {job_id}: {e}")
            return False

    async def complete_job(
        self, 
        job_id: str, 
        subreddits_found: int = 0,
        leads_found: int = 0,
        posts_found: int = 0
    ) -> bool:
        """Mark a job as completed with results."""
        try:
            self.client.table("scrape_jobs").update({
                "status": "completed",
                "subreddits_found": subreddits_found,
                "leads_found": leads_found,
                "posts_found": posts_found,
                "completed_at": datetime.utcnow().isoformat(),
            }).eq("id", job_id).execute()
            return True
        except Exception as e:
            print(f"Error completing job {job_id}: {e}")
            return False

    async def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark a job as failed."""
        try:
            self.client.table("scrape_jobs").update({
                "status": "failed",
                "error_message": error_message,
                "completed_at": datetime.utcnow().isoformat(),
            }).eq("id", job_id).execute()
            return True
        except Exception as e:
            print(f"Error failing job {job_id}: {e}")
            return False

    async def update_keyword_scraped(self, keyword_id: str) -> bool:
        """Update keyword stats after scraping."""
        try:
            # Get current times_scraped
            result = self.client.table("search_keywords").select("times_scraped").eq(
                "id", keyword_id
            ).execute()
            
            current = result.data[0].get("times_scraped", 0) if result.data else 0
            
            self.client.table("search_keywords").update({
                "times_scraped": current + 1,
                "last_scraped_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", keyword_id).execute()
            return True
        except Exception as e:
            print(f"Error updating keyword {keyword_id}: {e}")
            return False

    async def get_active_keywords(self) -> list[dict]:
        """Get all active search keywords."""
        try:
            result = self.client.table("search_keywords").select("*").eq(
                "is_active", True
            ).order("priority", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Error fetching keywords: {e}")
            return []


