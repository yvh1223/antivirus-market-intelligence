#!/usr/bin/env python3
"""
Simple Results Viewer - Uses working database methods
"""

import sys
import os

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import get_db_manager

def view_simple_results():
    """View results using working database methods"""
    
    print("📊 AI ANALYSIS RESULTS (Simple View)")
    print("=" * 50)
    
    db_manager = get_db_manager()
    
    # Get sample of processed reviews
    try:
        reviews = db_manager.get_reviews(limit=100)
        processed_reviews = [r for r in reviews if r.get('sentiment_label')]
        
        print(f"✅ Sample Reviews Checked: {len(reviews)}")
        print(f"🤖 AI Processed Reviews: {len(processed_reviews)}")
        
        if processed_reviews:
            print(f"\n😊 SENTIMENT BREAKDOWN:")
            print("-" * 25)
            
            sentiments = {}
            scores = []
            
            for review in processed_reviews:
                sentiment = review.get('sentiment_label', 'unknown')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
                
                score = review.get('sentiment_score')
                if score is not None:
                    scores.append(score)
            
            for sentiment, count in sentiments.items():
                pct = (count / len(processed_reviews)) * 100
                print(f"{sentiment.title():>12}: {count:>3} ({pct:.1f}%)")
            
            if scores:
                avg_score = sum(scores) / len(scores)
                print(f"{'Average':>12}: {avg_score:.2f}/5.0")
            
            print(f"\n🏷️ SAMPLE TOPICS:")
            print("-" * 20)
            
            all_topics = []
            for review in processed_reviews[:20]:  # Sample topics
                topics = review.get('key_topics', [])
                if isinstance(topics, list):
                    all_topics.extend(topics)
            
            unique_topics = list(set(all_topics))
            for topic in unique_topics[:10]:
                print(f"• {topic}")
            
            print(f"\n📝 SAMPLE ANALYZED REVIEWS:")
            print("-" * 30)
            
            for i, review in enumerate(processed_reviews[:5]):
                content = review.get('content', '')[:60] + "..."
                sentiment = review.get('sentiment_label', 'unknown')
                score = review.get('sentiment_score', 0)
                
                print(f"{i+1}. {sentiment.upper()} ({score:.1f}) - {content}")
            
            print(f"\n🎉 SUCCESS! Your reviews are now enriched with AI insights!")
            print(f"💡 You can now use these insights for business intelligence!")
            
        else:
            print("⚠️ No AI-processed reviews found in sample")
            print("💡 Try running the AI analyzer again")
    
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    view_simple_results()

if __name__ == "__main__":
    main()
