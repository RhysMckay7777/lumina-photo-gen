# Virtual Try-On Research Report
**Date:** 2026-01-29  
**For:** Lumina Photo Gen Tool  
**Use Case:** Thousands of products, women 40-65, realistic quality

---

## Executive Summary

**Top Recommendation:** **CatVTON (open source)** or **Fashn.ai API (paid)**

- **CatVTON** for cost-efficiency and good quality
- **Fashn.ai** if you need highest quality and can budget $75/1000 images

---

## Open Source Options

### 1. **CatVTON** ⭐ TOP PICK (Open Source)
- **Paper:** ICLR 2025 (accepted)
- **GitHub:** 1.4k stars, 160+ forks
- **Quality:** Excellent - matches or beats more complex models
- **Performance:**
  - Lightweight: 899M parameters (vs 2B+ for others)
  - Efficient training: 49M trainable parameters
  - Low VRAM: <8GB for 1024x768 resolution
- **Setup:** Simple, well-documented
- **Cost:** $0 (just compute - GPU required)
- **Best for:** High volume, good quality, cost-conscious

**Pros:**
- Lightweight and fast
- Great quality despite simplicity
- Low hardware requirements
- Active development

**Cons:**
- Requires local GPU or cloud instance
- Self-hosted maintenance

---

### 2. **IDM-VTON**
- **Paper:** ECCV 2024
- **Quality:** Excellent - preserves fine details (text, YOUR_AIRTABLE_TOKEN_HERE)
- **Performance:**
  - More complex than CatVTON
  - Higher hardware requirements
  - Slightly better detail preservation
- **Cost:** $0 (compute only)
- **Best for:** When maximum detail accuracy matters

**Pros:**
- Top-tier detail preservation
- Well-documented
- Active community

**Cons:**
- Heavier compute requirements
- Slower than CatVTON
- More complex setup

---

### 3. **OOTDiffusion**
- **Paper:** AAAI 2025
- **Quality:** Very good
- **Approach:** Integrates clothing info early in generation pipeline
- **Cost:** $0 (compute only)

**Pros:**
- Good quality
- Research-backed

**Cons:**
- Not as efficient as CatVTON
- Less documentation than CatVTON/IDM-VTON

---

### 4. **StableVITON**
- **Paper:** CVPR 2024
- **Quality:** Good
- **Approach:** Latent diffusion model
- **Cost:** $0 (compute only)

**Pros:**
- Decent quality
- Stable Diffusion-based (familiar for devs)

**Cons:**
- Lower quality vs CatVTON/IDM-VTON
- Older approach

---

## Paid API Options

### 1. **Fashn.ai** ⭐ TOP PICK (Paid)
- **Quality:** Excellent - industry-leading
- **Pricing:**
  - Via fal.ai API: **$0.075 per image**
  - **1,000 images = $75**
  - Direct API: $0.10/credit (unclear credits per image)
- **Features:**
  - Product to Model
  - Virtual Try-On
  - Model Swap
  - 4K upscaling
  - AI model creation
- **Setup:** Simple REST API
- **Support:** Good documentation, active support

**Pros:**
- Zero infrastructure management
- Consistent quality
- Fast (seconds per image)
- Scales automatically
- Good for women 40-65 demographic

**Cons:**
- Cost adds up at scale (but still cheapest paid option)
- Ongoing monthly cost

---

### 2. **Botika.io**
- **Quality:** Very good - fashion-specific models
- **Pricing:**
  - **1 credit = 1 photo**
  - Pro plan: $35/month for 30 credits
  - **Effective cost: $1.17 per image**
  - **1,000 images = $1,170**
- **Features:**
  - 50+ AI models
  - Multiple backgrounds
  - 4K resolution
  - White-glove quality control (human review)
  - Flat lay support
- **Turnaround:** ~15 minutes + optional human review

**Pros:**
- Human QA available
- Fashion-specific training
- Good model variety
- Flat lay support

**Cons:**
- **Very expensive** ($1.17 vs $0.075 for Fashn)
- 15.6x more expensive than Fashn.ai
- Not viable for thousands of products

---

### 3. **Revery.ai**
- **Status:** Website down / rebranding
- **Pricing:** Unknown (likely enterprise-only)
- ❌ Not viable for evaluation

---

### 4. **Vue.ai**
- **Status:** Enterprise-only (no public pricing)
- **Focus:** Full e-commerce personalization suite (beyond virtual try-on)
- ❌ Overkill for this use case

---

### 5. **Zalando FEIDEGGER**
- **Status:** Internal tool (not public API)
- ❌ Not accessible

---

## Cost Comparison (1,000 Images)

| Solution | Cost per 1k images | Quality | Setup | Maintenance |
|----------|-------------------|---------|-------|-------------|
| **CatVTON** | **~$10-20** (compute) | ⭐⭐⭐⭐ | Medium | Self-hosted |
| **IDM-VTON** | ~$15-30 (compute) | ⭐⭐⭐⭐⭐ | Medium-Hard | Self-hosted |
| **Fashn.ai** | **$75** | ⭐⭐⭐⭐⭐ | Easy | None |
| **Botika** | $1,170 | ⭐⭐⭐⭐ | Easy | None |

---

## Recommendations by Priority

### **Priority: Cost Efficiency**
→ **CatVTON (open source)**
- $10-20 per 1,000 images (GPU compute only)
- Great quality
- One-time setup, then runs forever

**Setup:**
- Rent GPU instance (RunPod/Vast.ai: $0.30-0.50/hr)
- Or use local GPU if available
- 1,000 images ≈ 5-10 GPU hours = $2-5

---

### **Priority: Quality + Reasonable Cost**
→ **Fashn.ai API**
- $75 per 1,000 images
- Zero infrastructure
- Consistent results
- Fast turnaround
- Best paid option

---

### **Priority: Maximum Quality + Budget OK**
→ **IDM-VTON (open source)**
- Slight quality edge over CatVTON
- Best for detail-critical products
- Similar cost to CatVTON (~$15-30/1k)

---

## Testing Plan

### Phase 1: Quick Feasibility Test
Test with 5-10 sample products:

1. **CatVTON** (open source)
   - Deploy on RunPod ($0.50/hr GPU)
   - Test with flat lay + model photos
   - Measure: quality, speed, VRAM usage

2. **Fashn.ai API** (paid)
   - Sign up for free trial (10 credits)
   - Test same products
   - Measure: quality, API ease of use

3. **IDM-VTON** (open source - if time allows)
   - Same test as CatVTON
   - Compare detail preservation

### Phase 2: Quality Comparison
- Generate side-by-side comparisons
- Evaluate for women 40-65 demographic
- Check fabric detail accuracy
- Test with various product types (cardigans, tops, dresses)

### Phase 3: Cost-Benefit Analysis
- Calculate total cost for 1,000 and 10,000 products
- Factor in setup time, maintenance, reliability
- Make final recommendation

---

## Next Steps

1. ✅ Research complete
2. ⏳ Deploy CatVTON test instance
3. ⏳ Sign up for Fashn.ai trial
4. ⏳ Run test batch (5-10 products)
5. ⏳ Generate comparison report with sample outputs
6. ⏳ Final recommendation with cost breakdown

---

## Timeline Estimate

- **Research:** ✅ Complete (30 min)
- **Setup & Testing:** 2-3 hours
- **Comparison Report:** 30 min
- **Total:** ~3-4 hours

---

## Questions for You

1. Do you have GPU access locally? (Will affect whether we test open source options)
2. What's your monthly product volume? (Affects cost calculations)
3. Would you prefer:
   - a) Lower cost, self-hosted (CatVTON)
   - b) Higher cost, zero maintenance (Fashn.ai)
   - c) Test both and decide?

---

**Status:** Ready to begin testing phase
