#!/usr/bin/env python3
"""
Platform Mapping Management Script
Helps add and manage product-platform mappings for review collection
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Any

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import DatabaseManager, get_db_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PlatformMappingManager:
    """Manages product-platform mappings"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def add_mapping(self, product_id: int, platform_name: str, app_id: str):
        """Add a new platform mapping for a product"""
        
        # Get platform ID
        platforms = self.db_manager.get_platforms()
        platform = next((p for p in platforms if p['name'] == platform_name), None)
        
        if not platform:
            raise ValueError(f"Platform '{platform_name}' not found")
        
        # Check if product exists
        products = self.db_manager.get_products()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        # Check if mapping already exists
        existing_mappings = self.db_manager.get_product_mappings()
        existing = next((m for m in existing_mappings 
                        if m['product_id'] == product_id and m['platform_id'] == platform['id']), None)
        
        if existing:
            logger.warning(f"⚠️ Mapping already exists for {product['name']} on {platform['display_name']}")
            return existing['id']
        
        # Create new mapping
        mapping_data = {
            'product_id': product_id,
            'platform_id': platform['id'],
            'platform_app_id': app_id,
            'is_active': True
        }
        
        try:
            # Insert mapping (this method may vary based on your database manager)
            query = """
            INSERT INTO product_platform_mappings (product_id, platform_id, platform_app_id, is_active)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """
            result = self.db_manager.execute_sql(query, 
                (product_id, platform['id'], app_id, True))
            
            mapping_id = result[0]['id'] if result else None
            
            logger.info(f"✅ Added mapping: {product['name']} -> {platform['display_name']} ({app_id})")
            return mapping_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add mapping: {e}")
            raise
    
    def list_products_without_mappings(self):
        """List products that don't have platform mappings"""
        
        query = """
        SELECT p.id, p.name, p.company, p.category
        FROM products p
        LEFT JOIN product_platform_mappings pm ON p.id = pm.product_id
        WHERE pm.product_id IS NULL
        ORDER BY p.company, p.name
        """
        
        products = self.db_manager.execute_sql(query)
        
        print("\n" + "="*80)
        print("PRODUCTS WITHOUT PLATFORM MAPPINGS")
        print("="*80)
        
        if not products:
            print("✅ All products have platform mappings!")
            return
        
        header = f"{'ID':<3} {'Product Name':<35} {'Company':<25} {'Category':<15}"
        print(header)
        print("-" * 80)
        
        for product in products:
            name = product['name'][:34] + "..." if len(product['name']) > 34 else product['name']
            company = product['company'][:24] + "..." if len(product['company']) > 24 else product['company']
            
            row = f"{product['id']:<3} {name:<35} {company:<25} {product['category']:<15}"
            print(row)
        
        print("-" * 80)
        print(f"Total: {len(products)} products need platform mappings")
        print("="*80)
    
    def suggest_mappings(self):
        """Suggest common app IDs for popular security products"""
        
        suggestions = {
            # Security Suites - Google Play
            'norton 360': 'com.symantec.mobilesecurity',
            'norton antivirus plus': 'com.symantec.mobilesecurity',
            'mcafee total protection': 'com.mcafee.security',
            'mcafee antivirus plus': 'com.mcafee.security',
            'bitdefender total security': 'com.bitdefender.security',
            'bitdefender antivirus plus': 'com.bitdefender.security',
            'kaspersky internet security': 'com.kms.free',
            'kaspersky anti-virus': 'com.kms.free',
            'avast premium security': 'com.avast.android.mobilesecurity',
            'avast free antivirus': 'com.avast.android.mobilesecurity',
            'avg internet security': 'com.antivirus',
            'avg antivirus free': 'com.antivirus',
            'eset internet security': 'com.eset.ems2.gp',
            'eset nod32 antivirus': 'com.eset.ems2.gp',
            'trend micro maximum security': 'com.trendmicro.tmmspersonal',
            'f-secure safe': 'com.fsecure.ms.dc',
            'malwarebytes premium': 'org.malwarebytes.antimalware'
        }
        
        print("\n" + "="*80)
        print("SUGGESTED GOOGLE PLAY APP IDs FOR SECURITY PRODUCTS")
        print("="*80)
        
        for product_name, app_id in suggestions.items():
            print(f"{product_name:<35} -> {app_id}")
        
        print("="*80)
        print("Note: These are common app IDs. Verify on Google Play Store before adding.")
        print("="*80)

# Common mappings for easy bulk addition
COMMON_MAPPINGS = [
    # Norton products
    {'product_name': 'Norton 360', 'platform': 'google_play', 'app_id': 'com.symantec.mobilesecurity'},
    {'product_name': 'Norton AntiVirus Plus', 'platform': 'google_play', 'app_id': 'com.symantec.mobilesecurity'},
    
    # McAfee products  
    {'product_name': 'McAfee Total Protection', 'platform': 'google_play', 'app_id': 'com.mcafee.security'},
    {'product_name': 'McAfee AntiVirus Plus', 'platform': 'google_play', 'app_id': 'com.mcafee.security'},
    
    # Bitdefender products
    {'product_name': 'Bitdefender Total Security', 'platform': 'google_play', 'app_id': 'com.bitdefender.security'},
    {'product_name': 'Bitdefender Antivirus Plus', 'platform': 'google_play', 'app_id': 'com.bitdefender.security'},
    
    # Kaspersky products
    {'product_name': 'Kaspersky Internet Security', 'platform': 'google_play', 'app_id': 'com.kms.free'},
    {'product_name': 'Kaspersky Anti-Virus', 'platform': 'google_play', 'app_id': 'com.kms.free'},
    
    # Avast products
    {'product_name': 'Avast Premium Security', 'platform': 'google_play', 'app_id': 'com.avast.android.mobilesecurity'},
    {'product_name': 'Avast Free Antivirus', 'platform': 'google_play', 'app_id': 'com.avast.android.mobilesecurity'},
    
    # AVG products
    {'product_name': 'AVG Internet Security', 'platform': 'google_play', 'app_id': 'com.antivirus'},
    {'product_name': 'AVG AntiVirus FREE', 'platform': 'google_play', 'app_id': 'com.antivirus'},
    
    # ESET products
    {'product_name': 'ESET Internet Security', 'platform': 'google_play', 'app_id': 'com.eset.ems2.gp'},
    {'product_name': 'ESET NOD32 Antivirus', 'platform': 'google_play', 'app_id': 'com.eset.ems2.gp'},
    
    # Other products
    {'product_name': 'Trend Micro Maximum Security', 'platform': 'google_play', 'app_id': 'com.trendmicro.tmmspersonal'},
    {'product_name': 'F-Secure SAFE', 'platform': 'google_play', 'app_id': 'com.fsecure.ms.dc'},
    {'product_name': 'Malwarebytes Premium', 'platform': 'google_play', 'app_id': 'org.malwarebytes.antimalware'},
]

def main():
    """Command line interface for platform mapping management"""
    parser = argparse.ArgumentParser(description="Platform Mapping Management System")
    
    # Action selection
    parser.add_argument('--action', choices=['list', 'add', 'suggest', 'bulk_add'], 
                       default='list', help='Action to perform')
    
    # Mapping parameters
    parser.add_argument('--product_id', type=int, help='Product ID')
    parser.add_argument('--platform', choices=['google_play', 'apple_store', 'amazon'],
                       help='Platform name')
    parser.add_argument('--app_id', help='Platform-specific app ID')
    
    args = parser.parse_args()
    
    try:
        manager = PlatformMappingManager()
        
        if args.action == 'list':
            manager.list_products_without_mappings()
            return 0
        
        elif args.action == 'suggest':
            manager.suggest_mappings()
            return 0
        
        elif args.action == 'add':
            if not all([args.product_id, args.platform, args.app_id]):
                logger.error("❌ For add action, --product_id, --platform, and --app_id are required")
                return 1
            
            mapping_id = manager.add_mapping(args.product_id, args.platform, args.app_id)
            print(f"✅ Mapping added with ID: {mapping_id}")
            return 0
        
        elif args.action == 'bulk_add':
            print("🚀 Adding common platform mappings...")
            
            # Get all products to match names
            products = manager.db_manager.get_products()
            
            added_count = 0
            for mapping in COMMON_MAPPINGS:
                # Find product by name
                product = next((p for p in products if p['name'].lower() == mapping['product_name'].lower()), None)
                
                if product:
                    try:
                        manager.add_mapping(product['id'], mapping['platform'], mapping['app_id'])
                        added_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to add mapping for {mapping['product_name']}: {e}")
                else:
                    logger.warning(f"⚠️ Product '{mapping['product_name']}' not found in database")
            
            print(f"\n✅ Bulk add completed: {added_count} mappings added")
            return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
