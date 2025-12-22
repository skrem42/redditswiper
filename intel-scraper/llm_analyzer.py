"""
LLM-based Subreddit Analysis

Uses OpenAI GPT-4o-mini to analyze subreddit rules, description, and metadata
to extract structured information about verification, seller policies, and niche.

Now includes analysis of recent posts and user profiles for better accuracy.
"""
import os
import json
import logging
import asyncio
import httpx
from typing import Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables from scraper/.env
load_dotenv("/Users/calummelling/Desktop/redditscraper/scraper/.env")

logger = logging.getLogger(__name__)


class SubredditLLMAnalyzer:
    """Analyzes subreddit data using LLM to extract structured metadata."""
    
    def __init__(self, api_key: Optional[str] = None, proxy_url: Optional[str] = None, rotation_callback = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        # Using GPT-4o-mini: Latest mini model
        # Cost: $0.150 per 1M input tokens, $0.600 per 1M output tokens
        # Average ~$0.0002 per subreddit analysis
        self.model = "gpt-4o-mini"
        
        # Proxy support
        self.proxy_url = proxy_url
        self.rotation_callback = rotation_callback  # Function to call when rate limited
        logger.info(f"LLM Analyzer initialized with proxy: {'Yes' if proxy_url else 'No'}")
    
    async def _fetch_recent_posts(self, subreddit_name: str, limit: int = 10) -> list:
        """Fetch recent posts from subreddit to analyze posting patterns."""
        url = f"https://www.reddit.com/r/{subreddit_name}/new.json?limit={limit}"
        
        # Use better headers to avoid Reddit blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # Retry with backoff and IP rotation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client_kwargs = {
                    "timeout": 30.0,
                    "follow_redirects": True
                }
                if self.proxy_url:
                    client_kwargs["proxy"] = self.proxy_url
                
                async with httpx.AsyncClient(**client_kwargs) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        posts = data.get("data", {}).get("children", [])
                        
                        post_data = []
                        for post in posts[:limit]:
                            post_info = post.get("data", {})
                            post_data.append({
                                "author": post_info.get("author"),
                                "title": post_info.get("title", ""),
                                "selftext": post_info.get("selftext", "")[:200],  # First 200 chars
                                "is_self": post_info.get("is_self", False),
                                "link_flair_text": post_info.get("link_flair_text"),
                            })
                        return post_data
                    
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited fetching posts for r/{subreddit_name} (attempt {attempt+1}/{max_retries})")
                        if self.rotation_callback and attempt < max_retries - 1:
                            logger.info("Rotating IP due to rate limit...")
                            await self.rotation_callback()
                            await asyncio.sleep(5)
                        else:
                            logger.error(f"Rate limited after {max_retries} attempts")
                            return []
                    
                    else:
                        logger.warning(f"Reddit API returned {response.status_code} for r/{subreddit_name} posts")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        else:
                            return []
                            
            except Exception as e:
                logger.warning(f"Could not fetch posts for r/{subreddit_name} (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return []
    
    async def _fetch_user_profile(self, username: str) -> dict:
        """Fetch user profile to check for seller indicators."""
        url = f"https://www.reddit.com/user/{username}/about.json"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # Retry with backoff and IP rotation
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client_kwargs = {
                    "timeout": 15.0,
                    "follow_redirects": True
                }
                if self.proxy_url:
                    client_kwargs["proxy"] = self.proxy_url
                
                async with httpx.AsyncClient(**client_kwargs) as client:
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        user_data = data.get("data", {})
                        
                        # Check for seller indicators
                        subreddit_name = user_data.get("subreddit", {}).get("display_name", "")
                        description = user_data.get("subreddit", {}).get("public_description", "")
                        
                        # Check for links/CTAs
                        has_links = bool(description and ("http" in description.lower() or "onlyfans" in description.lower() or ".com" in description.lower()))
                        has_cta = bool(description and any(word in description.lower() for word in ["subscribe", "follow", "dm", "message me", "link in", "check out"]))
                        
                        return {
                            "username": username,
                            "has_profile": bool(subreddit_name),
                            "profile_description": description[:200] if description else "",
                            "has_links": has_links,
                            "has_cta": has_cta,
                        }
                    
                    elif response.status_code == 429:
                        logger.warning(f"Rate limited fetching profile for u/{username} (attempt {attempt+1}/{max_retries})")
                        if self.rotation_callback and attempt < max_retries - 1:
                            logger.info("Rotating IP due to rate limit...")
                            await self.rotation_callback()
                            await asyncio.sleep(5)
                        else:
                            logger.error(f"Rate limited after {max_retries} attempts")
                            return {"username": username, "has_profile": False}
                    
                    else:
                        logger.warning(f"Reddit API returned {response.status_code} for u/{username}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)
                        else:
                            return {"username": username, "has_profile": False}
                            
            except Exception as e:
                logger.warning(f"Could not fetch profile for u/{username} (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
        
        return {"username": username, "has_profile": False}

    async def analyze_subreddit(
        self,
        subreddit_name: str,
        description: str,
        rules: list,
        subscribers: int = 0,
        check_posts: bool = True,
    ) -> dict:
        """
        Analyze subreddit metadata using LLM.
        
        Args:
            check_posts: If True, fetch recent posts and user profiles for better accuracy
        
        Returns dict with:
        - verification_required: bool
        - sellers_allowed: str ('allowed', 'not_allowed', 'unknown')
        - niche_categories: list of strings
        - confidence: str ('high', 'medium', 'low')
        - reasoning: str
        """
        try:
            # Build rules text
            rules_text = "\n".join([
                f"- {rule.get('short_name', 'Rule')}: {rule.get('description', '')}"
                for rule in rules
            ]) if rules else "No rules provided"
            
            # Check if rules mention seller policy
            rules_mention_sellers = any(
                keyword in rules_text.lower() 
                for keyword in ["onlyfans", "seller", "promotion", "spam", "advertising", "selling", "promo"]
            )
            
            # Fetch recent posts and analyze posting patterns
            # Only if check_posts is True AND rules don't clearly state seller policy
            posts_data = []
            profile_data = []
            
            should_check_posts = check_posts and not rules_mention_sellers
            
            if should_check_posts:
                logger.info(f"Rules unclear about sellers - checking recent posts for r/{subreddit_name}...")
                posts_data = await self._fetch_recent_posts(subreddit_name, limit=10)
                
                # Sample a few unique authors to check profiles
                if posts_data:
                    unique_authors = list(set([p["author"] for p in posts_data if p["author"] and p["author"] != "[deleted]"]))[:5]
                    logger.info(f"Checking {len(unique_authors)} user profiles...")
                    for author in unique_authors:
                        profile = await self._fetch_user_profile(author)
                        if profile.get("has_profile"):
                            profile_data.append(profile)
                            logger.info(f"  u/{author}: links={profile.get('has_links')}, cta={profile.get('has_cta')}")
                        # Small delay to avoid rate limits
                        await asyncio.sleep(1.5)
            elif check_posts and rules_mention_sellers:
                logger.info(f"Rules clearly mention seller policy - skipping post check for r/{subreddit_name}")
            
            # Create analysis prompt
            prompt = self._build_prompt(
                subreddit_name,
                description,
                rules_text,
                subscribers,
                posts_data,
                profile_data
            )
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing NSFW subreddit rules and policies. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent output
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            logger.info(f"LLM analyzed r/{subreddit_name}: {result.get('confidence', 'unknown')} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis error for r/{subreddit_name}: {e}")
            return self._get_fallback_result()
    
    def _build_prompt(
        self,
        subreddit_name: str,
        description: str,
        rules_text: str,
        subscribers: int,
        posts_data: list = None,
        profile_data: list = None
    ) -> str:
        """Build the analysis prompt for the LLM."""
        
        # Build posts section if available
        posts_section = ""
        if posts_data:
            posts_section = "\n\n**Recent Posts Analysis:**"
            posts_section += f"\nFound {len(posts_data)} recent posts."
            
            # Count self posts vs links
            self_posts = sum(1 for p in posts_data if p.get("is_self"))
            posts_section += f"\n- {self_posts} self posts (text/discussion)"
            posts_section += f"\n- {len(posts_data) - self_posts} link posts (images/videos)"
            
            # Sample titles
            sample_titles = [p["title"][:60] for p in posts_data[:3]]
            if sample_titles:
                posts_section += "\n- Sample titles: " + " | ".join([f'"{t}"' for t in sample_titles])
        
        # Build profile section if available
        profile_section = ""
        if profile_data:
            profile_section = "\n\n**User Profile Analysis:**"
            profile_section += f"\nChecked {len(profile_data)} recent posters:"
            for profile in profile_data:
                indicators = []
                if profile.get("has_links"):
                    indicators.append("has external links")
                if profile.get("has_cta"):
                    indicators.append("has CTAs")
                if indicators:
                    profile_section += f"\n- u/{profile['username']}: {', '.join(indicators)}"
                    if profile.get("profile_description"):
                        profile_section += f" ('{profile['profile_description'][:80]}...')"
        
        return f"""Analyze this NSFW subreddit and extract key information:

**Subreddit:** r/{subreddit_name}
**Subscribers:** {subscribers:,}
**Description:** {description or "No description"}

**Rules:**
{rules_text}{posts_section}{profile_section}

Based on ALL the above information (rules, posts, and user profiles), determine:

1. **Verification Required**: Does this subreddit require users to verify their identity before posting? Look for mentions of "verification", "verified", "verify", "proof", verification posts, etc.

2. **Sellers Allowed**: Are OnlyFans creators, sellers, or self-promotion allowed? Consider BOTH rules AND actual posting patterns:
   
   **FROM RULES:**
   - Return "allowed" if creators/sellers are explicitly welcome OR no restrictions mentioned
   - Return "not_allowed" if there are explicit bans on OnlyFans, sellers, promotion, spam, or "amateur only" rules
   
   **FROM USER PROFILES:**
   - If multiple users have external links, OnlyFans mentions, or CTAs in profiles → likely "allowed"
   - If users are clean with no promotional content → may indicate "not_allowed" policy
   
   **FINAL DECISION:**
   - If rules explicitly ban sellers → "not_allowed" (rules override behavior)
   - If rules allow OR profiles show sellers → "allowed"
   - If unclear from both → "unknown"

3. **Niche Categories**: What are the main content themes/niches? Consider the subreddit name, description, and context. Choose from categories like:
   - Content type: amateur, professional, homemade, verified, gone_wild
   - Body type: petite, curvy, thick, bbw, slim, fit, athletic
   - Ethnicity: asian, latina, ebony, indian, arab, white
   - Content focus: pics, gifs, videos, audio
   - Age/role: milf, teen, college, mature
   - Specific: anal, oral, feet, lingerie, cosplay, roleplay
   - Kink: bdsm, fetish, dom, sub, cuckold
   - Relationship: wife, girlfriend, couples, swingers
   - Other: specific body parts, specific acts, celebrity, etc.

4. **Confidence**: How confident are you in this analysis? (high/medium/low)

Return a JSON object:
{{
  "verification_required": true or false,
  "sellers_allowed": "allowed" or "not_allowed" or "unknown",
  "niche_categories": ["category1", "category2", "category3"],
  "confidence": "high" or "medium" or "low",
  "reasoning": "Brief 1-2 sentence explanation of your analysis"
}}"""
    
    def _get_fallback_result(self) -> dict:
        """Return fallback result if LLM analysis fails."""
        return {
            "verification_required": False,
            "sellers_allowed": "unknown",
            "niche_categories": ["unknown"],
            "confidence": "low",
            "reasoning": "Analysis failed - using fallback defaults"
        }

