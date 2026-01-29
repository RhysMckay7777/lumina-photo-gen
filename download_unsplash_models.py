#!/usr/bin/env python3
"""
Download curated model photos from Unsplash (no API key needed)
"""
import requests
from pathlib import Path
import time

def download_unsplash_models():
    """Download pre-selected professional model photos from Unsplash"""
    
    model_dir = Path("model_photos_new")
    model_dir.mkdir(exist_ok=True)
    
    # Curated list of full-body model photos (mature women, good poses)
    # Format: (url, description)
    photos = [
        ("https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=800", "mature_woman_professional_01"),
        ("https://images.unsplash.com/photo-1580489944761-15a19d654956?w=800", "woman_standing_portrait_01"),
        ("https://images.unsplash.com/photo-1594744803329-e58b31de8bf5?w=800", "elegant_woman_fullbody_01"),
        ("https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800", "professional_woman_02"),
        ("https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800", "mature_professional_03"),
        ("https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800", "standing_woman_04"),
        ("https://images.unsplash.com/photo-1551836022-deb4988cc6c0?w=800", "elegant_professional_05"),
        ("https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800", "model_portrait_06"),
        ("https://images.unsplash.com/photo-1488426862026-3ee34a7d66df?w=800", "woman_professional_07"),
        ("https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=800", "elegant_standing_08"),
        ("https://images.unsplash.com/photo-1543965170-4c01a586684e?w=800", "professional_model_09"),
        ("https://images.unsplash.com/photo-1552058544-f2b08422138a?w=800", "mature_elegant_10"),
    ]
    
    downloaded = 0
    
    print("🖼️  Downloading professional model photos from Unsplash...\n")
    
    for i, (url, description) in enumerate(photos, 1):
        try:
            print(f"[{i}/{len(photos)}] {description}...", end=" ")
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                filename = f"{description}.jpg"
                filepath = model_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅")
                downloaded += 1
            else:
                print(f"❌ Error {response.status_code}")
        
        except Exception as e:
            print(f"❌ {str(e)[:50]}")
        
        time.sleep(0.5)  # Be nice to Unsplash
    
    print(f"\n✅ Downloaded {downloaded}/{len(photos)} photos to model_photos_new/")
    
    if downloaded > 0:
        print("\n🎯 Next: Test these with Fashn.ai")
        print("   python3 test_new_models.py")
    
    return downloaded

if __name__ == "__main__":
    download_unsplash_models()
