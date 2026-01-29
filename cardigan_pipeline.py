#!/usr/bin/env python3
"""
Complete pipeline: CJ cardigan products → Mature model photos → Fashn.ai try-on
"""
import os
import sys
import json
import time
import requests
from pathlib import Path

# Add scraper path
sys.path.insert(0, "/Users/rhysmckay/clawd/dropship-automate/backend")

FASHN_API_KEY = "sk-uf9dqnuaxdjaxocfadw7fhvq5jk11fv1"
FASHN_API_URL = "https://api.fashn.ai/v1/run"

def scrape_cj_cardigans(max_products=5):
    """Scrape cardigan products from CJ"""
    print("🔍 Scraping cardigans from CJ...")
    
    # Use the existing scraper
    from app.services.scraper.aliexpress import AliExpressScraper
    
    url = "https://www.cjdropshipping.com/search/cardigan+women+loose.html"
    
    scraper = AliExpressScraper(headless=True, verbose=False)
    products = []
    
    try:
        import asyncio
        async def scrape():
            async for product in scraper.scrape(url=url, max_products=max_products, fetch_details=True):
                products.append(product)
                print(f"  ✓ {product['title'][:50]}...")
        
        asyncio.run(scrape())
    finally:
        import asyncio
        asyncio.run(scraper.close())
    
    print(f"✅ Scraped {len(products)} cardigans")
    return products

def generate_with_fashn(product_image_url, model_photo_path, output_path):
    """Generate try-on image with Fashn.ai"""
    
    # Download product image
    product_img_path = "/tmp/product.jpg"
    response = requests.get(product_image_url)
    with open(product_img_path, 'wb') as f:
        f.write(response.content)
    
    # Prepare request
    with open(model_photo_path, 'rb') as model_file:
        with open(product_img_path, 'rb') as product_file:
            files = {
                'model_image': model_file,
                'garment_image': product_file
            }
            
            headers = {
                'Authorization': f'Bearer {FASHN_API_KEY}'
            }
            
            data = {
                'category': 'tops'  # cardigans are tops
            }
            
            print(f"  🎨 Generating try-on...")
            response = requests.post(FASHN_API_URL, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Poll for result
                if 'id' in result:
                    job_id = result['id']
                    max_attempts = 30
                    
                    for attempt in range(max_attempts):
                        time.sleep(2)
                        status_response = requests.get(
                            f"https://api.fashn.ai/v1/status/{job_id}",
                            headers=headers
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if status_data.get('status') == 'completed':
                                # Download result
                                result_url = status_data.get('output_url')
                                if result_url:
                                    result_img = requests.get(result_url)
                                    with open(output_path, 'wb') as f:
                                        f.write(result_img.content)
                                    return True
                            elif status_data.get('status') == 'failed':
                                print(f"  ❌ Failed: {status_data.get('error')}")
                                return False
                
                return False
            else:
                print(f"  ❌ API error: {response.status_code} - {response.text}")
                return False

def main():
    print("="*70)
    print("CARDIGAN PHOTO GENERATION PIPELINE")
    print("="*70)
    print()
    
    # Step 1: Get model photos
    model_dir = Path("/Users/rhysmckay/lumina-photo-gen/model_photos")
    model_photos = list(model_dir.glob("mature-woman-*.png"))
    
    if not model_photos:
        print("❌ No model photos found. Run batch_generate_models.py first!")
        return
    
    print(f"✅ Found {len(model_photos)} model photos")
    
    # Step 2: Scrape cardigans
    products = scrape_cj_cardigans(max_products=3)
    
    if not products:
        print("❌ No products scraped")
        return
    
    # Step 3: Generate try-on images
    output_dir = Path("/Users/rhysmckay/lumina-photo-gen/output")
    output_dir.mkdir(exist_ok=True)
    
    print()
    print("🎨 Generating try-on images...")
    print()
    
    for idx, product in enumerate(products, 1):
        print(f"Product {idx}: {product['title'][:50]}...")
        
        # Get first product image
        if not product.get('images'):
            print("  ⚠️  No product images, skipping")
            continue
        
        product_img_url = product['images'][0]
        
        # Use first model photo
        model_photo = model_photos[0]
        
        output_path = output_dir / f"cardigan-{idx:02d}-result.png"
        
        success = generate_with_fashn(product_img_url, model_photo, output_path)
        
        if success:
            print(f"  ✅ Saved: {output_path}")
            print(f"  MEDIA:{output_path}")
        else:
            print(f"  ❌ Failed to generate")
        
        print()
    
    print("✅ Pipeline complete!")

if __name__ == "__main__":
    main()
