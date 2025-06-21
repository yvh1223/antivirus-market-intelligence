"""
Database configuration and connection management for Supabase
"""
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import pandas as pd
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration from environment variables"""
    supabase_url: str
    supabase_key: str
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Load configuration from environment variables"""
        return cls(
            supabase_url=os.getenv('SUPABASE_URL', ''),
            supabase_key=os.getenv('SUPABASE_ANON_KEY', ''),
            db_host=os.getenv('DB_HOST', ''),
            db_port=int(os.getenv('DB_PORT', 5432)),
            db_name=os.getenv('DB_NAME', ''),
            db_user=os.getenv('DB_USER', ''),
            db_password=os.getenv('DB_PASSWORD', '')
        )

class DatabaseManager:
    """Manages database connections and operations for the review analysis system"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
        self._supabase_client: Optional[Client] = None
        self._pg_connection = None
        
    @property
    def supabase(self) -> Client:
        """Get Supabase client (lazy initialization)"""
        if self._supabase_client is None:
            self._supabase_client = create_client(
                self.config.supabase_url,
                self.config.supabase_key
            )
        return self._supabase_client
    
    def get_pg_connection(self):
        """Get direct PostgreSQL connection for complex operations"""
        if self._pg_connection is None or self._pg_connection.closed:
            self._pg_connection = psycopg2.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                database=self.config.db_name,
                user=self.config.db_user,
                password=self.config.db_password,
                cursor_factory=RealDictCursor
            )
        return self._pg_connection
    
    def execute_sql(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Execute SQL query and return results"""
        with self.get_pg_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
    
    def execute_sql_df(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame"""
        with self.get_pg_connection() as conn:
            return pd.read_sql(query, conn, params=params)
    
    # Platform Management
    def get_platforms(self, active_only: bool = True) -> List[Dict]:
        """Get all platforms"""
        result = self.supabase.table('platforms').select('*')
        if active_only:
            result = result.eq('is_active', True)
        return result.order('display_name', desc=False).execute().data
    
    def add_platform(self, platform_data: Dict[str, Any]) -> Dict:
        """Add a new platform"""
        return self.supabase.table('platforms').insert(platform_data).execute().data[0]
    
    # Product Management
    def get_products(self, active_only: bool = True) -> List[Dict]:
        """Get all products"""
        result = self.supabase.table('products').select('*')
        if active_only:
            result = result.eq('is_active', True)
        return result.order('company', desc=False).order('name', desc=False).execute().data
    
    def add_product(self, product_data: Dict[str, Any]) -> Dict:
        """Add a new product"""
        return self.supabase.table('products').insert(product_data).execute().data[0]
    
    def get_product_by_name(self, name: str, company: str = None) -> Optional[Dict]:
        """Get product by name and optionally company"""
        result = self.supabase.table('products').select('*').eq('name', name)
        if company:
            result = result.eq('company', company)
        
        data = result.execute().data
        return data[0] if data else None
    
    # Product-Platform Mappings
    def get_product_mappings(self, product_id: int = None, platform_id: int = None) -> List[Dict]:
        """Get product-platform mappings"""
        query = """
        SELECT ppm.*, p.name as product_name, p.company, pl.name as platform_name, pl.display_name
        FROM product_platform_mappings ppm
        JOIN products p ON ppm.product_id = p.id
        JOIN platforms pl ON ppm.platform_id = pl.id
        WHERE ppm.is_active = true
        """
        params = []
        
        if product_id:
            query += " AND ppm.product_id = %s"
            params.append(product_id)
        
        if platform_id:
            query += " AND ppm.platform_id = %s"
            params.append(platform_id)
        
        query += " ORDER BY p.company, p.name, pl.display_name"
        
        return self.execute_sql(query, tuple(params) if params else None)
    
    def add_product_mapping(self, mapping_data: Dict[str, Any]) -> Dict:
        """Add product-platform mapping"""
        return self.supabase.table('product_platform_mappings').insert(mapping_data).execute().data[0]
    
    # Review Management
    def insert_reviews(self, reviews: List[Dict[str, Any]]) -> int:
        """Insert multiple reviews in batches to avoid timeout"""
        if not reviews:
            return 0
        
        # Insert in batches of 1000 to avoid timeout
        batch_size = 1000
        total_inserted = 0
        
        try:
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                
                # Log progress
                logger.info(f"Inserting batch {i//batch_size + 1}/{(len(reviews) + batch_size - 1)//batch_size} ({len(batch)} reviews)")
                
                result = self.supabase.table('reviews').upsert(
                    batch,
                    on_conflict='platform_id,platform_review_id'
                ).execute()
                
                total_inserted += len(result.data)
                
                # Small delay between batches
                import time
                time.sleep(0.5)
            
            logger.info(f"Successfully inserted {total_inserted} reviews in {(len(reviews) + batch_size - 1)//batch_size} batches")
            return total_inserted
            
        except Exception as e:
            logger.error(f"Error inserting reviews: {e}")
            return total_inserted  # Return what we managed to insert
    
    def get_reviews(self, product_id: int = None, platform_id: int = None, 
                   limit: int = 1000, offset: int = 0) -> List[Dict]:
        """Get reviews with optional filtering"""
        result = self.supabase.table('reviews').select('*')
        
        if product_id:
            result = result.eq('product_id', product_id)
        if platform_id:
            result = result.eq('platform_id', platform_id)
        
        return result.order('review_date', desc=True).limit(limit).offset(offset).execute().data
    
    def get_unprocessed_reviews(self, limit: int = 100) -> List[Dict]:
        """Get reviews that haven't been processed by AI yet"""
        result = self.supabase.table('reviews').select('*').is_('processed_at', 'null')
        return result.limit(limit).execute().data
    
    def mark_review_processed(self, review_id: int, processing_data: Dict[str, Any]):
        """Mark a review as processed with AI analysis results"""
        processing_data['processed_at'] = datetime.utcnow().isoformat()
        return self.supabase.table('reviews').update(processing_data).eq('id', review_id).execute()
    
    # Collection Jobs Management
    def create_collection_job(self, job_data: Dict[str, Any]) -> Dict:
        """Create a new collection job"""
        return self.supabase.table('collection_jobs').insert(job_data).execute().data[0]
    
    def update_collection_job(self, job_id: int, updates: Dict[str, Any]) -> Dict:
        """Update collection job status and progress"""
        updates['updated_at'] = datetime.utcnow().isoformat()
        return self.supabase.table('collection_jobs').update(updates).eq('id', job_id).execute().data[0]
    
    def get_pending_jobs(self) -> List[Dict]:
        """Get pending collection jobs"""
        return self.supabase.table('collection_jobs').select('*').eq('status', 'pending').execute().data
    
    # Analytics and Reporting
    def get_review_stats(self, product_id: int = None, platform_id: int = None, 
                        days: int = 30) -> Dict[str, Any]:
        """Get review statistics for the specified period"""
        query = """
        SELECT 
            COUNT(*) as total_reviews,
            AVG(rating) as avg_rating,
            COUNT(CASE WHEN sentiment_label = 'positive' THEN 1 END) as positive_reviews,
            COUNT(CASE WHEN sentiment_label = 'negative' THEN 1 END) as negative_reviews,
            COUNT(CASE WHEN sentiment_label = 'neutral' THEN 1 END) as neutral_reviews,
            AVG(sentiment_score) as avg_sentiment,
            COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star,
            COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star,
            COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star,
            COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star,
            COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star
        FROM reviews 
        WHERE review_date >= NOW() - INTERVAL '%s days'
        """
        params = [days]
        
        if product_id:
            query += " AND product_id = %s"
            params.append(product_id)
        
        if platform_id:
            query += " AND platform_id = %s"
            params.append(platform_id)
        
        result = self.execute_sql(query, tuple(params))
        return result[0] if result else {}
    
    def get_trending_topics(self, product_id: int = None, days: int = 7, limit: int = 10) -> List[Dict]:
        """Get trending topics from recent reviews"""
        query = """
        SELECT 
            topic,
            COUNT(*) as mention_count,
            AVG(sentiment_score) as avg_sentiment
        FROM (
            SELECT 
                jsonb_array_elements_text(key_topics) as topic,
                sentiment_score
            FROM reviews 
            WHERE review_date >= NOW() - INTERVAL '%s days'
            AND key_topics IS NOT NULL
        """
        params = [days]
        
        if product_id:
            query += " AND product_id = %s"
            params.append(product_id)
        
        query += """
        ) topics
        GROUP BY topic
        ORDER BY mention_count DESC
        LIMIT %s
        """
        params.append(limit)
        
        return self.execute_sql(query, tuple(params))
    
    def close(self):
        """Close database connections"""
        if self._pg_connection and not self._pg_connection.closed:
            self._pg_connection.close()


# Convenience functions for common operations
def get_db_manager() -> DatabaseManager:
    """Get a database manager instance"""
    return DatabaseManager()

def setup_initial_data(db_manager: DatabaseManager):
    """Set up initial platforms and products data"""
    
    # Initial platforms
    platforms = [
        {
            'name': 'apple_store',
            'display_name': 'Apple App Store',
            'base_url': 'https://apps.apple.com',
            'platform_type': 'app_store',
            'scraping_method': 'api'
        },
        {
            'name': 'google_play',
            'display_name': 'Google Play Store',
            'base_url': 'https://play.google.com',
            'platform_type': 'app_store',
            'scraping_method': 'api'
        },
        {
            'name': 'amazon',
            'display_name': 'Amazon',
            'base_url': 'https://amazon.com',
            'platform_type': 'ecommerce',
            'scraping_method': 'web'
        },
        {
            'name': 'trustpilot',
            'display_name': 'Trustpilot',
            'base_url': 'https://trustpilot.com',
            'platform_type': 'review_site',
            'scraping_method': 'web'
        },
        {
            'name': 'pcworld',
            'display_name': 'PCWorld',
            'base_url': 'https://pcworld.com',
            'platform_type': 'review_site',
            'scraping_method': 'web'
        }
    ]
    
    # Initial products (major antivirus software)
    products = [
        {
            'name': 'Norton 360',
            'company': 'NorTech (Broadcom)',
            'category': 'security_suite',
            'subcategory': 'premium',
            'description': 'Comprehensive security suite with antivirus, VPN, and identity protection',
            'official_website': 'https://norton.com',
            'pricing_model': 'subscription'
        },
        {
            'name': 'McAfee Total Protection',
            'company': 'McAfee',
            'category': 'security_suite',
            'subcategory': 'premium',
            'description': 'Complete antivirus and security protection suite',
            'official_website': 'https://mcafee.com',
            'pricing_model': 'subscription'
        },
        {
            'name': 'Bitdefender Total Security',
            'company': 'Bitdefender',
            'category': 'security_suite',
            'subcategory': 'premium',
            'description': 'Advanced cybersecurity with multiple layers of protection',
            'official_website': 'https://bitdefender.com',
            'pricing_model': 'subscription'
        },
        {
            'name': 'Kaspersky Internet Security',
            'company': 'Kaspersky',
            'category': 'security_suite',
            'subcategory': 'premium',
            'description': 'Internet security with advanced protection features',
            'official_website': 'https://kaspersky.com',
            'pricing_model': 'subscription'
        },
        {
            'name': 'AVG AntiVirus',
            'company': 'AVG (Avast)',
            'category': 'antivirus',
            'subcategory': 'freemium',
            'description': 'Essential antivirus protection with free and premium tiers',
            'official_website': 'https://avg.com',
            'pricing_model': 'freemium'
        },
        {
            'name': 'Avast Free Antivirus',
            'company': 'Avast',
            'category': 'antivirus',
            'subcategory': 'free',
            'description': 'Free antivirus protection for basic security needs',
            'official_website': 'https://avast.com',
            'pricing_model': 'freemium'
        }
    ]
    
    try:
        # Insert platforms
        for platform in platforms:
            try:
                db_manager.add_platform(platform)
                print(f"✅ Added platform: {platform['display_name']}")
            except Exception as e:
                print(f"⚠️ Platform {platform['name']} might already exist: {e}")
        
        # Insert products
        for product in products:
            try:
                db_manager.add_product(product)
                print(f"✅ Added product: {product['name']} by {product['company']}")
            except Exception as e:
                print(f"⚠️ Product {product['name']} might already exist: {e}")
                
        print("\n🎉 Initial data setup completed!")
        
    except Exception as e:
        print(f"❌ Error setting up initial data: {e}")

if __name__ == "__main__":
    # Test database connection
    db = get_db_manager()
    
    # Test basic operations
    print("Testing database connection...")
    
    try:
        platforms = db.get_platforms()
        print(f"✅ Found {len(platforms)} platforms")
        
        products = db.get_products()
        print(f"✅ Found {len(products)} products")
        
        print("🎉 Database connection successful!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure to set up your .env file with database credentials")
