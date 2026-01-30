#!/usr/bin/env python3
"""
Shopify API client for product management
Enhanced with product creation, image management, and updates
"""
import os
import requests
import json
import base64
from typing import List, Dict, Optional
from pathlib import Path


class ShopifyClient:
    """
    Shopify REST Admin API client.
    
    Supports:
    - Product CRUD operations
    - Image upload and deletion
    - Product publishing
    """
    
    def __init__(self, store_url: str = None, access_token: str = None):
        self.store_url = (store_url or os.environ.get("SHOPIFY_STORE", "")).replace('https://', '').replace('http://', '')
        self.access_token = access_token or os.environ.get("SHOPIFY_TOKEN")
        
        if not self.store_url or not self.access_token:
            raise ValueError("SHOPIFY_STORE and SHOPIFY_TOKEN must be set")
        
        self.api_version = "2024-01"
        self.base_url = f"https://{self.store_url}/admin/api/{self.api_version}"
        
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }
    
    # ============= PRODUCT READ =============
    
    def get_products(self, limit: int = 50) -> List[Dict]:
        """Get products from store."""
        url = f"{self.base_url}/products.json?limit={limit}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get products: {response.status_code} - {response.text}")
        
        return response.json().get("products", [])
    
    def get_product(self, product_id: int) -> Dict:
        """Get single product."""
        url = f"{self.base_url}/products/{product_id}.json"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to get product: {response.status_code}")
        
        return response.json().get("product")
    
    def list_products_summary(self, limit: int = 50) -> List[Dict]:
        """Get simple product list for UI."""
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
    
    # ============= PRODUCT CREATE =============
    
    def create_product(
        self,
        title: str,
        description_html: str = "",
        price: float = 0,
        compare_at_price: float = None,
        vendor: str = "",
        product_type: str = "",
        tags: List[str] = None,
        images: List[str] = None,
        publish: bool = True
    ) -> Optional[Dict]:
        """
        Create a new product.
        
        Args:
            title: Product title
            description_html: HTML description
            price: Selling price
            compare_at_price: Original/compare price (for showing discount)
            vendor: Product vendor
            product_type: Product type/category
            tags: List of tags
            images: List of image URLs to attach
            publish: Whether to publish immediately
            
        Returns:
            Created product dict or None if failed
        """
        url = f"{self.base_url}/products.json"
        
        # Build variant
        variant = {
            "price": str(price),
            "inventory_policy": "continue",
            "requires_shipping": True
        }
        if compare_at_price:
            variant["compare_at_price"] = str(compare_at_price)
        
        # Build product
        product_data = {
            "product": {
                "title": title,
                "body_html": description_html,
                "vendor": vendor or "Lumina",
                "product_type": product_type,
                "tags": ",".join(tags) if tags else "",
                "variants": [variant],
                "status": "active" if publish else "draft"
            }
        }
        
        # Add images if provided
        if images:
            product_data["product"]["images"] = [{"src": url} for url in images]
        
        response = requests.post(url, headers=self.headers, json=product_data)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create product: {response.status_code} - {response.text}")
            return None
        
        return response.json().get("product")
    
    # ============= PRODUCT UPDATE =============
    
    def update_product(
        self,
        product_id: int,
        title: str = None,
        description_html: str = None,
        tags: List[str] = None
    ) -> Optional[Dict]:
        """Update an existing product."""
        url = f"{self.base_url}/products/{product_id}.json"
        
        product_data = {"product": {"id": product_id}}
        
        if title:
            product_data["product"]["title"] = title
        if description_html:
            product_data["product"]["body_html"] = description_html
        if tags is not None:
            product_data["product"]["tags"] = ",".join(tags)
        
        response = requests.put(url, headers=self.headers, json=product_data)
        
        if response.status_code != 200:
            print(f"❌ Failed to update product: {response.status_code} - {response.text}")
            return None
        
        return response.json().get("product")
    
    # ============= IMAGE MANAGEMENT =============
    
    def get_product_images(self, product_id: int) -> List[Dict]:
        """Get all images for a product."""
        url = f"{self.base_url}/products/{product_id}/images.json"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
        
        return response.json().get("images", [])
    
    def upload_image(self, product_id: int, image_path: str, alt_text: str = None) -> Optional[Dict]:
        """Upload image to product from local file."""
        url = f"{self.base_url}/products/{product_id}/images.json"
        
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {
            "image": {
                "attachment": image_data,
                "filename": Path(image_path).name
            }
        }
        if alt_text:
            payload["image"]["alt"] = alt_text
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to upload image: {response.status_code} - {response.text}")
            return None
        
        return response.json().get("image")
    
    def upload_image_from_url(self, product_id: int, image_url: str, alt_text: str = None) -> Optional[Dict]:
        """Upload image to product from URL."""
        url = f"{self.base_url}/products/{product_id}/images.json"
        
        payload = {
            "image": {
                "src": image_url
            }
        }
        if alt_text:
            payload["image"]["alt"] = alt_text
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to upload image from URL: {response.status_code}")
            return None
        
        return response.json().get("image")
    
    def delete_image(self, product_id: int, image_id: int) -> bool:
        """Delete a specific image from product."""
        url = f"{self.base_url}/products/{product_id}/images/{image_id}.json"
        response = requests.delete(url, headers=self.headers)
        
        return response.status_code == 200
    
    def delete_all_images(self, product_id: int) -> int:
        """Delete all images from a product. Returns count deleted."""
        images = self.get_product_images(product_id)
        deleted = 0
        
        for img in images:
            if self.delete_image(product_id, img["id"]):
                deleted += 1
        
        return deleted
    
    def replace_images(self, product_id: int, new_image_paths: List[str]) -> List[Dict]:
        """Delete all existing images and upload new ones."""
        # Delete existing
        deleted = self.delete_all_images(product_id)
        print(f"   🗑️  Deleted {deleted} old images")
        
        # Upload new
        uploaded = []
        for path in new_image_paths:
            img = self.upload_image(product_id, path)
            if img:
                uploaded.append(img)
        
        print(f"   ✅ Uploaded {len(uploaded)} new images")
        return uploaded
    
    # ============= PRODUCT DELETE =============
    
    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        url = f"{self.base_url}/products/{product_id}.json"
        response = requests.delete(url, headers=self.headers)
        return response.status_code == 200


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Shopify API Client")
    parser.add_argument("--store", help="Shopify store URL")
    parser.add_argument("--token", help="Shopify access token")
    parser.add_argument("--list", action="store_true", help="List products")
    parser.add_argument("--product-id", type=int, help="Product ID for operations")
    parser.add_argument("--list-images", action="store_true", help="List images for product")
    
    args = parser.parse_args()
    
    client = ShopifyClient(args.store, args.token)
    
    if args.list:
        products = client.list_products_summary()
        print(f"\n📦 Found {len(products)} products:\n")
        for p in products:
            print(f"ID: {p['id']} - {p['title']} ({p['image_count']} images)")
    
    elif args.product_id and args.list_images:
        images = client.get_product_images(args.product_id)
        print(f"\n🖼️  Images for product {args.product_id}:\n")
        for img in images:
            print(f"ID: {img['id']} - {img['src'][:60]}...")

