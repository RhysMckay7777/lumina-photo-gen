#!/usr/bin/env python3
"""
Bulk assign Kiwi Size Charts to Shopify products
If Kiwi doesn't support bulk assignment via CSV
"""

import csv
import requests
import json
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bulk_assign_size_charts(
    shopify_url: str,
    api_key: str,
    api_password: str,
    assignments_csv: str,
    size_chart_id: str = None
):
    """
    Bulk assign size chart to products
    
    CSV format:
    Product ID, Size Chart Name
    123456789, Fleece Sizing
    987654321, T-Shirt Sizing
    """
    
    # Shopify API setup
    api_base = f"{shopify_url.rstrip('/')}/admin/api/2024-01"
    auth = (api_key, api_password)
    
    # Read assignments
    assignments = []
    with open(assignments_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            assignments.append({
                'product_id': row['Product ID'],
                'size_chart': row.get('Size Chart Name', size_chart_id)
            })
    
    logger.info(f"📦 Assigning size charts to {len(assignments)} products")
    
    # For each product, update metafields
    # Kiwi likely uses metafields to store size chart assignments
    
    for assignment in assignments:
        product_id = assignment['product_id']
        chart_name = assignment['size_chart']
        
        try:
            # Update product metafield
            # Note: Exact metafield key depends on Kiwi's implementation
            metafield_data = {
                "metafield": {
                    "namespace": "kiwi",
                    "key": "size_chart",
                    "value": chart_name,
                    "type": "single_line_text_field"
                }
            }
            
            response = requests.post(
                f"{api_base}/products/{product_id}/metafields.json",
                auth=auth,
                json=metafield_data
            )
            
            if response.status_code == 201:
                logger.info(f"✅ Assigned '{chart_name}' to product {product_id}")
            else:
                logger.error(f"❌ Failed for product {product_id}: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Error for product {product_id}: {e}")
    
    logger.info("✅ Bulk assignment complete!")


def generate_assignment_csv_template():
    """Generate a template CSV for bulk assignment"""
    
    template = """Product ID,Size Chart Name
8765432109876,Fleece Sizing
1234567890123,T-Shirt Sizing
9876543210987,Dress Sizing
"""
    
    with open('kiwi_assignments_template.csv', 'w') as f:
        f.write(template)
    
    print("✅ Created template: kiwi_assignments_template.csv")
    print("\nFill in your product IDs and size chart names, then run:")
    print("python kiwi_bulk_assign.py --csv your_assignments.csv")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Bulk assign Kiwi size charts")
    parser.add_argument("--shopify-url", help="Shopify store URL")
    parser.add_argument("--api-key", help="Shopify API key")
    parser.add_argument("--api-password", help="Shopify API password")
    parser.add_argument("--csv", help="CSV file with assignments")
    parser.add_argument("--template", action="store_true", help="Generate CSV template")
    
    args = parser.parse_args()
    
    if args.template:
        generate_assignment_csv_template()
    elif args.csv:
        bulk_assign_size_charts(
            shopify_url=args.shopify_url,
            api_key=args.api_key,
            api_password=args.api_password,
            assignments_csv=args.csv
        )
    else:
        parser.print_help()
