#!/usr/bin/env python3
"""
Shopify OAuth Helper
Get access token using OAuth 2.0 flow

Usage:
    python shopify_oauth.py --store YOUR_STORE.myshopify.com
"""

import os
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests

# Your app credentials
CLIENT_ID = "2883e52ba712fb1dacf5317dc7da170d"
CLIENT_SECRET = "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"

# Scopes needed for the photo gen pipeline
SCOPES = [
    "read_products",
    "write_products",
    "read_product_images",
    "write_product_images",
]

# Local callback server
REDIRECT_URI = "http://localhost:3000/callback"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback from Shopify."""
    
    def do_GET(self):
        # Parse the callback URL
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if "code" in params:
            code = params["code"][0]
            shop = params.get("shop", [self.server.shop])[0]
            
            print(f"\n✅ Received authorization code!")
            print(f"   Shop: {shop}")
            
            # Exchange code for access token
            token_url = f"https://{shop}/admin/oauth/access_token"
            data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code
            }
            
            response = requests.post(token_url, data=data)
            
            if response.status_code == 200:
                result = response.json()
                access_token = result.get("access_token")
                
                print(f"\n{'='*60}")
                print(f"🎉 SUCCESS! Your access token:")
                print(f"{'='*60}")
                print(f"\n{access_token}\n")
                print(f"{'='*60}")
                print(f"\nAdd this to your .env file:")
                print(f"SHOPIFY_STORE={shop}")
                print(f"SHOPIFY_TOKEN={access_token}")
                print(f"{'='*60}\n")
                
                # Store for later
                self.server.access_token = access_token
                
                # Send success page
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"""
                <html>
                <body style="font-family: Arial; padding: 40px; text-align: center;">
                    <h1>✅ Authorization Successful!</h1>
                    <p>Your access token has been printed in the terminal.</p>
                    <p>You can close this window.</p>
                    <pre style="background: #f0f0f0; padding: 20px; border-radius: 8px;">
SHOPIFY_STORE={shop}
SHOPIFY_TOKEN={access_token[:20]}...
                    </pre>
                </body>
                </html>
                """.encode())
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                self.send_response(500)
                self.end_headers()
        else:
            error = params.get("error", ["Unknown error"])[0]
            print(f"❌ Authorization failed: {error}")
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default logging


def start_oauth(store_url: str):
    """Start the OAuth flow."""
    
    # Clean store URL
    store = store_url.replace("https://", "").replace("http://", "").rstrip("/")
    if not store.endswith(".myshopify.com"):
        store = f"{store}.myshopify.com"
    
    print(f"\n{'='*60}")
    print(f"🔐 SHOPIFY OAUTH FLOW")
    print(f"{'='*60}")
    print(f"Store: {store}")
    print(f"Client ID: {CLIENT_ID[:20]}...")
    print(f"Scopes: {', '.join(SCOPES)}")
    print(f"{'='*60}\n")
    
    # Build authorization URL
    auth_url = f"https://{store}/admin/oauth/authorize"
    params = {
        "client_id": CLIENT_ID,
        "scope": ",".join(SCOPES),
        "redirect_uri": REDIRECT_URI,
    }
    full_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    
    print(f"1. Opening browser for authorization...")
    print(f"   If browser doesn't open, visit this URL:\n")
    print(f"   {full_url}\n")
    
    # Start local server
    server = HTTPServer(("localhost", 3000), OAuthCallbackHandler)
    server.shop = store
    server.access_token = None
    
    # Open browser
    webbrowser.open(full_url)
    
    print(f"2. Waiting for callback on {REDIRECT_URI}...")
    print(f"   (Press Ctrl+C to cancel)\n")
    
    # Handle one request
    server.handle_request()
    
    return server.access_token


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Shopify OAuth Helper")
    parser.add_argument("--store", required=True, help="Your Shopify store URL (e.g., my-store.myshopify.com)")
    
    args = parser.parse_args()
    
    token = start_oauth(args.store)
    
    if token:
        print("✅ OAuth complete! Add the token to your .env file.")
    else:
        print("❌ OAuth failed. Check the error above.")
