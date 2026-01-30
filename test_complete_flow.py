#!/usr/bin/env python3
"""
Complete Flow Test - Photo Gen V2 Pipeline
Tests: CJ → Gemini → Claude → Shopify

This script tests each component individually then runs the complete flow.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_env_vars():
    """Test that all required environment variables are set"""
    print("\n" + "="*70)
    print("TEST 1: ENVIRONMENT VARIABLES")
    print("="*70)
    
    required = {
        "CJ_TOKEN": os.getenv("CJ_TOKEN"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
        "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY"),
        "SHOPIFY_STORE": os.getenv("SHOPIFY_STORE"),
        "SHOPIFY_TOKEN": os.getenv("SHOPIFY_TOKEN")
    }
    
    all_set = True
    for key, value in required.items():
        if value:
            print(f"✅ {key}: {value[:20]}..." if len(value) > 20 else f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: NOT SET")
            all_set = False
    
    return all_set

async def test_cj_client():
    """Test CJ Dropshipping API"""
    print("\n" + "="*70)
    print("TEST 2: CJ DROPSHIPPING API")
    print("="*70)
    
    try:
        from cj_client import CJClient
        
        client = CJClient()
        print("\n🔍 Testing CJ API with search: 'cardigan'")
        
        products = await client.search_products(
            keyword="cardigan",
            max_results=2,
            min_price=5,
            max_price=50
        )
        
        if products:
            print(f"✅ PASS: Found {len(products)} products")
            print(f"\nSample product:")
            print(f"   Title: {products[0].title}")
            print(f"   Price: ${products[0].price}")
            print(f"   Image: {products[0].image_url[:60]}...")
            return True, products[0]
        else:
            print(f"⚠️  WARN: No products found (might be API issue)")
            return False, None
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_bio_generator():
    """Test Claude bio generation"""
    print("\n" + "="*70)
    print("TEST 3: CLAUDE BIO GENERATION")
    print("="*70)
    
    try:
        from bio_generator import BioGenerator
        
        bio_gen = BioGenerator()
        print("\n✍️  Generating product copy...")
        
        result = bio_gen.generate_bio(
            product_name="Women's Elegant Cardigan Sweater",
            product_description="Soft knit cardigan, button front, long sleeves",
            price=55.99,
            category="Sweaters"
        )
        
        if result and result.seo_title:
            print(f"✅ PASS: Bio generated")
            print(f"\n   SEO Title: {result.seo_title}")
            print(f"   Description: {result.description_html[:100]}...")
            print(f"   Tags: {result.tags}")
            return True
        else:
            print(f"❌ FAIL: Bio generation returned empty")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_generator():
    """Test Gemini image generation"""
    print("\n" + "="*70)
    print("TEST 4: GEMINI IMAGE GENERATION")
    print("="*70)
    
    try:
        from generator import ModelPhotoGenerator
        
        generator = ModelPhotoGenerator()
        output_dir = Path("output/test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / "test_model.png"
        
        print("\n🎨 Generating AI model photo (text-only)...")
        
        image_path = generator.generate_image(
            product_title="Women's Cardigan Sweater",
            product_description="Soft knit cardigan",
            demographic="women-50-60",
            output_path=str(output_path),
            product_image_url=None  # Text-only for now
        )
        
        if image_path and Path(image_path).exists():
            print(f"✅ PASS: Image generated at {image_path}")
            return True
        else:
            print(f"❌ FAIL: Image not generated")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shopify_client():
    """Test Shopify connection"""
    print("\n" + "="*70)
    print("TEST 5: SHOPIFY CONNECTION")
    print("="*70)
    
    try:
        from shopify_client import ShopifyClient
        
        client = ShopifyClient(
            os.getenv("SHOPIFY_STORE"),
            os.getenv("SHOPIFY_TOKEN")
        )
        
        print("\n🏪 Testing Shopify connection...")
        products = client.get_products(limit=3)
        
        if products is not None:
            print(f"✅ PASS: Connected to Shopify")
            print(f"   Found {len(products)} products")
            if products:
                print(f"   Sample: {products[0].get('title', 'N/A')}")
            return True
        else:
            print(f"❌ FAIL: Could not connect")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_complete_pipeline():
    """Test the complete unified pipeline (dry run)"""
    print("\n" + "="*70)
    print("TEST 6: COMPLETE PIPELINE (DRY RUN)")
    print("="*70)
    
    try:
        from unified_pipeline import UnifiedPipeline, PipelineConfig
        
        config = PipelineConfig(
            cj_token=os.getenv("CJ_TOKEN"),
            gemini_key=os.getenv("GEMINI_API_KEY"),
            anthropic_key=os.getenv("ANTHROPIC_API_KEY"),
            shopify_store=os.getenv("SHOPIFY_STORE"),
            shopify_token=os.getenv("SHOPIFY_TOKEN"),
            max_products=1,
            dry_run=True  # Don't upload to Shopify
        )
        
        pipeline = UnifiedPipeline(config)
        
        print("\n🚀 Running complete pipeline with keyword: 'cardigan'")
        print("   Mode: DRY RUN (no Shopify upload)")
        
        results = await pipeline.run(
            keyword="cardigan",
            max_products=1,
            min_price=10,
            max_price=50
        )
        
        if results and len(results) > 0:
            result = results[0]
            print(f"\n✅ PASS: Pipeline completed")
            print(f"\n   Product: {result.cj_product.title}")
            print(f"   Generated images: {len(result.generated_images)}")
            print(f"   SEO title: {result.bio.seo_title if result.bio else 'N/A'}")
            print(f"   Success: {result.success}")
            if result.error:
                print(f"   Error: {result.error}")
            return True
        else:
            print(f"❌ FAIL: No results returned")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 LUMINA PHOTO GEN V2 - COMPLETE FLOW TEST")
    print("="*70)
    
    results = {}
    
    # Test 1: Environment
    results['env'] = test_env_vars()
    
    if not results['env']:
        print("\n❌ CRITICAL: Environment variables not set. Please update .env")
        print("\nRequired:")
        print("  - CJ_TOKEN")
        print("  - GEMINI_API_KEY")
        print("  - ANTHROPIC_API_KEY")
        print("  - SHOPIFY_STORE")
        print("  - SHOPIFY_TOKEN")
        return False
    
    # Test 2: CJ API
    results['cj'], sample_product = await test_cj_client()
    
    # Test 3: Claude Bio
    results['bio'] = test_bio_generator()
    
    # Test 4: Gemini Images
    results['gemini'] = test_gemini_generator()
    
    # Test 5: Shopify
    results['shopify'] = test_shopify_client()
    
    # Test 6: Complete Pipeline
    results['pipeline'] = await test_complete_pipeline()
    
    # Summary
    print("\n\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name.upper()}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Pipeline ready!")
        print("\nNext steps:")
        print("  1. Run with real data: python3 unified_pipeline.py --keyword 'cardigan' --max 1 --dry-run")
        print("  2. Deploy to production (no dry-run flag)")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        print("\nCommon issues:")
        print("  - CJ_TOKEN: Verify format from CJ dashboard")
        print("  - GEMINI_API_KEY: Generate new key if flagged")
        print("  - ANTHROPIC_API_KEY: Check validity at console.anthropic.com")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
