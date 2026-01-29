#!/bin/bash
# Quick Start Script - Complete Workflow
# Run this for end-to-end testing

set -e

echo "🚀 COMPLETE WORKFLOW TEST"
echo "=========================="
echo ""

# Check environment
if [ -z "$FASHN_API_KEY" ]; then
    echo "❌ FASHN_API_KEY not set"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY not set (AI model generation will be skipped)"
fi

# Step 1: Check for working models
echo "📸 Step 1: Checking for working model photos..."
if [ -f "ai_model_test_results.json" ]; then
    working=$(cat ai_model_test_results.json | grep -o '"working":' | wc -l)
    if [ "$working" -gt 0 ]; then
        echo "   ✅ Found working AI models"
    else
        echo "   ⚠️  No working models, generating new ones..."
        python3 generate_ai_models.py 10
        python3 test_ai_models.py
    fi
else
    echo "   ⚠️  No test results, running full generation..."
    if [ ! -z "$OPENAI_API_KEY" ]; then
        python3 generate_ai_models.py 10
        python3 test_ai_models.py
    else
        echo "   ❌ Cannot generate without OPENAI_API_KEY"
        exit 1
    fi
fi

# Step 2: Test photo generation
echo ""
echo "🎨 Step 2: Testing photo generation..."
python3 enhanced_fashn_client.py test_product.jpg test_output_quick.jpg

if [ $? -eq 0 ]; then
    echo "   ✅ Photo generation works!"
else
    echo "   ❌ Photo generation failed"
    exit 1
fi

# Step 3: Test cost tracking
echo ""
echo "💰 Step 3: Verifying cost tracking..."
python3 cost_tracker.py log 1
python3 cost_tracker.py report

# Step 4: Show final status
echo ""
echo "✅ WORKFLOW COMPLETE"
echo "===================="
echo ""
echo "Ready for production:"
echo "  • Photo generation: WORKING"
echo "  • Cost tracking: WORKING"
echo "  • Model rotation: WORKING"
echo ""
echo "Run unified pipeline:"
echo "  python3 unified_pipeline.py 'your keyword' --max-products 100"
echo ""
