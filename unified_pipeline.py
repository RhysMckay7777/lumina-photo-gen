#!/usr/bin/env python3
"""
Unified Photo Generation Pipeline

Complete CJ → Gemini → Claude → Shopify Pipeline

Flow:
1. Scrape products from CJ API
2. For each product:
   a. Download/use product image
   b. Generate AI model photo via Gemini 2.5 FLASH
   c. Generate product bio via Claude
   d. Create product in Shopify with AI images and bio
   e. Publish to store
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

# Local imports
from cj_client import CJClient, CJProduct
from bio_generator import BioGenerator, BioResult
from generator import ModelPhotoGenerator
from shopify_client import ShopifyClient


@dataclass
class PipelineConfig:
    """Configuration for the unified pipeline."""
    # CJ
    cj_token: str
    
    # Gemini
    gemini_key: str
    
    # Claude
    anthropic_key: str
    
    # Shopify
    shopify_store: str
    shopify_token: str
    
    # Processing
    max_products: int = 10
    demographics: List[str] = None
    markup_percent: float = 250  # Price markup from CJ cost
    dry_run: bool = False  # Don't upload to Shopify
    
    def __post_init__(self):
        if self.demographics is None:
            self.demographics = ["women-40-50", "women-50-60", "women-60-65"]


@dataclass
class ProcessedProduct:
    """Result of processing a single product."""
    cj_product: CJProduct
    bio: BioResult
    generated_images: List[str]  # Local file paths
    shopify_product_id: Optional[int] = None
    success: bool = True
    error: Optional[str] = None


class UnifiedPipeline:
    """
    Complete CJ → Gemini → Claude → Shopify Pipeline
    
    Usage:
        pipeline = UnifiedPipeline(config)
        results = await pipeline.run(keyword="cardigan", max_products=10)
    """
    
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.output_dir = Path("/tmp/lumina-unified")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize clients
        self.cj = CJClient(config.cj_token)
        self.bio_gen = BioGenerator(config.anthropic_key)
        self.image_gen = ModelPhotoGenerator(config.gemini_key)
        
        if not config.dry_run:
            self.shopify = ShopifyClient(config.shopify_store, config.shopify_token)
        else:
            self.shopify = None
    
    async def run(
        self,
        keyword: str,
        max_products: int = None,
        min_price: float = None,
        max_price: float = None
    ) -> List[ProcessedProduct]:
        """
        Run the full pipeline.
        
        Args:
            keyword: Search keyword for CJ
            max_products: Override config max_products
            min_price: Minimum CJ price filter
            max_price: Maximum CJ price filter
            
        Returns:
            List of ProcessedProduct results
        """
        max_products = max_products or self.config.max_products
        
        print(f"\n{'='*70}")
        print(f"🚀 UNIFIED PHOTO GENERATION PIPELINE")
        print(f"{'='*70}")
        print(f"Keyword: {keyword}")
        print(f"Max products: {max_products}")
        print(f"Demographics: {', '.join(self.config.demographics)}")
        print(f"Dry run: {self.config.dry_run}")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        results = []
        
        # Step 1: Scrape products from CJ
        print("\n📦 STEP 1: Fetching products from CJ...\n")
        products = await self.cj.search_products(
            keyword=keyword,
            max_products=max_products,
            min_price=min_price,
            max_price=max_price
        )
        
        if not products:
            print("❌ No products found")
            return []
        
        # Step 2-5: Process each product
        for i, product in enumerate(products, 1):
            print(f"\n{'='*70}")
            print(f"📦 PROCESSING {i}/{len(products)}: {product.title[:50]}")
            print(f"{'='*70}")
            
            result = await self._process_product(product)
            results.append(result)
            
            if result.success:
                print(f"✅ Product processed successfully")
            else:
                print(f"❌ Failed: {result.error}")
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        successful = sum(1 for r in results if r.success)
        
        print(f"\n{'='*70}")
        print(f"✅ PIPELINE COMPLETE")
        print(f"{'='*70}")
        print(f"Total products: {len(results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {len(results) - successful}")
        print(f"Duration: {duration:.1f}s")
        print(f"{'='*70}\n")
        
        return results
    
    async def _process_product(self, product: CJProduct) -> ProcessedProduct:
        """Process a single product through the pipeline."""
        
        try:
            # Step 2: Generate AI model photos
            print(f"\n🎨 Generating AI model photos...")
            generated_images = []
            
            for demo in self.config.demographics:
                output_path = self.output_dir / f"{product.id}_{demo}.png"
                
                img = self.image_gen.generate_image(
                    product_title=product.title,
                    product_description=product.description,
                    demographic=demo,
                    output_path=str(output_path),
                    product_image_url=product.image_url
                )
                
                if img and output_path.exists():
                    generated_images.append(str(output_path))
                    print(f"   ✅ Generated: {demo}")
                else:
                    print(f"   ⚠️ Failed: {demo}")
            
            if not generated_images:
                return ProcessedProduct(
                    cj_product=product,
                    bio=None,
                    generated_images=[],
                    success=False,
                    error="No images generated"
                )
            
            # Step 3: Generate product bio with Claude
            print(f"\n📝 Generating product bio with Claude...")
            bio = self.bio_gen.generate(
                original_title=product.title,
                price=product.price * (self.config.markup_percent / 100),
                category=product.category,
                original_description=product.description
            )
            
            if bio.success:
                print(f"   ✅ Title: {bio.title}")
            else:
                print(f"   ⚠️ Using fallback bio")
            
            # Step 4: Upload to Shopify
            if self.config.dry_run:
                print(f"\n🔶 DRY RUN - Skipping Shopify upload")
                return ProcessedProduct(
                    cj_product=product,
                    bio=bio,
                    generated_images=generated_images,
                    success=True
                )
            
            print(f"\n🛒 Creating product in Shopify...")
            
            # Calculate retail price with markup
            retail_price = product.price * (self.config.markup_percent / 100)
            compare_price = retail_price * 1.3  # Show 30% "discount"
            
            # Create product WITHOUT images initially
            # We'll add ONLY the AI-generated images (not the CJ source image)
            shopify_product = self.shopify.create_product(
                title=bio.title,
                description_html=bio.description_html,
                price=retail_price,
                compare_at_price=compare_price,
                vendor="CJ Dropshipping",
                product_type=product.category,
                tags=bio.tags + ["ai-generated", "lumina"],
                images=None,  # NO CJ image - only AI images will be uploaded
                publish=True
            )
            
            if not shopify_product:
                return ProcessedProduct(
                    cj_product=product,
                    bio=bio,
                    generated_images=generated_images,
                    success=False,
                    error="Failed to create Shopify product"
                )
            
            product_id = shopify_product["id"]
            print(f"   ✅ Created product ID: {product_id}")
            
            # Step 5: Upload ONLY AI-generated images (no CJ source image)
            print(f"\n🖼️ Uploading AI model photos (replacing CJ source image)...")
            for img_path in generated_images:
                result = self.shopify.upload_image(
                    product_id, 
                    img_path,
                    alt_text=f"Model wearing {bio.title}"
                )
                if result:
                    print(f"   ✅ Uploaded: {Path(img_path).name}")
            
            return ProcessedProduct(
                cj_product=product,
                bio=bio,
                generated_images=generated_images,
                shopify_product_id=product_id,
                success=True
            )
            
        except Exception as e:
            return ProcessedProduct(
                cj_product=product,
                bio=None,
                generated_images=[],
                success=False,
                error=str(e)
            )


def load_config_from_env() -> PipelineConfig:
    """Load configuration from environment variables."""
    
    required = {
        "CJ_TOKEN": os.environ.get("CJ_TOKEN"),
        "GEMINI_API_KEY": os.environ.get("GEMINI_API_KEY"),
        "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
        "SHOPIFY_STORE": os.environ.get("SHOPIFY_STORE"),
        "SHOPIFY_TOKEN": os.environ.get("SHOPIFY_TOKEN"),
    }
    
    missing = [k for k, v in required.items() if not v]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("\nSet them in .env file or export them:")
        for k in missing:
            print(f"  export {k}=your_value")
        sys.exit(1)
    
    return PipelineConfig(
        cj_token=required["CJ_TOKEN"],
        gemini_key=required["GEMINI_API_KEY"],
        anthropic_key=required["ANTHROPIC_API_KEY"],
        shopify_store=required["SHOPIFY_STORE"],
        shopify_token=required["SHOPIFY_TOKEN"],
    )


async def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Photo Generation Pipeline: CJ → Gemini → Claude → Shopify"
    )
    
    parser.add_argument("--keyword", required=True, help="Search keyword for CJ products")
    parser.add_argument("--max", type=int, default=10, help="Max products to process")
    parser.add_argument("--min-price", type=float, help="Min CJ price filter")
    parser.add_argument("--max-price", type=float, help="Max CJ price filter")
    parser.add_argument("--markup", type=float, default=250, help="Markup percentage (default: 250)")
    parser.add_argument("--dry-run", action="store_true", help="Don't upload to Shopify")
    parser.add_argument("--demographics", nargs="+", 
                       default=["women-40-50", "women-50-60", "women-60-65"],
                       help="Demographics to generate")
    
    args = parser.parse_args()
    
    # Load .env if present
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print("📄 Loading .env file...")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    
    # Load config
    config = load_config_from_env()
    config.max_products = args.max
    config.markup_percent = args.markup
    config.dry_run = args.dry_run
    config.demographics = args.demographics
    
    # Run pipeline
    pipeline = UnifiedPipeline(config)
    results = await pipeline.run(
        keyword=args.keyword,
        max_products=args.max,
        min_price=args.min_price,
        max_price=args.max_price
    )
    
    # Print summary
    print("\n📊 RESULTS SUMMARY:\n")
    for r in results:
        status = "✅" if r.success else "❌"
        title = r.cj_product.title[:40]
        images = len(r.generated_images)
        shopify_id = r.shopify_product_id or "N/A"
        print(f"{status} {title}... | {images} images | Shopify: {shopify_id}")


if __name__ == "__main__":
    asyncio.run(main())
