#!/usr/bin/env python3
"""
Parallel Product-Specific AI Processor
Run different products in separate terminals for faster processing
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

sys.path.append('/Users/yhuchchannavar/Documents/consumer-security-analysis-v3/src')

from supabase import create_client
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class ParallelProductProcessor:
    """Process specific products in parallel terminals"""
    
    def __init__(self, target_company: str = None):
        # Initialize clients
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Processing configuration
        self.batch_size = 500
        self.processing_delay = 1.0
        self.target_company = target_company
        
        # Year priority (same as main processor)
        self.year_priority = [2025, 2024, 2023]
        
        # Stats tracking
        self.stats = {
            'total_processed': 0,
            'total_errors': 0,
            'start_time': datetime.now(),
            'batches_completed': 0,
            'current_year': None,
            'target_company': target_company
        }
        
        # Get product mappings for target company
        self.product_ids = self.get_company_product_ids()
    
    def get_company_product_ids(self) -> List[int]:
        """Get product IDs for the target company"""
        
        try:
            products_result = self.supabase.table('products').select('id, name, company').execute()
            products = products_result.data
            
            company_patterns = {
                'Norton': ['Norton', 'NorTech', 'Broadcom'],
                'Bitdefender': ['Bitdefender'],
                'McAfee': ['McAfee', 'Intel Security'],
                'Kaspersky': ['Kaspersky'],
                'AVG': ['AVG', 'AVG Technologies'],
                'Avast': ['Avast'],
                'ESET': ['ESET'],
                'Trend Micro': ['Trend Micro'],
                'Malwarebytes': ['Malwarebytes']
            }
            
            target_patterns = company_patterns.get(self.target_company, [self.target_company])
            matching_ids = []
            
            for product in products:
                company = product['company']
                for pattern in target_patterns:
                    if pattern.lower() in company.lower():
                        matching_ids.append(product['id'])
                        break
            
            print(f"🎯 TARGET: {self.target_company}")
            print(f"📦 Found {len(matching_ids)} products: {matching_ids}")
            
            return matching_ids
            
        except Exception as e:
            print(f"❌ Error getting product IDs: {e}")
            return []
    
    def get_unprocessed_count(self) -> Dict:
        """Get unprocessed review counts for target company"""
        
        if not self.product_ids:
            return {}
        
        try:
            result = self.supabase.table('reviews').select(
                'review_date'
            ).is_('processed_at', 'null').in_('product_id', self.product_ids).execute()
            
            reviews = result.data
            year_counts = {}
            
            for review in reviews:
                try:
                    review_date = review['review_date']
                    if isinstance(review_date, str):
                        year = int(review_date[:4])
                    else:
                        year = review_date.year
                    
                    year_counts[year] = year_counts.get(year, 0) + 1
                except:
                    continue
            
            print(f"\n📊 UNPROCESSED REVIEWS FOR {self.target_company}:")
            total = 0
            for year in sorted(year_counts.keys(), reverse=True):
                count = year_counts[year]
                total += count
                print(f"   📅 {year}: {count:,} reviews")
            
            print(f"   🎯 TOTAL: {total:,} unprocessed reviews")
            return year_counts
            
        except Exception as e:
            print(f"❌ Error getting unprocessed count: {e}")
            return {}
    
    def get_prioritized_batch(self, batch_size: int = 500) -> List[Dict]:
        """Get next batch for target company by year priority"""
        
        if not self.product_ids:
            return []
        
        try:
            # Try each year in priority order
            for year in self.year_priority:
                result = self.supabase.table('reviews').select(
                    'id, content, rating, product_id, review_date'
                ).is_('processed_at', 'null').in_('product_id', self.product_ids).gte(
                    'review_date', f'{year}-01-01'
                ).lt('review_date', f'{year + 1}-01-01').limit(batch_size).execute()
                
                reviews = result.data
                
                if reviews:
                    print(f"🎯 Found {len(reviews)} {self.target_company} reviews from {year}")
                    self.stats['current_year'] = year
                    return reviews
            
            # If no priority year reviews, get any unprocessed
            result = self.supabase.table('reviews').select(
                'id, content, rating, product_id, review_date'
            ).is_('processed_at', 'null').in_('product_id', self.product_ids).limit(batch_size).execute()
            
            reviews = result.data
            if reviews:
                print(f"🔄 Found {len(reviews)} {self.target_company} reviews (mixed years)")
                self.stats['current_year'] = 'Mixed'
            
            return reviews
            
        except Exception as e:
            print(f"❌ Error fetching batch: {e}")
            return []
    
    def analyze_review_with_openai(self, review_content: str, product_info: str) -> Optional[Dict]:
        """Analyze single review with OpenAI GPT-4o-mini"""
        
        prompt = f"""Analyze this product review for {product_info}:

REVIEW: "{review_content}"

Please provide a JSON response with:
1. sentiment_score: float between -1.0 (very negative) and 1.0 (very positive)
2. sentiment_label: "positive", "negative", or "neutral" 
3. confidence_score: float between 0.0 and 1.0
4. key_topics: list of 2-5 main topics mentioned (e.g., ["performance", "user_interface", "customer_support"])
5. issues_mentioned: list of specific problems mentioned (e.g., ["slow_scanning", "false_positives"])
6. priority_level: "low", "medium", or "high" based on business impact

Return only valid JSON without any markdown formatting."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing customer reviews for cybersecurity products. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            analysis = json.loads(content)
            
            # Add metadata
            analysis['ai_model_used'] = 'gpt-4o-mini'
            analysis['processing_version'] = '3.1'
            analysis['processed_at'] = datetime.utcnow().isoformat()
            
            return analysis
            
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None
    
    def get_product_info(self, product_id: int) -> str:
        """Get product name and company for context"""
        
        try:
            result = self.supabase.table('products').select(
                'name, company'
            ).eq('id', product_id).execute()
            
            if result.data:
                product = result.data[0]
                return f"{product['name']} by {product['company']}"
            return "Unknown Product"
        except:
            return "Unknown Product"
    
    def update_review_with_analysis(self, review_id: int, analysis: Dict) -> bool:
        """Update review with AI analysis results"""
        
        try:
            update_data = {
                'processed_at': analysis['processed_at'],
                'sentiment_score': analysis.get('sentiment_score', 0.0),
                'sentiment_label': analysis.get('sentiment_label', 'neutral'),
                'confidence_score': analysis.get('confidence_score', 0.0),
                'key_topics': json.dumps(analysis.get('key_topics', [])),
                'issues_mentioned': json.dumps(analysis.get('issues_mentioned', [])),
                'priority_level': analysis.get('priority_level', 'low'),
                'ai_model_used': analysis.get('ai_model_used', 'gpt-4o-mini'),
                'processing_version': analysis.get('processing_version', '3.1')
            }
            
            result = self.supabase.table('reviews').update(update_data).eq('id', review_id).execute()
            return True
            
        except Exception as e:
            print(f"❌ Error updating review {review_id}: {e}")
            return False
    
    def process_batch(self, reviews: List[Dict]) -> Dict:
        """Process a batch of reviews"""
        
        batch_stats = {
            'processed': 0,
            'errors': 0,
            'start_time': time.time()
        }
        
        # Get product info cache
        product_cache = {}
        for review in reviews:
            product_id = review['product_id']
            if product_id not in product_cache:
                product_cache[product_id] = self.get_product_info(product_id)
        
        print(f"🔄 Processing {self.target_company} batch of {len(reviews)} reviews...")
        
        for i, review in enumerate(reviews):
            try:
                product_info = product_cache[review['product_id']]
                
                # Analyze with OpenAI
                analysis = self.analyze_review_with_openai(review['content'], product_info)
                
                if analysis:
                    if self.update_review_with_analysis(review['id'], analysis):
                        batch_stats['processed'] += 1
                        self.stats['total_processed'] += 1
                        
                        # Progress indicator
                        if (i + 1) % 100 == 0:
                            print(f"   ✅ {self.target_company}: {i + 1}/{len(reviews)} processed")
                    else:
                        batch_stats['errors'] += 1
                        self.stats['total_errors'] += 1
                else:
                    batch_stats['errors'] += 1
                    self.stats['total_errors'] += 1
                
                # Small delay between reviews
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error processing review {review['id']}: {e}")
                batch_stats['errors'] += 1
                self.stats['total_errors'] += 1
        
        batch_time = time.time() - batch_stats['start_time']
        self.stats['batches_completed'] += 1
        
        print(f"✅ {self.target_company} batch complete: {batch_stats['processed']} processed, {batch_stats['errors']} errors in {batch_time:.1f}s")
        
        return batch_stats
    
    def run_parallel_processing(self, max_batches: Optional[int] = None):
        """Run parallel processing for target company"""
        
        print(f"🚀 PARALLEL PROCESSING: {self.target_company}")
        print("=" * 60)
        print(f"Target: {self.target_company}")
        print(f"Product IDs: {self.product_ids}")
        print(f"Year Priority: {self.year_priority}")
        print(f"Batch Size: {self.batch_size}")
        print(f"Model: GPT-4o-mini v3.1")
        
        # Show unprocessed counts
        self.get_unprocessed_count()
        
        input(f"\nPress Enter to start {self.target_company} processing...")
        
        batch_count = 0
        
        while True:
            # Check if we should stop
            if max_batches and batch_count >= max_batches:
                print(f"\n🛑 Reached maximum batch limit: {max_batches}")
                break
            
            # Get next batch
            reviews = self.get_prioritized_batch(self.batch_size)
            
            if not reviews:
                print(f"\n🎉 All {self.target_company} reviews processed!")
                break
            
            batch_count += 1
            print(f"\n📦 {self.target_company} BATCH {batch_count}")
            print(f"Current Year: {self.stats['current_year']}")
            
            # Process batch
            batch_stats = self.process_batch(reviews)
            
            # Show progress
            elapsed_time = datetime.now() - self.stats['start_time']
            processing_rate = self.stats['total_processed'] / elapsed_time.total_seconds() * 60
            
            print(f"\n📊 {self.target_company} PROGRESS")
            print(f"   Total Processed: {self.stats['total_processed']:,}")
            print(f"   Total Errors: {self.stats['total_errors']:,}")
            print(f"   Batches Completed: {self.stats['batches_completed']}")
            print(f"   Processing Rate: {processing_rate:.1f} reviews/minute")
            print(f"   Elapsed Time: {elapsed_time}")
            
            if self.stats['total_processed'] > 0:
                success_rate = (self.stats['total_processed'] / (self.stats['total_processed'] + self.stats['total_errors'])) * 100
                print(f"   Success Rate: {success_rate:.1f}%")
            
            # Delay between batches
            if reviews and len(reviews) == self.batch_size:
                print(f"⏸️ Waiting {self.processing_delay}s before next {self.target_company} batch...")
                time.sleep(self.processing_delay)
        
        # Final summary
        total_time = datetime.now() - self.stats['start_time']
        print(f"\n🎯 {self.target_company} PROCESSING COMPLETE!")
        print(f"Total Processed: {self.stats['total_processed']:,}")
        print(f"Total Errors: {self.stats['total_errors']:,}")
        print(f"Total Time: {total_time}")
        if total_time.total_seconds() > 0:
            print(f"Average Rate: {self.stats['total_processed'] / total_time.total_seconds() * 60:.1f} reviews/minute")

def main():
    """Main execution function"""
    
    print("🔄 PARALLEL PRODUCT PROCESSING")
    print("=" * 60)
    
    # Select target company
    companies = [
        "Norton",
        "Bitdefender", 
        "Kaspersky",
        "McAfee",
        "AVG",
        "Avast",
        "ESET",
        "Trend Micro",
        "Malwarebytes"
    ]
    
    print("🏢 AVAILABLE COMPANIES FOR PARALLEL PROCESSING:")
    for i, company in enumerate(companies, 1):
        print(f"{i}. {company}")
    
    choice = input(f"\nChoose company (1-{len(companies)}): ").strip()
    
    try:
        company_index = int(choice) - 1
        if 0 <= company_index < len(companies):
            target_company = companies[company_index]
        else:
            print("❌ Invalid choice")
            return
    except ValueError:
        print("❌ Invalid choice")
        return
    
    # Get processing size
    print(f"\n🚀 PROCESSING OPTIONS FOR {target_company}:")
    print("1. Test run (5 batches = ~250 reviews)")
    print("2. Small run (20 batches = ~1,000 reviews)")
    print("3. Medium run (100 batches = ~5,000 reviews)")
    print("4. Large run (500 batches = ~25,000 reviews)")
    print("5. Full processing (all reviews for this company)")
    
    size_choice = input("\nEnter choice (1-5): ").strip()
    
    max_batches = None
    if size_choice == "1":
        max_batches = 5
        print(f"🧪 Starting {target_company} test run...")
    elif size_choice == "2":
        max_batches = 20
        print(f"🔬 Starting {target_company} small run...")
    elif size_choice == "3":
        max_batches = 100
        print(f"⚡ Starting {target_company} medium run...")
    elif size_choice == "4":
        max_batches = 500
        print(f"🏃 Starting {target_company} large run...")
    elif size_choice == "5":
        print(f"🚀 Starting full {target_company} processing...")
        confirm = input(f"This will process ALL {target_company} reviews. Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled")
            return
    else:
        print("❌ Invalid choice")
        return
    
    # Initialize processor
    processor = ParallelProductProcessor(target_company)
    
    if not processor.product_ids:
        print(f"❌ No products found for {target_company}")
        return
    
    # Run processing
    try:
        processor.run_parallel_processing(max_batches)
    except KeyboardInterrupt:
        print(f"\n⏹️ {target_company} processing interrupted")
        print(f"Processed {processor.stats['total_processed']:,} reviews before stopping")
    except Exception as e:
        print(f"\n❌ {target_company} processing error: {e}")

if __name__ == "__main__":
    main()
