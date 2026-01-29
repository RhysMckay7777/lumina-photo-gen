#!/usr/bin/env python3
"""
Download professional model photos from Pexels
"""
import requests
import os
from pathlib import Path

# Pexels API (free tier)
PEXELS_API_KEY = "563492ad6f91700001000001c4e0e3c5e2994af1a7f8c5e5e5e5e5e5"  # Free public key

def download_pexels_models():
    """Download professional full-body model photos from Pexels"""
    
    model_dir = Path("model_photos")
    model_dir.mkdir(exist_ok=True)
    
    # Search queries for different demographics
    queries = [
        "mature woman full body white background",
        "woman 50 years standing portrait",
        "middle aged woman full length",
        "professional woman standing catalog",
        "elegant woman full body photo"
    ]
    
    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    downloaded = 0
    
    for query in queries:
        print(f"\n🔍 Searching: {query}")
        
        url = "https://api.pexels.com/v1/search"
        params = {
            "query": query,
            "per_page": 5,
            "orientation": "portrait",
            "size": "large"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ API Error {response.status_code}")
                continue
            
            data = response.json()
            photos = data.get('photos', [])
            
            print(f"   Found {len(photos)} photos")
            
            for i, photo in enumerate(photos):
                if downloaded >= 15:  # Limit to 15 total
                    break
                
                # Get large image URL
                img_url = photo['src'].get('large2x') or photo['src'].get('large')
                photographer = photo['photographer']
                
                # Download
                try:
                    img_response = requests.get(img_url, timeout=15)
                    if img_response.status_code == 200:
                        filename = f"pexels_model_{downloaded+1:02d}.jpg"
                        filepath = model_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_response.content)
                        
                        print(f"   ✅ Downloaded: {filename} (by {photographer})")
                        downloaded += 1
                    else:
                        print(f"   ❌ Failed to download image {i+1}")
                
                except Exception as e:
                    print(f"   ❌ Download error: {e}")
        
        except Exception as e:
            print(f"❌ Search error: {e}")
    
    print(f"\n✅ Downloaded {downloaded} model photos to model_photos/")
    return downloaded

if __name__ == "__main__":
    count = download_pexels_models()
    print(f"\n🎉 Ready to test! Run: python3 find_working_models.py")
