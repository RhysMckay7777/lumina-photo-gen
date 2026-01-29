#!/usr/bin/env python3
"""
Unified Pipeline: Scrape → Generate Photos → Upload to Shopify
One command to rule them all.
"""
import sys
import os
import argparse
import json
from pathlib import Path
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "dropship-automate"))

from enhanced_fashn_client import FashnClient

class UnifiedPipeline:
    """Complete automation: CJ scraping + AI photo generation + Shopify upload"""
    
    def __init__(self, config_file: str = "pipeline_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        # Initialize Fashn client
        self.fashn_client = FashnClient(self.config["fashn_api_key"])
    
    def _load_config(self) -> dict:
        """Load or create pipeline configuration"""
        
        default_config = {
            "fashn_api_key": os.getenv("FASHN_API_KEY", ""),
            "cj_token": os.getenv("CJ_TOKEN", ""),
            "shopify_store": os.getenv("SHOPIFY_STORE", ""),
            "shopify_token": os.getenv("SHOPIFY_TOKEN", ""),
            "markup_percent": 250,
            "scraper_path": "../dropship-automate/cj-dropship.py",
            "generate_photos": True,
            "photos_per_product": 3,
            "use_airtable": True,
            "airtable_api_key": os.getenv("AIRTABLE_API_KEY", ""),
            "airtable_base_id": os.getenv("AIRTABLE_BASE_ID", "")
        }
        
        if self.config_file.exists():
            with open(self.config_file) as f:
                loaded = json.load(f)
                return {**default_config, **loaded}
        else:
            # Save default config
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def scrape_products(self, keyword: str, max_products: int = 100) -> str:
        """Step 1: Scrape products from CJ Dropshipping"""
        
        print(f"\n{'='*70}")
        print(f"STEP 1: SCRAPING PRODUCTS")
        print(f"{'='*70}\n")
        
        output_csv = f"scraped_{keyword.replace(' ', '_')}.csv"
        
        scraper_path = Path(self.config["scraper_path"]).resolve()
        
        if not scraper_path.exists():
            raise FileNotFoundError(f"Scraper not found: {scraper_path}")
        
        cmd = [
            str(scraper_path),
            "--keyword", keyword,
            "--max-products", str(max_products),
            "--cj-token", self.config["cj_token"],
            "--output", output_csv,
            "--no-upload"  # Don't upload yet
        ]
        
        print(f"🔍 Searching CJ for: {keyword}")
        print(f"   Max products: {max_products}")
        print(f"   Output: {output_csv}\n")
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            raise Exception(f"Scraper failed with code {result.returncode}")
        
        if not Path(output_csv).exists():
            raise Exception(f"Output CSV not created: {output_csv}")
        
        print(f"\n✅ Scraping complete: {output_csv}")
        return output_csv
    
    def generate_photos(self, csv_file: str) -> str:
        """Step 2: Generate model photos for each product"""
        
        if not self.config["generate_photos"]:
            print("\n⏭️  Photo generation disabled, skipping...")
            return csv_file
        
        print(f"\n{'='*70}")
        print(f"STEP 2: GENERATING MODEL PHOTOS")
        print(f"{'='*70}\n")
        
        # Read CSV
        import csv
        
        products = []
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            products = list(reader)
        
        print(f"📸 Generating photos for {len(products)} products")
        print(f"   Photos per product: {self.config['photos_per_product']}\n")
        
        output_dir = Path("generated_photos")
        output_dir.mkdir(exist_ok=True)
        
        # Generate photos for each product
        enhanced_products = []
        
        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] {product['title'][:50]}...")
            
            # Download main product image
            product_image_url = product.get('image1') or product.get('image_url')
            
            if not product_image_url:
                print("   ⚠️  No product image, skipping")
                enhanced_products.append(product)
                continue
            
            # Download product image
            product_image_path = output_dir / f"product_{i}.jpg"
            
            try:
                import requests
                response = requests.get(product_image_url, timeout=15)
                with open(product_image_path, 'wb') as f:
                    f.write(response.content)
            except Exception as e:
                print(f"   ❌ Failed to download image: {e}")
                enhanced_products.append(product)
                continue
            
            # Generate model photos
            generated_images = []
            
            for photo_num in range(self.config['photos_per_product']):
                output_path = output_dir / f"product_{i}_model_{photo_num+1}.jpg"
                
                success = self.fashn_client.generate(
                    str(product_image_path),
                    str(output_path)
                )
                
                if success:
                    generated_images.append(str(output_path))
                    print(f"   ✅ Generated photo {photo_num + 1}")
                else:
                    print(f"   ⚠️  Photo {photo_num + 1} failed")
            
            # Update product with generated images
            product_copy = product.copy()
            for idx, img_path in enumerate(generated_images, 1):
                product_copy[f'image{idx}'] = img_path
            
            enhanced_products.append(product_copy)
        
        # Save enhanced CSV
        output_csv = csv_file.replace('.csv', '_with_photos.csv')
        
        with open(output_csv, 'w', newline='') as f:
            if enhanced_products:
                writer = csv.DictWriter(f, fieldnames=enhanced_products[0].keys())
                writer.writeheader()
                writer.writerows(enhanced_products)
        
        print(f"\n✅ Photo generation complete: {output_csv}")
        
        self.fashn_client.print_stats()
        
        return output_csv
    
    def upload_to_shopify(self, csv_file: str):
        """Step 3: Upload products to Shopify"""
        
        print(f"\n{'='*70}")
        print(f"STEP 3: UPLOADING TO SHOPIFY")
        print(f"{'='*70}\n")
        
        upload_script = Path(self.config["scraper_path"]).parent / "upload-csv.py"
        
        if not upload_script.exists():
            raise FileNotFoundError(f"Upload script not found: {upload_script}")
        
        cmd = [
            str(upload_script),
            csv_file,
            "--store", self.config["shopify_store"],
            "--token", self.config["shopify_token"],
            "--markup", str(self.config["markup_percent"])
        ]
        
        print(f"🚀 Uploading to Shopify: {self.config['shopify_store']}")
        print(f"   Markup: {self.config['markup_percent']}%\n")
        
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            raise Exception(f"Upload failed with code {result.returncode}")
        
        print(f"\n✅ Upload complete!")
    
    def run(self, keyword: str, max_products: int = 100):
        """Run complete pipeline"""
        
        print("\n" + "="*70)
        print("🚀 UNIFIED PIPELINE - COMPLETE AUTOMATION")
        print("="*70)
        print(f"\nKeyword: {keyword}")
        print(f"Max Products: {max_products}")
        print(f"Photo Generation: {'✅ Enabled' if self.config['generate_photos'] else '❌ Disabled'}")
        print(f"Shopify Upload: ✅ Enabled")
        print("="*70 + "\n")
        
        input("Press Enter to start or Ctrl+C to cancel... ")
        
        try:
            # Step 1: Scrape
            csv_file = self.scrape_products(keyword, max_products)
            
            # Step 2: Generate photos
            if self.config["generate_photos"]:
                csv_file = self.generate_photos(csv_file)
            
            # Step 3: Upload
            self.upload_to_shopify(csv_file)
            
            print("\n" + "="*70)
            print("🎉 PIPELINE COMPLETE!")
            print("="*70)
            print(f"\n✅ {max_products} products processed")
            print(f"✅ Uploaded to: {self.config['shopify_store']}")
            
            if self.config["generate_photos"]:
                self.fashn_client.print_stats()
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Pipeline cancelled by user")
            sys.exit(1)
        except Exception as e:
            print(f"\n\n❌ Pipeline failed: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Unified dropshipping pipeline: Scrape → Generate Photos → Upload"
    )
    
    parser.add_argument("keyword", help="Search keyword for products")
    parser.add_argument("--max-products", type=int, default=100, 
                       help="Maximum products to process")
    parser.add_argument("--no-photos", action="store_true",
                       help="Skip photo generation")
    parser.add_argument("--config", default="pipeline_config.json",
                       help="Config file path")
    
    args = parser.parse_args()
    
    pipeline = UnifiedPipeline(args.config)
    
    if args.no_photos:
        pipeline.config["generate_photos"] = False
    
    pipeline.run(args.keyword, args.max_products)


if __name__ == "__main__":
    main()
