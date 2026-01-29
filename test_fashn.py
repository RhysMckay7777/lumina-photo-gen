#!/usr/bin/env python3
"""
Quick Fashn.ai test script
"""
import os
import requests
import base64
import json
import time
from pathlib import Path

# API key
FASHN_API_KEY = "fa-lgsY84c32rTX-krZ1EKidFOkzhndCIzv3SlcD"

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def generate_tryon(garment_path, model_path="model_photo.jpg", output_path="output.jpg"):
    """Generate virtual try-on using Fashn.ai"""
    
    # Encode images
    garment_b64 = encode_image(garment_path)
    model_b64 = encode_image(model_path)
    
    # Fashn.ai API endpoint
    url = "https://api.fashn.ai/v1/run"
    
    headers = {
        "Authorization": f"Bearer {FASHN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Request payload
    payload = {
        "model_name": "tryon-v1.6",
        "inputs": {
            "category": "tops",
            "garment_image": f"data:image/jpeg;base64,{garment_b64}",
            "model_image": f"data:image/jpeg;base64,{model_b64}",
            "num_samples": 1
        }
    }
    
    print(f"   Model: {model_path}")
    
    print("🎨 Generating virtual try-on with Fashn.ai...")
    print(f"   Garment: {garment_path}")
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        
        # Check if we got a job ID (async mode)
        if 'id' in result and 'output' not in result:
            job_id = result['id']
            print(f"⏳ Job created: {job_id}")
            print(f"   Waiting for completion...")
            
            # Poll for result
            max_attempts = 60  # 2 minutes max
            for attempt in range(max_attempts):
                time.sleep(2)
                
                status_response = requests.get(
                    f"https://api.fashn.ai/v1/status/{job_id}",
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    
                    if status_result.get('status') == 'succeeded':
                        print(f"✅ Generation complete!")
                        result = status_result
                        break
                    elif status_result.get('status') == 'failed':
                        print(f"❌ Generation failed: {status_result.get('error')}")
                        return None
                    else:
                        print(f"   Status: {status_result.get('status')}... ({attempt+1}/{max_attempts})")
                
                time.sleep(2)
        
        # Save result
        if 'output' in result and len(result['output']) > 0:
            output_b64 = result['output'][0].split(',')[1] if ',' in result['output'][0] else result['output'][0]
            output_data = base64.b64decode(output_b64)
            
            with open(output_path, 'wb') as f:
                f.write(output_data)
            
            print(f"💾 Saved to: {output_path}")
            return output_path
        else:
            print(f"❌ No output in response: {result}")
            return None
    else:
        print(f"❌ API Error {response.status_code}: {response.text}")
        return None

if __name__ == "__main__":
    import sys
    
    garment = "test_product.jpg"
    model = sys.argv[1] if len(sys.argv) > 1 else "model_photo.jpg"
    output = "test_output.jpg"
    
    result = generate_tryon(garment, model, output)
    
    if result:
        print("\n✅ Success! Check test_output.jpg")
    else:
        print("\n❌ Generation failed")
