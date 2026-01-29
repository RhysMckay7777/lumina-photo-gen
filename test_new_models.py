#!/usr/bin/env python3
"""
Test new Unsplash model photos with Fashn.ai
"""
import requests
import base64
import json
import time
from pathlib import Path

FASHN_API_KEY = "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD"

def encode_image(image_path):
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def test_model(model_path, garment_path="test_product.jpg"):
    """Quick pose detection test"""
    
    try:
        model_b64 = encode_image(model_path)
        garment_b64 = encode_image(garment_path)
    except:
        return "read_error", None
    
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
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            return "api_error", response.status_code
        
        result = response.json()
        
        if 'id' not in result:
            return "no_job_id", None
        
        job_id = result['id']
        
        # Poll for result (max 30 seconds)
        for _ in range(15):
            time.sleep(2)
            
            status_response = requests.get(
                f"https://api.fashn.ai/v1/status/{job_id}",
                headers=headers,
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                status = status_result.get('status')
                
                if status == 'succeeded':
                    return "success", job_id
                elif status == 'failed':
                    error = status_result.get('error', {})
                    return "failed", error
        
        return "timeout", job_id
    
    except Exception as e:
        return "exception", str(e)

def main():
    model_dir = Path("model_photos_new")
    
    if not model_dir.exists():
        print("❌ model_photos_new/ not found")
        return
    
    models = sorted(list(model_dir.glob("*.jpg")))
    
    if not models:
        print("❌ No JPG files found")
        return
    
    print(f"🧪 Testing {len(models)} models with Fashn.ai\n")
    print("=" * 70)
    
    results = {
        "working": [],
        "failed": [],
        "errors": []
    }
    
    for i, model_path in enumerate(models, 1):
        name = model_path.name
        print(f"\n[{i}/{len(models)}] {name}")
        print("   Testing...", end=" ", flush=True)
        
        status, info = test_model(str(model_path))
        
        if status == "success":
            print(f"✅ WORKS!")
            results["working"].append(name)
        elif status == "failed":
            error_msg = info.get('message', 'Unknown') if isinstance(info, dict) else str(info)
            print(f"❌ Failed: {error_msg}")
            results["failed"].append({"name": name, "error": error_msg})
        else:
            print(f"⚠️  Error: {status} - {info}")
            results["errors"].append({"name": name, "status": status, "info": str(info)})
        
        time.sleep(1)  # Rate limit protection
    
    print("\n" + "=" * 70)
    print("\n📊 RESULTS:\n")
    
    print(f"✅ Working models ({len(results['working'])}):")
    for name in results['working']:
        print(f"   • {name}")
    
    print(f"\n❌ Failed pose detection ({len(results['failed'])}):")
    for item in results['failed']:
        print(f"   • {item['name']}: {item['error']}")
    
    print(f"\n⚠️  Errors/Timeouts ({len(results['errors'])}):")
    for item in results['errors']:
        print(f"   • {item['name']}: {item['status']}")
    
    # Save results
    output = {
        "working": results["working"],
        "failed": [{"name": f["name"], "error": f["error"]} for f in results["failed"]],
        "errors": results["errors"],
        "tested_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_tested": len(models)
    }
    
    with open("model_test_results.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Saved: model_test_results.json")
    
    if results["working"]:
        print(f"\n🎉 SUCCESS! {len(results['working'])} working models found")
        print(f"\n📝 Next: Update production_pipeline.py to use these models")
    else:
        print(f"\n😞 No working models found. May need different photos.")

if __name__ == "__main__":
    main()
