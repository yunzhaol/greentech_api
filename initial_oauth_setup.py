#!/usr/bin/env python3
"""
GreenTech Painting - Initial OAuth 2.0 Setup
Run this ONCE to get your initial refresh token.
"""
import os
import webbrowser
import requests
from dotenv import load_dotenv

load_dotenv()

# Get credentials from .env
CLIENT_ID = os.getenv("QBO_CLIENT_ID")
CLIENT_SECRET = os.getenv("QBO_CLIENT_SECRET")
QBO_MODE = os.getenv("QBO_MODE", "sandbox")

# Redirect URI - use Intuit's default for testing
REDIRECT_URI = "https://developer.intuit.com/oauth2/http-redirect"

# OAuth endpoints
AUTH_ENDPOINT = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_ENDPOINT = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"

def validate_config():
    """Validates that required config is set"""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ ERROR: QBO_CLIENT_ID and QBO_CLIENT_SECRET must be set in .env file")
        print()
        print("Steps to fix:")
        print("1. Copy .env.example to .env")
        print("2. Go to https://developer.intuit.com")
        print("3. Create an app and get your Client ID and Client Secret")
        print("4. Add them to your .env file")
        return False
    return True

def generate_auth_url():
    """Generates the OAuth authorization URL"""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting openid profile email",
        "redirect_uri": REDIRECT_URI,
        "state": "security_token_greentech_12345"
    }
    
    url_params = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{AUTH_ENDPOINT}?{url_params}"

def exchange_code_for_tokens(auth_code):
    """Exchanges authorization code for access and refresh tokens"""
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': REDIRECT_URI,
    }
    
    print("\n🔄 Exchanging authorization code for tokens...")
    
    response = requests.post(
        TOKEN_ENDPOINT,
        headers=headers,
        data=data,
        auth=(CLIENT_ID, CLIENT_SECRET)
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Token exchange failed: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    """Main OAuth setup flow"""
    print("=" * 70)
    print("GreenTech Painting - QuickBooks OAuth 2.0 Setup")
    print("=" * 70)
    print()
    print(f"Mode: {QBO_MODE.upper()}")
    print()
    
    # Validate configuration
    if not validate_config():
        return
    
    print("✅ Configuration validated")
    print()
    
    # Generate authorization URL
    auth_url = generate_auth_url()
    
    print("STEP 1: Authorize the application")
    print("-" * 70)
    print()
    print("Opening your browser to the QuickBooks authorization page...")
    print()
    print("If the browser doesn't open, manually visit this URL:")
    print(auth_url)
    print()
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("In the browser:")
    print("1. Sign in to your QuickBooks account")
    print("2. Select the company you want to connect")
    print("3. Click 'Connect' to authorize the app")
    print()
    print("You will be redirected to a URL that looks like:")
    print(f"{REDIRECT_URI}?code=...&realmId=...&state=...")
    print()
    
    # Get authorization code from user
    print("STEP 2: Enter the authorization code")
    print("-" * 70)
    print()
    auth_code = input("Paste the 'code' parameter from the URL here: ").strip()
    
    if not auth_code:
        print("❌ No code provided. Exiting.")
        return
    
    print()
    realm_id = input("Paste the 'realmId' parameter from the URL here: ").strip()
    
    if not realm_id:
        print("❌ No realmId provided. Exiting.")
        return
    
    # Exchange code for tokens
    token_data = exchange_code_for_tokens(auth_code)
    
    if not token_data:
        print("❌ Failed to get tokens. Please try again.")
        return
    
    # Display results
    print()
    print("=" * 70)
    print("✅ SUCCESS! Tokens obtained")
    print("=" * 70)
    print()
    print("IMPORTANT: Add these values to your .env file:")
    print()
    print(f"QBO_REFRESH_TOKEN={token_data['refresh_token']}")
    print(f"QBO_REALM_ID={realm_id}")
    print()
    print("Token details:")
    print(f"  Access Token (expires in {token_data['expires_in']}s): {token_data['access_token'][:30]}...")
    print(f"  Refresh Token (expires in ~100 days): {token_data['refresh_token'][:30]}...")
    print(f"  Realm ID (Company ID): {realm_id}")
    print()
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Copy the QBO_REFRESH_TOKEN and QBO_REALM_ID to your .env file")
    print("2. Test the connection by running: python quickbooks_client.py")
    print("3. Process a test quote: python cli_push_estimate.py --json quote_sample.json")
    print()
    print("⚠️  SECURITY REMINDER:")
    print("   - Never commit your .env file to version control")
    print("   - Keep your refresh token secure")
    print("   - Refresh tokens expire after 100 days - you'll need to reauthorize")
    print()

if __name__ == "__main__":
    main()
