#!/usr/bin/env python3
"""
Comprehensive test of the full pipeline
"""
import sys
from pipeline import PhotoGenerationPipeline
from pathlib import Path

SHOPIFY_STORE = "ibzfrj-xh.myshopify.com"
SHOPIFY_TOKEN = "YOUR_SHOPIFY_TOKEN_HERE"

def test_full_pipeline():
    print("="*60)
    print("COMPREHENSIVE PIPELINE TEST")
    print("="*60)
    
    pipeline = PhotoGenerationPipeline(SHOPIFY_STORE, SHOPIFY_TOKEN)
    
    # Test 1: Get products
    print("\n📋 TEST 1: Fetching products...")
    products = pipeline.list_products()
    print(f"✅ Found {len(products)} products")
    
    if len(products) < 3:
        print("❌ Not enough products to test")
        return False
    
    # Test 2: Test with 3 different products (different types)
    print("\n🎨 TEST 2: Generating for 3 different products...")
    test_products = products[:3]
    
    for i, product in enumerate(test_products, 1):
        print(f"\n--- Product {i}/3 ---")
        print(f"ID: {product['id']}")
        print(f"Title: {product['title']}")
        
        try:
            # Test with only women-50-60 for speed
            results = pipeline.process_product(
                product['id'],
                demographics=['women-50-60'],
                upload=False,  # Don't upload yet
                output_dir=f"/tmp/test-pipeline/product-{product['id']}"
            )
            
            if results and len(results) > 0:
                print(f"✅ Generated {len(results)} images")
                
                # Check file exists
                for result in results:
                    if Path(result['path']).exists():
                        size = Path(result['path']).stat().st_size
                        print(f"  ✅ {result['demographic']}: {size} bytes")
                    else:
                        print(f"  ❌ File not found: {result['path']}")
                        return False
            else:
                print(f"❌ No results generated")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Test 3: Test upload functionality
    print("\n📤 TEST 3: Testing Shopify upload...")
    test_product_id = test_products[0]['id']
    test_image = f"/tmp/test-pipeline/product-{test_product_id}/model-women-50-60-01.png"
    
    if not Path(test_image).exists():
        print(f"❌ Test image not found: {test_image}")
        return False
    
    try:
        result = pipeline.shopify.upload_image(test_product_id, test_image)
        print(f"✅ Upload successful: {result['src'][:60]}...")
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False
    
    # Test 4: Test different demographics
    print("\n👥 TEST 4: Testing all demographics...")
    test_product_id = test_products[1]['id']
    
    try:
        results = pipeline.process_product(
            test_product_id,
            demographics=['women-40-50', 'women-50-60', 'women-60-65'],
            upload=False,
            output_dir=f"/tmp/test-pipeline/demographics"
        )
        
        if len(results) == 3:
            print(f"✅ All 3 demographics generated successfully")
        else:
            print(f"❌ Expected 3 results, got {len(results)}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 5: Quality check - verify images are not empty
    print("\n🔍 TEST 5: Quality check...")
    for result in results:
        path = Path(result['path'])
        size = path.stat().st_size
        
        if size < 10000:  # Less than 10KB is suspicious
            print(f"❌ Image too small: {path} ({size} bytes)")
            return False
        
        print(f"✅ {result['demographic']}: {size} bytes")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60)
    return True

if __name__ == "__main__":
    success = test_full_pipeline()
    sys.exit(0 if success else 1)
