#!/usr/bin/env python3
"""
Test IDM-VTON via Replicate API with local file upload
"""
import os
import sys
import replicate

REPLICATE_API_TOKEN = os.environ.get("REPLICATE_API_TOKEN")

if not REPLICATE_API_TOKEN:
    print("❌ REPLICATE_API_TOKEN not set!")
    sys.exit(1)

# Set token
os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

def test_vton_simple():
    """
    Simple test using Replicate Python client
    """
    print("🧪 Testing IDM-VTON on Replicate...")
    print()
    
    # Use public URLs that are known to work
    # Woman in white t-shirt
    model_url = "https://replicate.delivery/pbxt/KJRu8JlyDUi9kQdXWi8SYCj0cHfKv05hnAyGLz7s6r51vCIe/model_8.png"
    
    # Garment - dress
    garment_url = "https://replicate.delivery/pbxt/KJRu8JoAWvGxPXTwh6fJQv6lHrp7pnNUFtixD6mZOhIPfvJB/04564_00.jpg"
    
    print(f"Model: {model_url}")
    print(f"Garment: {garment_url}")
    print()
    print("📤 Running prediction...")
    print()
    
    try:
        output = replicate.run(
            "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
            input={
                "human_img": model_url,
                "garm_img": garment_url,
                "garment_des": "dress"
            }
        )
        
        print("✅ Success!")
        print(f"Result URL: {output}")
        print()
        
        # Download result
        import requests
        img_data = requests.get(output).content
        output_path = "/tmp/idm-vton-result.png"
        with open(output_path, 'wb') as f:
            f.write(img_data)
        
        print(f"Saved to: {output_path}")
        print()
        print("=" * 60)
        print("TEST SUCCESSFUL!")
        print("=" * 60)
        print()
        print("Cost: ~$0.023 per image")
        print("Quality: Best-in-class virtual try-on")
        print()
        print("Ready to build full Shopify integration!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("IDM-VTON TEST - Replicate API")
    print("=" * 60)
    print()
    
    # Install replicate client if needed
    try:
        import replicate
    except ImportError:
        print("Installing replicate client...")
        os.system("pip3 install -q replicate")
        import replicate
    
    test_vton_simple()

if __name__ == "__main__":
    main()
