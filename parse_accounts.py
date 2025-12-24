#!/usr/bin/env python3
"""
Parse Reddit account cookies from browser export JSON.
Extracts the 3 essential cookies needed for authentication.

Usage:
    1. Export cookies from browser (use Cookie-Editor extension)
    2. Save to intel-scraper/redditaccounts.json
    3. Run: python parse_accounts.py
    4. Copy output to intel-scraper/config.py REDDIT_ACCOUNTS list
"""
import json
import sys
from pathlib import Path

def parse_reddit_cookies(cookies_json_path):
    """Extract Reddit session cookies from browser export."""
    
    with open(cookies_json_path, 'r') as f:
        data = json.load(f)
    
    # Check if it's an array of arrays (multiple accounts)
    if isinstance(data, list) and len(data) > 0:
        # Check if first item is a list (array of arrays format)
        if isinstance(data[0], list):
            cookie_arrays = data
        else:
            # Single array of cookies
            cookie_arrays = [data]
    else:
        print("❌ Invalid JSON format")
        return []
    
    all_accounts = []
    
    for cookies in cookie_arrays:
        # Extract account from this cookie set
        account = {}
        for cookie in cookies:
            if isinstance(cookie, dict):
                name = cookie.get('name')
                value = cookie.get('value')
                
                if name == 'reddit_session':
                    account['reddit_session'] = value
                elif name == 'token_v2':
                    account['token_v2'] = value
                elif name == 'loid':
                    account['loid'] = value
        
        # Only add if we have essential cookies
        if 'reddit_session' in account and 'token_v2' in account:
            if 'loid' not in account:
                account['loid'] = ''
            all_accounts.append(account)
    
    # Add usernames
    for i, acc in enumerate(all_accounts, 1):
        acc['username'] = f'reddit_account_{i}'
    
    return all_accounts

def main():
    cookies_file = Path(__file__).parent / 'intel-scraper' / 'redditaccounts.json'
    
    if not cookies_file.exists():
        print(f"❌ File not found: {cookies_file}")
        print("\n📝 To create it:")
        print("  1. Install Cookie-Editor extension in your browser")
        print("  2. Log into Reddit")
        print("  3. Export cookies as JSON")
        print("  4. Save to: intel-scraper/redditaccounts.json")
        sys.exit(1)
    
    if cookies_file.stat().st_size == 0:
        print(f"❌ File is empty: {cookies_file}")
        print("   Add Reddit cookies JSON to the file first")
        sys.exit(1)
    
    print("🔍 Parsing Reddit account cookies...")
    
    try:
        accounts = parse_reddit_cookies(cookies_file)
        
        if not accounts:
            print("❌ No valid Reddit accounts found in cookies")
            print("   Make sure the JSON includes reddit_session and token_v2 cookies")
            sys.exit(1)
        
        print(f"\n✅ Found {len(accounts)} Reddit account(s)\n")
        
        # Validate each account
        for i, acc in enumerate(accounts, 1):
            has_session = len(acc.get('reddit_session', '')) > 100
            has_token = len(acc.get('token_v2', '')) > 100
            has_loid = len(acc.get('loid', '')) > 10
            
            status = "✅" if (has_session and has_token) else "⚠️"
            print(f"  {status} Account {i}: Session={has_session}, Token={has_token}, LOID={has_loid}")
        
        # Generate config format
        print("\n" + "="*80)
        print("COPY THIS TO intel-scraper/config.py (REDDIT_ACCOUNTS list):")
        print("="*80)
        print("\nREDDIT_ACCOUNTS = [")
        
        for acc in accounts:
            print("    {")
            print(f'        "username": "{acc["username"]}",')
            print(f'        "reddit_session": "{acc["reddit_session"]}",')
            print(f'        "token_v2": "{acc["token_v2"]}",')
            print(f'        "loid": "{acc["loid"]}",')
            print("    },")
        
        print("]")
        print("\n" + "="*80)
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {cookies_file}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

