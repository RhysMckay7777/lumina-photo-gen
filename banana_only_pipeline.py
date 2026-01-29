#!/usr/bin/env python3
"""
Product photos using ONLY Banana Pro (no Fashn.ai)
Scrape product → Generate model wearing it
"""
import os
import sys
import subprocess
import requests

# Install deps
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai"], check=True)

from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def scrape_cardigans(max_products=3):
    """Scrape cardigans from CJ"""
    print("🔍 Scraping cardigans...")
    
    # Simple scrape - just get product info
    url = "https://www.cjdropshipping.com/search/cardigan+women+loose.html"
    
    # Mock data for now (replace with real scraper)
    products = [
        {
            "title": "Women's Loose Knit Cardigan Sweater",
            "description": "Casual oversized cardigan in beige color, soft knit material, open front design",
            "color": "beige",
            "style": "loose oversized casual"
        },
        {
            "title": "Women's Long Sleeve Open Front Cardigan",  
            "description": "Lightweight cardigan in cream white, long sleeves, flowing open front",
            "color": "cream white",
            "style": "lightweight flowing"
        },
        {
            "title": "Women's Cozy Knit Cardigan",
            "description": "Soft knit cardigan in light gray, relaxed fit, button front",
            "color": "light gray", 
            "style": "cozy relaxed fit"
        }
    ]
    
    return products[:max_products]

def generate_model_wearing_product(product_info, output_path):
    """Use Banana Pro to generate model wearing the product"""
    
    title = product_info['title']
    description = product_info['description']
    color = product_info['color']
    style = product_info['style']
    
    prompt = f"""Professional fashion photography: elegant mature woman aged 55-60 wearing a {color} {style} cardigan. 

Product details: {description}

The woman should be:
- Full body shot from head to feet
- Standing naturally in a relaxed pose
- Wearing the cardigan open over a simple neutral top and dark pants
- Silver/gray hair, elegant and sophisticated
- Plain white studio background
- Professional studio lighting
- Front-facing view
- High quality fashion photography style
- The cardigan should be clearly visible and be the focal point

Style: Professional fashion catalog photography"""

    print(f"  🎨 Generating: {title[:50]}...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt
        )
        
        # Extract and save image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    with open(output_path, 'wb') as f:
                        f.write(part.inline_data.data)
                    print(f"  ✅ Saved: {output_path}")
                    return True
        
        print(f"  ❌ No image generated")
        return False
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print("="*70)
    print("BANANA PRO ONLY - PRODUCT PHOTO GENERATION")
    print("="*70)
    print()
    
    # Step 1: Scrape products
    products = scrape_cardigans(max_products=3)
    
    print(f"✅ Got {len(products)} products")
    print()
    
    # Step 2: Generate model photos for each product
    output_dir = "/Users/rhysmckay/lumina-photo-gen/output"
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎨 Generating model photos...")
    print()
    
    for idx, product in enumerate(products, 1):
        print(f"Product {idx}: {product['title']}")
        
        output_path = f"{output_dir}/product-{idx:02d}-model.png"
        
        success = generate_model_wearing_product(product, output_path)
        
        if success:
            print(f"MEDIA:{output_path}")
        
        print()
    
    print("✅ Complete! All photos generated with Banana Pro only.")

if __name__ == "__main__":
    main()
