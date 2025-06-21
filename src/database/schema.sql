-- Enhanced Consumer Security Analysis V3 Database Schema
-- Designed for Supabase (PostgreSQL)

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Platforms Table (App Stores, Review Sites, etc.)
CREATE TABLE IF NOT EXISTS platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    base_url VARCHAR(255),
    api_endpoint VARCHAR(255),
    platform_type VARCHAR(30) NOT NULL, -- 'app_store', 'review_site', 'ecommerce', 'forum'
    requires_api BOOLEAN DEFAULT false,
    scraping_method VARCHAR(20) DEFAULT 'web', -- 'api', 'web', 'selenium'
    rate_limit_per_hour INTEGER DEFAULT 1000,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Products Table (Antivirus Software)
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    company VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'antivirus', 'security_suite', 'vpn', etc.
    subcategory VARCHAR(50), -- 'free', 'premium', 'business', etc.
    description TEXT,
    official_website VARCHAR(255),
    logo_url VARCHAR(255),
    current_version VARCHAR(50),
    release_date DATE,
    pricing_model VARCHAR(30), -- 'free', 'freemium', 'subscription', 'one-time'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Product-Platform Mappings
CREATE TABLE IF NOT EXISTS product_platform_mappings (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
    platform_app_id VARCHAR(255) NOT NULL, -- App Store ID, Package name, etc.
    platform_url VARCHAR(500),
    alternate_names JSONB, -- Array of alternative product names on this platform
    is_active BOOLEAN DEFAULT true,
    last_checked TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(product_id, platform_id)
);

-- 4. Main Reviews Table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
    
    -- Core Review Data
    platform_review_id VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    user_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    review_date TIMESTAMPTZ NOT NULL,
    
    -- Location & Language
    country_code VARCHAR(3),
    country_name VARCHAR(100),
    language_code VARCHAR(5),
    language_name VARCHAR(50),
    
    -- Platform Specific Metadata
    helpful_count INTEGER DEFAULT 0,
    total_votes INTEGER DEFAULT 0,
    verified_purchase BOOLEAN,
    version_reviewed VARCHAR(50),
    review_source_url VARCHAR(500),
    
    -- Content Metrics
    word_count INTEGER,
    character_count INTEGER,
    has_images BOOLEAN DEFAULT false,
    has_video BOOLEAN DEFAULT false,
    
    -- AI Analysis Fields
    sentiment_score DECIMAL(4,3), -- -1.000 to 1.000
    sentiment_label VARCHAR(20), -- 'positive', 'negative', 'neutral'
    confidence_score DECIMAL(4,3), -- 0.000 to 1.000
    
    -- Derived Insights (AI Generated)
    key_topics JSONB, -- Array of extracted topics
    issues_mentioned JSONB, -- Array of issues/problems
    features_mentioned JSONB, -- Array of features mentioned
    suggested_improvements TEXT,
    competitive_mentions JSONB, -- Mentions of other products
    
    -- Business Intelligence
    priority_level VARCHAR(10), -- 'low', 'medium', 'high', 'critical'
    requires_response BOOLEAN DEFAULT false,
    response_urgency VARCHAR(10), -- 'low', 'medium', 'high'
    
    -- Processing Metadata
    processed_at TIMESTAMPTZ,
    processing_version VARCHAR(10) DEFAULT '1.0',
    ai_model_used VARCHAR(50),
    processing_duration_ms INTEGER,
    
    -- Quality Scores
    spam_probability DECIMAL(4,3),
    authenticity_score DECIMAL(4,3),
    helpfulness_score DECIMAL(4,3),
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(platform_id, platform_review_id)
);

-- 5. Advanced Review Analysis
CREATE TABLE IF NOT EXISTS review_analysis (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES reviews(id) ON DELETE CASCADE UNIQUE,
    
    -- Advanced Sentiment Analysis
    emotion_scores JSONB, -- {'anger': 0.1, 'joy': 0.7, 'fear': 0.2, 'surprise': 0.1, etc.}
    aspect_sentiment JSONB, -- {'price': 'positive', 'performance': 'negative', 'support': 'neutral', etc.}
    subjectivity_score DECIMAL(4,3), -- 0.000 (objective) to 1.000 (subjective)
    
    -- Content Analysis
    readability_score DECIMAL(4,3),
    complexity_score DECIMAL(4,3),
    formality_score DECIMAL(4,3),
    
    -- Topic Modeling
    primary_topic VARCHAR(100),
    topic_distribution JSONB, -- {'performance': 0.4, 'pricing': 0.3, 'support': 0.3}
    named_entities JSONB, -- Extracted names, organizations, locations
    
    -- User Intent Analysis
    intent_type VARCHAR(30), -- 'complaint', 'praise', 'question', 'suggestion', 'comparison'
    action_required BOOLEAN DEFAULT false,
    escalation_needed BOOLEAN DEFAULT false,
    
    -- Competitive Intelligence
    competitor_mentions JSONB,
    comparison_type VARCHAR(30), -- 'favorable', 'unfavorable', 'neutral'
    switching_intent BOOLEAN DEFAULT false,
    
    -- Temporal Analysis
    trend_indicator VARCHAR(20), -- 'improving', 'declining', 'stable'
    seasonality_factor DECIMAL(4,3),
    anomaly_score DECIMAL(4,3), -- How unusual this review is
    
    -- Business Metrics
    customer_lifetime_value_impact DECIMAL(10,2),
    churn_risk_score DECIMAL(4,3),
    upsell_opportunity BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Collection Jobs (Track Data Collection Tasks)
CREATE TABLE IF NOT EXISTS collection_jobs (
    id SERIAL PRIMARY KEY,
    job_uuid UUID DEFAULT uuid_generate_v4(),
    product_id INTEGER REFERENCES products(id),
    platform_id INTEGER REFERENCES platforms(id),
    
    -- Job Configuration
    job_type VARCHAR(30) DEFAULT 'full_collection', -- 'full_collection', 'incremental', 'monitoring'
    parameters JSONB, -- Store collection parameters (country, max_reviews, etc.)
    
    -- Progress Tracking
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    total_reviews_found INTEGER,
    reviews_collected INTEGER DEFAULT 0,
    reviews_processed INTEGER DEFAULT 0,
    reviews_failed INTEGER DEFAULT 0,
    
    -- Performance Metrics
    collection_rate_per_minute DECIMAL(8,2),
    processing_rate_per_minute DECIMAL(8,2),
    
    -- Error Handling
    error_message TEXT,
    error_count INTEGER DEFAULT 0,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Scheduling
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    
    -- Metadata
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Platform Configuration (Dynamic Settings)
CREATE TABLE IF NOT EXISTS platform_configs (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT false, -- For API keys, passwords
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(platform_id, config_key)
);

-- 8. Review Trends (Aggregated Data for Performance)
CREATE TABLE IF NOT EXISTS review_trends (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    platform_id INTEGER REFERENCES platforms(id) ON DELETE CASCADE,
    
    -- Time Period
    period_type VARCHAR(10) NOT NULL, -- 'daily', 'weekly', 'monthly'
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Aggregated Metrics
    total_reviews INTEGER DEFAULT 0,
    average_rating DECIMAL(3,2),
    rating_distribution JSONB, -- {'1': 10, '2': 5, '3': 15, '4': 30, '5': 40}
    
    -- Sentiment Metrics
    positive_reviews INTEGER DEFAULT 0,
    negative_reviews INTEGER DEFAULT 0,
    neutral_reviews INTEGER DEFAULT 0,
    average_sentiment DECIMAL(4,3),
    
    -- Topic Trends
    trending_topics JSONB,
    trending_issues JSONB,
    trending_features JSONB,
    
    -- Competitive Intelligence
    competitor_mention_count INTEGER DEFAULT 0,
    switching_intent_count INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(product_id, platform_id, period_type, period_start)
);

-- 9. AI Models Configuration
CREATE TABLE IF NOT EXISTS ai_models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    version VARCHAR(20) NOT NULL,
    model_type VARCHAR(30) NOT NULL, -- 'sentiment', 'topic', 'classification', etc.
    provider VARCHAR(50), -- 'openai', 'anthropic', 'local', etc.
    endpoint_url VARCHAR(255),
    model_config JSONB,
    performance_metrics JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_reviews_product_platform ON reviews(product_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_reviews_rating ON reviews(rating);
CREATE INDEX IF NOT EXISTS idx_reviews_country ON reviews(country_code);
CREATE INDEX IF NOT EXISTS idx_reviews_processing ON reviews(processed_at);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_status ON collection_jobs(status);
CREATE INDEX IF NOT EXISTS idx_collection_jobs_product_platform ON collection_jobs(product_id, platform_id);
CREATE INDEX IF NOT EXISTS idx_trends_period ON review_trends(period_type, period_start);

-- Create GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_reviews_topics_gin ON reviews USING GIN(key_topics);
CREATE INDEX IF NOT EXISTS idx_reviews_issues_gin ON reviews USING GIN(issues_mentioned);
CREATE INDEX IF NOT EXISTS idx_reviews_features_gin ON reviews USING GIN(features_mentioned);
CREATE INDEX IF NOT EXISTS idx_analysis_emotions_gin ON review_analysis USING GIN(emotion_scores);
CREATE INDEX IF NOT EXISTS idx_analysis_aspects_gin ON review_analysis USING GIN(aspect_sentiment);

-- Row Level Security (RLS) Setup for Supabase
ALTER TABLE platforms ENABLE ROW LEVEL SECURITY;
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE collection_jobs ENABLE ROW LEVEL SECURITY;

-- Basic RLS Policies (adjust based on your authentication needs)
CREATE POLICY "Enable read access for all users" ON platforms FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON products FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON reviews FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON review_analysis FOR SELECT USING (true);

-- Add helpful comments
COMMENT ON TABLE reviews IS 'Main table storing all collected reviews from various platforms';
COMMENT ON TABLE review_analysis IS 'Advanced AI-powered analysis of reviews including sentiment, topics, and business intelligence';
COMMENT ON TABLE collection_jobs IS 'Tracks data collection jobs and their progress';
COMMENT ON TABLE review_trends IS 'Aggregated review data for performance and trend analysis';
