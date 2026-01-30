#!/usr/bin/env python3
"""
CJ Dropshipping API Client
Standalone client for searching and fetching products from CJ catalog.
"""

import os
import json
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import httpx
except ImportError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "httpx"], check=True)
    import httpx


@dataclass
class CJProduct:
    """Standardized product data from CJ."""
    id: str
    title: str
    price: float
    image_url: str
    images: List[str]
    description: str
    category: str
    sku: str
    inventory: int
    source_url: str


class CJClient:
    """CJ Dropshipping API client."""
    
    BASE_URL = "https://developers.cjdropshipping.com/api2.0/v1"
    TOKEN_CACHE_FILE = Path(__file__).parent / ".cj-token-cache.json"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("CJ_TOKEN")
        if not self.api_key:
            raise ValueError("CJ_TOKEN not set. Get your API key from https://www.cjdropshipping.com")
        
        self.access_token = None
        self.headers = None
    
    def _get_key_hash(self) -> str:
        """Get stable hash of API key for caching."""
        return hashlib.md5(self.api_key.encode()).hexdigest()
    
    def _load_cached_token(self) -> Optional[str]:
        """Load cached token if still valid."""
        try:
            if not self.TOKEN_CACHE_FILE.exists():
                return None
            
            with open(self.TOKEN_CACHE_FILE, 'r') as f:
                cache = json.load(f)
            
            key_hash = self._get_key_hash()
            if key_hash not in cache:
                return None
            
            return cache[key_hash].get('access_token')
        except Exception:
            return None
    
    def _cache_token(self, access_token: str, expiry_date: str):
        """Cache the access token."""
        try:
            cache = {}
            if self.TOKEN_CACHE_FILE.exists():
                with open(self.TOKEN_CACHE_FILE, 'r') as f:
                    cache = json.load(f)
            
            cache[self._get_key_hash()] = {
                'access_token': access_token,
                'expiry': expiry_date,
                'cached_at': datetime.now(timezone.utc).isoformat()
            }
            
            with open(self.TOKEN_CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
        except Exception:
            pass
    
    async def authenticate(self):
        """Get access token from API key (or use cached)."""
        
        # Try cached token first
        cached_token = self._load_cached_token()
        if cached_token:
            self.access_token = cached_token
            self.headers = {
                "CJ-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            print("✅ Using cached CJ token")
            return self.access_token
        
        # Get new token
        print("🔐 Authenticating with CJ API...")
        url = f"{self.BASE_URL}/authentication/getAccessToken"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json={"apiKey": self.api_key})
            response.raise_for_status()
            result = response.json()
            
            if not result.get("result"):
                raise Exception(f"CJ Authentication failed: {result.get('message')}")
            
            data = result.get("data", {})
            self.access_token = data.get("accessToken")
            expiry_date = data.get("accessTokenExpiryDate")
            
            # Cache the token
            self._cache_token(self.access_token, expiry_date)
            
            self.headers = {
                "CJ-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }
            
            print("✅ CJ authentication successful")
            return self.access_token
    
    async def search_products(
        self,
        keyword: str = "",
        min_price: float = None,
        max_price: float = None,
        max_products: int = 100,
        category_id: str = None
    ) -> List[CJProduct]:
        """Search products with filters."""
        
        if not self.headers:
            await self.authenticate()
        
        url = f"{self.BASE_URL}/product/listV2"
        products = []
        page = 1
        
        print(f"\n🔍 Searching CJ for: '{keyword}'")
        print(f"   Max products: {max_products}")
        if min_price: print(f"   Min price: ${min_price}")
        if max_price: print(f"   Max price: ${max_price}")
        print()
        
        while len(products) < max_products:
            params = {
                "page": page,
                "size": min(100, max_products - len(products)),
                "countryCode": "US",
                "features": ["enable_description", "enable_category"]
            }
            
            if keyword:
                params["keyWord"] = keyword
            if min_price:
                params["startSellPrice"] = min_price
            if max_price:
                params["endSellPrice"] = max_price
            if category_id:
                params["categoryId"] = category_id
            
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    result = response.json()
                
                if not result.get("result"):
                    print(f"❌ API Error: {result.get('message')}")
                    break
                
                data = result.get("data", {})
                content = data.get("content", [])
                
                # Handle different response formats
                if isinstance(content, list):
                    if content and isinstance(content[0], dict) and 'productList' in content[0]:
                        product_list = content[0].get('productList', [])
                    else:
                        product_list = content
                elif isinstance(content, dict):
                    product_list = content.get("productList", [])
                else:
                    product_list = []
                
                if not product_list:
                    print("   ✅ No more products")
                    break
                
                for p in product_list:
                    if len(products) >= max_products:
                        break
                    if isinstance(p, dict):
                        products.append(self._format_product(p))
                
                print(f"   📄 Page {page}: Found {len(product_list)} products (total: {len(products)})")
                page += 1
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error on page {page}: {e}")
                break
        
        print(f"\n✅ Total products found: {len(products)}")
        return products
    
    def _format_product(self, product: Dict) -> CJProduct:
        """Format CJ product to standardized format."""
        
        def safe_float(value, default=0.0):
            if value is None:
                return default
            try:
                if isinstance(value, str) and '--' in value:
                    value = value.split('--')[0].strip()
                return float(value)
            except (ValueError, TypeError):
                return default
        
        images = []
        if product.get("bigImage"):
            images.append(product["bigImage"])
        
        return CJProduct(
            id=str(product.get("id", "")),
            title=product.get("nameEn", "Product"),
            price=safe_float(product.get("sellPrice")),
            image_url=product.get("bigImage", ""),
            images=images,
            description=product.get("description", ""),
            category=product.get("threeCategoryName", "General"),
            sku=product.get("sku", ""),
            inventory=product.get("warehouseInventoryNum", 0),
            source_url=f"https://www.cjdropshipping.com/product/{product.get('id')}"
        )
    
    async def get_product_details(self, product_id: str) -> Optional[Dict]:
        """Get detailed product information."""
        
        if not self.headers:
            await self.authenticate()
        
        url = f"{self.BASE_URL}/product/query"
        params = {
            "pid": product_id,
            "features": ["enable_description", "enable_video", "enable_inventory"]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            result = response.json()
            
            if result.get("result"):
                return result.get("data")
            return None


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CJ Dropshipping API Client")
    parser.add_argument("--keyword", default="cardigan", help="Search keyword")
    parser.add_argument("--max", type=int, default=5, help="Max products")
    parser.add_argument("--min-price", type=float, help="Min price")
    parser.add_argument("--max-price", type=float, help="Max price")
    
    args = parser.parse_args()
    
    async def main():
        client = CJClient()
        products = await client.search_products(
            keyword=args.keyword,
            max_products=args.max,
            min_price=args.min_price,
            max_price=args.max_price
        )
        
        print(f"\n📦 Products found:\n")
        for i, p in enumerate(products, 1):
            print(f"{i}. {p.title[:50]}")
            print(f"   💰 ${p.price:.2f}")
            print(f"   🖼️  {p.image_url[:60]}...")
            print()
    
    asyncio.run(main())
