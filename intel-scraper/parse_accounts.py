#!/usr/bin/env python3
"""
Parse Reddit account cookies from browser export JSON.
Extracts only the 3 essential cookies needed: reddit_session, token_v2, loid

Usage:
    1. Export cookies from browser (JSON format)
    2. Save to redditaccounts.json
    3. Run: python parse_accounts.py
    4. Copy output to config.py REDDIT_ACCOUNTS list
"""
import json
import sys
from pathlib import Path

def parse_reddit_cookies(cookies_file='redditaccounts.json'):
    """Parse Reddit cookies and extract accounts."""
    
    file_path = Path(cookies_file)
    if not file_path.exists():
        print(f"❌ Error: {cookies_file} not found!")
        print("\n📝 Instructions:")
        print("   1. Log into Reddit in browser")
        print("   2. Export cookies (use browser extension or DevTools)")
        print("   3. Save as 'redditaccounts.json' in intel-scraper/")
        print("   4. Run this script again")
        return []
    
    if file_path.stat().st_size == 0:
        print(f"❌ Error: {cookies_file} is empty!")
        print("\n📝 Please paste your Reddit account cookies into the file")
        return []
    
    try:
        with open(file_path, 'r') as f:
            cookies = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON Error: {e}")
        print("\nMake sure the file contains valid JSON (array of cookie objects)")
        return []
    
    if not isinstance(cookies, list):
        print("❌ Error: Expected JSON array of cookies")
        return []
    
    print(f"📊 Found {len(cookies)} cookies")
    
    # Group cookies by account (look for reddit_session which identifies unique accounts)
    accounts = []
    current_account = {}
    
    for cookie in cookies:
        if not isinstance(cookie, dict):
            continue
            
        name = cookie.get('name')
        value = cookie.get('value')
        
        if not name or not value:
            continue
        
        if name == 'reddit_session':
            # Start new account
            if current_account and 'reddit_session' in current_account:
                accounts.append(current_account)
            current_account = {'reddit_session': value}
        elif name == 'token_v2' and current_account:
            current_account['token_v2'] = value
        elif name == 'loid' and current_account:
            current_account['loid'] = value
    
    # Add last account
    if current_account and 'reddit_session' in current_account:
        accounts.append(current_account)
    
    # Add usernames
    for i, acc in enumerate(accounts, 1):
        acc['username'] = f'reddit_account_{i}'
    
    print(f"✅ Extracted {len(accounts)} Reddit accounts\n")
    
    # Validate accounts
    valid_accounts = []
    for i, acc in enumerate(accounts, 1):
        has_session = 'reddit_session' in acc and len(acc['reddit_session']) > 100
        has_token = 'token_v2' in acc and len(acc['token_v2']) > 100
        has_loid = 'loid' in acc
        
        if has_session and has_token:
            valid_accounts.append(acc)
            print(f"  ✅ Account {i}: Valid (session={len(acc['reddit_session'])} chars, token={len(acc['token_v2'])} chars, loid={'yes' if has_loid else 'no'})")
        else:
            print(f"  ⚠️  Account {i}: Missing data (session={has_session}, token={has_token})")
    
    return valid_accounts

def format_for_config(accounts):
    """Format accounts for config.py"""
    if not accounts:
        return "REDDIT_ACCOUNTS = []"
    
    output = "REDDIT_ACCOUNTS = [\n"
    for acc in accounts:
        output += "    {\n"
        output += f"        \"username\": \"{acc['username']}\",\n"
        output += f"        \"reddit_session\": \"{acc['reddit_session']}\",\n"
        output += f"        \"token_v2\": \"{acc.get('token_v2', '')}\",\n"
        output += f"        \"loid\": \"{acc.get('loid', '')}\",\n"
        output += "    },\n"
    output += "]"
    return output

def main():
    print("=" * 60)
    print("REDDIT ACCOUNT COOKIE PARSER")
    print("=" * 60)
    print()
    
    accounts = parse_reddit_cookies()
    
    if not accounts:
        print("\n❌ No valid accounts found!")
        sys.exit(1)
    
    print(f"\n✅ {len(accounts)} valid accounts ready!")
    print("\n" + "=" * 60)
    print("COPY THIS TO intel-scraper/config.py:")
    print("=" * 60)
    print()
    print(format_for_config(accounts))
    print()
    print("=" * 60)
    print(f"\n💡 Tip: You now have {len(accounts)} accounts for parallel scraping")
    print(f"   Set BROWSER_POOL_SIZE={min(len(accounts), 10)} in config.py")

if __name__ == "__main__":
    main()

