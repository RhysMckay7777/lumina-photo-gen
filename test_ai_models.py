#!/usr/bin/env python3
"""
Test AI-generated models with Fashn.ai
Comprehensive testing with immediate feedback
"""
import sys
import os
import json
import time
from pathlib import Path
from enhanced_fashn_client import FashnClient

def test_ai_models():
    """Test all AI-generated model photos"""
    
    model_dir = Path("ai_generated_models")
    
    if not model_dir.exists():
        print("❌ ai_generated_models/ directory not found")
        print("   Run: python generate_ai_models.py first")
        return
    
    models = sorted(list(model_dir.glob("*.jpg")))
    
    if not models:
        print("❌ No AI-generated models found")
        return
    
    print(f"🧪 Testing {len(models)} AI-generated models with Fashn.ai\n")
    print("="*70)
    
    # Initialize Fashn client
    api_key = os.getenv("FASHN_API_KEY", "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD")
    client = FashnClient(api_key, model_photos_dir=str(model_dir))
    
    # Use test product
    test_product = "test_product.jpg"
    if not Path(test_product).exists():
        print(f"⚠️  {test_product} not found, skipping generation test")
        return
    
    results = {
        "working": [],
        "failed": [],
        "tested_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Test each model
    for i, model_path in enumerate(models, 1):
        name = model_path.name
        print(f"\n[{i}/{len(models)}] {name}")
        
        output_path = f"test_output_{i}.jpg"
        
        # Try generation
        success = client.generate(
            test_product,
            output_path,
            max_retries=1  # Quick test, single attempt
        )
        
        if success:
            print(f"   ✅ WORKS! Generated: {output_path}")
            results["working"].append({
                "model": name,
                "output": output_path
            })
        else:
            print(f"   ❌ Failed")
            results["failed"].append(name)
        
        time.sleep(1)  # Rate limit
    
    # Summary
    print("\n" + "="*70)
    print("\n📊 AI MODEL TEST RESULTS:\n")
    
    print(f"✅ Working models: {len(results['working'])}")
    for item in results['working']:
        print(f"   • {item['model']}")
    
    print(f"\n❌ Failed models: {len(results['failed'])}")
    for name in results['failed']:
        print(f"   • {name}")
    
    # Save results
    with open("ai_model_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved: ai_model_test_results.json")
    
    # Update client stats
    client.print_stats()
    
    # Next steps
    if results["working"]:
        print(f"\n🎉 SUCCESS! {len(results['working'])} working models found")
        print(f"\n📝 Next steps:")
        print(f"1. These models are ready for production")
        print(f"2. Update production_pipeline.py to use ai_generated_models/")
        print(f"3. Run unified pipeline to test full workflow")
        
        # Auto-update config
        config_file = Path("pipeline_config.json")
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
            
            config["model_photos_dir"] = "ai_generated_models"
            config["working_models"] = [item["model"] for item in results["working"]]
            
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"   ✅ Updated pipeline_config.json with working models")
    else:
        print(f"\n😞 No working models found")
        print(f"   Need to try different approach")
    
    return len(results["working"]) > 0


if __name__ == "__main__":
    success = test_ai_models()
    sys.exit(0 if success else 1)
