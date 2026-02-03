"""
Photo Enhancement Pipeline - Production Version.

Features:
1. Tiered parallel processing (Tier 1 + Free keys = 60 IPM)
2. Content filtering (skip adult/wellness products)
3. Limited product fetch (only fetch what's needed)
4. Text-only generation for products without images
5. Direct Shopify upload (no Cloudinary)
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from shopify_graphql import ShopifyGraphQLClient, ShopifyProduct
from parallel_gemini import ParallelGeminiProcessor, ImageTask, EnhancedImage
from content_filter import filter_products, is_product_safe
from config import GEMINI_KEYS, TOTAL_IPM, PROCESSING_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("photo.enhancer")

# Number of AI images to generate per product
IMAGES_PER_PRODUCT = PROCESSING_CONFIG.get("images_per_product", 3)


@dataclass
class ProductResult:
    """Result for a single product."""
    product_id: str
    product_title: str
    original_image_count: int
    generated_image_count: int
    success: bool = False
    error: Optional[str] = None
    filtered: bool = False
    filter_reason: Optional[str] = None


@dataclass
class EnhancementResult:
    """Overall enhancement job result."""
    store_url: str
    total_products: int
    successful_products: int
    failed_products: int
    filtered_products: int
    total_images: int
    enhanced_images: int
    start_time: datetime
    end_time: Optional[datetime] = None
    total_seconds: float = 0
    images_per_minute: float = 0
    products: List[ProductResult] = field(default_factory=list)
    successful_product_names: List[str] = field(default_factory=list)  # For frontend display
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "store_url": self.store_url,
            "total_products": self.total_products,
            "successful_products": self.successful_products,
            "failed_products": self.failed_products,
            "filtered_products": self.filtered_products,
            "total_images": self.total_images,
            "enhanced_images": self.enhanced_images,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_seconds": self.total_seconds,
            "total_minutes": self.total_seconds / 60,
            "images_per_minute": self.images_per_minute,
            "successful_product_names": self.successful_product_names,  # List of enhanced product names
            "products": [
                {
                    "product_id": p.product_id,
                    "product_title": p.product_title,
                    "original_images": p.original_image_count,
                    "generated_images": p.generated_image_count,
                    "success": p.success,
                    "error": p.error,
                    "filtered": p.filtered,
                    "filter_reason": p.filter_reason
                }
                for p in self.products
            ]
        }


class PhotoEnhancer:
    """
    Production photo enhancement orchestrator.
    
    Features:
    - Tiered parallel processing with mixed key types
    - Content filtering for policy compliance
    - Limited product fetching (only what's needed)
    - Text-only generation when no reference image
    """
    
    def __init__(
        self,
        store_url: str,
        access_token: str,
        gemini_keys: List = None  # Use config if not provided
    ):
        self.shopify = ShopifyGraphQLClient(store_url, access_token)
        
        # Use config keys if not explicitly provided
        if gemini_keys is None:
            from config import GEMINI_KEYS
            gemini_configs = GEMINI_KEYS
        else:
            # Legacy: convert string keys to configs
            from config import GeminiKeyConfig
            gemini_configs = [
                GeminiKeyConfig(
                    api_key=key,
                    key_name=f"Key#{i+1}",
                    tier="tier1" if i < 5 else "free",
                    ipm_limit=10 if i < 5 else 2
                )
                for i, key in enumerate(gemini_keys)
            ]
        
        self.gemini = ParallelGeminiProcessor(gemini_configs)
        self.num_keys = len(gemini_configs)
        self.total_ipm = sum(k.ipm_limit for k in gemini_configs)
        
        # State
        self.is_running = False
        self.should_stop = False
        self.current_product_index = 0
        self.total_products = 0
        
        # Progress callback
        self._progress_callback: Optional[Callable] = None
        
        logger.info(f"PhotoEnhancer initialized: {self.num_keys} keys, {self.total_ipm} IPM")
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates."""
        self._progress_callback = callback
    
    async def validate_connection(self) -> Dict[str, Any]:
        """Validate Shopify connection."""
        return await self.shopify.validate_connection()
    
    async def enhance_store(
        self,
        max_products: int = None,
        skip_ai_enhanced: bool = True,
        delete_old_images: bool = True
    ) -> EnhancementResult:
        """
        Enhance products with full pipeline:
        1. Fetch LIMITED products from Shopify
        2. Filter content policy violations
        3. Generate images in parallel (tiered rate limiting)
        4. Upload to Shopify
        """
        if self.is_running:
            raise Exception("Enhancement already in progress")
        
        self.is_running = True
        self.should_stop = False
        self.current_product_index = 0
        start_time = datetime.now()
        
        result = EnhancementResult(
            store_url=self.shopify.store_url,
            total_products=0,
            successful_products=0,
            failed_products=0,
            filtered_products=0,
            total_images=0,
            enhanced_images=0,
            start_time=start_time
        )
        
        try:
            # =====================================================================
            # STEP 1: Fetch LIMITED products from Shopify
            # =====================================================================
            logger.info(f"📦 Fetching products... (limit: {max_products or 'All'})")
            
            products = await self.shopify.list_all_products(
                skip_ai_enhanced=skip_ai_enhanced,
                max_products=max_products  # Only fetch what we need!
            )
            
            logger.info(f"   Fetched: {len(products)} products")
            
            if not products:
                logger.info("   No products to process!")
                return result
            
            logger.info(f"🔍 Filtering products...")
            
            # Convert ShopifyProduct to dict for filter
            product_dicts = [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "tags": p.tags,
                    "_product": p  # Keep original for later
                }
                for p in products
            ]
            
            safe_dicts, blocked_dicts = filter_products(product_dicts)
            
            # Extract safe products
            safe_products = [d["_product"] for d in safe_dicts]
            blocked_products = [d["_product"] for d in blocked_dicts]
            
            # Record filtered products
            for d in blocked_dicts:
                result.products.append(ProductResult(
                    product_id=d["id"],
                    product_title=d.get("title", ""),
                    original_image_count=len(d["_product"].images),
                    generated_image_count=0,
                    filtered=True,
                    filter_reason=d.get("_block_reason", "Content policy")
                ))
            
            result.filtered_products = len(blocked_products)
            self.total_products = len(safe_products)
            result.total_products = len(safe_products)
            result.total_images = len(safe_products) * IMAGES_PER_PRODUCT
            logger.info(f"   Safe: {len(safe_products)}, Filtered: {len(blocked_products)}")
            
            if not safe_products:
                logger.info("   No safe products to process!")
                return result
            
            # STEP 3: Create image generation tasks
            
            all_tasks: List[ImageTask] = []
            
            for product in safe_products:
                # Get reference image URL (if exists)
                reference_url = ""
                if product.images:
                    reference_url = product.images[0].get("url", "")
                
                # Create 3 tasks per product
                for img_idx in range(IMAGES_PER_PRODUCT):
                    all_tasks.append(ImageTask(
                        product_id=product.id,
                        product_title=product.title,
                        product_description=product.description or "",
                        image_url=reference_url,
                        image_index=img_idx
                    ))
            
            logger.info(f"   Created {len(all_tasks)} tasks ({len(safe_products)} × {IMAGES_PER_PRODUCT})")
            logger.info(f"   Estimated time: {len(all_tasks) / self.total_ipm:.1f} minutes")
            logger.info("")
            
            # =====================================================================
            # STEP 4: Process ALL images in parallel (tiered rate limiting)
            # =====================================================================
            logger.info("🚀 STEP 4: Generating images (tiered parallel)...")
            logger.info(f"   Keys: {self.num_keys} ({self.total_ipm} IPM)")
            logger.info("")
            
            def on_progress(done: int, total: int, title: str):
                product_progress = done // IMAGES_PER_PRODUCT
                if self._progress_callback:
                    self._progress_callback(
                        min(product_progress, len(safe_products)),
                        len(safe_products),
                        f"Generating: {title[:30]}..."
                    )
            
            generated_images = await self.gemini.enhance_batch(
                all_tasks,
                progress_callback=on_progress
            )
            
            logger.info("📤 Uploading to Shopify...")
            
            # Group images by product
            product_images: Dict[str, List[EnhancedImage]] = {}
            for img in generated_images:
                if img.product_id not in product_images:
                    product_images[img.product_id] = []
                product_images[img.product_id].append(img)
            
            # Parallel upload with semaphore (5 concurrent uploads)
            upload_semaphore = asyncio.Semaphore(5)
            
            async def upload_product(product: ShopifyProduct) -> ProductResult:
                """Upload images for a single product"""
                async with upload_semaphore:
                    images = product_images.get(product.id, [])
                    successful = [img for img in images if img.success and img.enhanced_bytes]
                    
                    pr = ProductResult(
                        product_id=product.id,
                        product_title=product.title,
                        original_image_count=len(product.images),
                        generated_image_count=0
                    )
                    
                    if not successful:
                        pr.error = "All image generations failed"
                        logger.warning(f"   ⚠️ {product.title[:35]}: No images generated")
                        return pr
                    
                    try:
                        # Delete old images if requested (don't fail if this errors)
                        if delete_old_images and product.images:
                            try:
                                media_ids = [img["id"] for img in product.images if img.get("id")]
                                if media_ids:
                                    await self.shopify.delete_product_images(product.id, media_ids)
                            except Exception:
                                pass  # Non-critical, continue with upload
                        
                        # Upload new images
                        for img in successful:
                            filename = f"ai_model_{product.numeric_id}_{img.image_index}.png"
                            url = await self.shopify.upload_enhanced_image(
                                product.id,
                                img.enhanced_bytes,
                                filename,
                                alt_text=f"AI Model Photo - {product.title}"
                            )
                            if url:
                                pr.generated_image_count += 1
                        
                        # Add AI enhanced tag
                        await self.shopify.add_tag_to_product(product.id, "ai-enhanced")
                        
                        pr.success = pr.generated_image_count > 0
                        
                        # Only log failures
                        if not pr.success:
                            logger.warning(f"   ⚠️ {product.title[:40]}: Upload failed")
                    
                    except Exception as e:
                        pr.error = str(e)[:100]
                        logger.error(f"   ❌ {product.title[:35]}: {e}")
                    
                    return pr
            
            # Run all uploads in parallel with semaphore limiting concurrent
            upload_tasks = [upload_product(p) for p in safe_products if not self.should_stop]
            product_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # Process results
            successful_product_names = []  # Track successful products for frontend
            for i, pr in enumerate(product_results):
                if isinstance(pr, Exception):
                    pr = ProductResult(
                        product_id=safe_products[i].id,
                        product_title=safe_products[i].title,
                        original_image_count=len(safe_products[i].images),
                        generated_image_count=0,
                        error=str(pr)[:100]
                    )
                
                result.products.append(pr)
                
                if pr.success:
                    result.successful_products += 1
                    result.enhanced_images += pr.generated_image_count
                    successful_product_names.append(pr.product_title)
                else:
                    if not pr.filtered:
                        result.failed_products += 1
                
                self.current_product_index += 1
                
                # Progress update
                if self._progress_callback:
                    self._progress_callback(
                        self.current_product_index,
                        len(safe_products),
                        pr.product_title
                    )
            
            # =====================================================================
            # FINALIZE
            # =====================================================================
            result.end_time = datetime.now()
            result.total_seconds = (result.end_time - result.start_time).total_seconds()
            result.images_per_minute = (
                result.enhanced_images / result.total_seconds * 60
                if result.total_seconds > 0 else 0
            )
            result.successful_product_names = successful_product_names  # For frontend display
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ ENHANCEMENT COMPLETE!")
            logger.info(f"   Products: {result.successful_products}/{result.total_products}")
            logger.info(f"   Filtered: {result.filtered_products} (content policy)")
            logger.info(f"   Images: {result.enhanced_images}/{result.total_images}")
            logger.info(f"   Time: {result.total_seconds:.1f}s ({result.total_seconds/60:.1f} min)")
            logger.info(f"   Rate: {result.images_per_minute:.1f} images/min")
            logger.info("=" * 60)
            logger.info("")
            
            return result
        
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            raise
        finally:
            self.is_running = False
    
    def stop(self):
        """Stop enhancement process."""
        self.should_stop = True
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current progress."""
        return {
            "is_running": self.is_running,
            "current_product": self.current_product_index,
            "total_products": self.total_products,
            "percent_complete": (
                self.current_product_index / self.total_products * 100
                if self.total_products > 0 else 0
            )
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================

async def main():
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description="Photo Enhancement Pipeline")
    parser.add_argument("--store", required=True, help="Shopify store URL")
    parser.add_argument("--token", required=True, help="Shopify access token")
    parser.add_argument("--max", type=int, default=None, help="Max products")
    parser.add_argument("--keep-old", action="store_true", help="Keep original images")
    
    args = parser.parse_args()
    
    from config import GEMINI_KEYS, print_config
    print_config()
    
    if not GEMINI_KEYS:
        print("❌ No Gemini API keys found in .env!")
        return
    
    enhancer = PhotoEnhancer(args.store, args.token)
    
    print("\n🔗 Connecting to Shopify...")
    try:
        shop = await enhancer.validate_connection()
        print(f"✅ Connected to: {shop['name']}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    print("\n🎨 Starting enhancement...")
    result = await enhancer.enhance_store(
        max_products=args.max,
        delete_old_images=not args.keep_old
    )
    
    print(f"\n📊 Results:")
    print(f"   Products: {result.successful_products}/{result.total_products}")
    print(f"   Filtered: {result.filtered_products}")
    print(f"   Images: {result.enhanced_images}")
    print(f"   Time: {result.total_seconds/60:.1f} minutes")


if __name__ == "__main__":
    asyncio.run(main())
