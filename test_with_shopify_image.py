#!/usr/bin/env python3
"""
Test IDM-VTON with real Shopify product image
"""
import os
import requests
import time

API_TOKEN = "YOUR_REPLICATE_TOKEN_HERE"

# Read product URL
with open("/tmp/shopify_product_url.txt") as f:
    GARMENT_IMG = f.read().strip()

# Use a stock model image (woman in plain clothing)
# This URL is stable and publicly accessible
MODEL_IMG = "https://raw.githubusercontent.com/yisol/IDM-VTON/main/example/model/model_1.png"

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

print("🧪 IDM-VTON Test with Shopify Product\n")
print(f"Product: 3D Digital Printing Cardigan")
print(f"Garment URL: {GARMENT_IMG}")
print(f"Model URL: {MODEL_IMG}\n")

# Start
response = requests.post(
    "https://api.replicate.com/v1/predictions",
    headers=headers,
    json={
        "version": "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
        "input": {
            "human_img": MODEL_IMG,
            "garm_img": GARMENT_IMG,
            "garment_des": "cardigan knitted coat"
        }
    }
)

if response.status_code != 201:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
    exit(1)

prediction = response.json()
pred_id = prediction["id"]
print(f"✅ Prediction ID: {pred_id}\n")
print("⏳ Processing (takes ~20 seconds)...\n")

# Poll
start_time = time.time()
while True:
    r = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
    p = r.json()
    status = p["status"]
    
    elapsed = int(time.time() - start_time)
    print(f"[{elapsed}s] Status: {status}")
    
    if status == "succeeded":
        print(f"\n✅ SUCCESS!\n")
        print(f"Result URL: {p['output']}\n")
        
        # Download
        try:
            img = requests.get(p['output']).content
            output_path = "/tmp/idm-vton-shopify-result.png"
            with open(output_path, "wb") as f:
                f.write(img)
            print(f"✅ Saved to: {output_path}\n")
        except Exception as e:
            print(f"⚠️ Download error: {e}\n")
        
        # Metrics
        if "metrics" in p:
            predict_time = p['metrics'].get('predict_time', 'N/A')
            print(f"⏱️  Processing time: {predict_time}s")
        
        print(f"\n💰 Cost: $0.023")
        print(f"💰 1,000 products = $23\n")
        
        print("=" * 60)
        print("✅ PROOF OF CONCEPT COMPLETE!")
        print("=" * 60)
        print("\nIDM-VTON works with your Shopify product images!")
        print("\nNext: Build full pipeline with:")
        print("  - Web UI to select products")
        print("  - Batch processing")
        print("  - Auto-upload to Shopify")
        print("  - Preview before uploading")
        break
    
    elif status == "failed":
        print(f"\n❌ FAILED")
        if "error" in p:
            print(f"Error: {p['error']}")
        break
    
    elif status == "canceled":
        print(f"\n❌ CANCELED")
        break
    
    time.sleep(3)
