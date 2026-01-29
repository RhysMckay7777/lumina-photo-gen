#!/usr/bin/env python3
"""Quick Gemini image generation test"""
import os
import sys

# Check API key
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

print(f"API key found: {api_key[:20]}...")
print("Installing google-genai...")

# Install deps
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai", "pillow"], check=True)

print("Importing modules...")
from google import genai
from google.genai import types

print("Creating client...")
client = genai.Client(api_key=api_key)

print("Generating image...")
prompt = "professional female model, full body standing straight, arms at sides, plain white background, fashion photography"

try:
    response = client.models.generate_images(
        model="gemini-2.5-flash-image",
        prompt=prompt
    )
    
    print("Image generated!")
    
    # Save image
    if response.generated_images:
        img = response.generated_images[0].image
        output_path = "/Users/rhysmckay/lumina-photo-gen/model_photos/gemini-test-01.png"
        img._pil_image.save(output_path)
        print(f"✅ Saved: {output_path}")
        print(f"MEDIA:{output_path}")
    else:
        print("❌ No images generated")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
