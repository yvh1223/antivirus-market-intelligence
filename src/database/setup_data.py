#!/usr/bin/env python3
"""
Initial data setup script for Consumer Security Analysis V3
Populates database with platforms, products, and their mappings
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Any

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import DatabaseManager, get_db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSetup:
    """Handles initial data population"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
    def setup_platforms(self) -> Dict[str, int]:
        """Set up initial platforms and return name->id mapping"""
        platforms = [
            {
                'name': 'apple_store',
                'display_name': 'Apple App Store',
                'base_url': 'https://apps.apple.com',
                'platform_type': 'app_store',
                'scraping_method': 'api',
                'rate_limit_per_hour': 500
            },
            {
                'name': 'google_play',
                'display_name': 'Google Play Store',
                'base_url': 'https://play.google.com',
                'platform_type': 'app_store',
                'scraping_method': 'api',
                'rate_limit_per_hour': 1000
            },
            {
                'name': 'amazon',
                'display_name': 'Amazon',
                'base_url': 'https://amazon.com',
                'platform_type': 'ecommerce',
                'scraping_method': 'web',
                'rate_limit_per_hour': 200
            },
            {
                'name': 'trustpilot',
                'display_name': 'Trustpilot',
                'base_url': 'https://trustpilot.com',
                'platform_type': 'review_site',
                'scraping_method': 'web',
                'rate_limit_per_hour': 300
            },
            {
                'name': 'pcworld',
                'display_name': 'PCWorld',
                'base_url': 'https://pcworld.com',
                'platform_type': 'review_site',
                'scraping_method': 'web',
                'rate_limit_per_hour': 100
            },
            {
                'name': 'techradar',
                'display_name': 'TechRadar',
                'base_url': 'https://techradar.com',
                'platform_type': 'review_site',
                'scraping_method': 'web',
                'rate_limit_per_hour': 150
            },
            {
                'name': 'cnet',
                'display_name': 'CNET',
                'base_url': 'https://cnet.com',
                'platform_type': 'review_site',
                'scraping_method': 'web',
                'rate_limit_per_hour': 100
            },
            {
                'name': 'best_buy',
                'display_name': 'Best Buy',
                'base_url': 'https://bestbuy.com',
                'platform_type': 'ecommerce',
                'scraping_method': 'web',
                'rate_limit_per_hour': 200
            },
            {
                'name': 'reddit',
                'display_name': 'Reddit',
                'base_url': 'https://reddit.com',
                'platform_type': 'forum',
                'scraping_method': 'api',
                'rate_limit_per_hour': 600
            }
        ]
        
        platform_map = {}
        
        for platform in platforms:
            try:
                # Check if platform already exists
                existing = self.db_manager.get_platforms()
                existing_platform = next((p for p in existing if p['name'] == platform['name']), None)
                
                if existing_platform:
                    platform_map[platform['name']] = existing_platform['id']
                    logger.info(f"✅ Platform {platform['display_name']} already exists (ID: {existing_platform['id']})")
                else:
                    result = self.db_manager.add_platform(platform)
                    platform_map[platform['name']] = result['id']
                    logger.info(f"✅ Added platform: {platform['display_name']} (ID: {result['id']})")
                    
            except Exception as e:
                logger.error(f"❌ Failed to add platform {platform['name']}: {e}")
        
        return platform_map
    
    def setup_products(self) -> Dict[str, int]:
        """Set up initial products and return name->id mapping"""
        products = [
            {
                'name': 'Norton 360',
                'company': 'NorTech (Broadcom)',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Comprehensive security suite with antivirus, VPN, and identity protection',
                'official_website': 'https://norton.com',
                'pricing_model': 'subscription',
                'current_version': '24.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Norton AntiVirus Plus',
                'company': 'NorTech (Broadcom)',
                'category': 'antivirus',
                'subcategory': 'premium',
                'description': 'Essential antivirus protection with real-time threat detection',
                'official_website': 'https://norton.com',
                'pricing_model': 'subscription',
                'current_version': '24.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'McAfee Total Protection',
                'company': 'McAfee',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Complete antivirus and security protection suite',
                'official_website': 'https://mcafee.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'McAfee AntiVirus Plus',
                'company': 'McAfee',
                'category': 'antivirus',
                'subcategory': 'premium',
                'description': 'Essential antivirus protection for PC',
                'official_website': 'https://mcafee.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Bitdefender Total Security',
                'company': 'Bitdefender',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Advanced cybersecurity with multiple layers of protection',
                'official_website': 'https://bitdefender.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Bitdefender Antivirus Plus',
                'company': 'Bitdefender',
                'category': 'antivirus',
                'subcategory': 'premium',
                'description': 'Essential antivirus protection with advanced threat detection',
                'official_website': 'https://bitdefender.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Kaspersky Internet Security',
                'company': 'Kaspersky',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Internet security with advanced protection features',
                'official_website': 'https://kaspersky.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Kaspersky Anti-Virus',
                'company': 'Kaspersky',
                'category': 'antivirus',
                'subcategory': 'premium',
                'description': 'Essential antivirus protection with proven security',
                'official_website': 'https://kaspersky.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'AVG Internet Security',
                'company': 'AVG (Avast)',
                'category': 'security_suite',
                'subcategory': 'freemium',
                'description': 'Complete internet security with advanced features',
                'official_website': 'https://avg.com',
                'pricing_model': 'freemium',
                'current_version': '24.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'AVG AntiVirus FREE',
                'company': 'AVG (Avast)',
                'category': 'antivirus',
                'subcategory': 'free',
                'description': 'Free antivirus protection with essential security features',
                'official_website': 'https://avg.com',
                'pricing_model': 'freemium',
                'current_version': '24.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Avast Premium Security',
                'company': 'Avast',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Premium security suite with advanced protection',
                'official_website': 'https://avast.com',
                'pricing_model': 'freemium',
                'current_version': '24.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Avast Free Antivirus',
                'company': 'Avast',
                'category': 'antivirus',
                'subcategory': 'free',
                'description': 'Free antivirus protection for basic security needs',
                'official_website': 'https://avast.com',
                'pricing_model': 'freemium',
                'current_version': '24.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Windows Defender',
                'company': 'Microsoft',
                'category': 'antivirus',
                'subcategory': 'free',
                'description': 'Built-in Windows security with real-time protection',
                'official_website': 'https://microsoft.com/windows/security',
                'pricing_model': 'free',
                'current_version': '4.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'ESET Internet Security',
                'company': 'ESET',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Multilayered internet security for everyday users',
                'official_website': 'https://eset.com',
                'pricing_model': 'subscription',
                'current_version': '17.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'ESET NOD32 Antivirus',
                'company': 'ESET',
                'category': 'antivirus',
                'subcategory': 'premium',
                'description': 'Fast and light antivirus protection',
                'official_website': 'https://eset.com',
                'pricing_model': 'subscription',
                'current_version': '17.0',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Trend Micro Maximum Security',
                'company': 'Trend Micro',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Complete security suite with advanced threat protection',
                'official_website': 'https://trendmicro.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'F-Secure SAFE',
                'company': 'F-Secure',
                'category': 'security_suite',
                'subcategory': 'premium',
                'description': 'Easy-to-use internet security for all your devices',
                'official_website': 'https://f-secure.com',
                'pricing_model': 'subscription',
                'current_version': '2024',
                'release_date': '2024-01-01'
            },
            {
                'name': 'Malwarebytes Premium',
                'company': 'Malwarebytes',
                'category': 'antimalware',
                'subcategory': 'premium',
                'description': 'Advanced malware detection and removal',
                'official_website': 'https://malwarebytes.com',
                'pricing_model': 'freemium',
                'current_version': '5.0',
                'release_date': '2024-01-01'
            }
        ]
        
        product_map = {}
        
        for product in products:
            try:
                # Check if product already exists
                existing = self.db_manager.get_product_by_name(product['name'], product['company'])
                
                if existing:
                    product_map[f"{product['name']}_{product['company']}"] = existing['id']
                    logger.info(f"✅ Product {product['name']} by {product['company']} already exists (ID: {existing['id']})")
                else:
                    result = self.db_manager.add_product(product)
                    product_map[f"{product['name']}_{product['company']}"] = result['id']
                    logger.info(f"✅ Added product: {product['name']} by {product['company']} (ID: {result['id']})")
                    
            except Exception as e:
                logger.error(f"❌ Failed to add product {product['name']}: {e}")
        
        return product_map
    
    def setup_product_mappings(self, platform_map: Dict[str, int], product_map: Dict[str, int]):
        """Set up product-platform mappings with known app IDs"""
        
        # Known app IDs for various platforms
        mappings = [
            # Norton products
            {
                'product_key': 'Norton 360_NorTech (Broadcom)',
                'platform': 'apple_store',
                'app_id': '724596345',
                'url': 'https://apps.apple.com/us/app/norton-360-mobile-security/id724596345'
            },
            {
                'product_key': 'Norton 360_NorTech (Broadcom)',
                'platform': 'google_play',
                'app_id': 'com.symantec.mobilesecurity',
                'url': 'https://play.google.com/store/apps/details?id=com.symantec.mobilesecurity'
            },
            
            # McAfee products
            {
                'product_key': 'McAfee Total Protection_McAfee',
                'platform': 'apple_store',
                'app_id': '520234411',
                'url': 'https://apps.apple.com/us/app/mcafee-mobile-security/id520234411'
            },
            {
                'product_key': 'McAfee Total Protection_McAfee',
                'platform': 'google_play',
                'app_id': 'com.wsandroid.suite',
                'url': 'https://play.google.com/store/apps/details?id=com.wsandroid.suite'
            },
            
            # Bitdefender products
            {
                'product_key': 'Bitdefender Total Security_Bitdefender',
                'platform': 'apple_store',
                'app_id': '1127716399',
                'url': 'https://apps.apple.com/us/app/bitdefender-mobile-security/id1127716399'
            },
            {
                'product_key': 'Bitdefender Total Security_Bitdefender',
                'platform': 'google_play',
                'app_id': 'com.bitdefender.security',
                'url': 'https://play.google.com/store/apps/details?id=com.bitdefender.security'
            },
            
            # Kaspersky products
            {
                'product_key': 'Kaspersky Internet Security_Kaspersky',
                'platform': 'apple_store',
                'app_id': '1430738996',
                'url': 'https://apps.apple.com/us/app/kaspersky-security-cloud/id1430738996'
            },
            {
                'product_key': 'Kaspersky Internet Security_Kaspersky',
                'platform': 'google_play',
                'app_id': 'com.kms.free',
                'url': 'https://play.google.com/store/apps/details?id=com.kms.free'
            },
            
            # AVG products
            {
                'product_key': 'AVG AntiVirus FREE_AVG (Avast)',
                'platform': 'apple_store',
                'app_id': '519235025',
                'url': 'https://apps.apple.com/us/app/avg-mobile-security/id519235025'
            },
            {
                'product_key': 'AVG AntiVirus FREE_AVG (Avast)',
                'platform': 'google_play',
                'app_id': 'com.antivirus',
                'url': 'https://play.google.com/store/apps/details?id=com.antivirus'
            },
            
            # Avast products
            {
                'product_key': 'Avast Free Antivirus_Avast',
                'platform': 'apple_store',
                'app_id': '793096595',
                'url': 'https://apps.apple.com/us/app/avast-security-privacy/id793096595'
            },
            {
                'product_key': 'Avast Free Antivirus_Avast',
                'platform': 'google_play',
                'app_id': 'com.avast.android.mobilesecurity',
                'url': 'https://play.google.com/store/apps/details?id=com.avast.android.mobilesecurity'
            },
            
            # ESET products
            {
                'product_key': 'ESET Internet Security_ESET',
                'platform': 'apple_store',
                'app_id': '1091665828',
                'url': 'https://apps.apple.com/us/app/eset-mobile-security/id1091665828'
            },
            {
                'product_key': 'ESET Internet Security_ESET',
                'platform': 'google_play',
                'app_id': 'com.eset.ems2.gp',
                'url': 'https://play.google.com/store/apps/details?id=com.eset.ems2.gp'
            },
            
            # Trend Micro products
            {
                'product_key': 'Trend Micro Maximum Security_Trend Micro',
                'platform': 'apple_store',
                'app_id': '1006214921',
                'url': 'https://apps.apple.com/us/app/trend-micro-mobile-security/id1006214921'
            },
            {
                'product_key': 'Trend Micro Maximum Security_Trend Micro',
                'platform': 'google_play',
                'app_id': 'com.trendmicro.tmmms',
                'url': 'https://play.google.com/store/apps/details?id=com.trendmicro.tmmms'
            },
            
            # Malwarebytes products
            {
                'product_key': 'Malwarebytes Premium_Malwarebytes',
                'platform': 'apple_store',
                'app_id': '1327105431',
                'url': 'https://apps.apple.com/us/app/malwarebytes-mobile-security/id1327105431'
            },
            {
                'product_key': 'Malwarebytes Premium_Malwarebytes',
                'platform': 'google_play',
                'app_id': 'org.malwarebytes.antimalware',
                'url': 'https://play.google.com/store/apps/details?id=org.malwarebytes.antimalware'
            }
        ]
        
        # Add Amazon mappings for desktop software
        amazon_mappings = [
            {
                'product_key': 'Norton 360_NorTech (Broadcom)',
                'platform': 'amazon',
                'app_id': 'B08CVHJ4RZ',  # Example ASIN
                'url': 'https://amazon.com/dp/B08CVHJ4RZ'
            },
            {
                'product_key': 'McAfee Total Protection_McAfee',
                'platform': 'amazon',
                'app_id': 'B08CVHJ4R1',
                'url': 'https://amazon.com/dp/B08CVHJ4R1'
            },
            {
                'product_key': 'Bitdefender Total Security_Bitdefender',
                'platform': 'amazon',
                'app_id': 'B08CVHJ4R2',
                'url': 'https://amazon.com/dp/B08CVHJ4R2'
            }
        ]
        
        all_mappings = mappings + amazon_mappings
        
        for mapping in all_mappings:
            try:
                product_id = product_map.get(mapping['product_key'])
                platform_id = platform_map.get(mapping['platform'])
                
                if not product_id:
                    logger.warning(f"⚠️ Product not found: {mapping['product_key']}")
                    continue
                
                if not platform_id:
                    logger.warning(f"⚠️ Platform not found: {mapping['platform']}")
                    continue
                
                # Check if mapping already exists
                existing_mappings = self.db_manager.get_product_mappings(product_id=product_id, platform_id=platform_id)
                
                if existing_mappings:
                    logger.info(f"✅ Mapping already exists for {mapping['product_key']} on {mapping['platform']}")
                    continue
                
                mapping_data = {
                    'product_id': product_id,
                    'platform_id': platform_id,
                    'platform_app_id': mapping['app_id'],
                    'platform_url': mapping['url']
                }
                
                result = self.db_manager.add_product_mapping(mapping_data)
                logger.info(f"✅ Added mapping: {mapping['product_key']} -> {mapping['platform']} ({mapping['app_id']})")
                
            except Exception as e:
                logger.error(f"❌ Failed to add mapping for {mapping['product_key']} on {mapping['platform']}: {e}")
    
    def setup_ai_models(self):
        """Set up AI models configuration"""
        models = [
            {
                'name': 'gpt-4.1-nano',
                'version': '2024-07-18',
                'model_type': 'sentiment',
                'provider': 'openai',
                'model_config': {
                    'temperature': 0.3,
                    'max_tokens': 1500
                },
                'performance_metrics': {
                    'accuracy': 0.92,
                    'processing_time_ms': 800
                }
            },
            {
                'name': 'textblob',
                'version': '0.17.1',
                'model_type': 'sentiment',
                'provider': 'local',
                'model_config': {},
                'performance_metrics': {
                    'accuracy': 0.75,
                    'processing_time_ms': 50
                }
            }
        ]
        
        for model in models:
            try:
                # Check if model exists
                existing = self.db_manager.execute_sql(
                    "SELECT * FROM ai_models WHERE name = %s AND version = %s",
                    (model['name'], model['version'])
                )
                
                if existing:
                    logger.info(f"✅ AI model {model['name']} v{model['version']} already exists")
                else:
                    self.db_manager.supabase.table('ai_models').insert(model).execute()
                    logger.info(f"✅ Added AI model: {model['name']} v{model['version']}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to add AI model {model['name']}: {e}")
    
    def run_full_setup(self):
        """Run complete data setup"""
        logger.info("🚀 Starting full data setup...")
        
        try:
            # Setup platforms
            logger.info("📱 Setting up platforms...")
            platform_map = self.setup_platforms()
            
            # Setup products
            logger.info("🛡️ Setting up products...")
            product_map = self.setup_products()
            
            # Setup mappings
            logger.info("🔗 Setting up product-platform mappings...")
            self.setup_product_mappings(platform_map, product_map)
            
            # Setup AI models
            logger.info("🤖 Setting up AI models...")
            self.setup_ai_models()
            
            logger.info("🎉 Full setup completed successfully!")
            
            # Print summary
            platforms = self.db_manager.get_platforms()
            products = self.db_manager.get_products()
            mappings = self.db_manager.get_product_mappings()
            
            logger.info(f"📊 Setup Summary:")
            logger.info(f"   Platforms: {len(platforms)}")
            logger.info(f"   Products: {len(products)}")
            logger.info(f"   Mappings: {len(mappings)}")
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            raise

def main():
    """Main CLI function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Data Setup for Consumer Security Analysis V3")
    parser.add_argument('--action', choices=['full', 'platforms', 'products', 'mappings', 'ai_models'],
                       default='full', help='Setup action to perform')
    
    args = parser.parse_args()
    
    setup = DataSetup()
    
    try:
        if args.action == 'full':
            setup.run_full_setup()
        elif args.action == 'platforms':
            setup.setup_platforms()
        elif args.action == 'products':
            setup.setup_products()
        elif args.action == 'mappings':
            platform_map = {p['name']: p['id'] for p in setup.db_manager.get_platforms()}
            product_map = {f"{p['name']}_{p['company']}": p['id'] for p in setup.db_manager.get_products()}
            setup.setup_product_mappings(platform_map, product_map)
        elif args.action == 'ai_models':
            setup.setup_ai_models()
            
        logger.info("✅ Setup completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
