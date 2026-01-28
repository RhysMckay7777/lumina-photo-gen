# Airtable Image Library Setup

## Step 1: Create Airtable Base

1. Go to https://airtable.com/signup
2. Create free account
3. Create new base called "**Product Image Library**"

## Step 2: Create Tables

### Table 1: Products

**Fields:**
- `CJ Product ID` (Single line text) - PRIMARY KEY
- `Product Name` (Single line text)
- `Category` (Single select)
- `Original Image URL` (URL)
- `CJ Link` (URL)
- `Has Generated Images` (Checkbox)
- `Generation Date` (Date)
- `Generation Method` (Single select: Fashn.ai, CatVTON)
- `Notes` (Long text)

### Table 2: Generated Images

**Fields:**
- `Image ID` (Autonumber)
- `CJ Product ID` (Link to Products table)
- `Variant Number` (Number: 1, 2, or 3)
- `Image File` (Attachment) - The actual image
- `Cloud URL` (URL) - If uploaded to cloud storage
- `Model Photo Used` (Single line text)
- `Generation Method` (Single select: Fashn.ai, CatVTON)
- `Created Date` (Date)
- `Quality Rating` (Rating: 1-5 stars)

### Table 3: Store Usage

**Fields:**
- `Record ID` (Autonumber)
- `CJ Product ID` (Link to Products table)
- `Store Name` (Single line text)
- `Shopify Store URL` (URL)
- `Shopify Product ID` (Single line text)
- `Upload Date` (Date)
- `Status` (Single select: Pending, Uploaded, Failed)

## Step 3: Get API Credentials

1. Go to https://airtable.com/create/tokens
2. Click "Create new token"
3. Name it: "Product Image Library API"
4. Add scopes:
   - `data.records:read`
   - `data.records:write`
   - `schema.bases:read`
5. Add access to your "Product Image Library" base
6. Click "Create token"
7. **Copy the token** - you'll need to give this to me

## Step 4: Get Base ID

1. Go to your "Product Image Library" base
2. Click "Help" → "API documentation"
3. Your Base ID is in the URL: `https://airtable.com/appXXXXXXXXXXXXXX/api/docs`
4. Copy the `appXXXXXXXXXXXXXX` part

## Step 5: Get Table IDs

In the API documentation:
- Products table ID: Look for "Products" section
- Generated Images table ID: Look for "Generated Images" section  
- Store Usage table ID: Look for "Store Usage" section

## What to Give Me

Once you've set up Airtable, send me:
1. **API Token** (from Step 3)
2. **Base ID** (from Step 4)
3. **Table Names** (should be: Products, Generated Images, Store Usage)

I'll configure the system and we're good to go!

---

## Airtable Plan Needed

**Free Plan**: 
- ✅ Up to 1,200 records per base
- ✅ 2GB attachments
- ✅ Good for ~400 products (3 images each = 1,200 images)

**Plus Plan ($20/month)**:
- ✅ Up to 5,000 records per base  
- ✅ 5GB attachments
- ✅ Good for ~1,600 products

**Pro Plan ($45/month)**:
- ✅ Up to 50,000 records per base
- ✅ 20GB attachments
- ✅ Good for ~16,000 products

**Recommendation**: Start with **Free**, upgrade when needed.
