#!/usr/bin/env python3
"""
Simple script to collect reviews for other products
Uses the working incremental_fetch_reviews.py as base
"""

import os
import sys
import subprocess
import logging

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_products_with_mappings():
    """Get products that have platform mappings"""
    db_manager = get_db_manager()
    
    try:
        # Get all products
        products = db_manager.get_products()
        mappings = db_manager.get_product_mappings()
        
        # Group mappings by product
        product_mappings = {}
        for mapping in mappings:
            pid = mapping['product_id']
            if pid not in product_mappings:
                product_mappings[pid] = []
            product_mappings[pid].append(mapping)
        
        # Show available products
        print("\n" + "="*80)
        print("PRODUCTS AVAILABLE FOR REVIEW COLLECTION")
        print("="*80)
        print(f"{'ID':<3} {'Product Name':<30} {'Company':<20} {'Mappings'}")
        print("-" * 80)
        
        available_products = []
        for product in products:
            if product['id'] in product_mappings:
                mappings_info = []
                for mapping in product_mappings[product['id']]:
                    platform = mapping['platform_name']
                    app_id = mapping['platform_app_id'][:20]
                    mappings_info.append(f"{platform}:{app_id}")
                
                name = product['name'][:29]
                company = product['company'][:19]
                mapping_str = ", ".join(mappings_info)[:30]
                
                print(f"{product['id']:<3} {name:<30} {company:<20} {mapping_str}")
                available_products.append({
                    'product': product,
                    'mappings': product_mappings[product['id']]
                })
        
        print("-" * 80)
        print(f"Total: {len(available_products)} products have platform mappings")
        print("="*80)
        
        return available_products
        
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return []

def collect_for_product(product_id, platform_name='google_play', max_reviews=10000, 
                       incremental=False, start_date=None):
    """Collect reviews for a specific product"""
    
    db_manager = get_db_manager()
    
    # Get product info
    products = db_manager.get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        print(f"❌ Product ID {product_id} not found")
        return False
    
    # Get mappings for this product
    mappings = db_manager.get_product_mappings(product_id=product_id)
    
    if not mappings:
        print(f"❌ No platform mappings found for {product['name']}")
        return False
    
    # Find the right mapping
    mapping = next((m for m in mappings if m['platform_name'] == platform_name), None)
    
    if not mapping:
        print(f"❌ No {platform_name} mapping found for {product['name']}")
        available_platforms = [m['platform_name'] for m in mappings]
        print(f"Available platforms: {', '.join(available_platforms)}")
        return False
    
    # Build command
    script_path = "src/data_collection/incremental_fetch_reviews.py"
    
    # Map platform names
    platform_map = {
        'google_play': 'google',
        'apple_store': 'apple',
        'amazon': 'amazon'
    }
    
    platform_arg = platform_map.get(platform_name, platform_name)
    
    cmd = [
        "python", script_path,
        "--platform", platform_arg,
        "--app_id", mapping['platform_app_id'],
        "--max_reviews", str(max_reviews),
        "--product_name", product['name'],
        "--company", product['company'],
        "--country", "us",
        "--language", "en"
    ]
    
    if incremental:
        cmd.append("--incremental")
    
    if start_date:
        cmd.extend(["--start_date", start_date])
    
    print(f"\n🚀 Collecting reviews for: {product['name']}")
    print(f"📱 Platform: {mapping['display_name']}")
    print(f"🆔 App ID: {mapping['platform_app_id']}")
    print(f"📊 Max Reviews: {max_reviews}")
    
    if incremental:
        print("🔄 Mode: Incremental")
    if start_date:
        print(f"📅 Start Date: {start_date}")
    
    print(f"\n⚙️ Running command: {' '.join(cmd)}")
    print("-" * 50)
    
    # Run the command
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ Collection completed for {product['name']}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Collection failed for {product['name']}: {e}")
        return False

def main():
    print("🔍 SIMPLE REVIEW COLLECTOR")
    print("Uses your working incremental_fetch_reviews.py script")
    
    # Show available products
    products = get_products_with_mappings()
    
    if not products:
        print("❌ No products with platform mappings found")
        return
    
    print("\n📋 QUICK COLLECTION COMMANDS:")
    print("=" * 60)
    
    # Show some example commands for products that have mappings
    for i, item in enumerate(products[:5]):  # Show first 5
        product = item['product']
        mappings = item['mappings']
        
        for mapping in mappings[:1]:  # Show first mapping
            platform = mapping['platform_name']
            platform_short = {'google_play': 'google', 'apple_store': 'apple', 'amazon': 'amazon'}.get(platform, platform)
            
            print(f"\n{i+1}. {product['name']} from {mapping['display_name']}:")
            print(f"   python src/data_collection/incremental_fetch_reviews.py \\")
            print(f"     --platform {platform_short} \\")
            print(f"     --app_id {mapping['platform_app_id']} \\")
            print(f"     --max_reviews 10000 \\")
            print(f"     --product_name \"{product['name']}\" \\")
            print(f"     --company \"{product['company']}\" \\")
            print(f"     --country us --language en")
    
    print("\n" + "=" * 60)
    print("💡 TIP: Add --incremental for auto-detection of start date")
    print("💡 TIP: Add --start_date 2024-09-01 for specific date")
    print("💡 TIP: Add --days_back 30 for last 30 days only")

if __name__ == "__main__":
    main()
