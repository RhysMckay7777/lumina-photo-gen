#!/usr/bin/env python3
"""
Pull a product image from Shopify to test IDM-VTON
"""
import requests
import json

SHOPIFY_STORE = "ibzfrj-xh.myshopify.com"
SHOPIFY_TOKEN = "YOUR_SHOPIFY_TOKEN_HERE"

headers = {
    "X-Shopify-Access-Token": SHOPIFY_TOKEN,
    "Content-Type": "application/json"
}

print("📦 Fetching products from Shopify...\n")

# Get products
response = requests.get(
    f"https://{SHOPIFY_STORE}/admin/api/2024-01/products.json?limit=5",
    headers=headers
)

if response.status_code != 200:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
    exit(1)

products = response.json().get("products", [])

if not products:
    print("No products found")
    exit(1)

print(f"✅ Found {len(products)} products\n")

# Show first product
product = products[0]
print(f"Product: {product['title']}")

if product.get('images'):
    img_url = product['images'][0]['src']
    print(f"Image: {img_url}\n")
    
    # Save for testing
    with open("/tmp/shopify_product_url.txt", "w") as f:
        f.write(img_url)
    
    print(f"✅ Saved image URL for testing\n")
    print("Now run: python3 test_with_shopify_image.py")
else:
    print("No images found")
