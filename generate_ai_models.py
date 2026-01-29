#!/usr/bin/env python3
"""
Generate full-body model photos using AI (DALL-E or similar)
Designed specifically for Fashn.ai pose detection requirements
"""
import os
import requests
import base64
from pathlib import Path
import time

def generate_with_dalle(prompt: str, output_path: str, api_key: str) -> bool:
    """Generate image using DALL-E 3"""
    
    try:
        url = "https://api.openai.com/v1/images/generations"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1792",  # Portrait, good for full body
            "quality": "hd"
        }
        
        print(f"   Generating: {prompt[:60]}...")
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            
            # Download image
            img_response = requests.get(image_url, timeout=30)
            
            with open(output_path, 'wb') as f:
                f.write(img_response.content)
            
            print(f"   ✅ Saved: {output_path}")
            return True
        else:
            print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
            return False
    
    except Exception as e:
        print(f"   ❌ Exception: {str(e)[:100]}")
        return False


def generate_model_photos(api_key: str, count: int = 15):
    """Generate multiple full-body model photos optimized for Fashn.ai"""
    
    output_dir = Path("ai_generated_models")
    output_dir.mkdir(exist_ok=True)
    
    # Carefully crafted prompts for Fashn.ai compatibility
    base_prompts = [
        "Professional full-body photograph of a 50-year-old woman standing straight, arms at sides, front view, plain white background, studio lighting, fashion catalog style, photorealistic, high quality, full body visible from head to feet",
        
        "Full-body studio portrait of an elegant 55-year-old woman, standing upright, hands relaxed at sides, facing camera directly, white seamless background, professional fashion photography, clear lighting, entire body visible including feet",
        
        "Professional e-commerce photo of a mature woman age 50, full body shot from head to toes, standing pose, arms naturally at sides, neutral expression, white studio background, catalog photography style, photorealistic",
        
        "Full-length professional photograph of a 52-year-old woman, standing position, complete body visible from head to feet, white background, studio lighting, fashion model pose, arms at sides, front-facing",
        
        "High-quality full-body portrait of an elegant mature woman aged 55-60, standing straight, full body visible including feet and head, white seamless background, professional studio photography, catalog style",
    ]
    
    # Variations: different ages, poses, styles
    variations = [
        ("45-year-old", "slightly turned 3/4 view"),
        ("48-year-old", "one hand on hip, professional pose"),
        ("52-year-old", "arms crossed, confident stance"),
        ("58-year-old", "walking pose, full body"),
        ("50-year-old", "fashion pose, arms relaxed"),
        ("55-year-old", "business casual, standing straight"),
        ("60-year-old", "elegant pose, arms at sides"),
    ]
    
    print(f"🎨 Generating {count} AI model photos...\n")
    
    generated = 0
    
    # Generate from base prompts
    for i, prompt in enumerate(base_prompts[:count], 1):
        if generated >= count:
            break
        
        output_path = output_dir / f"ai_model_{generated+1:02d}.jpg"
        
        success = generate_with_dalle(prompt, str(output_path), api_key)
        
        if success:
            generated += 1
        
        time.sleep(1)  # Rate limit
    
    # Generate variations if needed
    remaining = count - generated
    if remaining > 0:
        for i, (age, pose) in enumerate(variations[:remaining], 1):
            prompt = f"Professional full-body photograph of a {age} woman, {pose}, plain white background, studio lighting, fashion catalog style, photorealistic, complete body visible from head to feet"
            
            output_path = output_dir / f"ai_model_{generated+1:02d}.jpg"
            
            success = generate_with_dalle(prompt, str(output_path), api_key)
            
            if success:
                generated += 1
            
            time.sleep(1)
    
    print(f"\n✅ Generated {generated}/{count} AI model photos")
    print(f"📁 Location: {output_dir}/")
    
    return generated


if __name__ == "__main__":
    import sys
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("\nSet it with:")
        print("export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    
    generated = generate_model_photos(api_key, count)
    
    if generated > 0:
        print(f"\n🎯 Next: Test these with Fashn.ai")
        print(f"   python test_ai_models.py")
