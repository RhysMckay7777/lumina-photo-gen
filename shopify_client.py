#!/usr/bin/env python3
"""
Shopify API client for product management
"""
import requests
import json
from typing import List, Dict

class ShopifyClient:
    def __init__(self, store_url, access_token):
        self.store_url = store_url.replace('https://', '').replace('http://', '')
        self.access_token = access_token
        self.api_version = "2024-01"
        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    def get_products(self, limit=50):
        """Get products from store"""
        url = f"{self.base_url}/products.json?limit={limit}"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get products: {response.status_code} - {response.text}")
        
        return response.json().get("products", [])
    
    def get_product(self, product_id):
        """Get single product"""
        url = f"{self.base_url}/products/{product_id}.json"
        
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get product: {response.status_code}")
        
        return response.json().get("product")
    
    def upload_image(self, product_id, image_path):
        """Upload image to product"""
        url = f"{self.base_url}/products/{product_id}/images.json"
        
        # Read image as base64
        import base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {
            "image": {
                "attachment": image_data,
                "filename": f"model-photo-{product_id}.png"
            }
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code not in [200, 201]:
            raise Exception(f"Failed to upload image: {response.status_code} - {response.text}")
        
        return response.json().get("image")
    
    def list_products_summary(self, limit=50):
        """Get simple product list for UI"""
        products = self.get_products(limit)
        
        summary = []
        for p in products:
            summary.append({
                "id": p["id"],
                "title": p["title"],
                "description": p.get("body_html", ""),
                "image_url": p["images"][0]["src"] if p.get("images") else None,
                "image_count": len(p.get("images", []))
            })
        
        return summary

# CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python3 shopify_client.py <store_url> <access_token>")
        sys.exit(1)
    
    store = sys.argv[1]
    token = sys.argv[2]
    
    client = ShopifyClient(store, token)
    products = client.list_products_summary()
    
    print(f"\n📦 Found {len(products)} products:\n")
    
    for p in products:
        print(f"ID: {p['id']}")
        print(f"Title: {p['title']}")
        print(f"Images: {p['image_count']}")
        print(f"URL: {p['image_url']}")
        print()
