"""
Convert browser cookie exports to Playwright format for intel scraper.
Run this once to set up your REDDIT_ACCOUNTS environment variable.
"""
import json

# Paste your cookie arrays here
raw_cookies = [
    # Account 1
    [{"domain": ".reddit.com", "expirationDate": 1798102763.62, "hostOnly": False, "httpOnly": False, "name": "rdt", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": "0", "value": "34d06d3ed340ad0c7233133f12b45bd9"}, {"domain": ".reddit.com", "expirationDate": 1798102763.62, "hostOnly": False, "httpOnly": False, "name": "edgebucket", "path": "/", "sameSite": "unspecified", "secure": True, "session": False, "storeId": "0", "value": "rZ3vgr4F090EhFNtqh"}, {"domain": ".reddit.com", "expirationDate": 1801126774.928012, "hostOnly": False, "httpOnly": False, "name": "loid", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": "0", "value": "000000001ceq8goqi5.2.1730903236896.Z0FBQUFBQm5LM3pFR3dFenlMdzhDWFdMZTVEWlZ2UTFreVcwTzlyYkh6Uk5heF9JR2lsclRKNjh1Z1Z2cjc4al9fVFgxbXhkOUQzN2Y0dmF4Q2hRcUx2bVJBelpfbFI5ME8wZnBXeUZkdWFWVVYyeTAxTlZ2UTVpZlI1a2dkU0xkR285QVNVTGt0Ujk"}, {"domain": ".reddit.com", "expirationDate": 1798102763.62, "hostOnly": False, "httpOnly": False, "name": "csv", "path": "/", "sameSite": "no_restriction", "secure": True, "session": False, "storeId": "0", "value": "2"}, {"domain": "www.reddit.com", "hostOnly": True, "httpOnly": False, "name": "reddit_chat_view", "path": "/", "sameSite": "unspecified", "secure": False, "session": True, "storeId": "0", "value": "closed"}, {"domain": ".reddit.com", "expirationDate": 1798102763.62, "hostOnly": False, "httpOnly": False, "name": "csrf_token", "path": "/", "sameSite": "strict", "secure": True, "session": False, "storeId": "0", "value": "a23a857bca2d95ffc68aea37caf40fb7"}, {"domain": "www.reddit.com", "expirationDate": 1782291574.928549, "hostOnly": True, "httpOnly": False, "name": "subreddit_sort", "path": "/", "sameSite": "strict", "secure": True, "session": False, "storeId": "0", "value": "AUKffAc="}, {"domain": "www.reddit.com", "expirationDate": 1798103077, "hostOnly": True, "httpOnly": False, "name": "reddit_supported_media_codecs", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "video/avc%2Cvideo/vp9"}, {"domain": ".reddit.com", "expirationDate": 1782205357.710422, "hostOnly": False, "httpOnly": True, "name": "reddit_session", "path": "/", "sameSite": "unspecified", "secure": True, "session": False, "storeId": "0", "value": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xY2VxOGdvcWk1IiwiZXhwIjoxNzgyMjA1MzU4LjQ3ODYzMSwiaWF0IjoxNzY2NTY2OTU4LjQ3ODYzMSwianRpIjoiTkNBREtsYTlWNTV0dU9QVFVtUFFVNk9DeGUtemJRIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTczMDkwMzIzNjg5Niwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6MiwiYW1yIjpbInB3ZCJdfQ.F9vPV15DcQOuW_rY_P5jZNdh6m-CNCDbn3SEqqf52iFEjY8aluYjVha89QWa0TN8TQFZkuV3yhF83PF--5bkjIsWxZxd2My0MqntDcyhiIzT2Qnv6wdXn-gxxctgFpK-fm1gfXU07u3cDspSGug81ytfme7oBxfQVMDWPU4ReQDHul2j0FWmp1MTfmVe6egffqJqBGgmkY56nGkiafygM1Eu42pRaHR-3E8fv03aTom6dS1XolPkN98MTU7ox7loL3C3PFush4uta-PocTnSllq_0Af5NCEBuAMZp5r8EvjaXGpBsd61wTpGlEs6DdkO2R9w6FjFTmOUrdQS5zOErg"}, {"domain": ".reddit.com", "expirationDate": 1766653359.283706, "hostOnly": False, "httpOnly": True, "name": "token_v2", "path": "/", "sameSite": "unspecified", "secure": True, "session": False, "storeId": "0", "value": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NjUzMzU5LjA3MDU1OSwiaWF0IjoxNzY2NTY2OTU5LjA3MDU1OSwianRpIjoiU3U3WmxNTEtuUlNZN2RqakNYU1I1YmZZUDMzbGdRIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xY2VxOGdvcWk1IiwiYWlkIjoidDJfMWNlcThnb3FpNSIsImF0IjoxLCJsY2EiOjE3MzA5MDMyMzY4OTYsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJIbE9HWnNKbUpkdjhxV0JiUGVsSE84QmJtRlVSd0xZZURKa21OQU1GbGRrIiwiZmxvIjoyfQ.nIuRxnarq_UfjSGisY_tXUxUWByKfMiuAe3LtaPZ-gSV_vcbkAbqbfNMdIPmcPK1vENBj-_xSSE-TO1vk93N0iCJI2pcXi7c3WHKiK3zAA21pc_G8DyOb_BXcSAxvAHpDyHtp2xQ2Dn6XzYyf-6eCbdE55jPs2cPv_9RFBOzbJdKuImLWTFUeu-rXNmhcJN85oywm0veplcPzVKaGJfkF687OJhWGs3iSQqHXMYorEn6AuhW53Hih8ZPaCJWFv-qPTjb41XY2A7aml6hOUohCSStXJBfDcczDQn3Qm8D3zganjE3UegcTmx6xSkRIcBJ9nW7PEs38WDqc4EhaOp71A"}, {"domain": "www.reddit.com", "expirationDate": 1801126961.456207, "hostOnly": True, "httpOnly": False, "name": "eu_cookie", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "{%22opted%22:true%2C%22nonessential%22:true}"}, {"domain": ".reddit.com", "expirationDate": 1798102964, "hostOnly": False, "httpOnly": False, "name": "theme", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "1"}, {"domain": "www.reddit.com", "expirationDate": 1782118966, "hostOnly": True, "httpOnly": False, "name": "g_state", "path": "/", "sameSite": "unspecified", "secure": False, "session": False, "storeId": "0", "value": "{\"i_l\":0,\"i_ll\":1766566966218,\"i_b\":\"CdkqJL6EHhzjJSe1UHy5AvVxiC5D0FDeo87J5RT+ZFg\",\"i_e\":{\"enable_itp_optimization\":0}}"}, {"domain": ".reddit.com", "hostOnly": False, "httpOnly": False, "name": "session_tracker", "path": "/", "sameSite": "no_restriction", "secure": True, "session": True, "storeId": "0", "value": "onjbgmdkjenrhjnagq.0.1766567079381.Z0FBQUFBQnBTNnlua2hHMm5KR3k1aU1RVmxweVVqUXdQcWVIRHlULWIxZUJ3elZUdm92dUpwRHc0VUJXTEpqWnF0d0pqbEhpcjZFSHZaSUl3cm5qUGpEeXlLVlZYb1JfckNGeTg5UjVwcjJsU2QxU2U5Nm9sRmtSOFlOZnJLeFd0emRiLXhxV1ZkOTk"}],
    # Account 2... (I'll add placeholder structure for remaining accounts)
]

def convert_browser_cookies_to_playwright(browser_cookies):
    """Convert browser extension cookie format to Playwright format."""
    playwright_cookies = []
    
    for cookie in browser_cookies:
        # Skip session cookies (no expirationDate)
        if cookie.get("session"):
            continue
            
        pw_cookie = {
            "name": cookie["name"],
            "value": cookie["value"],
            "domain": cookie["domain"],
            "path": cookie["path"],
            "secure": cookie.get("secure", False),
            "httpOnly": cookie.get("httpOnly", False),
        }
        
        # Add expiration if present
        if "expirationDate" in cookie:
            pw_cookie["expires"] = int(cookie["expirationDate"])
        
        # Add sameSite if present and valid
        same_site = cookie.get("sameSite", "").lower()
        if same_site in ["strict", "lax", "none"]:
            pw_cookie["sameSite"] = same_site.capitalize()
        
        playwright_cookies.append(pw_cookie)
    
    return playwright_cookies

def extract_username_from_loid(cookies):
    """Try to extract username from loid cookie value."""
    for cookie in cookies:
        if cookie["name"] == "loid":
            # The loid value contains the user ID
            return f"reddit_user_{cookie['value'][:15]}"
    return f"reddit_user_unknown"

# Convert all accounts
accounts = []
for idx, raw_cookie_set in enumerate(raw_cookies, 1):
    username = extract_username_from_loid(raw_cookie_set)
    pw_cookies = convert_browser_cookies_to_playwright(raw_cookie_set)
    
    accounts.append({
        "username": username,
        "cookies": pw_cookies
    })

# Output as JSON for environment variable
print("Add this to your .env file as REDDIT_ACCOUNTS:")
print("=" * 80)
print(json.dumps(accounts, indent=2))
print("=" * 80)
print(f"\nTotal accounts: {len(accounts)}")

