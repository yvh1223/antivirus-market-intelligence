#!/usr/bin/env python3
"""
View AI Analysis Results
Shows processed review insights and statistics
"""

import os
import sys
from collections import Counter
import json

# Local imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import get_db_manager

def show_analysis_results():
    """Show comprehensive analysis results"""
    
    print("📊 AI ANALYSIS RESULTS")
    print("=" * 60)
    
    db_manager = get_db_manager()
    
    # Get processed reviews
    all_reviews = db_manager.get_reviews(limit=2000)
    processed_reviews = [r for r in all_reviews if r.get('processed_at')]
    
    print(f"✅ Total Reviews Analyzed: {len(processed_reviews)}")
    
    if not processed_reviews:
        print("❌ No processed reviews found")
        return
    
    # Sentiment Analysis Summary
    print(f"\n😊 SENTIMENT ANALYSIS:")
    print("-" * 30)
    
    sentiments = [r.get('sentiment_label', 'unknown') for r in processed_reviews]
    sentiment_counts = Counter(sentiments)
    
    for sentiment, count in sentiment_counts.most_common():
        percentage = (count / len(processed_reviews)) * 100
        print(f"{sentiment.title():>10}: {count:>4} ({percentage:.1f}%)")
    
    # Average sentiment score
    scores = [r.get('sentiment_score', 0) for r in processed_reviews if r.get('sentiment_score')]
    if scores:
        avg_score = sum(scores) / len(scores)
        print(f"{'Average':>10}: {avg_score:.2f}/5.0")
    
    # Topic Analysis
    print(f"\n🏷️ TOP TOPICS MENTIONED:")
    print("-" * 30)
    
    all_topics = []
    for review in processed_reviews:
        topics = review.get('key_topics', [])
        if isinstance(topics, list):
            all_topics.extend(topics)
    
    topic_counts = Counter(all_topics)
    for topic, count in topic_counts.most_common(10):
        percentage = (count / len(processed_reviews)) * 100
        print(f"{topic.title():>15}: {count:>4} ({percentage:.1f}%)")
    
    # Priority Analysis
    print(f"\n🚨 PRIORITY LEVELS:")
    print("-" * 30)
    
    priorities = [r.get('priority_level', 'low') for r in processed_reviews]
    priority_counts = Counter(priorities)
    
    for priority, count in priority_counts.most_common():
        percentage = (count / len(processed_reviews)) * 100
        print(f"{priority.title():>10}: {count:>4} ({percentage:.1f}%)")
    
    # Product Breakdown
    print(f"\n📱 BY PRODUCT:")
    print("-" * 30)
    
    products = db_manager.get_products()
    product_map = {p['id']: f"{p['name']} ({p['company']})" for p in products}
    
    product_reviews = {}
    product_sentiments = {}
    
    for review in processed_reviews:
        pid = review.get('product_id')
        if pid in product_map:
            product_name = product_map[pid]
            
            # Count reviews
            product_reviews[product_name] = product_reviews.get(product_name, 0) + 1
            
            # Track sentiment
            sentiment = review.get('sentiment_label', 'neutral')
            if product_name not in product_sentiments:
                product_sentiments[product_name] = []
            product_sentiments[product_name].append(sentiment)
    
    for product, count in sorted(product_reviews.items(), key=lambda x: x[1], reverse=True):
        sentiments = product_sentiments[product]
        positive_pct = (sentiments.count('positive') / len(sentiments)) * 100 if sentiments else 0
        
        product_short = product[:35] + "..." if len(product) > 35 else product
        print(f"{product_short:<38}: {count:>4} reviews ({positive_pct:.0f}% positive)")
    
    # Recent Analysis
    print(f"\n🕐 RECENT ACTIVITY:")
    print("-" * 30)
    
    recent_reviews = [r for r in processed_reviews if r.get('processed_at')][-10:]
    for review in recent_reviews:
        review_id = review.get('id', 'N/A')
        sentiment = review.get('sentiment_label', 'neutral')
        score = review.get('sentiment_score', 0)
        content_preview = review.get('content', '')[:50] + "..." if review.get('content') else ''
        
        print(f"Review {review_id}: {sentiment} ({score:.1f}) - {content_preview}")
    
    print(f"\n" + "=" * 60)
    print("🎉 Analysis complete! Your reviews are now enriched with AI insights.")

def show_insights_by_product():
    """Show insights for each product"""
    
    print("\n📱 DETAILED PRODUCT INSIGHTS:")
    print("=" * 60)
    
    db_manager = get_db_manager()
    products = db_manager.get_products()
    
    for product in products[:5]:  # Show top 5 products
        print(f"\n🔍 {product['name']} by {product['company']}")
        print("-" * 50)
        
        try:
            stats = db_manager.get_review_stats(product_id=product['id'], days=365)
            if stats and stats.get('total_reviews', 0) > 0:
                print(f"📊 Total Reviews: {stats.get('total_reviews', 0)}")
                print(f"⭐ Average Rating: {stats.get('avg_rating', 0):.2f}/5")
                print(f"😊 Positive: {stats.get('positive_reviews', 0)}")
                print(f"😞 Negative: {stats.get('negative_reviews', 0)}")
                print(f"😐 Neutral: {stats.get('neutral_reviews', 0)}")
            else:
                print("📊 No processed reviews found for this product")
        except Exception as e:
            print(f"❌ Error getting stats: {e}")

def main():
    """Main function"""
    try:
        show_analysis_results()
        show_insights_by_product()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
