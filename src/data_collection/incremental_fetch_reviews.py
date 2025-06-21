#!/usr/bin/env python3
"""
Enhanced Review Collection System with Incremental Loading Support
Supports loading reviews from a specific start date to avoid duplicates
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
    """Base class for platform-specific scrapers with incremental support"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def fetch_reviews(self, app_id: str, max_reviews: int, start_date: Optional[datetime] = None, **kwargs) -> List[ReviewData]:
        """Fetch reviews from the platform. Override in subclasses."""
        raise NotImplementedError
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information. Override in subclasses."""
        raise NotImplementedError
    
    def get_latest_review_date(self, product_id: int, platform_id: int) -> Optional[datetime]:
        """Get the latest review date for incremental loading"""
        try:
            query = """
            SELECT MAX(review_date) as latest_date 
            FROM reviews 
            WHERE product_id = %s AND platform_id = %s
            """
            result = self.db_manager.execute_sql(query, (product_id, platform_id))
            if result and result[0]['latest_date']:
                return datetime.fromisoformat(result[0]['latest_date'].replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Could not get latest review date: {e}")
        return None

class GooglePlayScraper(BasePlatformScraper):
    """Google Play Store review scraper with incremental support"""
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {'name': 'google_play', 'display_name': 'Google Play Store'}
    
    def fetch_reviews(self, app_id: str, max_reviews: int, country: str = 'us', 
                     language: str = 'en', start_date: Optional[datetime] = None, **kwargs) -> List[ReviewData]:
        """Fetch reviews from Google Play Store with optional start date filtering"""
        logger.info(f"🔍 Fetching Google Play reviews for {app_id}")
        if start_date:
            logger.info(f"📅 Incremental mode: Starting from {start_date.strftime('%Y-%m-%d')}")
        
        all_reviews = []
        token = None
        reviews_before_start_date = 0
        
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
                
                # Convert to standardized format and filter by date
                batch_reviews = []
                for review in result:
                    review_date = review['at']
                    
                    # Ensure both dates are timezone-aware for comparison
                    if start_date:
                        # Make sure start_date is timezone-aware
                        compare_start_date = start_date
                        if start_date.tzinfo is None:
                            compare_start_date = start_date.replace(tzinfo=timezone.utc)
                        
                        # Make sure review_date is timezone-aware
                        if hasattr(review_date, 'tzinfo') and review_date.tzinfo is None:
                            review_date = review_date.replace(tzinfo=timezone.utc)
                        
                        # Skip reviews older than start_date
                        if review_date < compare_start_date:
                            reviews_before_start_date += 1
                            # If we're getting too many old reviews, we can break early
                            if reviews_before_start_date > 1000:
                                logger.info(f"📅 Found {reviews_before_start_date} reviews before start date, stopping...")
                                return all_reviews
                        continue
                    
                    review_data = ReviewData(
                        platform_review_id=review['reviewId'],
                        user_name=review.get('userName', 'Anonymous'),
                        user_id=review.get('userImage'),
                        title=None,
                        content=review['content'],
                        rating=review['score'],
                        review_date=review_date,
                        country_code=country.upper(),
                        language_code=language,
                        helpful_count=review.get('thumbsUpCount', 0),
                        version_reviewed=review.get('appVersion')
                    )
                    batch_reviews.append(review_data)
                
                all_reviews.extend(batch_reviews)
                
                logger.info(f"📥 Google Play: {len(all_reviews)}/{max_reviews} reviews collected")
                if reviews_before_start_date > 0:
                    logger.info(f"📅 Skipped {reviews_before_start_date} reviews before start date")
                
                if token is None:
                    break
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"❌ Error fetching Google Play reviews: {e}")
                break
        
        return all_reviews

class AppleStoreScraper(BasePlatformScraper):
    """Apple App Store review scraper with incremental support"""
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {'name': 'apple_store', 'display_name': 'Apple App Store'}
    
    def fetch_reviews(self, app_id: str, max_reviews: int, country: str = 'us', 
                     start_date: Optional[datetime] = None, **kwargs) -> List[ReviewData]:
        """Fetch reviews from Apple App Store with optional start date filtering"""
        logger.info(f"🔍 Fetching Apple Store reviews for {app_id}")
        if start_date:
            logger.info(f"📅 Incremental mode: Starting from {start_date.strftime('%Y-%m-%d')}")
        
        try:
            app = AppStoreEntry(app_id=int(app_id), country=country.lower())
            reviews = []
            reviews_before_start_date = 0
            
            for idx, review in enumerate(app.reviews()):
                if len(reviews) >= max_reviews:
                    break
                
                # Check date filter
                if start_date:
                    # Ensure both dates are timezone-aware for comparison
                    compare_start_date = start_date
                    if start_date.tzinfo is None:
                        compare_start_date = start_date.replace(tzinfo=timezone.utc)
                    
                    review_date = review.date
                    if hasattr(review_date, 'tzinfo') and review_date.tzinfo is None:
                        review_date = review_date.replace(tzinfo=timezone.utc)
                    
                    if review_date < compare_start_date:
                        reviews_before_start_date += 1
                        if reviews_before_start_date > 1000:
                            logger.info(f"📅 Found {reviews_before_start_date} reviews before start date, stopping...")
                            break
                    continue
                
                review_data = ReviewData(
                    platform_review_id=review.id,
                    user_name=review.user_name or 'Anonymous',
                    user_id=None,
                    title=review.title,
                    content=review.content,
                    rating=review.rating,
                    review_date=review.date,
                    country_code=country.upper(),
                    version_reviewed=getattr(review, 'version', None)
                )
                reviews.append(review_data)
                
                if idx % 100 == 0:
                    logger.info(f"📥 Apple Store: {len(reviews)}/{max_reviews} reviews collected")
                    if reviews_before_start_date > 0:
                        logger.info(f"📅 Skipped {reviews_before_start_date} reviews before start date")
            
            logger.info(f"✅ Apple Store: Collected {len(reviews)} reviews")
            return reviews
            
        except Exception as e:
            logger.error(f"❌ Error fetching Apple Store reviews: {e}")
            return []

class AmazonScraper(BasePlatformScraper):
    """Amazon review scraper with incremental support"""
    
    def get_platform_info(self) -> Dict[str, Any]:
        return {'name': 'amazon', 'display_name': 'Amazon'}
    
    def fetch_reviews(self, app_id: str, max_reviews: int, site: str = 'com', 
                     max_pages: int = 10, start_date: Optional[datetime] = None, **kwargs) -> List[ReviewData]:
        """Fetch reviews from Amazon with optional start date filtering"""
        logger.info(f"🔍 Fetching Amazon reviews for {app_id}")
        if start_date:
            logger.info(f"📅 Incremental mode: Starting from {start_date.strftime('%Y-%m-%d')}")
        
        scraper = cloudscraper.create_scraper()
        reviews = []
        reviews_before_start_date = 0
        
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
                
                page_reviews_before_start = 0
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
                        
                        # Check date filter
                        if start_date:
                            # Ensure both dates are timezone-aware for comparison
                            compare_start_date = start_date
                            if start_date.tzinfo is None:
                                compare_start_date = start_date.replace(tzinfo=timezone.utc)
                            
                            if hasattr(review_date, 'tzinfo') and review_date.tzinfo is None:
                                review_date = review_date.replace(tzinfo=timezone.utc)
                            
                            if review_date < compare_start_date:
                                reviews_before_start_date += 1
                                page_reviews_before_start += 1
                                continue
                        
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
                
                # If this entire page was before start_date, we can stop
                if start_date and page_reviews_before_start == len(review_elements):
                    logger.info(f"📅 Page {page} entirely before start date, stopping...")
                    break
                
                logger.info(f"📥 Amazon: Page {page}, {len(reviews)}/{max_reviews} reviews collected")
                if reviews_before_start_date > 0:
                    logger.info(f"📅 Skipped {reviews_before_start_date} reviews before start date")
                
                time.sleep(2)  # Rate limiting for Amazon
                
            except Exception as e:
                logger.error(f"❌ Error fetching Amazon page {page}: {e}")
                break
        
        logger.info(f"✅ Amazon: Collected {len(reviews)} reviews")
        return reviews

class ReviewCollectionManager:
    """Manages the entire review collection process with incremental support"""
    
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
    
    def get_last_review_date(self, product_id: int, platform: str) -> Optional[datetime]:
        """Get the date of the most recent review for incremental loading"""
        platform_id = self._get_platform_id(platform)
        scraper = self.scrapers[platform]
        return scraper.get_latest_review_date(product_id, platform_id)
    
    def collect_reviews(self, platform: str, app_id: str, product_id: int, 
                       max_reviews: int = 1000, start_date: Optional[datetime] = None,
                       incremental: bool = False, **kwargs) -> Dict[str, Any]:
        """Collect reviews for a specific product from a platform"""
        
        if platform not in self.scrapers:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Get platform ID
        platform_id = self._get_platform_id(platform)
        
        # Handle incremental mode
        if incremental and not start_date:
            start_date = self.get_last_review_date(product_id, platform)
            if start_date:
                # Add a small buffer to avoid missing reviews
                start_date = start_date - timedelta(days=1)
                logger.info(f"📅 Incremental mode: Auto-detected start date as {start_date.strftime('%Y-%m-%d')}")
            else:
                logger.info("📅 No previous reviews found, running full collection")
        
        # Create collection job
        job_data = {
            'product_id': product_id,
            'platform_id': platform_id,
            'job_type': 'incremental_collection' if incremental else 'full_collection',
            'parameters': {
                'app_id': app_id,
                'max_reviews': max_reviews,
                'start_date': start_date.isoformat() if start_date else None,
                **kwargs
            },
            'status': 'running',
            'started_at': datetime.now(timezone.utc).isoformat()
        }
        
        job = self.db_manager.create_collection_job(job_data)
        job_id = job['id']
        
        try:
            logger.info(f"🚀 Starting collection job {job_id} for {platform}/{app_id}")
            if start_date:
                logger.info(f"📅 Start date: {start_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Fetch reviews using the appropriate scraper
            scraper = self.scrapers[platform]
            reviews = scraper.fetch_reviews(app_id, max_reviews, start_date=start_date, **kwargs)
            
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
            
            # Insert reviews into database (this should handle duplicates)
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
                'app_id': app_id,
                'start_date': start_date.isoformat() if start_date else None
            }
            
        except Exception as e:
            logger.error(f"❌ Job {job_id} failed: {e}")
            self.db_manager.update_collection_job(job_id, {
                'status': 'failed',
                'error_message': str(e),
                'completed_at': datetime.now(timezone.utc).isoformat()
            })
            raise

def main():
    """Command line interface for review collection with incremental support"""
    parser = argparse.ArgumentParser(description="Enhanced Review Collection System with Incremental Loading")
    
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
    
    # Incremental loading parameters
    parser.add_argument('--incremental', action='store_true', 
                       help='Enable incremental mode (auto-detect last review date)')
    parser.add_argument('--start_date', type=str, 
                       help='Start date for incremental loading (YYYY-MM-DD format)')
    parser.add_argument('--days_back', type=int, 
                       help='Number of days to go back from today for start date')
    
    # Amazon-specific parameters
    parser.add_argument('--site', default='com', help='Amazon site (com, co.uk, etc.)')
    parser.add_argument('--max_pages', type=int, default=10, help='Max pages for Amazon')
    
    # Output options
    parser.add_argument('--output_csv', help='Save reviews to CSV file (optional)')
    
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
        
        # Handle start date parameter
        start_date = None
        if args.start_date:
            try:
                start_date = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
                logger.info(f"📅 Using provided start date: {start_date.strftime('%Y-%m-%d')}")
            except ValueError:
                logger.error(f"❌ Invalid date format: {args.start_date}. Use YYYY-MM-DD format.")
                return 1
        elif args.days_back:
            start_date = datetime.now(timezone.utc) - timedelta(days=args.days_back)
            logger.info(f"📅 Using start date {args.days_back} days back: {start_date.strftime('%Y-%m-%d')}")
        
        # Prepare collection parameters
        collection_params = {
            'country': args.country,
            'language': args.language,
            'incremental': args.incremental,
            'start_date': start_date
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
        logger.info(f"   Incremental: {args.incremental}")
        if start_date:
            logger.info(f"   Start Date: {start_date.strftime('%Y-%m-%d')}")
        
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
        if result.get('start_date'):
            logger.info(f"   Start Date Used: {result['start_date']}")
        
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
