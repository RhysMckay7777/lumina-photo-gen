#!/usr/bin/env python3
"""
Strategic approach to finding ACTUAL full-body model photos
Focus on fashion lookbooks, athletic wear, catalog photos
"""
import requests
from pathlib import Path
import time

def download_curated_fullbody_photos():
    """
    Download curated list of known full-body model photos
    These are specifically selected to meet Fashn.ai requirements
    """
    
    model_dir = Path("fullbody_models")
    model_dir.mkdir(exist_ok=True)
    
    # Curated list of ACTUAL full-body fashion/catalog photos
    # Selected from Unsplash collections known for full-body shots
    photos = [
        # Fashion lookbook style (full body)
        ("https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600&h=900&fit=crop", "fullbody_fashion_01"),
        ("https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&h=900&fit=crop", "fullbody_fashion_02"),
        ("https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600&h=900&fit=crop", "fullbody_fashion_03"),
        
        # E-commerce catalog style
        ("https://images.unsplash.com/photo-1483985988355-763728e1935b?w=600&h=900&fit=crop", "fullbody_catalog_01"),
        ("https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&h=900&fit=crop", "fullbody_catalog_02"),
        
        # Fitness/athletic (definitely full body)
        ("https://images.unsplash.com/photo-1518459031867-a89b944bffe4?w=600&h=900&fit=crop", "fullbody_athletic_01"),
        ("https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&h=900&fit=crop", "fullbody_athletic_02"),
        
        # Professional standing poses
        ("https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=600&h=900&fit=crop", "fullbody_professional_01"),
        ("https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=600&h=900&fit=crop", "fullbody_professional_02"),
        
        # Additional variations
        ("https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=600&h=900&fit=crop", "fullbody_fashion_04"),
        ("https://images.unsplash.com/photo-1445205170230-053b83016050?w=600&h=900&fit=crop", "fullbody_fashion_05"),
        ("https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&h=900&fit=crop", "fullbody_fashion_06"),
        
        # Mature women full body (closer to target demographic)
        ("https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=600&h=900&fit=crop", "mature_fullbody_01"),
        ("https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=600&h=900&fit=crop", "mature_fullbody_02"),
        ("https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=600&h=900&fit=crop", "mature_fullbody_03"),
    ]
    
    print("📸 Downloading curated full-body model photos...")
    print("   Focus: Fashion lookbooks, athletic wear, catalog photos\n")
    
    downloaded = 0
    
    for i, (url, name) in enumerate(photos, 1):
        try:
            print(f"[{i}/{len(photos)}] {name}...", end=" ", flush=True)
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                filepath = model_dir / f"{name}.jpg"
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print("✅")
                downloaded += 1
            else:
                print(f"❌ {response.status_code}")
        
        except Exception as e:
            print(f"❌ {str(e)[:30]}")
        
        time.sleep(0.5)
    
    print(f"\n✅ Downloaded {downloaded}/{len(photos)} photos to {model_dir}/")
    
    return downloaded


def download_pexels_fullbody():
    """
    Alternative: Try Pexels with specific full-body queries
    """
    # Pexels free API (if available)
    queries = [
        "woman full body white background",
        "fashion model full length",
        "woman standing full body studio",
        "athletic woman full body",
        "mature woman full length portrait"
    ]
    
    print("\n🔍 Searching Pexels for full-body photos...")
    print("   (Requires Pexels API key - skipping for now)\n")
    
    # Would implement Pexels API here
    return 0


if __name__ == "__main__":
    downloaded = download_curated_fullbody_photos()
    
    if downloaded > 0:
        print(f"\n🎯 Next: Test these with Fashn.ai")
        print(f"   python test_fullbody_models.py")
    else:
        print(f"\n😞 No photos downloaded")
        print(f"   May need to try different approach")
