#!/usr/bin/env python3
"""Batch generate model photos for specific demographic"""
import os
import sys
import subprocess

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai"], check=True)

from google import genai

client = genai.Client(api_key=api_key)

# Generate 5 different mature women models
prompts = [
    "Professional fashion model photo, woman aged 50-55, full body from head to feet, standing straight with arms relaxed at sides, plain white studio background, wearing simple beige cardigan and white top, elegant mature woman, natural gray hair, professional studio lighting, front facing pose, high quality fashion photography",
    
    "Professional fashion model photo, woman aged 55-60, full body from head to feet, standing upright with arms at sides, plain white background, wearing neutral cardigan, sophisticated mature woman with short gray hair, studio fashion photography, front view, professional lighting",
    
    "Professional fashion model photo, woman aged 50-55, complete body shot head to feet, standing pose with arms down, white studio backdrop, wearing simple cardigan, elegant mature woman with shoulder-length gray hair, fashion photography style, frontal pose, studio lighting",
    
    "Professional fashion model photo, woman aged 60-65, full body standing straight, arms at sides, plain white background, wearing cardigan, mature elegant woman with silver hair, professional fashion photography, front facing, high quality studio shot",
    
    "Professional fashion model photo, woman aged 55-60, full body from head to toes, standing upright arms relaxed, white studio background, wearing neutral cardigan, sophisticated mature woman, professional studio lighting, front view, fashion photography"
]

output_dir = "/Users/rhysmckay/lumina-photo-gen/model_photos"
os.makedirs(output_dir, exist_ok=True)

for idx, prompt in enumerate(prompts, 1):
    print(f"\n🎨 Generating model {idx}/5...")
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=prompt
        )
        
        # Extract image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    output_path = f"{output_dir}/mature-woman-{idx:02d}.png"
                    with open(output_path, 'wb') as f:
                        f.write(part.inline_data.data)
                    print(f"✅ Saved: {output_path}")
                    print(f"MEDIA:{output_path}")
                    break
        else:
            print(f"❌ Model {idx} failed - no image in response")
            
    except Exception as e:
        print(f"❌ Model {idx} error: {e}")

print("\n✅ Batch generation complete!")
