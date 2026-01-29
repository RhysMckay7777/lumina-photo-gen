#!/usr/bin/env python3
"""
Simple IDM-VTON test via direct API
"""
import os
import requests
import time
import json

API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "YOUR_REPLICATE_TOKEN_HERE")

# Working test images from Replicate CDN
MODEL_IMG = "https://replicate.delivery/pbxt/KJRu8JlyDUi9kQdXWi8SYCj0cHfKv05hnAyGLz7s6r51vCIe/model_8.png"
GARMENT_IMG = "https://replicate.delivery/pbxt/KJRu8JoAWvGxPXTwh6fJQv6lHrp7pnNUFtixD6mZOhIPfvJB/04564_00.jpg"

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

print("🧪 Testing IDM-VTON...")
print(f"Model: {MODEL_IMG}")
print(f"Garment: {GARMENT_IMG}\n")

# Start prediction
response = requests.post(
    "https://api.replicate.com/v1/predictions",
    headers=headers,
    json={
        "version": "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
        "input": {
            "human_img": MODEL_IMG,
            "garm_img": GARMENT_IMG,
            "garment_des": "dress"
        }
    }
)

prediction = response.json()
pred_id = prediction["id"]
print(f"✅ Started: {pred_id}\n")

# Poll
print("⏳ Processing...")
while True:
    r = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
    p = r.json()
    status = p["status"]
    
    if status == "succeeded":
        print(f"\n✅ SUCCESS!\n")
        print(f"Result: {p['output']}")
        
        # Download
        img = requests.get(p['output']).content
        with open("/tmp/result.png", "wb") as f:
            f.write(img)
        print(f"Saved: /tmp/result.png")
        
        # Show metrics
        if "metrics" in p:
            print(f"\nTime: {p['metrics'].get('predict_time', 'N/A')}s")
        
        print(f"\n💰 Cost: ~$0.023")
        print(f"💰 1,000 images: ~$23")
        break
    
    elif status == "failed":
        print(f"\n❌ Failed: {p.get('error', 'Unknown error')}")
        break
    
    time.sleep(2)
