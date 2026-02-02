#!/usr/bin/env python3
"""
Shopify Image Upgrade Pipeline

Simple flow:
1. Get existing products from Shopify
2. Use current product images as reference
3. Generate AI model photos via Fashn.ai
4. Replace/update images in Shopify

Usage:
    python3 shopify_image_upgrade.py --max 5 --dry-run
"""
import os
import sys
import asyncio
import argparse
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

# Load environment
load_dotenv()

from shopify_client import ShopifyClient
from generator import ModelPhotoGenerator


@dataclass
class ProcessedProduct:
    """Result of processing one product"""
    product_id: int
    title: str
    original_images: List[str]
    generated_images: List[str]
    success: bool = False
    error: Optional[str] = None


class ShopifyImageUpgrade:
    """Upgrade Shopify product images with AI model photos"""
    
    def __init__(self, dry_run: bool = False, demographics: List[str] = None):
        # Initialize clients
        self.shopify = ShopifyClient(
            os.getenv("SHOPIFY_STORE"),
            os.getenv("SHOPIFY_TOKEN")
        )
        
        self.generator = ModelPhotoGenerator(api_key=os.getenv("GEMINI_API_KEY"))
        
        self.dry_run = dry_run
        self.demographics = demographics or ["women-40-50", "women-50-60", "women-60-65"]
        self.output_dir = Path("output/shopify_upgrade")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def download_image(self, url: str, save_path: Path) -> bool:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
        return False
    
    def process_product(self, product: dict, photos_per_product: int = 3) -> ProcessedProduct:
        """
        Process one product:
        1. Download original image
        2. Generate AI model photos
        3. Replace images in Shopify
        """
        product_id = product['id']
        title = product['title']
        
        print(f"\n{'='*70}")
        print(f"Processing: {title}")
        print(f"Product ID: {product_id}")
        print(f"{'='*70}")
        
        result = ProcessedProduct(
            product_id=product_id,
            title=title,
            original_images=[],
            generated_images=[]
        )
        
        try:
            # Get original images
            images = product.get('images', [])
            if not images:
                raise Exception("No images found for product")
            
            print(f"\n📸 Found {len(images)} original images")
            
            # Use first image as reference
            original_image_url = images[0]['src']
            result.original_images.append(original_image_url)
            
            print(f"   Reference image: {original_image_url[:60]}...")
            
            # Download original image
            product_dir = self.output_dir / f"product_{product_id}"
            product_dir.mkdir(exist_ok=True)
            
            original_path = product_dir / "original.jpg"
            
            print(f"\n📥 Downloading original image...")
            if not self.download_image(original_image_url, original_path):
                raise Exception("Failed to download original image")
            
            print(f"   ✅ Saved: {original_path}")
            
            # Generate AI model photos with Gemini 2.5 Flash Image + product reference
            print(f"\n🎨 Generating {photos_per_product} AI model photos with Gemini 2.5...")
            print(f"   Using product image reference to match details...")
            
            for i in range(min(photos_per_product, len(self.demographics))):
                output_path = product_dir / f"model_{i+1}.png"
                demographic = self.demographics[i]
                
                print(f"\n   [{i+1}/{photos_per_product}] Generating with {demographic}...")
                
                try:
                    image_path = self.generator.generate_image(
                        product_title=title,
                        product_description=product.get('body_html', '')[:200],  # Truncate description
                        demographic=demographic,
                        output_path=str(output_path),
                        product_image_url=original_image_url  # Use original product as reference
                    )
                    
                    if image_path and Path(image_path).exists():
                        result.generated_images.append(str(output_path))
                        print(f"   ✅ Generated: {output_path}")
                    else:
                        print(f"   ⚠️  Failed to generate photo {i+1}")
                except Exception as e:
                    print(f"   ⚠️  Error: {e}")
            
            if not result.generated_images:
                raise Exception("No AI images generated successfully")
            
            print(f"\n✅ Generated {len(result.generated_images)} AI model photos")
            
            # Update Shopify (unless dry run)
            if not self.dry_run:
                print(f"\n🔄 Updating Shopify product...")
                
                # Delete old images
                print(f"   Deleting {len(images)} old images...")
                for img in images:
                    try:
                        self.shopify.delete_image(product_id, img['id'])
                        print(f"   ✅ Deleted image {img['id']}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to delete image: {e}")
                
                # Upload new images
                print(f"   Uploading {len(result.generated_images)} new images...")
                for img_path in result.generated_images:
                    try:
                        uploaded = self.shopify.upload_image(product_id, img_path)
                        print(f"   ✅ Uploaded: {uploaded['id']}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to upload: {e}")
                
                print(f"\n✅ Shopify updated!")
            else:
                print(f"\n⏭️  DRY RUN - Skipping Shopify update")
            
            result.success = True
            
        except Exception as e:
            result.error = str(e)
            print(f"\n❌ ERROR: {e}")
        
        return result
    
    def run(self, max_products: int = 5, auto_confirm: bool = False):
        """Process multiple products"""
        print("\n" + "="*70)
        print("🚀 SHOPIFY IMAGE UPGRADE PIPELINE")
        print("="*70)
        print(f"\nMax products: {max_products}")
        print(f"Photos per product: 3")
        print(f"Mode: {'DRY RUN (no Shopify changes)' if self.dry_run else 'LIVE (will update Shopify)'}")
        print("="*70)
        
        if not self.dry_run and not auto_confirm:
            confirm = input("\n⚠️  This will REPLACE images in Shopify. Continue? (y/N): ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return []
        
        # Get products from Shopify
        print(f"\n📦 Fetching products from Shopify...")
        products = self.shopify.get_products(limit=max_products)
        
        if not products:
            print("❌ No products found")
            return []
        
        print(f"✅ Found {len(products)} products")
        
        # Process each product
        results = []
        
        for i, product in enumerate(products, 1):
            print(f"\n\n{'#'*70}")
            print(f"# PRODUCT {i}/{len(products)}")
            print(f"{'#'*70}")
            
            result = self.process_product(product, photos_per_product=3)
            results.append(result)
        
        # Summary
        print("\n\n" + "="*70)
        print("📊 PIPELINE SUMMARY")
        print("="*70)
        
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n✅ Successful: {len(successful)}/{len(results)}")
        print(f"❌ Failed: {len(failed)}/{len(results)}")
        
        if successful:
            total_images = sum(len(r.generated_images) for r in successful)
            print(f"\n📸 Total AI images generated: {total_images}")
        
        if failed:
            print(f"\nFailed products:")
            for r in failed:
                print(f"   - {r.title} ({r.error})")
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Upgrade Shopify product images with AI model photos"
    )
    
    parser.add_argument("--max", type=int, default=5, help="Max products to process")
    parser.add_argument("--dry-run", action="store_true", help="Don't update Shopify")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    # Check environment
    required = ["SHOPIFY_STORE", "SHOPIFY_TOKEN", "GEMINI_API_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        sys.exit(1)
    
    # Run pipeline
    pipeline = ShopifyImageUpgrade(dry_run=args.dry_run)
    
    # Skip confirmation if --yes flag
    if not args.dry_run and not args.yes:
        # Original confirmation is in run(), we'll pass a flag
        pass
    
    results = pipeline.run(max_products=args.max, auto_confirm=args.yes)
    
    # Exit
    sys.exit(0 if all(r.success for r in results) else 1)


if __name__ == "__main__":
    main()
