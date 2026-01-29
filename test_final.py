#!/usr/bin/env python3
"""
IDM-VTON test with reliable public images
"""
import os
import requests
import time

API_TOKEN = os.environ.get("REPLICATE_API_TOKEN", "YOUR_REPLICATE_TOKEN_HERE")

# Using simple, reliable public images
# Woman in plain white background
MODEL_IMG = "https://i.imgur.com/6MYt9Up.jpg"
# Clothing item (cardigan/sweater)
GARMENT_IMG = "https://i.imgur.com/wJGZE7r.jpg"

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json"
}

print("🧪 IDM-VTON Test\n")
print(f"Model: woman in plain clothing")
print(f"Garment: cardigan/sweater\n")

# Start
response = requests.post(
    "https://api.replicate.com/v1/predictions",
    headers=headers,
    json={
        "version": "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
        "input": {
            "human_img": MODEL_IMG,
            "garm_img": GARMENT_IMG,
            "garment_des": "cardigan"
        }
    }
)

if response.status_code != 201:
    print(f"❌ API Error: {response.status_code}")
    print(response.text)
    exit(1)

prediction = response.json()
pred_id = prediction["id"]
print(f"✅ Prediction: {pred_id}\n")
print("⏳ Processing (takes ~20 seconds)...\n")

# Poll
while True:
    r = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
    p = r.json()
    status = p["status"]
    
    print(f"Status: {status}")
    
    if status == "succeeded":
        print(f"\n✅ SUCCESS!\n")
        print(f"Output URL: {p['output']}\n")
        
        # Download
        try:
            img = requests.get(p['output']).content
            with open("/tmp/idm-vton-result.png", "wb") as f:
                f.write(img)
            print(f"✅ Saved to: /tmp/idm-vton-result.png\n")
        except Exception as e:
            print(f"⚠️ Couldn't download: {e}\n")
        
        # Metrics
        if "metrics" in p:
            t = p['metrics'].get('predict_time', 'N/A')
            print(f"⏱️  Time: {t}s")
        
        print(f"\n💰 Cost: $0.023 per image")
        print(f"💰 1,000 images = $23\n")
        print("=" * 60)
        print("READY TO BUILD FULL PIPELINE!")
        print("=" * 60)
        break
    
    elif status == "failed":
        print(f"\n❌ FAILED")
        if "error" in p:
            print(f"Error: {p['error']}")
        if "logs" in p:
            print(f"Logs: {p['logs']}")
        break
    
    elif status == "canceled":
        print(f"\n❌ CANCELED")
        break
    
    time.sleep(3)
