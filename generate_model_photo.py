#!/usr/bin/env python3
"""Generate model photos with Gemini 2.5 Flash Image"""
import os
import sys

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

# Install deps quietly
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai", "pillow"], check=True)

from google import genai

client = genai.Client(api_key=api_key)

# Generate with generateContent
prompt = """Generate a professional fashion model photo with these exact specifications:
- Full body shot from head to feet
- Female model in her 30s
- Standing straight, arms relaxed at sides
- Plain white studio background  
- Professional fashion photography lighting
- Model wearing simple neutral clothing (white t-shirt and jeans)
- Front-facing pose
- High quality, sharp focus
- Studio photography style"""

print("Generating model photo...")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=prompt
    )
    
    print(f"Response: {response}")
    
    # Extract images from parts
    if response.candidates and response.candidates[0].content.parts:
        img_count = 0
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                img_count += 1
                output_path = f"/Users/rhysmckay/lumina-photo-gen/model_photos/gemini-model-{img_count:02d}.png"
                # Save image data
                with open(output_path, 'wb') as f:
                    f.write(part.inline_data.data)
                print(f"✅ Saved: {output_path}")
                print(f"MEDIA:{output_path}")
        
        if img_count == 0:
            print("❌ No images found in response parts")
    else:
        print(f"❌ No candidates or parts in response")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
