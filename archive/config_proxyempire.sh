#!/bin/bash

# This script configures the intel scraper to use ProxyEmpire mobile proxy
# instead of Brightdata residential proxies.

# =============================================================================
# PROXYEMPIRE MOBILE PROXY CONFIGURATION
# Replace with your actual ProxyEmpire credentials
# =============================================================================

# IMPORTANT: Fill in your ProxyEmpire details here
export PROXY_HOST="proxy.proxyempire.io"  # ProxyEmpire proxy server
export PROXY_PORT="9000"  # ProxyEmpire port (usually 9000 or 7777)
export PROXY_USER="YOUR_PROXYEMPIRE_USERNAME"  # Your ProxyEmpire username
export PROXY_PASS="YOUR_PROXYEMPIRE_PASSWORD"  # Your ProxyEmpire password

# ProxyEmpire IP rotation API endpoint (if available)
# This forces a new IP to be assigned to your session
export PROXY_ROTATION_URL="https://proxy.proxyempire.io/rotate?apikey=YOUR_API_KEY"

# =============================================================================
# DISABLE BRIGHTDATA
# =============================================================================
unset BRIGHTDATA_PROXY
unset PROXY_COUNTRY

# =============================================================================
# REDDIT ACCOUNTS CONFIGURATION (keep the same accounts)
# =============================================================================
export REDDIT_ACCOUNTS='[
  {
    "username": "reddit_sa_1ceq8goqi5",
    "reddit_session": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xY2VxOGdvcWk1IiwiZXhwIjoxNzgyMjA1MzU4LjQ3ODYzMSwiaWF0IjoxNzY2NTY2OTU4LjQ3ODYzMSwianRpIjoiTkNBREtsYTlWNTV0dU9QVFVtUFFVNk9DeGUtemJRIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTczMDkwMzIzNjg5Niwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6MiwiYW1yIjpbInB3ZCJdfQ.F9vPV15DcQOuW_rY_P5jZNdh6m-CNCDbn3SEqqf52iFEjY8aluYjVha89QWa0TN8TQFZkuV3yhF83PF--5bkjIsWxZxd2My0MqntDcyhiIzT2Qnv6wdXn-gxxctgFpK-fm1gfXU07u3cDspSGug81ytfme7oBxfQVMDWPU4ReQDHul2j0FWmp1MTfmVe6egffqJqBGgmkY56nGkiafygM1Eu42pRaHR-3E8fv03aTom6dS1XolPkN98MTU7ox7loL3C3PFush4uta-PocTnSllq_0Af5NCEBuAMZp5r8EvjaXGpBsd61wTpGlEs6DdkO2R9w6FjFTmOUrdQS5zOErg",
    "token_v2": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NjUzMzU5LjA3MDU1OSwiaWF0IjoxNzY2NTY2OTU5LjA3MDU1OSwianRpIjoiU3U3WmxNTEtuUlNZN2RqakNYU1I1YmZZUDMzbGdRIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xY2VxOGdvcWk1IiwiYWlkIjoidDJfMWNlcThnb3FpNSIsImF0IjoxLCJsY2EiOjE3MzA5MDMyMzY4OTYsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJIbE9HWnNKbUpkdjhxV0JiUGVsSE84QmJtRlVSd0xZZURKa21OQU1GbGRrIiwiZmxvIjoyfQ.nIuRxnarq_UfjSGisY_tXUxUWByKfMiuAe3LtaPZ-gSV_vcbkAbqbfNMdIPmcPK1vENBj-_xSSE-TO1vk93N0iCJI2pcXi7c3WHKiK3zAA21pc_G8DyOb_BXcSAxvAHpDyHtp2xQ2Dn6XzYyf-6eCbdE55jPs2cPv_9RFBOzbJdKuImLWTFUeu-rXNmhcJN85oywm0veplcPzVKaGJfkF687OJhWGs3iSQqHXMYorEn6AuhW53Hih8ZPaCJWFv-qPTjb41XY2A7aml6hOUohCSStXJBfDcczDQn3Qm8D3zganjE3UegcTmx6xSkRIcBJ9nW7PEs38WDqc4EhaOp71A",
    "loid": "000000001ceq8goqi5.2.1730903236896.Z0FBQUFBQm5LM3pFR3dFenlMdzhDWFdMZTVEWlZ2UTFreVcwTzlyYkh6Uk5heF9JR2lsclRKNjh1Z1Z2cjc4al9fVFgxbXhkOUQzN2Y0dmF4Q2hRcUx2bVJBelpfbFI5ME8wZnBXeUZkdWFWVVYyeTAxTlZ2UTVpZlI1a2dkU0xkR285QVNVTGt0Ujk"
  },
  {
    "username": "reddit_sa_1bb27vsk75",
    "reddit_session": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpsVFdYNlFVUEloWktaRG1rR0pVd1gvdWNFK01BSjBYRE12RU1kNzVxTXQ4IiwidHlwIjoiSldUIn0.eyJzdWIiOiJ0Ml8xYmIyN3Zzazc1IiwiZXhwIjoxNzgyMjA2NDIzLjk3MTQ1OCwiaWF0IjoxNzY2NTY4MDIzLjk3MTQ1OCwianRpIjoiaTRMaDVMWFNJT09YUTVBaGZoOW5PZFI1WFBVWUdnIiwiYXQiOjEsImNpZCI6ImNvb2tpZSIsImxjYSI6MTcyOTUxMzY0MDY0OCwic2NwIjoiZUp5S2pnVUVBQURfX3dFVkFMayIsImZsbyI6MiwiYW1yIjpbInB3ZCJdfQ.cEbH01ZTW0RKtUD7E1cvtPnjxlP7zS0QKv2Fl6odd4qeRqUh6aCzQvuujGsdaBsTAXA6AUQPeSPtkf-FCXr5f3-4qQuR_A0voOF0e4G-NgNOmOI25h4deMboqTN5RInr1tSR0GCOA0jSTbyfb2zdBW9XEfaggS9DbOQXTQETqOmDDsiHFx2flcX19uDOhU2FfOgrd0OCgO8RIkHd4u87LvGxmm6SgWemkshcQC0P3VzkEJIlUGV0Thv5mMP65pwCM0oQNKrrKb_jLB1YNJg3K53GDLgCa9sL-3-8yfKAXrBSbbhdaG6w9HHpUSo227gPQmV8CHlY68bfpPCkbPyPIw",
    "token_v2": "eyJhbGciOiJSUzI1NiIsImtpZCI6IlNIQTI1NjpzS3dsMnlsV0VtMjVmcXhwTU40cWY4MXE2OWFFdWFyMnpLMUdhVGxjdWNZIiwidHlwIjoiSldUIn0.eyJzdWIiOiJ1c2VyIiwiZXhwIjoxNzY2NjU0NDI0LjUxMzEyOSwiaWF0IjoxNzY2NTY4MDI0LjUxMzEyOCwianRpIjoiN3MySTc3MFFfVVpGUGUyTFdkUXRDeUQ2bTZwdXZRIiwiY2lkIjoiMFItV0FNaHVvby1NeVEiLCJsaWQiOiJ0Ml8xYmIyN3Zzazc1IiwiYWlkIjoidDJfMWJiMjd2c2s3NSIsImF0IjoxLCJsY2EiOjE3Mjk1MTM2NDA2NDgsInNjcCI6ImVKeGtrZEdPdERBSWhkLUZhNV9nZjVVX20wMXRjWWFzTFFhb2szbjdEVm9jazcwN2NENHBIUDlES29xRkRDWlhncW5BQkZnVHJUREJSdVQ5bkxtM2cyaU5lOHRZc1puQ0JGbXdGRHJrbUxHc2lRUW1lSklheXhzbW9JTE55Rnl1dEdOTkxUMFFKcWhjTXJlRkhwYzJvYmtiaTU2ZEdGVzVyRHlvc1ZmbDB0akdGTFlueGpjYnF3MnB1QzZuTWtuTFF2a3NYdlRqTjlXMzl2bXpfU2EwSjhPS3F1bUIzaGxKQ0c0c2ZwaW0zZDlUazU2dEN4YTE5M3FRMnVkNjNLNTkxaXcwTzdlZjZfbHJJeG1YWTJoLUp2dDMxeS1oQTQ4OEx6UHFBRWFzNFVjWmRtUWRfbFVIVUxtZ0pHTUo0dE1JNU1ybDIzOEp0bXZUdjhidEV6OThNLUttTl96V0ROUnpDZUxRcF9IMUd3QUFfXzhRMWVUUiIsInJjaWQiOiJKUXFJZUpUR1l2ajlkQk5MSDZPX3BvZHdya3NqT05vZTdUSDRmRUZIamRjIiwiZmxvIjoyfQ.Ui-2KIe6bpom447JtzBmEZ5srwf0h41Y4bWfZ_KiCGiJBfhuBQxWFXBA8ov9jyWHmsn6pJEo0_8KMfnH3w7snciPuwoVQgdpXOZWXS-5HrfgwxOkGcCtmZe8MCY2I-w_4o8Wl89Ek7TxdIYu8Gy1HM731wunuFbhfaDOtFa8xaI8_9Npd5xDFlLg4rLh4Y73GDyG_kU71BYCT_rlDGbdKoS8RFJ2nGKLf8-HG5nv8-GcsrPgQJukB-tjI2f28tZzrd6w9CPoGWWVcgb1mBA1gvrSVQ4mYcKzZsDCU0xRC4BsxbNX22eO9MZb3beu8U5zfWns7r_r262hP8fGkw",
    "loid": "000000001bb27vsk75.2.1729513640648.Z0FBQUFBQm5pcTZLamkzWGFRSUE1WTYtWC1LNWV2VjE4NTlSWHBvVERETVJBR1RIS19zcy1CZFdsUVM0a3FSUDBLRGFDZkJxZ1Z4ZzY4T3FDMGpTWU1rUE10V0hwQU16SlJINzJGNTZlUExDRTZOcUhCVEI1M0cxdGlGbTdpVVM3ZjBZbWEyMWZFQk0"
  }
]'

# =============================================================================
# BROWSER POOL SETTINGS
# =============================================================================
export BROWSER_POOL_SIZE="2"
export CONCURRENT_SUBREDDITS="2"
export HEADLESS="true"

# Reduce timeout back to 30s since mobile proxies should be faster
export PAGE_TIMEOUT_MS="30000"

echo "✓ Environment configured for ProxyEmpire mobile proxy"
echo "✓ Brightdata disabled"
echo "✓ Proxy: $PROXY_HOST:$PROXY_PORT"
echo "✓ Reddit accounts: $(echo "$REDDIT_ACCOUNTS" | jq '. | length') loaded"
echo "✓ Browser pool size: $BROWSER_POOL_SIZE"
echo ""
echo "⚠️  IMPORTANT: Update PROXY_USER, PROXY_PASS, and PROXY_ROTATION_URL above!"
echo ""
echo "Next steps:"
echo "1. Edit this file and add your ProxyEmpire credentials"
echo "2. Source this file: source config_proxyempire.sh"
echo "3. Run intel scraper: python intel_worker.py"

