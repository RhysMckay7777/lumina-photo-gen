#!/usr/bin/env python3
"""
Multi-Store Sync Tool
Syncs product images from library to new/existing Shopify stores
"""

import os
import csv
import json
import requests
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
import logging
from image_library import ImageLibrary

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoreSync:
    """Sync images from library to Shopify store"""
    
    def __init__(
        self,
        library: ImageLibrary,
        store_name: str,
        shopify_url: str,
        shopify_api_key: str,
        shopify_password: str
    ):
        self.library = library
        self.store_name = store_name
        self.shopify_url = shopify_url.rstrip('/')
        self.shopify_api_key = shopify_api_key
        self.shopify_password = shopify_password
        
        self.api_base = f"{self.shopify_url}/admin/api/2024-01"
        self.auth = (shopify_api_key, shopify_password)
    
    def _shopify_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """Make Shopify API request"""
        url = f"{self.api_base}/{endpoint}"
        
        if method == "GET":
            response = requests.get(url, auth=self.auth)
        elif method == "POST":
            response = requests.post(url, auth=self.auth, json=data)
        elif method == "PUT":
            response = requests.put(url, auth=self.auth, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    def upload_product_images(
        self,
        cj_product_id: str,
        shopify_product_id: str = None
    ) -> bool:
        """Upload product images from library to Shopify"""
        
        # Get images from library
        images = self.library.get_images(cj_product_id)
        
        if not images:
            logger.warning(f"⚠️  No images found for {cj_product_id}")
            return False
        
        try:
            # If no Shopify product ID provided, we need to create or find the product
            if not shopify_product_id:
                logger.info(f"  Creating Shopify product for {cj_product_id}")
                # TODO: Create product in Shopify
                # For now, skip
                logger.warning(f"  Skipping - need Shopify product ID for {cj_product_id}")
                return False
            
            # Upload each image variant
            for img in images:
                image_url = img.get('url') or img.get('attachment')
                
                if not image_url:
                    logger.warning(f"  No URL for variant {img['variant']}")
                    continue
                
                # Upload to Shopify
                image_data = {
                    "image": {
                        "src": image_url,
                        "alt": f"Variant {img['variant']}"
                    }
                }
                
                result = self._shopify_request(
                    "POST",
                    f"products/{shopify_product_id}/images.json",
                    image_data
                )
                
                logger.info(f"  ✅ Uploaded variant {img['variant']}")
            
            # Mark as used in this store
            self.library.mark_used_in_store(
                cj_product_id=cj_product_id,
                store_name=self.store_name,
                shopify_url=self.shopify_url,
                shopify_product_id=shopify_product_id
            )
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to upload images for {cj_product_id}: {e}")
            return False
    
    def sync_from_csv(
        self,
        csv_file: str,
        cj_id_column: str = "CJ Product ID",
        shopify_id_column: str = "Shopify Product ID"
    ):
        """Sync products from CSV file"""
        
        products = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                products.append({
                    "cj_id": row[cj_id_column],
                    "shopify_id": row.get(shopify_id_column)
                })
        
        logger.info(f"📦 Syncing {len(products)} products to {self.store_name}")
        
        stats = {
            "total": len(products),
            "succeeded": 0,
            "failed": 0,
            "skipped_no_images": 0,
            "reused": 0,
            "new": 0
        }
        
        for product in tqdm(products, desc="Syncing"):
            cj_id = product["cj_id"]
            shopify_id = product["shopify_id"]
            
            # Check if already has images
            has_images = self.library.has_images(cj_id)
            
            if not has_images:
                stats["skipped_no_images"] += 1
                logger.warning(f"⏭️  No images for {cj_id} - skipping")
                continue
            
            # Check if new or reused
            product_data = self.library.get_product(cj_id)
            if product_data:
                # Check if already used in another store
                # If yes, this is a reuse case
                stats["reused"] += 1
            else:
                stats["new"] += 1
            
            # Upload images
            success = self.upload_product_images(cj_id, shopify_id)
            
            if success:
                stats["succeeded"] += 1
            else:
                stats["failed"] += 1
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info(f"📊 Sync Complete - {self.store_name}")
        logger.info("="*60)
        logger.info(f"Total products: {stats['total']}")
        logger.info(f"✅ Successfully synced: {stats['succeeded']}")
        logger.info(f"♻️  Reused from library: {stats['reused']}")
        logger.info(f"🆕 New images used: {stats['new']}")
        logger.info(f"⏭️  Skipped (no images): {stats['skipped_no_images']}")
        logger.info(f"❌ Failed: {stats['failed']}")
        logger.info("="*60)
        
        return stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync images to Shopify store")
    parser.add_argument("--store-name", required=True, help="Store name identifier")
    parser.add_argument("--shopify-url", required=True, help="Shopify store URL")
    parser.add_argument("--shopify-api-key", help="Shopify API key")
    parser.add_argument("--shopify-password", help="Shopify API password")
    parser.add_argument("--csv", required=True, help="CSV file with product IDs")
    parser.add_argument("--cj-column", default="CJ Product ID", help="CJ ID column name")
    parser.add_argument("--shopify-column", default="Shopify Product ID", help="Shopify ID column name")
    
    args = parser.parse_args()
    
    # Get credentials from env if not provided
    api_key = args.shopify_api_key or os.environ.get("SHOPIFY_API_KEY")
    password = args.shopify_password or os.environ.get("SHOPIFY_PASSWORD")
    
    if not api_key or not password:
        logger.error("❌ Shopify credentials required")
        return
    
    # Initialize library
    library = ImageLibrary()
    
    # Initialize sync tool
    sync = StoreSync(
        library=library,
        store_name=args.store_name,
        shopify_url=args.shopify_url,
        shopify_api_key=api_key,
        shopify_password=password
    )
    
    # Sync from CSV
    sync.sync_from_csv(
        csv_file=args.csv,
        cj_id_column=args.cj_column,
        shopify_id_column=args.shopify_column
    )


if __name__ == "__main__":
    main()
