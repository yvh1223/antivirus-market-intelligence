#!/usr/bin/env python3
"""
Multi-Product Review Collection Script
Supports batch collection for multiple products across platforms
"""

import os
import sys
import argparse
import logging
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import DatabaseManager, get_db_manager

# Import the enhanced review collector
from incremental_fetch_reviews import ReviewCollectionManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultiProductCollector:
    """Manages review collection for multiple products"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.review_manager = ReviewCollectionManager()
    
    def get_products_with_platform_info(self) -> List[Dict[str, Any]]:
        """Get all products with their platform mappings and review statistics"""
        
        # Use the working database methods from the incremental script
        products = self.db_manager.get_products()
        mappings = self.db_manager.get_product_mappings()
        
        # Add review counts using simple query
        for product in products:
            try:
                reviews = self.db_manager.get_reviews(product_id=product['id'], limit=1)
                product['existing_reviews'] = len(reviews) if reviews else 0
                product['max_review_date'] = None
                product['min_review_date'] = None
            except:
                product['existing_reviews'] = 0
                product['max_review_date'] = None
                product['min_review_date'] = None
        
        # Organize mappings by product_id
        mappings_by_product = {}
        for mapping in mappings:
            product_id = mapping['product_id']
            if product_id not in mappings_by_product:
                mappings_by_product[product_id] = []
            mappings_by_product[product_id].append({
                'platform_name': mapping['platform_name'],
                'platform_display_name': mapping['display_name'],
                'app_id': mapping['platform_app_id']
            })
        
        # Combine products with their mappings
        for product in products:
            product['platforms'] = mappings_by_product.get(product['id'], [])
            
        return products
    
    def display_products_table(self):
        """Display a formatted table of all products with platform info"""
        products = self.get_products_with_platform_info()
        
        print("\n" + "="*120)
        print("AVAILABLE PRODUCTS FOR REVIEW COLLECTION")
        print("="*120)
        
        header = f"{'ID':<3} {'Product Name':<30} {'Company':<20} {'Category':<15} {'Reviews':<8} {'Latest Review':<12} {'Platforms':<25}"
        print(header)
        print("-" * 120)
        
        for product in products:
            # Format platform info
            if product['platforms']:
                platform_info = []
                for p in product['platforms']:
                    platform_short = {
                        'google_play': 'Google',
                        'apple_store': 'Apple', 
                        'amazon': 'Amazon'
                    }.get(p['platform_name'], p['platform_name'])
                    platform_info.append(f"{platform_short}({p['app_id'][:15]}...)" if len(p['app_id']) > 15 else f"{platform_short}({p['app_id']})")
                platforms_str = ", ".join(platform_info)
            else:
                platforms_str = "No mappings"
            
            # Format latest review date
            latest_date = "None"
            if product['max_review_date']:
                try:
                    date_obj = datetime.fromisoformat(product['max_review_date'].replace('Z', '+00:00'))
                    latest_date = date_obj.strftime('%Y-%m-%d')
                except:
                    latest_date = str(product['max_review_date'])[:10]
            
            # Truncate long names
            name = product['name'][:29] + "..." if len(product['name']) > 29 else product['name']
            company = product['company'][:19] + "..." if len(product['company']) > 19 else product['company']
            
            row = f"{product['id']:<3} {name:<30} {company:<20} {product['category']:<15} {product['existing_reviews']:<8} {latest_date:<12} {platforms_str[:24]}"
            print(row)
        
        print("-" * 120)
        print(f"Total products: {len(products)}")
        print(f"Products with reviews: {len([p for p in products if p['existing_reviews'] > 0])}")
        print(f"Products with platform mappings: {len([p for p in products if p['platforms']])}")
        print("="*120)
    
    def collect_for_product(self, product_id: int, platform_filter: Optional[str] = None, 
                           max_reviews: int = 10000, incremental: bool = False,
                           start_date: Optional[datetime] = None, **kwargs) -> Dict[str, Any]:
        """Collect reviews for a specific product from all its platforms"""
        
        products = self.get_products_with_platform_info()
        product = next((p for p in products if p['id'] == product_id), None)
        
        if not product:
            raise ValueError(f"Product with ID {product_id} not found")
        
        if not product['platforms']:
            logger.warning(f"⚠️ Product '{product['name']}' has no platform mappings")
            return {'product_id': product_id, 'results': []}
        
        logger.info(f"🚀 Starting collection for: {product['name']} by {product['company']}")
        
        results = []
        total_collected = 0
        
        for platform_info in product['platforms']:
            platform_name = platform_info['platform_name']
            app_id = platform_info['app_id']
            
            # Apply platform filter if specified
            if platform_filter and platform_name != platform_filter:
                logger.info(f"⏭️ Skipping {platform_name} (filtered)")
                continue
            
            # Map platform names to scraper keys
            platform_map = {
                'google_play': 'google',
                'apple_store': 'apple',
                'amazon': 'amazon'
            }
            
            scraper_key = platform_map.get(platform_name)
            if not scraper_key:
                logger.warning(f"⚠️ No scraper available for platform {platform_name}")
                continue
            
            try:
                logger.info(f"📱 Collecting from {platform_info['platform_display_name']} (ID: {app_id})")
                
                result = self.review_manager.collect_reviews(
                    platform=scraper_key,
                    app_id=app_id,
                    product_id=product_id,
                    max_reviews=max_reviews,
                    incremental=incremental,
                    start_date=start_date,
                    **kwargs
                )
                
                result['platform_name'] = platform_name
                result['platform_display_name'] = platform_info['platform_display_name']
                results.append(result)
                total_collected += result['reviews_collected']
                
                logger.info(f"✅ {platform_info['platform_display_name']}: {result['reviews_collected']} reviews collected")
                
                # Rate limiting between platforms
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Failed to collect from {platform_name}: {e}")
                results.append({
                    'platform_name': platform_name,
                    'platform_display_name': platform_info['platform_display_name'],
                    'error': str(e),
                    'reviews_collected': 0
                })
        
        logger.info(f"🎉 Total collected for {product['name']}: {total_collected} reviews")
        
        return {
            'product_id': product_id,
            'product_name': product['name'],
            'company': product['company'],
            'total_collected': total_collected,
            'results': results
        }
    
    def collect_for_multiple_products(self, product_ids: List[int], **kwargs) -> Dict[str, Any]:
        """Collect reviews for multiple products"""
        
        logger.info(f"🚀 Starting collection for {len(product_ids)} products")
        
        all_results = []
        total_collected = 0
        
        for i, product_id in enumerate(product_ids, 1):
            logger.info(f"\n📊 Progress: {i}/{len(product_ids)} - Product ID {product_id}")
            
            try:
                result = self.collect_for_product(product_id, **kwargs)
                all_results.append(result)
                total_collected += result['total_collected']
                
                # Rate limiting between products
                if i < len(product_ids):
                    logger.info("⏳ Waiting 5 seconds before next product...")
                    time.sleep(5)
                    
            except Exception as e:
                logger.error(f"❌ Failed to collect for product {product_id}: {e}")
                all_results.append({
                    'product_id': product_id,
                    'error': str(e),
                    'total_collected': 0
                })
        
        logger.info(f"\n🎉 Multi-product collection completed!")
        logger.info(f"📊 Total reviews collected: {total_collected}")
        
        return {
            'total_products': len(product_ids),
            'total_reviews_collected': total_collected,
            'results': all_results
        }
    
    def suggest_collection_targets(self) -> List[Dict[str, Any]]:
        """Suggest products that would benefit from review collection"""
        products = self.get_products_with_platform_info()
        
        suggestions = []
        
        for product in products:
            if not product['platforms']:
                continue  # Skip products without platform mappings
            
            # Calculate priority score
            priority_score = 0
            reasons = []
            
            # No reviews yet = high priority
            if product['existing_reviews'] == 0:
                priority_score += 10
                reasons.append("No reviews yet")
            
            # Old reviews = medium priority for incremental
            elif product['max_review_date']:
                try:
                    latest_date = datetime.fromisoformat(product['max_review_date'].replace('Z', '+00:00'))
                    days_old = (datetime.now(timezone.utc) - latest_date).days
                    
                    if days_old > 90:
                        priority_score += 8
                        reasons.append(f"Latest review {days_old} days old")
                    elif days_old > 30:
                        priority_score += 5
                        reasons.append(f"Latest review {days_old} days old")
                except:
                    pass
            
            # Multiple platforms = bonus
            if len(product['platforms']) > 1:
                priority_score += 2
                reasons.append(f"{len(product['platforms'])} platforms available")
            
            # Popular categories get priority
            if product['category'] in ['security_suite', 'antivirus']:
                priority_score += 3
                reasons.append("High-priority category")
            
            if priority_score > 0:
                suggestions.append({
                    'product': product,
                    'priority_score': priority_score,
                    'reasons': reasons
                })
        
        # Sort by priority score (highest first)
        suggestions.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return suggestions

def main():
    """Command line interface for multi-product review collection"""
    parser = argparse.ArgumentParser(description="Multi-Product Review Collection System")
    
    # Action selection
    parser.add_argument('--action', choices=['list', 'collect', 'suggest', 'batch'], 
                       default='list', help='Action to perform')
    
    # Product selection
    parser.add_argument('--product_id', type=int, help='Single product ID to collect')
    parser.add_argument('--product_ids', type=str, help='Comma-separated product IDs (e.g., "19,21,23")')
    parser.add_argument('--all_empty', action='store_true', help='Collect for all products with 0 reviews')
    parser.add_argument('--all_outdated', type=int, help='Collect for products with reviews older than N days')
    
    # Collection parameters
    parser.add_argument('--platform', choices=['google_play', 'apple_store', 'amazon'],
                       help='Collect from specific platform only')
    parser.add_argument('--max_reviews', type=int, default=10000, help='Maximum reviews per platform')
    parser.add_argument('--incremental', action='store_true', help='Use incremental collection')
    parser.add_argument('--start_date', type=str, help='Start date for collection (YYYY-MM-DD)')
    parser.add_argument('--days_back', type=int, help='Days back from today for start date')
    
    # Platform-specific parameters
    parser.add_argument('--country', default='us', help='Country code for reviews')
    parser.add_argument('--language', default='en', help='Language code for reviews')
    
    # Output options
    parser.add_argument('--output_json', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    try:
        collector = MultiProductCollector()
        
        if args.action == 'list':
            collector.display_products_table()
            return 0
        
        elif args.action == 'suggest':
            suggestions = collector.suggest_collection_targets()
            
            print("\n" + "="*80)
            print("COLLECTION SUGGESTIONS (Highest Priority First)")
            print("="*80)
            
            for i, suggestion in enumerate(suggestions[:10], 1):  # Top 10
                product = suggestion['product']
                print(f"\n{i}. {product['name']} by {product['company']} (ID: {product['id']})")
                print(f"   Priority Score: {suggestion['priority_score']}")
                print(f"   Reasons: {', '.join(suggestion['reasons'])}")
                print(f"   Platforms: {', '.join([p['platform_display_name'] for p in product['platforms']])}")
                print(f"   Current Reviews: {product['existing_reviews']}")
            
            return 0
        
        elif args.action == 'collect':
            if not args.product_id:
                logger.error("❌ --product_id required for collect action")
                return 1
            
            # Handle start date
            start_date = None
            if args.start_date:
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            elif args.days_back:
                start_date = datetime.now(timezone.utc) - timedelta(days=args.days_back)
            
            # Collection parameters
            collection_params = {
                'platform_filter': args.platform,
                'max_reviews': args.max_reviews,
                'incremental': args.incremental,
                'start_date': start_date,
                'country': args.country,
                'language': args.language
            }
            
            result = collector.collect_for_product(args.product_id, **collection_params)
            
            print(f"\n✅ Collection completed for {result['product_name']}")
            print(f"Total reviews collected: {result['total_collected']}")
            
            if args.output_json:
                with open(args.output_json, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"Results saved to: {args.output_json}")
            
            return 0
        
        elif args.action == 'batch':
            # Determine product IDs for batch collection
            product_ids = []
            
            if args.product_ids:
                product_ids = [int(pid.strip()) for pid in args.product_ids.split(',')]
            elif args.all_empty:
                products = collector.get_products_with_platform_info()
                product_ids = [p['id'] for p in products if p['existing_reviews'] == 0 and p['platforms']]
            elif args.all_outdated:
                products = collector.get_products_with_platform_info()
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=args.all_outdated)
                for p in products:
                    if p['max_review_date'] and p['platforms']:
                        try:
                            latest = datetime.fromisoformat(p['max_review_date'].replace('Z', '+00:00'))
                            if latest < cutoff_date:
                                product_ids.append(p['id'])
                        except:
                            product_ids.append(p['id'])  # Include if can't parse date
            else:
                logger.error("❌ For batch action, specify --product_ids, --all_empty, or --all_outdated")
                return 1
            
            if not product_ids:
                logger.info("ℹ️ No products found matching criteria")
                return 0
            
            logger.info(f"📋 Found {len(product_ids)} products for batch collection: {product_ids}")
            
            # Handle start date
            start_date = None
            if args.start_date:
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            elif args.days_back:
                start_date = datetime.now(timezone.utc) - timedelta(days=args.days_back)
            
            # Collection parameters
            collection_params = {
                'platform_filter': args.platform,
                'max_reviews': args.max_reviews,
                'incremental': args.incremental,
                'start_date': start_date,
                'country': args.country,
                'language': args.language
            }
            
            result = collector.collect_for_multiple_products(product_ids, **collection_params)
            
            if args.output_json:
                with open(args.output_json, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                print(f"Results saved to: {args.output_json}")
            
            return 0
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
