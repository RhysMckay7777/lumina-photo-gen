#!/usr/bin/env python3
"""
Test all model photos to find which ones work with Fashn.ai
"""
import os
import requests
import base64
import json
import time
from pathlib import Path

FASHN_API_KEY = "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD"

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def test_model_photo(model_path):
    """Test if a model photo works with Fashn.ai pose detection"""
    
    print(f"\n🧪 Testing: {model_path}")
    
    try:
        model_b64 = encode_image(model_path)
    except Exception as e:
        print(f"❌ Failed to read image: {e}")
        return False
    
    # Create a simple garment image (or use test_product.jpg)
    if not os.path.exists("test_product.jpg"):
        print("❌ test_product.jpg not found")
        return False
    
    garment_b64 = encode_image("test_product.jpg")
    
    url = "https://api.fashn.ai/v1/run"
    headers = {
        "Authorization": f"Bearer {FASHN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model_name": "tryon-v1.6",
        "inputs": {
            "category": "tops",
            "garment_image": f"data:image/jpeg;base64,{garment_b64}",
            "model_image": f"data:image/jpeg;base64,{model_b64}",
            "num_samples": 1
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code != 200:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return False
    
    result = response.json()
    
    # Check for async job
    if 'id' in result:
        job_id = result['id']
        print(f"⏳ Job created: {job_id}")
        
        # Poll for result
        for attempt in range(30):  # 1 minute max
            time.sleep(2)
            
            status_response = requests.get(
                f"https://api.fashn.ai/v1/status/{job_id}",
                headers=headers
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                
                if status_result.get('status') == 'succeeded':
                    print(f"✅ WORKS! Pose detected successfully")
                    return True
                elif status_result.get('status') == 'failed':
                    error = status_result.get('error', {})
                    print(f"❌ Failed: {error}")
                    return False
                else:
                    if attempt % 5 == 0:
                        print(f"   Still processing... ({attempt+1}/30)")
        
        print(f"⏱️  Timeout waiting for result")
        return False
    
    # Immediate result (unlikely)
    if 'output' in result:
        print(f"✅ WORKS! Got immediate result")
        return True
    
    print(f"❌ Unexpected response: {result}")
    return False

def main():
    """Test all model photos in model_photos/ directory"""
    
    model_dir = Path("model_photos")
    if not model_dir.exists():
        print("❌ model_photos/ directory not found")
        return
    
    # Get all image files
    image_files = sorted(
        list(model_dir.glob("*.jpg")) + 
        list(model_dir.glob("*.jpeg")) + 
        list(model_dir.glob("*.png"))
    )
    
    if not image_files:
        print("❌ No images found in model_photos/")
        return
    
    print(f"🔍 Found {len(image_files)} model photos to test\n")
    print("=" * 60)
    
    working_models = []
    failed_models = []
    
    for img_path in image_files:
        works = test_model_photo(str(img_path))
        
        if works:
            working_models.append(str(img_path))
        else:
            failed_models.append(str(img_path))
        
        # Rate limit protection
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("\n📊 RESULTS:")
    print(f"\n✅ Working models ({len(working_models)}):")
    for model in working_models:
        print(f"   - {model}")
    
    print(f"\n❌ Failed models ({len(failed_models)}):")
    for model in failed_models:
        print(f"   - {model}")
    
    # Save results
    results = {
        "working": working_models,
        "failed": failed_models,
        "tested_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("model_photo_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: model_photo_test_results.json")
    
    if working_models:
        print(f"\n🎉 Recommendation: Use {working_models[0]} for production")

if __name__ == "__main__":
    main()
