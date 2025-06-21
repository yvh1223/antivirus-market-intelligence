"""
AI-powered review analysis system
Provides sentiment analysis, topic extraction, and business intelligence using OpenAI API
"""

import os
import logging
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv
from openai import OpenAI
from textblob import TextBlob
import spacy
from collections import Counter
import asyncio
import aiohttp

# Load environment variables from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

# Local imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.manager import DatabaseManager, get_db_manager

logger = logging.getLogger(__name__)

class OpenAIAnalyzer:
    """Advanced AI analysis using OpenAI API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"  # Using the efficient model for analysis
        
        # Test connection
        try:
            test_response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            logger.info("✅ OpenAI API connected successfully")
        except Exception as e:
            logger.error(f"❌ OpenAI API connection failed: {e}")
            raise
    
    def analyze_review_comprehensive(self, review_text: str, product_name: str = "antivirus software") -> Dict[str, Any]:
        """Comprehensive review analysis using OpenAI"""
        
        prompt = f"""Analyze this review for {product_name}. JSON only:

{{
    "sentiment": {{"score": 0.5, "label": "positive", "confidence": 0.8}},
    "topics": ["performance"],
    "issues_mentioned": [],
    "business_intelligence": {{"priority_level": "low", "requires_response": false, "churn_risk": "low", "upsell_opportunity": false}},
    "intent_analysis": {{"primary_intent": "praise", "switching_intent": false, "recommendation_intent": true}},
    "summary": "Brief summary"
}}

Review: "{review_text[:300]}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert business analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,  # Reduced for speed
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to clean up the response if it has extra text
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            # Find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                result = json.loads(json_text)
            else:
                result = json.loads(response_text)
            
            # Add metadata
            result['ai_model_used'] = self.model
            result['processing_timestamp'] = datetime.now(timezone.utc).isoformat()
            
            # Validate required fields and add defaults if missing
            if 'sentiment' not in result:
                result['sentiment'] = {'score': 0.0, 'label': 'neutral', 'confidence': 0.0}
            if 'business_intelligence' not in result:
                result['business_intelligence'] = {
                    'priority_level': 'low',
                    'requires_response': False,
                    'churn_risk': 'low',
                    'upsell_opportunity': False
                }
            if 'intent_analysis' not in result:
                result['intent_analysis'] = {
                    'primary_intent': 'unknown',
                    'switching_intent': False,
                    'recommendation_intent': False
                }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse OpenAI response as JSON: {e}")
            # return self._fallback_analysis(review_text)  # COMMENTED OUT FOR SPEED
            return None  # Skip failed reviews
        except Exception as e:
            logger.error(f"❌ OpenAI analysis failed: {e}")
            # return self._fallback_analysis(review_text)  # COMMENTED OUT FOR SPEED
            return None  # Skip failed reviews
    
    def batch_analyze_reviews(self, reviews: List[Dict[str, Any]], product_name: str = "antivirus software") -> List[Dict[str, Any]]:
        """Analyze multiple reviews in batch"""
        results = []
        
        for i, review in enumerate(reviews):
            logger.info(f"🔄 Analyzing review {i+1}/{len(reviews)}")
            
            try:
                analysis = self.analyze_review_comprehensive(review['content'], product_name)
                analysis['review_id'] = review['id']
                results.append(analysis)
                
                # Rate limiting
                if i % 10 == 0 and i > 0:
                    logger.info(f"⏸️ Processed {i} reviews, pausing briefly...")
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Failed to analyze review {review['id']}: {e}")
                # Add empty result to maintain order
                results.append({
                    'review_id': review['id'],
                    'error': str(e),
                    'sentiment': {'score': 0, 'label': 'neutral', 'confidence': 0}
                })
        
        return results
    
    def _fallback_analysis(self, review_text: str) -> Dict[str, Any]:
        """Fallback analysis using TextBlob when OpenAI fails"""
        blob = TextBlob(review_text)
        polarity = blob.sentiment.polarity
        
        sentiment_label = 'positive' if polarity > 0.1 else 'negative' if polarity < -0.1 else 'neutral'
        
        return {
            'sentiment': {
                'score': round(polarity, 3),
                'label': sentiment_label,
                'confidence': round(abs(polarity), 3)
            },
            'emotions': {},
            'topics': [],
            'aspect_sentiment': {},
            'issues_mentioned': [],
            'features_mentioned': [],
            'competitive_mentions': [],
            'intent_analysis': {
                'primary_intent': 'unknown',
                'switching_intent': False,
                'recommendation_intent': False
            },
            'business_intelligence': {
                'priority_level': 'low',
                'requires_response': False,
                'churn_risk': 'low',
                'upsell_opportunity': False
            },
            'key_phrases': [],
            'suggested_improvements': '',
            'summary': 'Analysis unavailable - using fallback method',
            'ai_model_used': 'textblob_fallback',
            'processing_timestamp': datetime.now(timezone.utc).isoformat()
        }

class TopicExtractor:
    """Extract topics and themes from reviews using OpenAI"""
    
    def __init__(self):
        self.openai_analyzer = OpenAIAnalyzer()
        
        # Security-focused topic categories for fallback
        self.security_topics = {
            'performance': ['slow', 'fast', 'speed', 'performance', 'quick', 'lag', 'responsive'],
            'pricing': ['expensive', 'cheap', 'price', 'cost', 'money', 'subscription', 'free'],
            'usability': ['easy', 'difficult', 'user-friendly', 'interface', 'navigation', 'setup'],
            'protection': ['protect', 'secure', 'safety', 'block', 'detect', 'prevent', 'scan'],
            'support': ['support', 'help', 'customer service', 'response', 'assistance'],
            'features': ['feature', 'function', 'capability', 'tool', 'option'],
            'reliability': ['reliable', 'stable', 'crash', 'bug', 'error', 'problem'],
            'updates': ['update', 'upgrade', 'version', 'patch', 'latest'],
            'installation': ['install', 'setup', 'download', 'configure'],
            'compatibility': ['compatible', 'work', 'support', 'device', 'system']
        }
        
        self.competitor_names = [
            'norton', 'mcafee', 'bitdefender', 'kaspersky', 'avg', 'avast', 
            'windows defender', 'eset', 'trend micro', 'f-secure', 'malwarebytes'
        ]
    
    def extract_trending_topics(self, reviews: List[str], time_period: str = "last week") -> Dict[str, Any]:
        """Extract trending topics from a collection of reviews"""
        
        prompt = f"""
        Analyze these customer reviews from {time_period} and identify trending topics and themes.
        
        Provide analysis in this JSON format:
        {{
            "trending_topics": [
                {{
                    "topic": string,
                    "frequency": int,
                    "sentiment": string, // "positive", "negative", "mixed"
                    "urgency": string, // "low", "medium", "high"
                    "sample_quotes": [string] // 2-3 representative quotes
                }}
            ],
            "emerging_issues": [
                {{
                    "issue": string,
                    "severity": string, // "low", "medium", "high", "critical"
                    "affected_features": [string],
                    "frequency": int
                }}
            ],
            "competitive_insights": [
                {{
                    "competitor": string,
                    "mention_context": string, // "positive", "negative", "comparison"
                    "frequency": int
                }}
            ],
            "summary": {{
                "total_reviews_analyzed": int,
                "overall_sentiment_trend": string,
                "key_insights": [string],
                "recommended_actions": [string]
            }}
        }}
        
        Reviews:
        {json.dumps(reviews[:50])}  # Limit to first 50 reviews to avoid token limits
        """
        
        try:
            response = self.openai_analyzer.client.chat.completions.create(
                model=self.openai_analyzer.model,
                messages=[
                    {"role": "system", "content": "You are an expert business analyst specializing in customer feedback trend analysis for cybersecurity products."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"❌ Trending topics analysis failed: {e}")
            # return self._fallback_trending_analysis(reviews)  # COMMENTED OUT FOR SPEED
            return {'error': 'Analysis failed, no fallback'}  # Skip fallback
    
    def _fallback_trending_analysis(self, reviews: List[str]) -> Dict[str, Any]:
        """Fallback trending analysis without OpenAI"""
        # Simple keyword-based analysis
        all_text = " ".join(reviews).lower()
        
        trending_topics = []
        for topic, keywords in self.security_topics.items():
            frequency = sum(all_text.count(keyword) for keyword in keywords)
            if frequency > 0:
                trending_topics.append({
                    "topic": topic,
                    "frequency": frequency,
                    "sentiment": "mixed",
                    "urgency": "medium",
                    "sample_quotes": []
                })
        
        return {
            "trending_topics": sorted(trending_topics, key=lambda x: x["frequency"], reverse=True)[:10],
            "emerging_issues": [],
            "competitive_insights": [],
            "summary": {
                "total_reviews_analyzed": len(reviews),
                "overall_sentiment_trend": "mixed",
                "key_insights": ["Analysis performed using fallback method"],
                "recommended_actions": ["Implement advanced AI analysis"]
            }
        }

class ReviewProcessor:
    """Main class for processing reviews with AI analysis"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.openai_analyzer = OpenAIAnalyzer()
        self.topic_extractor = TopicExtractor()
    
    def process_unprocessed_reviews(self, batch_size: int = 50) -> Dict[str, Any]:
        """Process reviews that haven't been analyzed yet"""
        
        # Get unprocessed reviews
        reviews = self.db_manager.get_unprocessed_reviews(limit=batch_size)
        
        if not reviews:
            logger.info("✅ No unprocessed reviews found")
            return {'processed': 0, 'errors': 0}
        
        logger.info(f"🔄 Processing {len(reviews)} unprocessed reviews")
        
        processed_count = 0
        error_count = 0
        
        for review in reviews:
            try:
                # Get product info for context
                products = self.db_manager.get_products()
                product = next((p for p in products if p['id'] == review['product_id']), None)
                product_name = f"{product['name']} by {product['company']}" if product else "antivirus software"
                
                # Perform AI analysis
                analysis = self.openai_analyzer.analyze_review_comprehensive(
                    review['content'], 
                    product_name
                )
                
                # Skip if analysis failed (None returned)
                if analysis is None:
                    logger.warning(f"⚠️ Skipping review {review['id']} - analysis failed")
                    error_count += 1
                    continue
                
                # Prepare update data for reviews table
                sentiment_data = analysis.get('sentiment', {})
                business_data = analysis.get('business_intelligence', {})
                intent_data = analysis.get('intent_analysis', {})
                
                review_updates = {
                    'sentiment_score': sentiment_data.get('score', 0.0),
                    'sentiment_label': sentiment_data.get('label', 'neutral'),
                    'confidence_score': sentiment_data.get('confidence', 0.0),
                    'key_topics': analysis.get('topics', []),
                    'issues_mentioned': analysis.get('issues_mentioned', []),
                    'features_mentioned': analysis.get('features_mentioned', []),
                    'competitive_mentions': analysis.get('competitive_mentions', []),
                    'suggested_improvements': analysis.get('suggested_improvements', ''),
                    'priority_level': business_data.get('priority_level', 'low'),
                    'requires_response': business_data.get('requires_response', False),
                    'ai_model_used': analysis.get('ai_model_used', 'unknown'),
                    'processing_version': '2.1',
                    'processing_duration_ms': 1000  # Approximate
                }
                
                # Update review record
                self.db_manager.mark_review_processed(review['id'], review_updates)
                
                # Insert detailed analysis
                emotions_data = analysis.get('emotions', {})
                aspect_sentiment_data = analysis.get('aspect_sentiment', {})
                topics_data = analysis.get('topics', [])
                
                analysis_data = {
                    'review_id': review['id'],
                    'emotion_scores': emotions_data,
                    'aspect_sentiment': aspect_sentiment_data,
                    'subjectivity_score': 0.5,  # Default value
                    'primary_topic': topics_data[0] if topics_data else 'general',
                    'topic_distribution': {},
                    'intent_type': intent_data.get('primary_intent', 'unknown'),
                    'action_required': business_data.get('requires_response', False),
                    'escalation_needed': business_data.get('priority_level', 'low') in ['high', 'critical'],
                    'competitor_mentions': analysis.get('competitive_mentions', []),
                    'switching_intent': intent_data.get('switching_intent', False),
                    'churn_risk_score': {'low': 0.2, 'medium': 0.5, 'high': 0.8}.get(
                        business_data.get('churn_risk', 'low'), 0.2
                    ),
                    'upsell_opportunity': business_data.get('upsell_opportunity', False)
                }
                
                # Insert into review_analysis table
                try:
                    self.db_manager.supabase.table('review_analysis').insert(analysis_data).execute()
                except Exception as e:
                    logger.warning(f"⚠️ Failed to insert detailed analysis for review {review['id']}: {e}")
                
                processed_count += 1
                logger.info(f"✅ Processed review {review['id']} ({processed_count}/{len(reviews)})")
                
            except Exception as e:
                logger.error(f"❌ Failed to process review {review['id']}: {e}")
                error_count += 1
        
        result = {
            'processed': processed_count,
            'errors': error_count,
            'total_reviews': len(reviews)
        }
        
        logger.info(f"🎉 Processing complete: {processed_count} processed, {error_count} errors")
        return result
    
    def generate_insights_report(self, product_id: int = None, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive insights report"""
        
        # Get recent reviews
        reviews = self.db_manager.get_reviews(product_id=product_id, limit=1000)
        recent_reviews = [r for r in reviews if r.get('review_date')]  # Filter valid dates
        
        if not recent_reviews:
            return {'error': 'No reviews found for analysis'}
        
        # Extract review texts for trending analysis
        review_texts = [r['content'] for r in recent_reviews if r.get('content')]
        
        # Get trending topics
        trending_analysis = self.topic_extractor.extract_trending_topics(review_texts, f"last {days} days")
        
        # Get basic stats
        stats = self.db_manager.get_review_stats(product_id=product_id, days=days)
        
        # Get trending topics from database
        db_trending = self.db_manager.get_trending_topics(product_id=product_id, days=days)
        
        return {
            'period': f"Last {days} days",
            'basic_stats': stats,
            'ai_insights': trending_analysis,
            'database_trends': db_trending,
            'generated_at': datetime.utcnow().isoformat()
        }

def main():
    """CLI for review processing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Review Analysis System")
    parser.add_argument('--action', choices=['process', 'insights', 'test'], 
                       default='process', help='Action to perform')
    parser.add_argument('--batch_size', type=int, default=50, 
                       help='Batch size for processing')
    parser.add_argument('--product_id', type=int, help='Product ID for insights')
    parser.add_argument('--days', type=int, default=30, help='Days for insights')
    
    args = parser.parse_args()
    
    processor = ReviewProcessor()
    
    if args.action == 'test':
        # Test OpenAI connection
        logger.info("🧪 Testing AI analysis...")
        test_review = "This antivirus is amazing! Great protection and easy to use."
        result = processor.openai_analyzer.analyze_review_comprehensive(test_review)
        print(json.dumps(result, indent=2))
        
    elif args.action == 'process':
        # Process unprocessed reviews
        result = processor.process_unprocessed_reviews(args.batch_size)
        print(f"✅ Processed {result['processed']} reviews with {result['errors']} errors")
        
    elif args.action == 'insights':
        # Generate insights report
        report = processor.generate_insights_report(args.product_id, args.days)
        print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()
