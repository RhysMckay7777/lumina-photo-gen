#!/usr/bin/env python3
"""
Main pipeline: Shopify → AI Model Photos → Shopify
"""
import os
import sys
from pathlib import Path
from generator import ModelPhotoGenerator
from shopify_client import ShopifyClient

class PhotoGenerationPipeline:
    def __init__(self, shopify_store, shopify_token, gemini_key=None):
        self.shopify = ShopifyClient(shopify_store, shopify_token)
        self.generator = ModelPhotoGenerator(gemini_key)
    
    def process_product(self, product_id, demographics=None, upload=True, output_dir="/tmp/lumina-photos"):
        """
        Generate AI model photos for a single product
        """
        print(f"\n{'='*60}")
        print(f"Processing Product ID: {product_id}")
        print(f"{'='*60}\n")
        
        # Get product details
        product = self.shopify.get_product(product_id)
        title = product["title"]
        description = product.get("body_html", "")
        
        # Get product image URL for reference
        product_image_url = None
        if product.get("images") and len(product["images"]) > 0:
            product_image_url = product["images"][0]["src"]
        
        print(f"Title: {title}")
        print(f"Description: {description[:100] if description else 'N/A'}...")
        print(f"Product Image: {product_image_url}\n")
        
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Generate images with product image reference
        if demographics is None:
            demographics = ["women-40-50", "women-50-60", "women-60-65"]
        
        results = []
        for i, demo in enumerate(demographics):
            output_path = Path(output_dir) / f"model-{demo}-{i+1:02d}.png"
            
            img = self.generator.generate_image(
                title,
                description,
                demo,
                output_path,
                product_image_url=product_image_url  # Pass product image as reference
            )
            
            if img:
                results.append({
                    "path": str(output_path),
                    "demographic": demo
                })
        
        # Remove old generate_multiple call
        # results = self.generator.generate_multiple(
        #     title,
        #     description,
        #     count=len(demographics),
        #     demographics=demographics,
        #     output_dir=output_dir
        # )
        
        print(f"\n✅ Generated {len(results)} images")
        
        # Upload to Shopify
        if upload:
            print(f"\n📤 Uploading to Shopify...")
            uploaded = []
            
            for result in results:
                try:
                    img = self.shopify.upload_image(product_id, result["path"])
                    uploaded.append(img)
                    print(f"✅ Uploaded: {result['demographic']}")
                except Exception as e:
                    print(f"❌ Upload failed: {e}")
            
            print(f"\n✅ Uploaded {len(uploaded)}/{len(results)} images to Shopify")
        
        return results
    
    def process_multiple(self, product_ids, demographics=None, upload=True):
        """
        Batch process multiple products
        """
        results = {}
        
        for i, product_id in enumerate(product_ids, 1):
            print(f"\n[{i}/{len(product_ids)}] Processing product {product_id}")
            
            try:
                results[product_id] = self.process_product(
                    product_id,
                    demographics,
                    upload
                )
            except Exception as e:
                print(f"❌ Error processing {product_id}: {e}")
                results[product_id] = {"error": str(e)}
        
        return results
    
    def list_products(self):
        """List available products"""
        return self.shopify.list_products_summary()

# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate AI model photos for Shopify products")
    parser.add_argument("--store", required=True, help="Shopify store URL")
    parser.add_argument("--token", required=True, help="Shopify access token")
    parser.add_argument("--product-id", type=int, help="Single product ID to process")
    parser.add_argument("--list", action="store_true", help="List all products")
    parser.add_argument("--demographics", nargs="+", default=["women-50-60"], help="Demographics to generate")
    parser.add_argument("--no-upload", action="store_true", help="Don't upload to Shopify (preview only)")
    parser.add_argument("--output-dir", default="/tmp/lumina-photos", help="Output directory")
    
    args = parser.parse_args()
    
    pipeline = PhotoGenerationPipeline(args.store, args.token)
    
    if args.list:
        products = pipeline.list_products()
        print(f"\n📦 Products in {args.store}:\n")
        for p in products:
            print(f"ID: {p['id']} - {p['title']}")
    
    elif args.product_id:
        pipeline.process_product(
            args.product_id,
            args.demographics,
            upload=not args.no_upload,
            output_dir=args.output_dir
        )
    
    else:
        print("Use --list to see products or --product-id <id> to process one")
