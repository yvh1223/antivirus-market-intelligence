#!/usr/bin/env python3
"""
Enhanced Review Collection System with Supabase Integration
Supports multiple platforms: Apple Store, Google Play, Amazon, and more
"""

import os
import sys
import argparse
import logging
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import pandas as pd
from dataclasses import dataclass

# Third-party imports
import requests
from google_play_scraper import Sort, reviews as gp_reviews
from app_store_web_scraper import AppStoreEntry
from bs4 import BeautifulSoup
import cloudscraper

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import DatabaseManager, get_db_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ReviewData:
    """Standardized review data structure"""
    platform_review_id: str
    user_name: str
    user_id: Optional[str]
    title: Optional[str]
    content: str
    rating: int
    review_date: datetime
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    language_code: Optional[str] = None
    language_name: Optional[str] = None
    helpful_count: int = 0
    total_votes: int = 0
    verified_purchase: Optional[bool] = None
    version_reviewed: Optional[str] = None
    review_source_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database insertion"""
        data = {
            'platform_review_id': self.platform_review_id,
            'user_name': self.user_name,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'rating': self.rating,
            'review_date': self.review_date.isoformat(),
            'country_code': self.country_code,
            'country_name': self.country_name,
            'language_code': self.language_code,
            'language_name': self.language_name,
            'helpful_count': self.helpful_count,
            'total_votes': self.total_votes,
            'verified_purchase': self.verified_purchase,
            'version_reviewed': self.version_reviewed,
            'review_source_url': self.review_source_url,
            'word_count': len(self.content.split()) if self.content else 0,
            'character_count': len(self.content) if self.content else 0
        }
        return {k: v for k, v in data.items() if v is not None}

class BasePlatformScraper:
    """Base class for platform-specific scrapers"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_reviews(self, app_id: str, max_reviews: int, **kwargs) -> List[ReviewData]:
        """Fetch reviews from the platform. Override in subclasses."""
        raise NotImplementedError
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information. Override in subclasses."""
        raise NotImplementedError

class GooglePlayScraper(BasePlatformScraper):
    """Google Play Store review scraper"""
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {'name': 'google_play', 'display_name': 'Google Play Store'}
    
    def fetch_reviews(self, app_id: str, max_reviews: int, country: str = 'us', 
                     language: str = 'en', **kwargs) -> List[ReviewData]:
        """Fetch reviews from Google Play Store"""
        logger.info(f"🔍 Fetching Google Play reviews for {app_id}")
        
        all_reviews = []
        token = None
        
        while len(all_reviews) < max_reviews:
            try:
                batch_size = min(2000, max_reviews - len(all_reviews))
                
                result, token = gp_reviews(
                    app_id,
                    lang=language,
                    country=country,
                    sort=Sort.NEWEST,
                    count=batch_size,
                    continuation_token=token
                )
                
                if not result:
                    logger.info("✅ No more Google Play reviews available")
                    break
                
                # Convert to standardized format
                for review in result:
                    review_data = ReviewData(
                        platform_review_id=review['reviewId'],
                        user_name=review.get('userName', 'Anonymous'),
                        user_id=review.get('userImage'),  # Use image URL as user ID
                        title=None,  # Google Play doesn't have review titles
                        content=review['content'],
                        rating=review['score'],
                        review_date=review['at'],
                        country_code=country.upper(),
                        language_code=language,
                        helpful_count=review.get('thumbsUpCount', 0),
                        version_reviewed=review.get('appVersion')
                    )
                    all_reviews.append(review_data)
                
                logger.info(f"📥 Google Play: {len(all_reviews)}/{max_reviews} reviews collected")
                
                if token is None:
                    break
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error fetching Google Play reviews: {e}")
                break
        
        return all_reviews

class AppleStoreScraper(BasePlatformScraper):
    """Apple App Store review scraper"""
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {'name': 'apple_store', 'display_name': 'Apple App Store'}
    
    def fetch_reviews(self, app_id: str, max_reviews: int, country: str = 'us', **kwargs) -> List[ReviewData]:
        """Fetch reviews from Apple App Store"""
        logger.info(f"🔍 Fetching Apple Store reviews for {app_id}")
        
        try:
            app = AppStoreEntry(app_id=int(app_id), country=country.lower())
            reviews = []
            
            for idx, review in enumerate(app.reviews()):
                if len(reviews) >= max_reviews:
                    break
                
                review_data = ReviewData(
                    platform_review_id=review.id,
                    user_name=review.user_name or 'Anonymous',
                    user_id=None,
                    title=review.title,
                    content=review.content,  # Use .content instead of .review
                    rating=review.rating,
                    review_date=review.date,
                    country_code=country.upper(),
                    version_reviewed=getattr(review, 'version', None)  # Safe attribute access
                )
                reviews.append(review_data)
                
                if idx % 100 == 0:
                    logger.info(f"📥 Apple Store: {len(reviews)}/{max_reviews} reviews collected")
            
            logger.info(f"✅ Apple Store: Collected {len(reviews)} reviews")
            return reviews
            
        except Exception as e:
            logger.error(f"❌ Error fetching Apple Store reviews: {e}")
            return []

class AmazonScraper(BasePlatformScraper):
    """Amazon review scraper"""
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {'name': 'amazon', 'display_name': 'Amazon'}
    
    def fetch_reviews(self, app_id: str, max_reviews: int, site: str = 'com', 
                     max_pages: int = 10, **kwargs) -> List[ReviewData]:
        """Fetch reviews from Amazon"""
        logger.info(f"🔍 Fetching Amazon reviews for {app_id}")
        
        scraper = cloudscraper.create_scraper()
        reviews = []
        
        base_url = f"https://www.amazon.{site}/product-reviews/{app_id}/"
        
        for page in range(1, max_pages + 1):
            if len(reviews) >= max_reviews:
                break
            
            try:
                url = f"{base_url}?pageNumber={page}&sortBy=recent"
                response = scraper.get(url)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                review_elements = soup.find_all('div', {'data-hook': 'review'})
                
                if not review_elements:
                    logger.info("✅ No more Amazon reviews found")
                    break
                
                for review_elem in review_elements:
                    if len(reviews) >= max_reviews:
                        break
                    
                    try:
                        # Extract review data
                        review_id = review_elem.get('id', f"amazon_{page}_{len(reviews)}")
                        
                        # User info
                        user_elem = review_elem.find('span', class_='a-profile-name')
                        user_name = user_elem.text.strip() if user_elem else 'Anonymous'
                        
                        # Rating
                        rating_elem = review_elem.find('i', {'data-hook': 'review-star-rating'})
                        rating_text = rating_elem.text if rating_elem else '1 out of 5 stars'
                        rating = int(rating_text.split()[0]) if rating_text else 1
                        
                        # Title
                        title_elem = review_elem.find('a', {'data-hook': 'review-title'})
                        title = title_elem.text.strip() if title_elem else None
                        
                        # Content
                        content_elem = review_elem.find('span', {'data-hook': 'review-body'})
                        content = content_elem.text.strip() if content_elem else ''
                        
                        # Date
                        date_elem = review_elem.find('span', {'data-hook': 'review-date'})
                        date_text = date_elem.text if date_elem else ''
                        
                        # Parse date (Amazon format: "Reviewed in the United States on March 15, 2024")
                        review_date = datetime.now(timezone.utc)
                        if 'on ' in date_text:
                            try:
                                date_part = date_text.split('on ')[-1]
                                review_date = datetime.strptime(date_part, '%B %d, %Y').replace(tzinfo=timezone.utc)
                            except:
                                pass
                        
                        # Helpful votes
                        helpful_elem = review_elem.find('span', {'data-hook': 'helpful-vote-statement'})
                        helpful_count = 0
                        if helpful_elem:
                            helpful_text = helpful_elem.text
                            helpful_count = int(''.join(filter(str.isdigit, helpful_text))) if helpful_text else 0
                        
                        # Verified purchase
                        verified_elem = review_elem.find('span', {'data-hook': 'avp-badge'})
                        verified_purchase = verified_elem is not None
                        
                        review_data = ReviewData(
                            platform_review_id=review_id,
                            user_name=user_name,
                            user_id=None,
                            title=title,
                            content=content,
                            rating=rating,
                            review_date=review_date,
                            helpful_count=helpful_count,
                            verified_purchase=verified_purchase,
                            review_source_url=url
                        )
                        
                        reviews.append(review_data)
                        
                    except Exception as e:
                        logger.warning(f"⚠️ Error parsing Amazon review: {e}")
                        continue
                
                logger.info(f"📥 Amazon: Page {page}, {len(reviews)}/{max_reviews} reviews collected")
                time.sleep(2)  # Rate limiting for Amazon
                
            except Exception as e:
                logger.error(f"❌ Error fetching Amazon page {page}: {e}")
                break
        
        logger.info(f"✅ Amazon: Collected {len(reviews)} reviews")
        return reviews

class ReviewCollectionManager:
    """Manages the entire review collection process"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.scrapers = {
            'google': GooglePlayScraper(self.db_manager),
            'apple': AppleStoreScraper(self.db_manager),
            'amazon': AmazonScraper(self.db_manager)
        }
    
    def _get_platform_id(self, platform_name: str) -> int:
        """Get platform ID from database"""
        platforms = self.db_manager.get_platforms()
        platform_map = {
            'google': 'google_play',
            'apple': 'apple_store', 
            'amazon': 'amazon'
        }
        
        platform_db_name = platform_map.get(platform_name, platform_name)
        
        for platform in platforms:
            if platform['name'] == platform_db_name:
                return platform['id']
        
        raise ValueError(f"Platform {platform_name} not found in database")
    
    def collect_reviews(self, platform: str, app_id: str, product_id: int, 
                       max_reviews: int = 1000, **kwargs) -> Dict[str, Any]:
        """Collect reviews for a specific product from a platform"""
        
        if platform not in self.scrapers:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Get platform ID
        platform_id = self._get_platform_id(platform)
        
        # Create collection job
        job_data = {
            'product_id': product_id,
            'platform_id': platform_id,
            'job_type': 'full_collection',
            'parameters': {
                'app_id': app_id,
                'max_reviews': max_reviews,
                **kwargs
            },
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        job = self.db_manager.create_collection_job(job_data)
        job_id = job['id']
        
        try:
            logger.info(f"🚀 Starting collection job {job_id} for {platform}/{app_id}")
            
            # Fetch reviews using the appropriate scraper
            scraper = self.scrapers[platform]
            reviews = scraper.fetch_reviews(app_id, max_reviews, **kwargs)
            
            if not reviews:
                logger.warning(f"⚠️ No reviews collected for {platform}/{app_id}")
                self.db_manager.update_collection_job(job_id, {
                    'status': 'completed',
                    'total_reviews_found': 0,
                    'reviews_collected': 0,
                    'completed_at': datetime.now(timezone.utc).isoformat()
                })
                return {'job_id': job_id, 'reviews_collected': 0}
            
            # Convert reviews to database format
            review_dicts = []
            for review in reviews:
                review_dict = review.to_dict()
                review_dict['product_id'] = product_id
                review_dict['platform_id'] = platform_id
                review_dicts.append(review_dict)
            
            # Insert reviews into database
            inserted_count = self.db_manager.insert_reviews(review_dicts)
            
            # Update job status
            self.db_manager.update_collection_job(job_id, {
                'status': 'completed',
                'total_reviews_found': len(reviews),
                'reviews_collected': inserted_count,
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            
            logger.info(f"✅ Job {job_id} completed: {inserted_count} reviews inserted")
            
            return {
                'job_id': job_id,
                'reviews_collected': inserted_count,
                'total_found': len(reviews),
                'platform': platform,
                'app_id': app_id
            }
            
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
            self.db_manager.update_collection_job(job_id, {
                'status': 'failed',
                'error_message': str(e),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            raise
    
    def collect_for_product_mapping(self, mapping_id: int, max_reviews: int = 1000, **kwargs):
        """Collect reviews using a product-platform mapping"""
        mappings = self.db_manager.get_product_mappings()
        mapping = next((m for m in mappings if m['id'] == mapping_id), None)
        
        if not mapping:
            raise ValueError(f"Mapping {mapping_id} not found")
        
        platform_name = mapping['platform_name']
        app_id = mapping['platform_app_id']
        product_id = mapping['product_id']
        
        # Map platform names to scraper keys
        platform_map = {
            'google_play': 'google',
            'apple_store': 'apple',
            'amazon': 'amazon'
        }
        
        scraper_key = platform_map.get(platform_name)
        if not scraper_key:
            raise ValueError(f"No scraper available for platform {platform_name}")
        
        return self.collect_reviews(scraper_key, app_id, product_id, max_reviews, **kwargs)

def main():
    """Command line interface for review collection"""
    parser = argparse.ArgumentParser(description="Enhanced Review Collection System")
    
    # Platform and app identification
    parser.add_argument('--platform', required=True, choices=['google', 'apple', 'amazon'],
                       help='Platform to collect reviews from')
    parser.add_argument('--app_id', required=True, help='App/Product ID on the platform')
    
    # Product identification (required for database integration)
    parser.add_argument('--product_name', help='Product name (e.g., "Norton 360")')
    parser.add_argument('--company', help='Company name (e.g., "NorTech")')
    parser.add_argument('--product_id', type=int, help='Product ID (if known)')
    
    # Collection parameters
    parser.add_argument('--max_reviews', type=int, default=1000, help='Maximum reviews to collect')
    parser.add_argument('--country', default='us', help='Country code for geo-specific reviews')
    parser.add_argument('--language', default='en', help='Language code for reviews')
    
    # Amazon-specific parameters
    parser.add_argument('--site', default='com', help='Amazon site (com, co.uk, etc.)')
    parser.add_argument('--max_pages', type=int, default=10, help='Max pages for Amazon')
    
    # Output options
    parser.add_argument('--output_csv', help='Save reviews to CSV file (optional)')
    parser.add_argument('--job_only', action='store_true', help='Only create job, don\'t run collection')
    
    args = parser.parse_args()
    
    try:
        manager = ReviewCollectionManager()
        
        # Determine product_id
        product_id = args.product_id
        if not product_id:
            if not args.product_name:
                logger.error("❌ Either --product_id or --product_name must be provided")
                return 1
            
            # Try to find product in database
            product = manager.db_manager.get_product_by_name(args.product_name, args.company)
            if product:
                product_id = product['id']
                logger.info(f"✅ Found product: {product['name']} by {product['company']} (ID: {product_id})")
            else:
                logger.error(f"❌ Product '{args.product_name}' not found. Please add it to the database first.")
                return 1
        
        # Prepare collection parameters
        collection_params = {
            'country': args.country,
            'language': args.language
        }
        
        if args.platform == 'amazon':
            collection_params.update({
                'site': args.site,
                'max_pages': args.max_pages
            })
        
        # Run collection
        logger.info(f"🚀 Starting review collection...")
        logger.info(f"   Platform: {args.platform}")
        logger.info(f"   App ID: {args.app_id}")
        logger.info(f"   Product ID: {product_id}")
        logger.info(f"   Max Reviews: {args.max_reviews}")
        
        if args.job_only:
            # TODO: Implement job-only mode
            logger.info("📋 Job-only mode not yet implemented")
            return 1
        
        result = manager.collect_reviews(
            platform=args.platform,
            app_id=args.app_id,
            product_id=product_id,
            max_reviews=args.max_reviews,
            **collection_params
        )
        
        logger.info("🎉 Collection completed successfully!")
        logger.info(f"   Job ID: {result['job_id']}")
        logger.info(f"   Reviews Collected: {result['reviews_collected']}")
        logger.info(f"   Total Found: {result.get('total_found', result['reviews_collected'])}")
        
        # Optional CSV export
        if args.output_csv:
            reviews = manager.db_manager.get_reviews(product_id=product_id, limit=args.max_reviews)
            if reviews:
                df = pd.DataFrame(reviews)
                df.to_csv(args.output_csv, index=False)
                logger.info(f"💾 Reviews exported to: {args.output_csv}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Collection failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
