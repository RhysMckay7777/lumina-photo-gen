#!/usr/bin/env python3
"""
Test script for Lumina Photo Generator

This script helps you verify your setup and test the API.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fashn_generator import FashnGenerator


def test_api_key():
    """Test if API key is configured"""
    print("🔑 Testing API key configuration...")
    
    api_key = os.getenv("FASHN_API_KEY")
    
    if not api_key:
        print("❌ FASHN_API_KEY not found in environment")
        print("\nPlease create a .env file with your API key:")
        print("  FASHN_API_KEY=your_api_key_here")
        print("\nGet your API key from: https://fashn.ai")
        return False
    
    if api_key == "your_api_key_here":
        print("❌ FASHN_API_KEY is still set to the example value")
        print("\nPlease update .env with your real API key from https://fashn.ai")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    return True


def test_directories():
    """Test if required directories exist"""
    print("\n📁 Testing directories...")
    
    directories = ["output", "downloads", "reports"]
    
    for dir_name in directories:
        dir_path = Path(dir_name)
        dir_path.mkdir(exist_ok=True)
        print(f"✅ {dir_name}/ ready")
    
    return True


def test_dependencies():
    """Test if dependencies are installed"""
    print("\n📦 Testing dependencies...")
    
    try:
        import requests
        print("✅ requests")
    except ImportError:
        print("❌ requests - run: pip install requests")
        return False
    
    try:
        import PIL
        print("✅ PIL (Pillow)")
    except ImportError:
        print("❌ PIL - run: pip install Pillow")
        return False
    
    try:
        import aiohttp
        print("✅ aiohttp")
    except ImportError:
        print("❌ aiohttp - run: pip install aiohttp")
        return False
    
    try:
        import tqdm
        print("✅ tqdm")
    except ImportError:
        print("❌ tqdm - run: pip install tqdm")
        return False
    
    return True


def test_generator():
    """Test generator initialization"""
    print("\n🎨 Testing generator initialization...")
    
    api_key = os.getenv("FASHN_API_KEY")
    
    try:
        generator = FashnGenerator(api_key=api_key, output_dir="./output")
        print("✅ Generator initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize generator: {e}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 LUMINA PHOTO GENERATOR - SETUP TEST")
    print("="*60)
    
    # Load environment
    load_dotenv()
    
    # Run tests
    tests = [
        ("API Key", test_api_key),
        ("Directories", test_directories),
        ("Dependencies", test_dependencies),
        ("Generator", test_generator)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name} test failed with exception: {e}")
            results.append(False)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total-passed}/{total}")
    
    if all(results):
        print("\n🎉 All tests passed! You're ready to generate photos!")
        print("\nNext steps:")
        print("1. Test with a single image:")
        print("   python src/fashn_generator.py path/to/product-image.jpg")
        print("\n2. Or batch process from JSON:")
        print("   python src/batch_processor.py examples/sample_products.json")
        print("\n3. Read the README.md for more information")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
