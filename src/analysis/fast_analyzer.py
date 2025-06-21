#!/usr/bin/env python3
"""
Fast AI Analysis Runner - Optimized for Speed
Processes reviews with reduced API calls and faster batching
"""

import os
import sys
import logging
from datetime import datetime
import asyncio
import aiohttp
import json

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import get_db_manager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FastAIAnalyzer:
    """Optimized AI analyzer with minimal API calls"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.db_manager = get_db_manager()
    
    async def analyze_review_batch(self, reviews, session):
        """Analyze multiple reviews with simplified prompts"""
        tasks = []
        for review in reviews:
            task = self.analyze_single_review(review, session)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def analyze_single_review(self, review, session):
        """Fast single review analysis"""
        
        # Simplified prompt for speed
        prompt = f'''Rate this review sentiment (1-5) and extract 2-3 key topics. JSON only:
{{"sentiment_score": 3.5, "sentiment_label": "positive", "topics": ["performance"], "priority": "low"}}

Review: "{review['content'][:200]}"'''
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You analyze reviews. Respond only with JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,  # Reduced for speed
            "temperature": 0.1
        }
        
        try:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
                json=payload
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    content = data['choices'][0]['message']['content']
                    
                    # Quick JSON extraction
                    if content.startswith('```'):
                        content = content.split('```')[1].replace('json', '').strip()
                    
                    result = json.loads(content)
                    result['review_id'] = review['id']
                    return result
                else:
                    logger.error(f"API error: {data}")
                    return self.fallback_analysis(review)
                    
        except Exception as e:
            logger.error(f"Analysis failed for review {review['id']}: {e}")
            return self.fallback_analysis(review)
    
    def fallback_analysis(self, review):
        """Quick fallback without AI"""
        content = review['content'].lower()
        
        # Simple sentiment detection
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'best']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible', 'useless']
        
        pos_count = sum(1 for word in positive_words if word in content)
        neg_count = sum(1 for word in negative_words if word in content)
        
        if pos_count > neg_count:
            sentiment_score = 4.0
            sentiment_label = "positive"
        elif neg_count > pos_count:
            sentiment_score = 2.0
            sentiment_label = "negative"
        else:
            sentiment_score = 3.0
            sentiment_label = "neutral"
        
        return {
            'review_id': review['id'],
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label,
            'topics': ['general'],
            'priority': 'low'
        }
    
    def update_reviews_batch(self, results):
        """Update multiple reviews in database efficiently"""
        updates = []
        
        for result in results:
            if isinstance(result, dict) and 'review_id' in result:
                update_data = {
                    'sentiment_score': result.get('sentiment_score', 3.0),
                    'sentiment_label': result.get('sentiment_label', 'neutral'),
                    'key_topics': result.get('topics', []),
                    'priority_level': result.get('priority', 'low'),
                    'ai_model_used': 'gpt-4o-mini-fast',
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                # Update review
                try:
                    self.db_manager.supabase.table('reviews').update(update_data).eq('id', result['review_id']).execute()
                    updates.append(result['review_id'])
                except Exception as e:
                    logger.error(f"Failed to update review {result['review_id']}: {e}")
        
        return len(updates)

async def fast_process_reviews():
    """Fast processing with async/await"""
    
    print("🚀 FAST AI REVIEW ANALYZER")
    print("=" * 50)
    
    analyzer = FastAIAnalyzer()
    
    # Get unprocessed reviews
    unprocessed = analyzer.db_manager.get_unprocessed_reviews(limit=1000)
    total_reviews = len(unprocessed)
    
    if total_reviews == 0:
        print("✅ No unprocessed reviews found!")
        return
    
    print(f"📊 Found {total_reviews} unprocessed reviews")
    print(f"⚡ Using optimized fast processing")
    
    # Process in larger batches for speed
    batch_size = 10  # Process 10 reviews simultaneously
    total_processed = 0
    start_time = datetime.now()
    
    # Create aiohttp session for async processing
    connector = aiohttp.TCPConnector(limit=20)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        for i in range(0, total_reviews, batch_size):
            batch = unprocessed[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"📦 Batch {batch_num}: Processing {len(batch)} reviews...")
            
            # Analyze batch asynchronously
            results = await analyzer.analyze_review_batch(batch, session)
            
            # Update database
            updated_count = analyzer.update_reviews_batch(results)
            total_processed += updated_count
            
            # Progress update
            progress_pct = (total_processed / total_reviews) * 100
            elapsed = datetime.now() - start_time
            rate = total_processed / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
            
            print(f"✅ Batch {batch_num}: {updated_count}/{len(batch)} updated")
            print(f"📈 Progress: {total_processed}/{total_reviews} ({progress_pct:.1f}%)")
            print(f"⚡ Rate: {rate:.1f} reviews/second")
            
            if total_processed < total_reviews:
                remaining = total_reviews - total_processed
                eta_seconds = remaining / rate if rate > 0 else 0
                print(f"🕐 ETA: {eta_seconds/60:.1f} minutes")
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
    
    # Final summary
    elapsed = datetime.now() - start_time
    print(f"\n🎉 FAST ANALYSIS COMPLETE!")
    print(f"📊 Total processed: {total_processed}/{total_reviews}")
    print(f"⏱️ Total time: {elapsed}")
    print(f"🚀 Average rate: {total_processed/elapsed.total_seconds():.1f} reviews/second")

def main():
    """Run fast analysis"""
    try:
        # Check if we're in an async context
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in Jupyter or similar
            import nest_asyncio
            nest_asyncio.apply()
        
        asyncio.run(fast_process_reviews())
        
    except Exception as e:
        logger.error(f"❌ Fast analysis failed: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
