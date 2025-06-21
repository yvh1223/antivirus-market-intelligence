#!/usr/bin/env python3
"""
Simple AI Analysis Runner
Processes all unprocessed reviews with progress tracking
"""

import os
import sys
import logging
from datetime import datetime

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import get_db_manager
from analysis.ai_analyzer import ReviewProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ai_analysis():
    """Run AI analysis on all unprocessed reviews"""
    
    print("🤖 AI REVIEW ANALYZER")
    print("=" * 50)
    
    try:
        # Initialize components
        db_manager = get_db_manager()
        processor = ReviewProcessor()
        
        # Check how many unprocessed reviews we have
        unprocessed = db_manager.get_unprocessed_reviews(limit=10000)  # Get count
        total_unprocessed = len(unprocessed)
        
        print(f"📊 Found {total_unprocessed} unprocessed reviews")
        
        if total_unprocessed == 0:
            print("✅ All reviews are already processed!")
            return
        
        # Ask for confirmation
        print(f"\n⚠️  This will process {total_unprocessed} reviews using OpenAI API")
        print("💰 Estimated cost: $0.01-0.05 per review (depending on length)")
        print(f"💸 Total estimated cost: ${total_unprocessed * 0.03:.2f}")
        
        response = input("\n🤔 Continue? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled by user")
            return
        
        # Process in smaller batches for better progress tracking
        batch_size = 25
        total_processed = 0
        total_errors = 0
        
        print(f"\n🚀 Starting analysis in batches of {batch_size}...")
        start_time = datetime.now()
        
        while total_processed < total_unprocessed:
            batch_num = (total_processed // batch_size) + 1
            remaining = total_unprocessed - total_processed
            current_batch_size = min(batch_size, remaining)
            
            print(f"\n📦 Batch {batch_num}: Processing {current_batch_size} reviews...")
            print(f"📈 Progress: {total_processed}/{total_unprocessed} ({(total_processed/total_unprocessed)*100:.1f}%)")
            
            # Process batch
            result = processor.process_unprocessed_reviews(current_batch_size)
            
            # Update counters
            batch_processed = result['processed']
            batch_errors = result['errors']
            
            total_processed += batch_processed
            total_errors += batch_errors
            
            print(f"✅ Batch {batch_num} complete: {batch_processed} processed, {batch_errors} errors")
            
            # If we didn't process any reviews, we're done
            if batch_processed == 0:
                print("ℹ️ No more reviews to process")
                break
            
            # Show time estimates
            elapsed = datetime.now() - start_time
            if total_processed > 0:
                rate = total_processed / elapsed.total_seconds()
                remaining_reviews = total_unprocessed - total_processed
                eta_seconds = remaining_reviews / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                print(f"⏱️ Processing rate: {rate:.2f} reviews/second")
                print(f"🕐 ETA: {eta_minutes:.1f} minutes")
        
        # Final summary
        elapsed = datetime.now() - start_time
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"📊 Total processed: {total_processed}")
        print(f"❌ Total errors: {total_errors}")
        print(f"⏱️ Total time: {elapsed}")
        print(f"🚀 Average rate: {total_processed/elapsed.total_seconds():.2f} reviews/second")
        
        # Show some results
        if total_processed > 0:
            print(f"\n📈 QUICK INSIGHTS:")
            try:
                # Get some quick stats
                stats = db_manager.get_review_stats(days=30)
                if stats:
                    avg_rating = stats.get('avg_rating', 0)
                    sentiment_positive = stats.get('positive_reviews', 0)
                    sentiment_negative = stats.get('negative_reviews', 0)
                    
                    print(f"⭐ Average rating: {avg_rating:.2f}/5")
                    print(f"😊 Positive reviews: {sentiment_positive}")
                    print(f"😞 Negative reviews: {sentiment_negative}")
            except Exception as e:
                print(f"⚠️ Could not generate quick stats: {e}")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    run_ai_analysis()

if __name__ == "__main__":
    main()
