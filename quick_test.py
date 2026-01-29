#!/usr/bin/env python3
import requests
import base64
import json
import sys

API_KEY = "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD"

def encode(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

print("📸 Loading images...")
garment_b64 = encode("test_product.jpg")
model_b64 = encode("model_photos/model_mature_01.jpg")
print("✅ Images loaded")

print("\n🌐 Calling Fashn.ai API...")
response = requests.post(
    "https://api.fashn.ai/v1/run",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model_name": "tryon-v1.6",
        "inputs": {
            "category": "tops",
            "garment_image": f"data:image/jpeg;base64,{garment_b64}",
            "model_image": f"data:image/jpeg;base64,{model_b64}",
            "num_samples": 1
        }
    },
    timeout=30
)

print(f"📡 Response: {response.status_code}")
print(f"📄 Body: {response.text[:500]}")

if response.status_code == 200:
    result = response.json()
    if 'id' in result:
        print(f"\n⏳ Job ID: {result['id']}")
        print("Polling for result...")
        
        import time
        for i in range(30):
            time.sleep(2)
            status_resp = requests.get(
                f"https://api.fashn.ai/v1/status/{result['id']}",
                headers={"Authorization": f"Bearer {API_KEY}"}
            )
            status_data = status_resp.json()
            print(f"  [{i+1}/30] Status: {status_data.get('status')}")
            
            if status_data.get('status') == 'succeeded':
                print("\n✅ SUCCESS!")
                if 'output' in status_data:
                    output_b64 = status_data['output'][0].split(',')[1] if ',' in status_data['output'][0] else status_data['output'][0]
                    output_data = base64.b64decode(output_b64)
                    with open('test_output.jpg', 'wb') as f:
                        f.write(output_data)
                    print("💾 Saved to test_output.jpg")
                    sys.exit(0)
                break
            elif status_data.get('status') == 'failed':
                print(f"\n❌ FAILED: {status_data.get('error')}")
                sys.exit(1)
    else:
        print("❌ Unexpected response format")
else:
    print(f"❌ API Error")
