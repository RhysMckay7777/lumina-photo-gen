#!/usr/bin/env python3
"""
Airtable Image Library Manager
Manages product images across multiple stores
"""

import os
import requests
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import base64
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageLibrary:
    """Airtable-based image library for product photos"""
    
    def __init__(
        self,
        api_key: str = None,
        base_id: str = None
    ):
        self.api_key = api_key or os.environ.get("AIRTABLE_API_KEY")
        self.base_id = base_id or os.environ.get("AIRTABLE_BASE_ID")
        
        if not self.api_key or not self.base_id:
            raise ValueError("AIRTABLE_API_KEY and AIRTABLE_BASE_ID required")
        
        self.base_url = f"https://api.airtable.com/v0/{self.base_id}"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Table names
        self.products_table = "Products"
        self.images_table = "Generated Images"
        self.usage_table = "Store Usage"
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make Airtable API request"""
        url = f"{self.base_url}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=self.headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=self.headers, json=data)
        elif method == "PATCH":
            response = requests.patch(url, headers=self.headers, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def has_images(self, cj_product_id: str) -> bool:
        """Check if product already has generated images"""
        try:
            formula = f"{{CJ Product ID}}='{cj_product_id}'"
            result = self._request(
                "GET",
                self.products_table,
                {"filterByFormula": formula}
            )
            
            if result.get("records"):
                record = result["records"][0]
                return record["fields"].get("Has Generated Images", False)
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking product {cj_product_id}: {e}")
            return False
    
    def get_product(self, cj_product_id: str) -> Optional[Dict]:
        """Get product record from library"""
        try:
            formula = f"{{CJ Product ID}}='{cj_product_id}'"
            result = self._request(
                "GET",
                self.products_table,
                {"filterByFormula": formula}
            )
            
            if result.get("records"):
                return result["records"][0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting product {cj_product_id}: {e}")
            return None
    
    def get_images(self, cj_product_id: str) -> List[Dict]:
        """Get all generated images for a product"""
        try:
            # First get product record to link
            product = self.get_product(cj_product_id)
            if not product:
                return []
            
            product_record_id = product["id"]
            
            # Get linked images
            formula = f"SEARCH('{product_record_id}', {{CJ Product ID}})"
            result = self._request(
                "GET",
                self.images_table,
                {"filterByFormula": formula}
            )
            
            images = []
            for record in result.get("records", []):
                fields = record["fields"]
                images.append({
                    "variant": fields.get("Variant Number"),
                    "url": fields.get("Cloud URL"),
                    "attachment": fields.get("Image File", [{}])[0].get("url") if fields.get("Image File") else None,
                    "model": fields.get("Model Photo Used"),
                    "method": fields.get("Generation Method"),
                    "created": fields.get("Created Date")
                })
            
            return sorted(images, key=lambda x: x["variant"])
            
        except Exception as e:
            logger.error(f"Error getting images for {cj_product_id}: {e}")
            return []
    
    def save_product(
        self,
        cj_product_id: str,
        product_name: str,
        category: str = None,
        original_image_url: str = None,
        cj_link: str = None
    ) -> str:
        """Save or update product in library"""
        
        # Check if exists
        existing = self.get_product(cj_product_id)
        
        fields = {
            "CJ Product ID": cj_product_id,
            "Product Name": product_name,
            "Original Image URL": original_image_url,
        }
        
        if category:
            fields["Category"] = category
        if cj_link:
            fields["CJ Link"] = cj_link
        
        try:
            if existing:
                # Update
                record_id = existing["id"]
                result = self._request(
                    "PATCH",
                    f"{self.products_table}/{record_id}",
                    {"fields": fields}
                )
                logger.info(f"✅ Updated product {cj_product_id}")
                return result["id"]
            else:
                # Create
                result = self._request(
                    "POST",
                    self.products_table,
                    {"records": [{"fields": fields}]}
                )
                logger.info(f"✅ Created product {cj_product_id}")
                return result["records"][0]["id"]
                
        except Exception as e:
            logger.error(f"Error saving product {cj_product_id}: {e}")
            return None
    
    def save_images(
        self,
        cj_product_id: str,
        image_paths: List[str],
        model_photos: List[str] = None,
        generation_method: str = "CatVTON"
    ) -> bool:
        """Save generated images to library"""
        
        # Get or create product record
        product = self.get_product(cj_product_id)
        if not product:
            logger.error(f"Product {cj_product_id} not found. Create it first.")
            return False
        
        product_record_id = product["id"]
        
        try:
            records_to_create = []
            
            for idx, image_path in enumerate(image_paths):
                variant_num = idx + 1
                model_photo = model_photos[idx] if model_photos and idx < len(model_photos) else f"model_{variant_num}"
                
                # Read image file
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                
                # Upload to Airtable attachments
                # Note: Airtable requires images to be uploaded via URL or attachment
                # For now, we'll store the local path and cloud URL separately
                
                fields = {
                    "CJ Product ID": [product_record_id],
                    "Variant Number": variant_num,
                    "Model Photo Used": model_photo,
                    "Generation Method": generation_method,
                    "Created Date": datetime.now().isoformat()[:10]
                }
                
                # If image is already uploaded to cloud, add URL
                # TODO: Implement cloud upload (S3/R2) and add URL here
                
                records_to_create.append({"fields": fields})
            
            # Batch create image records
            result = self._request(
                "POST",
                self.images_table,
                {"records": records_to_create}
            )
            
            # Update product to mark as having images
            self._request(
                "PATCH",
                f"{self.products_table}/{product_record_id}",
                {
                    "fields": {
                        "Has Generated Images": True,
                        "Generation Date": datetime.now().isoformat()[:10],
                        "Generation Method": generation_method
                    }
                }
            )
            
            logger.info(f"✅ Saved {len(image_paths)} images for {cj_product_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving images for {cj_product_id}: {e}")
            return False
    
    def mark_used_in_store(
        self,
        cj_product_id: str,
        store_name: str,
        shopify_url: str = None,
        shopify_product_id: str = None
    ) -> bool:
        """Mark product as used in a specific store"""
        
        product = self.get_product(cj_product_id)
        if not product:
            logger.error(f"Product {cj_product_id} not found")
            return False
        
        product_record_id = product["id"]
        
        try:
            fields = {
                "CJ Product ID": [product_record_id],
                "Store Name": store_name,
                "Upload Date": datetime.now().isoformat()[:10],
                "Status": "Uploaded"
            }
            
            if shopify_url:
                fields["Shopify Store URL"] = shopify_url
            if shopify_product_id:
                fields["Shopify Product ID"] = shopify_product_id
            
            result = self._request(
                "POST",
                self.usage_table,
                {"records": [{"fields": fields}]}
            )
            
            logger.info(f"✅ Marked {cj_product_id} as used in {store_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking usage for {cj_product_id}: {e}")
            return False
    
    def get_stats(self) -> Dict:
        """Get library statistics"""
        try:
            # Count products
            products = self._request("GET", self.products_table)
            total_products = len(products.get("records", []))
            
            products_with_images = sum(
                1 for r in products.get("records", [])
                if r["fields"].get("Has Generated Images")
            )
            
            # Count images
            images = self._request("GET", self.images_table)
            total_images = len(images.get("records", []))
            
            # Count store usage
            usage = self._request("GET", self.usage_table)
            stores_used = len(set(
                r["fields"].get("Store Name")
                for r in usage.get("records", [])
                if r["fields"].get("Store Name")
            ))
            
            return {
                "total_products": total_products,
                "products_with_images": products_with_images,
                "total_images": total_images,
                "stores_using_library": stores_used,
                "reuse_rate": f"{(products_with_images/total_products*100):.1f}%" if total_products > 0 else "0%"
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}


def main():
    """Test the library"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Image Library Manager")
    parser.add_argument("--stats", action="store_true", help="Show library stats")
    parser.add_argument("--check", help="Check if product has images (CJ Product ID)")
    parser.add_argument("--get", help="Get images for product (CJ Product ID)")
    
    args = parser.parse_args()
    
    library = ImageLibrary()
    
    if args.stats:
        stats = library.get_stats()
        print("\n📊 Library Statistics:")
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
    
    elif args.check:
        has_images = library.has_images(args.check)
        print(f"\n{args.check}: {'✅ Has images' if has_images else '❌ No images'}")
    
    elif args.get:
        images = library.get_images(args.get)
        print(f"\n📸 Images for {args.get}:")
        for img in images:
            print(f"  Variant {img['variant']}: {img.get('url') or img.get('attachment')}")


if __name__ == "__main__":
    main()
