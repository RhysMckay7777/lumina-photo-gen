#!/usr/bin/env python3
"""
Generate model photos using Gemini with product image as reference
"""
import os
import sys

try:
    from google import genai
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "google-genai"], check=True)
    from google import genai

def generate_with_image_reference(product_image_url, product_title, demographic="women-50-60", output_path=None):
    """
    Use Gemini to generate model photo with product image as visual reference
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    
    client = genai.Client(api_key=api_key)
    
    demographics = {
        "women-50-60": {
            "description": "elegant mature woman aged 55",
            "hair": "silver-gray styled hair",
        }
    }
    
    demo = demographics.get(demographic, demographics["women-50-60"])
    
    # Download product image to pass to Gemini
    import requests
    img_data = requests.get(product_image_url).content
    
    prompt = f"""Professional fashion catalog photography - CRITICAL: Use the provided product image as your exact visual reference for the clothing.

PRODUCT IMAGE PROVIDED: This shows the EXACT item the model should wear. Match:
- The exact color, pattern, and texture shown in the reference image
- All details: buttons, print patterns, fabric texture, collar style
- The way the garment drapes and flows
- Any decorative elements or design features

Generate a photo of:

MODEL: {demo['description']}, {demo['hair']}, warm natural expression, genuine smile

POSE & FRAMING:
- Full body shot with generous space around model
- Relaxed, confident natural stance
- Weight shifted to one leg, slight hip tilt
- Arms hanging naturally at sides
- One foot slightly forward
- Shoulders relaxed, not stiff
- Looking directly at camera warmly
- Natural comfortable body language

COMPOSITION:
- Wide framing - model takes up 60-70% of frame height
- Plenty of breathing room and negative space
- Slightly off-center horizontal positioning
- Airy, spacious professional catalog feel

BACKGROUND:
- Pure white seamless studio backdrop
- Clean, minimal, professional

LIGHTING:
- Professional studio lighting, soft and even
- Natural skin rendering
- Gentle shadows for dimension

CLOTHING - EXACT MATCH TO REFERENCE IMAGE:
- The model MUST wear the exact garment shown in the reference image
- Match every detail: color, pattern, texture, style
- The garment should look identical to the reference
- Same fit and drape as shown in reference image

TECHNICAL:
- Ultra-high resolution (2K)
- Sharp focus, professional quality
- Natural realistic proportions - NO distortion
- Perfect human anatomy
- Photorealistic rendering
- Natural color grading
- Professional fashion catalog quality

CRITICAL: The clothing MUST match the provided reference image exactly. Do not improvise or approximate - use the visual reference."""
    
    print(f"🎨 Generating with image reference...")
    print(f"Product: {product_title}")
    print(f"Reference: {product_image_url}\n")
    
    try:
        # Generate with image as reference
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[
                genai.types.Content(parts=[
                    genai.types.Part.from_bytes(data=img_data, mime_type="image/jpeg"),
                    genai.types.Part.from_text(text=prompt)
                ])
            ]
        )
        
        # Extract generated image
        if response.candidates and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    output_data = part.inline_data.data
                    
                    if output_path:
                        with open(output_path, 'wb') as f:
                            f.write(output_data)
                        print(f"✅ Saved: {output_path}\n")
                        return output_path
                    else:
                        return output_data
        
        print("❌ No image generated")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate model photo with product image reference")
    parser.add_argument("--product-url", required=True, help="Product image URL")
    parser.add_argument("--title", required=True, help="Product title")
    parser.add_argument("--demographic", default="women-50-60", help="Target demographic")
    parser.add_argument("--output", default="/tmp/gemini-ref-result.png", help="Output path")
    
    args = parser.parse_args()
    
    result = generate_with_image_reference(
        args.product_url,
        args.title,
        args.demographic,
        args.output
    )
    
    if result:
        print(f"✅ Success! Result: {result}")
    else:
        print(f"❌ Failed")
        sys.exit(1)