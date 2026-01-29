#!/usr/bin/env python3
"""
Web UI for Lumina Photo Gen
"""
from flask import Flask, render_template, request, jsonify
import os
from pipeline import PhotoGenerationPipeline

app = Flask(__name__)

# Config (will be set via env vars or config file)
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE", "ibzfrj-xh.myshopify.com")
SHOPIFY_TOKEN = os.environ.get("SHOPIFY_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        pipeline = PhotoGenerationPipeline(SHOPIFY_STORE, SHOPIFY_TOKEN, GEMINI_API_KEY)
    return pipeline

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def api_products():
    """List products"""
    try:
        p = get_pipeline()
        products = p.list_products()
        return jsonify({"success": True, "products": products})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generate AI photos for product"""
    import sys
    import traceback
    
    try:
        data = request.json
        product_id = data.get('product_id')
        demographics = data.get('demographics', ['women-50-60'])
        upload = data.get('upload', True)
        
        print(f"\n=== API Generate Called ===", file=sys.stderr)
        print(f"Product ID: {product_id}", file=sys.stderr)
        print(f"Demographics: {demographics}", file=sys.stderr)
        print(f"Upload: {upload}", file=sys.stderr)
        
        p = get_pipeline()
        results = p.process_product(
            product_id,
            demographics=demographics,
            upload=upload,
            output_dir="/tmp/lumina-photos"
        )
        
        print(f"Results: {results}", file=sys.stderr)
        print(f"=== Generation Complete ===\n", file=sys.stderr)
        
        return jsonify({"success": True, "results": results})
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\n❌ ERROR in api_generate:", file=sys.stderr)
        print(error_trace, file=sys.stderr)
        return jsonify({"success": False, "error": str(e), "trace": error_trace}), 500

@app.route('/api/status')
def api_status():
    """Check system status"""
    return jsonify({
        "success": True,
        "store": SHOPIFY_STORE,
        "gemini_key_set": bool(GEMINI_API_KEY)
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("LUMINA PHOTO GEN - AI Model Photo Generator")
    print("="*60)
    print(f"\nStore: {SHOPIFY_STORE}")
    print(f"Gemini API: {'✅ Set' if GEMINI_API_KEY else '❌ Not set'}")
    print("\nStarting web UI at: http://localhost:5002")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5002, debug=True)
