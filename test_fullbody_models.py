#!/usr/bin/env python3
"""
Fast test of full-body model photos with Fashn.ai
Optimized for quick results
"""
import requests
import base64
import time
import json
from pathlib import Path

FASHN_API_KEY = "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD"

def quick_test(model_path: str, garment_path: str = "test_product.jpg") -> tuple:
    """Quick pose detection test - returns (success, message)"""
    
    try:
        # Encode images
        with open(model_path, 'rb') as f:
            model_b64 = base64.b64encode(f.read()).decode('utf-8')
        with open(garment_path, 'rb') as f:
            garment_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        # API request
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
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code != 200:
            return False, f"API error {response.status_code}"
        
        result = response.json()
        job_id = result.get('id')
        
        if not job_id:
            return False, "No job ID"
        
        # Quick poll (20 seconds max)
        for _ in range(10):
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
                    return True, "Success"
                elif status == 'failed':
                    error = status_result.get('error', {})
                    msg = error.get('message', 'Unknown error') if isinstance(error, dict) else str(error)
                    return False, msg
        
        return False, "Timeout"
    
    except Exception as e:
        return False, str(e)[:50]


def main():
    model_dir = Path("fullbody_models")
    
    if not model_dir.exists():
        print("❌ fullbody_models/ not found")
        print("   Run: python find_fullbody_photos.py first")
        return
    
    models = sorted(list(model_dir.glob("*.jpg")))
    
    if not models:
        print("❌ No models found")
        return
    
    print(f"⚡ FAST TEST: {len(models)} full-body models\n")
    print("="*60)
    
    results = {"working": [], "failed": []}
    
    for i, model in enumerate(models, 1):
        name = model.name
        print(f"\n[{i}/{len(models)}] {name}")
        print("   Testing...", end=" ", flush=True)
        
        success, message = quick_test(str(model))
        
        if success:
            print(f"✅ WORKS!")
            results["working"].append(name)
        else:
            print(f"❌ {message}")
            results["failed"].append({"name": name, "error": message})
    
    # Summary
    print("\n" + "="*60)
    print("\n📊 RESULTS:\n")
    print(f"✅ Working: {len(results['working'])}")
    for name in results["working"]:
        print(f"   • {name}")
    
    print(f"\n❌ Failed: {len(results['failed'])}")
    for item in results["failed"][:5]:  # Show first 5
        print(f"   • {item['name']}: {item['error'][:40]}")
    
    # Save
    with open("fullbody_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Saved: fullbody_test_results.json")
    
    if results["working"]:
        print(f"\n🎉 {len(results['working'])} working models found!")
        print(f"\n📝 Ready for production:")
        print(f"   • Copy working models to production directory")
        print(f"   • Update unified_pipeline.py config")
        print(f"   • Run end-to-end test")
    else:
        print(f"\n😞 No working models")
        print(f"\n🔄 Next steps:")
        print(f"   1. Try VModel.ai (different service, may work)")
        print(f"   2. Commission real photos ($200-500)")
        print(f"   3. Use scraper without photos (works now)")


if __name__ == "__main__":
    main()
