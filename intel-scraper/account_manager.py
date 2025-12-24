"""
Reddit Account Manager for Parallel Scraping

Manages a pool of Reddit accounts for parallel browser-based scraping.
Each browser context gets its own account to avoid session conflicts
when using rotating IPs.
"""
import asyncio
import logging
import json
import os
from typing import Optional
from dataclasses import dataclass
from datetime import datetime

from config import REDDIT_ACCOUNTS, REDDIT_USERNAME, REDDIT_PASSWORD

logger = logging.getLogger(__name__)


@dataclass
class RedditAccount:
    """Represents a Reddit account with session cookies."""
    username: str
    reddit_session: str  # Main session cookie (long-lived)
    token_v2: str  # Auth token (needs periodic refresh)
    loid: str = ""  # User identifier cookie
    eu_cookie: str = '{"opted":true,"nonessential":true}'  # Cookie consent
    
    # Tracking
    in_use: bool = False
    last_used: Optional[datetime] = None
    total_requests: int = 0
    failed_requests: int = 0
    
    def get_cookies(self) -> list[dict]:
        """Get cookies in Playwright format."""
        cookies = [
            {
                "name": "reddit_session",
                "value": self.reddit_session,
                "domain": ".reddit.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            },
            {
                "name": "token_v2",
                "value": self.token_v2,
                "domain": ".reddit.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            },
            {
                "name": "eu_cookie",
                "value": self.eu_cookie,
                "domain": "www.reddit.com",
                "path": "/",
            },
            {
                "name": "csv",
                "value": "2",
                "domain": ".reddit.com",
                "path": "/",
                "secure": True,
            },
        ]
        
        if self.loid:
            cookies.append({
                "name": "loid",
                "value": self.loid,
                "domain": ".reddit.com",
                "path": "/",
                "secure": True,
            })
        
        return cookies


class AccountManager:
    """
    Manages a pool of Reddit accounts for parallel scraping.
    
    Thread-safe account acquisition and release using asyncio locks.
    Each account can only be used by one browser context at a time.
    """
    
    def __init__(self, accounts: list[dict] = None):
        """
        Initialize account manager.
        
        Args:
            accounts: List of account dicts with keys:
                - username: Reddit username
                - reddit_session: Session cookie value
                - token_v2: Auth token cookie value
                - loid: (optional) User identifier cookie
        """
        self._accounts: list[RedditAccount] = []
        self._lock = asyncio.Lock()
        self._available = asyncio.Condition()
        
        # Load accounts from config or parameter
        account_data = accounts or REDDIT_ACCOUNTS
        
        if account_data:
            self._load_accounts(account_data)
            logger.info(f"AccountManager: Loaded {len(self._accounts)} accounts")
        else:
            # Fallback to legacy single account with hardcoded cookies
            logger.warning("AccountManager: No accounts configured, using legacy hardcoded session")
            self._load_legacy_account()
    
    def _load_accounts(self, accounts: list[dict]):
        """Load accounts from config data."""
        for acc in accounts:
            if not acc.get("username") or not acc.get("reddit_session"):
                logger.warning(f"Skipping incomplete account config: {acc.get('username', 'unknown')}")
                continue
            
            self._accounts.append(RedditAccount(
                username=acc["username"],
                reddit_session=acc["reddit_session"],
                token_v2=acc.get("token_v2", ""),
                loid=acc.get("loid", ""),
            ))
    
    def _load_legacy_account(self):
        """Load the legacy hardcoded account from stealth_browser.py."""
        # These are the hardcoded cookies from the original stealth_browser.py
        self._accounts.append(RedditAccount(
            username="petitebbyxoxod",
            reddit_session="eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xcWlkcG4zZXY2IiwiZXhwIjoxNzgxNDQxNzMzLjc0MTQ4NSwiaWF0IjoxNzY1ODAzMzMzLjc0MTQ4NSwianRpIjoibGJCWmllUDRZMm5DbjllbjRmWjF5WjJiN0xHVkNnIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTc0ODY4NzA2NDY0OCwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6Mn0.zXGMEwAUYTrPLomjba0YtBSyv6gOYWCD2qEs7fsMrniSuMta6HtNxPpIWrdmEfXfO9w-SLWeHmJMwz9HEMkWY6HVuEkGCWu77KzCmegInl3s9kYd3HVjRmT59ivtLjJG-AegYPLLQ_W11iVqETlDytbzEiXqldJlYtHomj2mJjzdrZbbs-JhvGMUiiR89PJIvKGVnMoKPhm4fJtqeBorZOOhNluNXyfKLVfEFlCborNT_GVmyf6J0ncm-TZDQqlbWR4JlnJhTxAo6-eOt2cisgZGrtaUoG_pg4UYKFpX4UyH7zWnuhqVRXtWfdloqLAi5nRsO7Shv4LArp1jDqN1WQ",
            token_v2="eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NTYzNTY5LjAxNzY4NywiaWF0IjoxNzY2NDc3MTY5LjAxNzY4NywianRpIjoiV2lMNWZ3NFVYWFoyZ0NuWk5FQ1BLaXhmd3pTUjJ3IiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xcWlkcG4zZXY2IiwiYWlkIjoidDJfMXFpZHBuM2V2NiIsImF0IjoxLCJsY2EiOjE3NDg2ODcwNjQ2NDgsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJOTldRUFlWUjhMUm85c1ROWXRDcHBVSVE3cWJCbGdVaUprSC1jU1VzUW5BIiwiZmxvIjoyfQ.Kfn7YF31igeXmjx5d6PzhfMQbSlmjpvuYYq6nqWITIkgBFB0v2MUUYXnvEmF6_kv5qstBLRbdxCYnG1pQBUV_06lsURz-3h7SXzf-cYiXlciOGwdVNhfLzmWA892g8cNQEzjOog3-05zIwHUuiDy6w_pOaS3AiIKgEiKNI_BVfCBmcyfmZgLRJzUSg5c88fjE7gZPNmeKV3p9uSK1N1PpftP33ZQjonGSGi66tVpXl01Rq1ZgBpjfRuRE2jeP2Q5aXlJsVZVz6wUHFpde5j9ZQiavjzm0JRp5k0_MOrwaR2TO9GsLO8LGwtgG80UW5F6kVH3I2HdgC-B_h96MHUE4w",
            loid="000000001qidpn3ev6.2.1748687064648.Z0FBQUFBQm9PdGpZb0NMZ0Z2NEFUVGZLN0hQVDBxZF84WWJ1TldhLXlFTHlUdWVSQWhXQThPdzFhODVxcllaLWZKZTk0UVRjUEI2cnBVUXNWZWpPdlhFeHY2SEVURy01OENIUkhsYzUycVJzS01mQS0ySll2SE5uZ0J2NkhnaWVnWDRnS25qbWp0ZDA",
        ))
    
    @property
    def total_accounts(self) -> int:
        """Total number of accounts in the pool."""
        return len(self._accounts)
    
    @property
    def available_accounts(self) -> int:
        """Number of accounts currently available."""
        return sum(1 for acc in self._accounts if not acc.in_use)
    
    async def acquire(self, timeout: float = 30.0) -> Optional[RedditAccount]:
        """
        Acquire an available account from the pool.
        
        Blocks until an account is available or timeout is reached.
        
        Args:
            timeout: Maximum seconds to wait for an account
            
        Returns:
            RedditAccount if acquired, None if timeout
        """
        async with self._lock:
            # First, try to find an available account
            for account in self._accounts:
                if not account.in_use:
                    account.in_use = True
                    account.last_used = datetime.utcnow()
                    logger.debug(f"AccountManager: Acquired account {account.username}")
                    return account
        
        # No accounts available, wait for one
        try:
            async with self._available:
                await asyncio.wait_for(
                    self._wait_for_available(),
                    timeout=timeout
                )
                
                async with self._lock:
                    for account in self._accounts:
                        if not account.in_use:
                            account.in_use = True
                            account.last_used = datetime.utcnow()
                            logger.debug(f"AccountManager: Acquired account {account.username}")
                            return account
        except asyncio.TimeoutError:
            logger.warning("AccountManager: Timeout waiting for available account")
            return None
        
        return None
    
    async def _wait_for_available(self):
        """Wait until an account becomes available."""
        async with self._available:
            await self._available.wait()
    
    async def release(self, account: RedditAccount):
        """
        Release an account back to the pool.
        
        Args:
            account: The account to release
        """
        async with self._lock:
            account.in_use = False
            logger.debug(f"AccountManager: Released account {account.username}")
        
        # Notify waiting tasks
        async with self._available:
            self._available.notify()
    
    async def record_request(self, account: RedditAccount, success: bool = True):
        """
        Record a request result for an account.
        
        Args:
            account: The account that made the request
            success: Whether the request succeeded
        """
        account.total_requests += 1
        if not success:
            account.failed_requests += 1
    
    def get_stats(self) -> dict:
        """Get statistics about account usage."""
        return {
            "total_accounts": self.total_accounts,
            "available_accounts": self.available_accounts,
            "accounts": [
                {
                    "username": acc.username,
                    "in_use": acc.in_use,
                    "total_requests": acc.total_requests,
                    "failed_requests": acc.failed_requests,
                    "last_used": acc.last_used.isoformat() if acc.last_used else None,
                }
                for acc in self._accounts
            ]
        }


# Singleton instance for easy access
_account_manager: Optional[AccountManager] = None


def get_account_manager() -> AccountManager:
    """Get the global account manager instance."""
    global _account_manager
    if _account_manager is None:
        _account_manager = AccountManager()
    return _account_manager

