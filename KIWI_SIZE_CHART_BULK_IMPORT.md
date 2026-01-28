# Kiwi Size Chart - Bulk Import Guide

Complete guide for bulk importing sizing data into Kiwi Size Chart Shopify app.

---

## Method 1: Kiwi's Built-In CSV Import (Easiest)

### Step 1: Prepare Your CSV

Create a CSV file with your sizing data:

**fleece_sizing.csv:**
```csv
Size,UK Size,Bust (CM),Waist (CM),Hips (CM)
X-Small,4,76,62.5,83.5
X-Small,6,80,65,87.5
Small,8,84,67.5,91.5
Small,10,86.5,71,95
Medium,12,90,74,99
Medium,14,94,79,105.5
Large,16,99,84,110.5
Large,18,104,91.5,117
X-Large,20,109,99,123
X-Large,22,114,103,127
XX-Large,24,123,109,131
XX-Large,26,128,116,137
```

### Step 2: Import into Kiwi

1. Go to **Shopify Admin** → **Apps** → **Kiwi Size Chart**
2. Click **"Create Size Chart"** or edit existing
3. Look for **"Import"** or **"Upload CSV"** button
4. Select your CSV file
5. Map columns:
   - Column 1 → Size
   - Column 2 → UK Size
   - Column 3 → Bust
   - etc.
6. Click **"Import"** or **"Save"**

---

## Method 2: Multiple Size Charts from CSVs

If you have different sizing for different product types:

### Create Separate CSV Files

**tops_sizing.csv:**
```csv
Size,Bust,Waist,Length
S,84-90,67-74,60
M,90-96,74-81,62
L,96-104,81-91,64
```

**bottoms_sizing.csv:**
```csv
Size,Waist,Hips,Inseam
S,67-74,91-99,75
M,74-81,99-107,77
L,81-91,107-117,79
```

**dresses_sizing.csv:**
```csv
Size,Bust,Waist,Hips,Length
S,84-90,67-74,91-99,95
M,90-96,74-81,99-107,97
L,96-104,81-91,107-117,99
```

### Import Each Chart

1. Import **tops_sizing.csv** → Name: "Tops Sizing"
2. Import **bottoms_sizing.csv** → Name: "Bottoms Sizing"
3. Import **dresses_sizing.csv** → Name: "Dresses Sizing"

---

## Method 3: Bulk Assign Charts to Products

### If Kiwi UI doesn't support bulk assignment:

#### Step 1: Get Product IDs

Export your products from Shopify:
- **Shopify Admin** → **Products** → **Export**
- Download CSV with product IDs

#### Step 2: Create Assignment CSV

**product_size_chart_assignments.csv:**
```csv
Product ID,Size Chart Name
8765432109876,Tops Sizing
1234567890123,Tops Sizing
9876543210987,Bottoms Sizing
5432109876543,Dresses Sizing
```

#### Step 3: Run Bulk Assignment Script

```bash
python kiwi_bulk_assign.py \
  --shopify-url https://your-store.myshopify.com \
  --api-key YOUR_API_KEY \
  --api-password YOUR_PASSWORD \
  --csv product_size_chart_assignments.csv
```

---

## Method 4: Automatic Assignment by Collection

Kiwi supports collection-based auto-assignment!

### In Kiwi App:

1. Create size chart
2. Under **"Assignment Rules"** or **"Auto-Apply"**:
   - Select **"Apply to collection"**
   - Choose collection: "Fleeces", "Tops", etc.
3. Save

**All products in that collection automatically get the chart!**

---

## Converting Your Data to CSV

If you have sizing data in other formats:

### From Excel/Google Sheets

1. Open your sizing table
2. **File** → **Download** → **CSV**
3. Upload to Kiwi

### From Website Table (like your screenshot)

```bash
# I can extract it for you
python extract_sizing_table.py \
  --url https://supplier-website.com/size-chart \
  --output sizing_data.csv
```

### From Image

Kiwi supports importing from images!
1. Take screenshot of size chart
2. Upload to Kiwi
3. Kiwi will OCR and convert to table

---

## Best Practices

### 1. Organize by Product Type

Don't use one chart for all products. Create:
- **Tops Chart** (shirts, sweaters, jackets)
- **Bottoms Chart** (pants, skirts, shorts)
- **Dresses Chart** (dresses, jumpsuits)
- **Outerwear Chart** (coats, heavy jackets)

### 2. Include Measurement Guide

In Kiwi, add a "How to Measure" tab:
- Bust: Measure around fullest part
- Waist: Measure around natural waistline
- Hips: Measure around fullest part
- Add diagram/image

### 3. Use Collection-Based Assignment

Set up once, never assign manually again:
- Create Shopify collection: "Women's Tops"
- Assign size chart to collection
- New products added to collection = auto-assigned chart

### 4. Test Before Full Import

1. Import 1 size chart
2. Assign to 1 test product
3. View on live site
4. Verify formatting looks good
5. Then bulk import all charts

---

## Troubleshooting

### CSV Import Fails

**Common issues:**
- Extra commas in data
- Missing headers
- Wrong encoding (use UTF-8)

**Fix:**
1. Open CSV in text editor
2. Remove any extra commas
3. Ensure first row is headers
4. Save as UTF-8 CSV

### Size Chart Doesn't Show on Product Page

**Check:**
1. Chart is assigned to product (check Kiwi app)
2. Kiwi app is enabled
3. Theme is compatible with Kiwi
4. Clear browser cache

### Bulk Assignment Not Working

**Options:**
1. Use Kiwi's collection-based auto-assignment instead
2. Contact Kiwi support for bulk import feature
3. Use script above (check Kiwi's metafield structure first)

---

## Alternative: Keep Your Custom Modal

If you prefer the custom size chart modal I built earlier:

**Pros:**
- Free
- Fully customized
- No monthly app fee

**Cons:**
- Manual updates
- No size recommender
- No analytics

**Decision:**
- Use **Kiwi** if you want size recommender + easy management
- Use **custom modal** if you want full control + no fees

---

## Getting Help

**Kiwi Support:**
- Email: support@kiwisizing.com
- In-app chat
- Documentation: https://kiwisizing.com/help

**Need help with bulk import?**
Let me know and I can:
1. Format your CSV properly
2. Test import process
3. Build automation scripts
4. Extract sizing from supplier websites

---

## Quick Summary

**Easiest Method:**
1. Create CSV with sizing data
2. Import via Kiwi app
3. Use collection-based auto-assignment

**Best for Scale:**
1. Create one chart per product type
2. Assign to Shopify collections
3. All future products auto-assigned

**Cost:**
- Kiwi app: Free plan available, paid plans from $9.99/mo
- Custom solution: $0 (use the modal I built earlier)

---

**Status**: Ready to help with whichever method you choose!
