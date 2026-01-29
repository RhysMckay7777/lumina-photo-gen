#!/usr/bin/env python3
"""
Test IDM-VTON via Replicate API
$0.023 per image = $23 per 1,000 images
"""
import os
import sys
import requests
import time
import json

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

if not REPLICATE_API_TOKEN:
    print("❌ REPLICATE_API_TOKEN not set!")
    print("\nGet your token from: https://replicate.com/account/api-tokens")
    print("Then run: export REPLICATE_API_TOKEN='YOUR_REPLICATE_TOKEN_HERE...'")
    sys.exit(1)

def test_vton(model_image_url, garment_image_url):
    """
    Test virtual try-on with IDM-VTON
    """
    print("🧪 Testing IDM-VTON on Replicate...")
    print(f"Model image: {model_image_url}")
    print(f"Garment image: {garment_image_url}")
    
    # Start prediction
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "version": "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
        "input": {
            "human_img": model_image_url,
            "garm_img": garment_image_url,
            "garment_des": "clothing item"
        }
    }
    
    print("\n📤 Starting prediction...")
    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=headers,
        json=payload
    )
    
    if response.status_code != 201:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None
    
    prediction = response.json()
    prediction_id = prediction["id"]
    print(f"✅ Prediction started: {prediction_id}")
    print(f"Status: {prediction['status']}")
    
    # Poll for result
    print("\n⏳ Waiting for result...")
    while True:
        response = requests.get(
            f"https://api.replicate.com/v1/predictions/{prediction_id}",
            headers=headers
        )
        
        prediction = response.json()
        status = prediction["status"]
        
        print(f"Status: {status}")
        
        if status == "succeeded":
            print("\n✅ Success!")
            output_url = prediction["output"]
            print(f"Result: {output_url}")
            
            # Download result
            output_path = "/tmp/idm-vton-result.png"
            img_data = requests.get(output_url).content
            with open(output_path, 'wb') as f:
                f.write(img_data)
            
            print(f"Saved to: {output_path}")
            
            # Show metrics
            if "metrics" in prediction:
                print(f"\nMetrics:")
                print(json.dumps(prediction["metrics"], indent=2))
            
            return output_path
        
        elif status == "failed":
            print(f"\n❌ Failed!")
            if "error" in prediction:
                print(f"Error: {prediction['error']}")
            return None
        
        elif status == "canceled":
            print(f"\n❌ Canceled")
            return None
        
        time.sleep(2)

def main():
    print("=" * 60)
    print("IDM-VTON TEST - Replicate API")
    print("=" * 60)
    print()
    
    # Test with sample images
    # Using public test images from IDM-VTON demo
    
    model_image = "https://github.com/yisol/IDM-VTON/raw/main/example/model/model_1.png"
    garment_image = "https://github.com/yisol/IDM-VTON/raw/main/example/cloth/cloth_1.jpg"
    
    print("Using sample images from IDM-VTON repo:")
    print(f"Model: {model_image}")
    print(f"Garment: {garment_image}")
    print()
    
    result = test_vton(model_image, garment_image)
    
    if result:
        print("\n" + "=" * 60)
        print("TEST SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"Cost: ~$0.023 per image")
        print(f"For 1,000 images: ~$23")
        print()
        print("Next steps:")
        print("1. Connect to Shopify API to pull products")
        print("2. For each product:")
        print("   - Use product image as garment")
        print("   - Use AI-generated model as human")
        print("   - Run IDM-VTON")
        print("   - Upload result back to Shopify")
        print()
    else:
        print("\n❌ Test failed - check errors above")

if __name__ == "__main__":
    main()
