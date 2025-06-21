-- 🔍 AI OUTPUT VERIFICATION QUERIES
-- Use these in Supabase SQL Editor or any PostgreSQL client

-- ============================================================================
-- 1. OVERALL AI PROCESSING STATUS
-- ============================================================================

-- Check processing progress
SELECT 
    COUNT(*) as total_reviews,
    COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) as ai_processed,
    COUNT(CASE WHEN processed_at IS NULL THEN 1 END) as unprocessed,
    ROUND(
        COUNT(CASE WHEN processed_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(*), 2
    ) as processing_percentage
FROM reviews;

-- ============================================================================
-- 2. AI PROCESSING QUALITY CHECK
-- ============================================================================

-- Check AI analysis completeness
SELECT 
    COUNT(*) as total_processed,
    COUNT(CASE WHEN sentiment_score IS NOT NULL THEN 1 END) as has_sentiment_score,
    COUNT(CASE WHEN sentiment_label IS NOT NULL THEN 1 END) as has_sentiment_label,
    COUNT(CASE WHEN confidence_score IS NOT NULL THEN 1 END) as has_confidence_score,
    COUNT(CASE WHEN key_topics IS NOT NULL AND key_topics != '[]' THEN 1 END) as has_topics,
    COUNT(CASE WHEN issues_mentioned IS NOT NULL AND issues_mentioned != '[]' THEN 1 END) as has_issues,
    COUNT(CASE WHEN priority_level IS NOT NULL THEN 1 END) as has_priority_level,
    ai_model_used,
    processing_version
FROM reviews 
WHERE processed_at IS NOT NULL
GROUP BY ai_model_used, processing_version
ORDER BY COUNT(*) DESC;

-- ============================================================================
-- 3. SENTIMENT ANALYSIS DISTRIBUTION
-- ============================================================================

-- Sentiment distribution overview
SELECT 
    sentiment_label,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment_score,
    ROUND(AVG(confidence_score), 3) as avg_confidence
FROM reviews 
WHERE processed_at IS NOT NULL
GROUP BY sentiment_label
ORDER BY count DESC;

-- Sentiment score distribution (detailed)
SELECT 
    CASE 
        WHEN sentiment_score >= 0.7 THEN 'Very Positive (0.7 to 1.0)'
        WHEN sentiment_score >= 0.3 THEN 'Positive (0.3 to 0.7)'
        WHEN sentiment_score >= -0.3 THEN 'Neutral (-0.3 to 0.3)'
        WHEN sentiment_score >= -0.7 THEN 'Negative (-0.7 to -0.3)'
        ELSE 'Very Negative (-1.0 to -0.7)'
    END as sentiment_range,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM reviews 
WHERE processed_at IS NOT NULL AND sentiment_score IS NOT NULL
GROUP BY 
    CASE 
        WHEN sentiment_score >= 0.7 THEN 'Very Positive (0.7 to 1.0)'
        WHEN sentiment_score >= 0.3 THEN 'Positive (0.3 to 0.7)'
        WHEN sentiment_score >= -0.3 THEN 'Neutral (-0.3 to 0.3)'
        WHEN sentiment_score >= -0.7 THEN 'Negative (-0.7 to -0.3)'
        ELSE 'Very Negative (-1.0 to -0.7)'
    END
ORDER BY 
    CASE 
        WHEN sentiment_score >= 0.7 THEN 5
        WHEN sentiment_score >= 0.3 THEN 4
        WHEN sentiment_score >= -0.3 THEN 3
        WHEN sentiment_score >= -0.7 THEN 2
        ELSE 1
    END DESC;

-- ============================================================================
-- 4. PRODUCT-WISE AI ANALYSIS
-- ============================================================================

-- AI processing status by product
SELECT 
    p.name as product_name,
    p.company,
    COUNT(r.*) as total_reviews,
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as ai_processed,
    ROUND(
        COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) * 100.0 / COUNT(r.*), 2
    ) as processing_percentage,
    ROUND(AVG(CASE WHEN r.processed_at IS NOT NULL THEN r.sentiment_score END), 3) as avg_sentiment,
    COUNT(CASE WHEN r.sentiment_label = 'positive' THEN 1 END) as positive_reviews,
    COUNT(CASE WHEN r.sentiment_label = 'negative' THEN 1 END) as negative_reviews,
    COUNT(CASE WHEN r.sentiment_label = 'neutral' THEN 1 END) as neutral_reviews
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name, p.company
HAVING COUNT(r.*) > 0
ORDER BY ai_processed DESC;

-- ============================================================================
-- 5. KEY TOPICS ANALYSIS
-- ============================================================================

-- Most mentioned topics (AI extracted)
SELECT 
    topic,
    COUNT(*) as mention_count,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment_when_mentioned
FROM (
    SELECT 
        jsonb_array_elements_text(key_topics::jsonb) as topic,
        sentiment_score
    FROM reviews 
    WHERE processed_at IS NOT NULL 
    AND key_topics IS NOT NULL 
    AND key_topics != '[]'
) topics
GROUP BY topic
HAVING COUNT(*) >= 3  -- Only topics mentioned 3+ times
ORDER BY mention_count DESC
LIMIT 20;

-- ============================================================================
-- 6. ISSUES ANALYSIS
-- ============================================================================

-- Most mentioned issues (AI extracted)
SELECT 
    issue,
    COUNT(*) as mention_count,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment_when_mentioned,
    COUNT(CASE WHEN priority_level = 'high' THEN 1 END) as high_priority_mentions
FROM (
    SELECT 
        jsonb_array_elements_text(issues_mentioned::jsonb) as issue,
        sentiment_score,
        priority_level
    FROM reviews 
    WHERE processed_at IS NOT NULL 
    AND issues_mentioned IS NOT NULL 
    AND issues_mentioned != '[]'
) issues
GROUP BY issue
HAVING COUNT(*) >= 2  -- Only issues mentioned 2+ times
ORDER BY mention_count DESC
LIMIT 15;

-- ============================================================================
-- 7. PRIORITY LEVEL ANALYSIS
-- ============================================================================

-- Priority level distribution
SELECT 
    priority_level,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment
FROM reviews 
WHERE processed_at IS NOT NULL AND priority_level IS NOT NULL
GROUP BY priority_level
ORDER BY 
    CASE priority_level 
        WHEN 'high' THEN 3 
        WHEN 'medium' THEN 2 
        WHEN 'low' THEN 1 
    END DESC;

-- ============================================================================
-- 8. CONFIDENCE SCORE ANALYSIS
-- ============================================================================

-- AI confidence distribution
SELECT 
    CASE 
        WHEN confidence_score >= 0.9 THEN 'Very High (0.9-1.0)'
        WHEN confidence_score >= 0.7 THEN 'High (0.7-0.9)'
        WHEN confidence_score >= 0.5 THEN 'Medium (0.5-0.7)'
        WHEN confidence_score >= 0.3 THEN 'Low (0.3-0.5)'
        ELSE 'Very Low (0.0-0.3)'
    END as confidence_range,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
FROM reviews 
WHERE processed_at IS NOT NULL AND confidence_score IS NOT NULL
GROUP BY 
    CASE 
        WHEN confidence_score >= 0.9 THEN 'Very High (0.9-1.0)'
        WHEN confidence_score >= 0.7 THEN 'High (0.7-0.9)'
        WHEN confidence_score >= 0.5 THEN 'Medium (0.5-0.7)'
        WHEN confidence_score >= 0.3 THEN 'Low (0.3-0.5)'
        ELSE 'Very Low (0.0-0.3)'
    END
ORDER BY 
    CASE 
        WHEN confidence_score >= 0.9 THEN 5
        WHEN confidence_score >= 0.7 THEN 4
        WHEN confidence_score >= 0.5 THEN 3
        WHEN confidence_score >= 0.3 THEN 2
        ELSE 1
    END DESC;

-- ============================================================================
-- 9. SAMPLE AI PROCESSED REVIEWS
-- ============================================================================

-- Sample of well-processed reviews (high confidence)
SELECT 
    r.id,
    p.name as product,
    p.company,
    LEFT(r.content, 100) || '...' as content_preview,
    r.rating,
    r.sentiment_label,
    r.sentiment_score,
    r.confidence_score,
    r.key_topics,
    r.issues_mentioned,
    r.priority_level,
    r.processed_at
FROM reviews r
JOIN products p ON r.product_id = p.id
WHERE r.processed_at IS NOT NULL 
AND r.confidence_score >= 0.7
ORDER BY r.processed_at DESC
LIMIT 10;

-- Sample of concerning reviews (low confidence or issues)
SELECT 
    r.id,
    p.name as product,
    LEFT(r.content, 100) || '...' as content_preview,
    r.sentiment_label,
    r.sentiment_score,
    r.confidence_score,
    r.priority_level,
    r.issues_mentioned
FROM reviews r
JOIN products p ON r.product_id = p.id
WHERE r.processed_at IS NOT NULL 
AND (r.confidence_score < 0.5 OR r.priority_level = 'high')
ORDER BY r.confidence_score ASC, r.processed_at DESC
LIMIT 10;

-- ============================================================================
-- 10. PROCESSING TIMELINE
-- ============================================================================

-- Processing progress over time
SELECT 
    DATE(processed_at) as processing_date,
    COUNT(*) as reviews_processed,
    ROUND(AVG(sentiment_score), 3) as avg_sentiment,
    ROUND(AVG(confidence_score), 3) as avg_confidence
FROM reviews 
WHERE processed_at IS NOT NULL
GROUP BY DATE(processed_at)
ORDER BY processing_date DESC;

-- Recent processing activity (last 100 reviews)
SELECT 
    r.id,
    p.name as product,
    r.sentiment_label,
    r.sentiment_score,
    r.confidence_score,
    r.processed_at
FROM reviews r
JOIN products p ON r.product_id = p.id
WHERE r.processed_at IS NOT NULL
ORDER BY r.processed_at DESC
LIMIT 100;

-- ============================================================================
-- 11. DATA QUALITY CHECKS
-- ============================================================================

-- Check for incomplete AI processing
SELECT 
    'Missing sentiment_score' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL AND sentiment_score IS NULL

UNION ALL

SELECT 
    'Missing sentiment_label' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL AND sentiment_label IS NULL

UNION ALL

SELECT 
    'Missing confidence_score' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL AND confidence_score IS NULL

UNION ALL

SELECT 
    'Empty key_topics' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL AND (key_topics IS NULL OR key_topics = '[]')

UNION ALL

SELECT 
    'Empty issues_mentioned' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL AND (issues_mentioned IS NULL OR issues_mentioned = '[]')

ORDER BY count DESC;

-- Check for processing errors or anomalies
SELECT 
    'Sentiment score out of range' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL 
AND (sentiment_score < -1.0 OR sentiment_score > 1.0)

UNION ALL

SELECT 
    'Confidence score out of range' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL 
AND (confidence_score < 0.0 OR confidence_score > 1.0)

UNION ALL

SELECT 
    'Invalid sentiment_label' as issue,
    COUNT(*) as count
FROM reviews 
WHERE processed_at IS NOT NULL 
AND sentiment_label NOT IN ('positive', 'negative', 'neutral')

ORDER BY count DESC;
