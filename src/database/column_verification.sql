-- 📊 COLUMN VERIFICATION QUERIES
-- Compare Initial Load vs AI Processing columns

-- ============================================================================
-- 1. INITIAL DATA LOAD COLUMNS (From Review Collection)
-- ============================================================================

-- Check what columns are populated during initial collection
SELECT 
    'INITIAL LOAD COLUMNS' as phase,
    COUNT(CASE WHEN content IS NOT NULL AND content != '' THEN 1 END) as content_filled,
    COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) as rating_filled,
    COUNT(CASE WHEN review_date IS NOT NULL THEN 1 END) as review_date_filled,
    COUNT(CASE WHEN product_id IS NOT NULL THEN 1 END) as product_id_filled,
    COUNT(CASE WHEN platform_id IS NOT NULL THEN 1 END) as platform_id_filled,
    COUNT(CASE WHEN platform_review_id IS NOT NULL THEN 1 END) as platform_review_id_filled,
    COUNT(CASE WHEN author_name IS NOT NULL THEN 1 END) as author_name_filled,
    COUNT(*) as total_reviews
FROM reviews;

-- Sample of initial load data (before AI processing)
SELECT 
    id,
    LEFT(content, 50) || '...' as content_preview,
    rating,
    review_date,
    product_id,
    platform_id,
    platform_review_id,
    processed_at  -- Should be NULL for unprocessed
FROM reviews 
WHERE processed_at IS NULL
LIMIT 5;

-- ============================================================================
-- 2. AI PROCESSING COLUMNS (From AI Analysis)
-- ============================================================================

-- Check what columns are populated during AI processing
SELECT 
    'AI PROCESSING COLUMNS' as phase,
    COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) as sentiment_score_filled,
    COUNT(CASE WHEN sentiment_label IS NOT NULL THEN 1 END) as sentiment_label_filled,
    COUNT(CASE WHEN confidence_score IS NOT NULL THEN 1 END) as confidence_score_filled,
    COUNT(CASE WHEN key_topics IS NOT NULL AND key_topics != '[]' THEN 1 END) as key_topics_filled,
    COUNT(CASE WHEN issues_mentioned IS NOT NULL AND issues_mentioned != '[]' THEN 1 END) as issues_mentioned_filled,
    COUNT(CASE WHEN priority_level IS NOT NULL THEN 1 END) as priority_level_filled,
    COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) as processed_at_filled,
    COUNT(CASE WHEN ai_model_used IS NOT NULL THEN 1 END) as ai_model_used_filled,
    COUNT(*) as total_reviews
FROM reviews;

-- Sample of AI processed data
SELECT 
    id,
    LEFT(content, 50) || '...' as content_preview,
    sentiment_label,
    sentiment_score,
    confidence_score,
    key_topics,
    issues_mentioned,
    priority_level,
    ai_model_used,
    processing_version,
    processed_at
FROM reviews 
WHERE processed_at IS NOT NULL
ORDER BY processed_at DESC
LIMIT 5;

-- ============================================================================
-- 3. PROCESSING PIPELINE STATUS
-- ============================================================================

-- Show the progression from initial load to AI processing
SELECT 
    'Pipeline Status' as stage,
    COUNT(*) as total_reviews,
    COUNT(CASE WHEN content IS NOT NULL AND content != '' THEN 1 END) as has_content,
    COUNT(CASE WHEN processed_at IS NULL THEN 1 END) as awaiting_ai_processing,
    COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) as ai_processed,
    ROUND(
        COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2
    ) as ai_processing_percentage
FROM reviews;

-- ============================================================================
-- 4. COLUMN FILL RATES BY PROCESSING STAGE
-- ============================================================================

-- Compare fill rates for unprocessed vs processed reviews
SELECT 
    CASE 
        WHEN processed_at IS NULL THEN 'UNPROCESSED (Initial Load Only)'
        ELSE 'PROCESSED (Initial + AI)'
    END as processing_stage,
    COUNT(*) as review_count,
    
    -- Initial load columns (should be high for both)
    ROUND(COUNT(CASE WHEN content IS NOT NULL AND content != '' THEN 1 END) * 100.0 / COUNT(*), 1) as content_fill_rate,
    ROUND(COUNT(CASE WHEN rating IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as rating_fill_rate,
    ROUND(COUNT(CASE WHEN product_id IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as product_id_fill_rate,
    
    -- AI processing columns (should be 0% for unprocessed, high for processed)
    ROUND(COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as sentiment_fill_rate,
    ROUND(COUNT(CASE WHEN key_topics IS NOT NULL AND key_topics != '[]' THEN 1 END) * 100.0 / COUNT(*), 1) as topics_fill_rate,
    ROUND(COUNT(CASE WHEN confidence_score IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 1) as confidence_fill_rate
    
FROM reviews
GROUP BY 
    CASE 
        WHEN processed_at IS NULL THEN 'UNPROCESSED (Initial Load Only)'
        ELSE 'PROCESSED (Initial + AI)'
    END
ORDER BY processing_stage;

-- ============================================================================
-- 5. AI MODEL USAGE TRACKING
-- ============================================================================

-- Show which AI models and versions are being used
SELECT 
    ai_model_used,
    processing_version,
    COUNT(*) as reviews_processed,
    MIN(processed_at) as first_processed,
    MAX(processed_at) as last_processed,
    ROUND(AVG(confidence_score), 3) as avg_confidence
FROM reviews 
WHERE processed_at IS NOT NULL
GROUP BY ai_model_used, processing_version
ORDER BY COUNT(*) DESC;

-- ============================================================================
-- 6. DATA QUALITY BY PHASE
-- ============================================================================

-- Check data quality at each phase
SELECT 
    'Initial Load Quality' as phase,
    COUNT(*) as total_reviews,
    COUNT(CASE WHEN content IS NULL OR content = '' THEN 1 END) as missing_content,
    COUNT(CASE WHEN rating IS NULL THEN 1 END) as missing_rating,
    COUNT(CASE WHEN product_id IS NULL THEN 1 END) as missing_product_id,
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN content IS NULL OR content = '' OR rating IS NULL OR product_id IS NULL THEN 1 END)) * 100.0 / COUNT(*), 2
    ) as quality_percentage
FROM reviews

UNION ALL

SELECT 
    'AI Processing Quality' as phase,
    COUNT(*) as total_processed,
    COUNT(CASE WHEN sentiment_score IS NULL THEN 1 END) as missing_sentiment,
    COUNT(CASE WHEN confidence_score IS NULL THEN 1 END) as missing_confidence,
    COUNT(CASE WHEN key_topics IS NULL OR key_topics = '[]' THEN 1 END) as missing_topics,
    ROUND(
        (COUNT(*) - COUNT(CASE WHEN sentiment_score IS NULL OR confidence_score IS NULL THEN 1 END)) * 100.0 / COUNT(*), 2
    ) as quality_percentage
FROM reviews
WHERE processed_at IS NOT NULL;

-- ============================================================================
-- 7. RECENT PROCESSING ACTIVITY
-- ============================================================================

-- Show recent AI processing activity
SELECT 
    DATE(processed_at) as processing_date,
    COUNT(*) as reviews_processed_today,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment_today,
    ROUND(AVG(confidence_score), 3) as avg_confidence_today,
    STRING_AGG(DISTINCT ai_model_used, ', ') as models_used
FROM reviews 
WHERE processed_at IS NOT NULL
AND processed_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(processed_at)
ORDER BY processing_date DESC;
