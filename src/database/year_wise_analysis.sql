-- 📊 COMPREHENSIVE YEAR-WISE ANALYSIS WITH AI DATA
-- Year-wise counts, feedback data, and AI column status

-- ============================================================================
-- 1. PRODUCT OVERVIEW WITH DATE RANGES (Your Base Query Enhanced)
-- ============================================================================

SELECT 
    p.id, 
    p.name,
    p.company, 
    p.category,
    COUNT(r.id) as existing_reviews,
    MIN(r.review_date) as MIN_review_date,
    MAX(r.review_date) as MAX_review_date,
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as ai_processed_reviews,
    COUNT(CASE WHEN r.processed_at IS NULL THEN 1 END) as unprocessed_reviews,
    ROUND(
        COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) * 100.0 / 
        NULLIF(COUNT(r.id), 0), 2
    ) as ai_processing_percentage
FROM products p 
LEFT JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
GROUP BY p.id, p.name, p.company, p.category 
ORDER BY p.company, p.name;

-- ============================================================================
-- 2. YEAR-WISE REVIEW COUNTS BY PRODUCT
-- ============================================================================

SELECT 
    p.id as product_id,
    p.name as product_name,
    p.company,
    EXTRACT(YEAR FROM r.review_date) as review_year,
    COUNT(r.id) as total_reviews,
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as ai_processed,
    COUNT(CASE WHEN r.processed_at IS NULL THEN 1 END) as unprocessed,
    ROUND(AVG(r.rating), 2) as avg_rating,
    ROUND(
        COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) * 100.0 / 
        COUNT(r.id), 2
    ) as processing_percentage
FROM products p 
LEFT JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.review_date IS NOT NULL
GROUP BY p.id, p.name, p.company, EXTRACT(YEAR FROM r.review_date)
ORDER BY p.company, p.name, review_year DESC;

-- ============================================================================
-- 3. DETAILED YEAR-WISE BREAKDOWN WITH AI ANALYSIS STATUS
-- ============================================================================

SELECT 
    p.company,
    p.name as product_name,
    EXTRACT(YEAR FROM r.review_date) as year,
    COUNT(r.id) as total_reviews,
    
    -- Processing status
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as ai_processed,
    COUNT(CASE WHEN r.processed_at IS NULL THEN 1 END) as pending_ai,
    
    -- AI analysis completeness
    COUNT(CASE WHEN r.sentiment_score IS NOT NULL THEN 1 END) as has_sentiment,
    COUNT(CASE WHEN r.key_topics IS NOT NULL AND r.key_topics != '[]' THEN 1 END) as has_topics,
    COUNT(CASE WHEN r.issues_mentioned IS NOT NULL AND r.issues_mentioned != '[]' THEN 1 END) as has_issues,
    
    -- Sentiment distribution
    COUNT(CASE WHEN r.sentiment_label = 'positive' THEN 1 END) as positive_sentiment,
    COUNT(CASE WHEN r.sentiment_label = 'negative' THEN 1 END) as negative_sentiment,
    COUNT(CASE WHEN r.sentiment_label = 'neutral' THEN 1 END) as neutral_sentiment,
    
    -- Rating analysis
    ROUND(AVG(r.rating), 2) as avg_rating,
    COUNT(CASE WHEN r.rating = 5 THEN 1 END) as five_star,
    COUNT(CASE WHEN r.rating = 4 THEN 1 END) as four_star,
    COUNT(CASE WHEN r.rating = 3 THEN 1 END) as three_star,
    COUNT(CASE WHEN r.rating = 2 THEN 1 END) as two_star,
    COUNT(CASE WHEN r.rating = 1 THEN 1 END) as one_star,
    
    -- AI quality metrics
    ROUND(AVG(r.sentiment_score), 3) as avg_ai_sentiment,
    ROUND(AVG(r.confidence_score), 3) as avg_ai_confidence
    
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.review_date IS NOT NULL
GROUP BY p.company, p.name, EXTRACT(YEAR FROM r.review_date)
ORDER BY p.company, p.name, year DESC;

-- ============================================================================
-- 4. AI PROCESSING PRIORITY ANALYSIS (2025 → 2024 → 2023)
-- ============================================================================

WITH priority_years AS (
    SELECT 2025 as year, 1 as priority
    UNION SELECT 2024, 2
    UNION SELECT 2023, 3
    UNION SELECT 2022, 4
    UNION SELECT 2021, 5
),
company_priority AS (
    SELECT 'McAfee' as company_pattern, 1 as priority
    UNION SELECT 'Norton', 2
    UNION SELECT 'NorTech', 2
    UNION SELECT 'Broadcom', 2
    UNION SELECT 'Bitdefender', 3
)

SELECT 
    py.priority as year_priority,
    EXTRACT(YEAR FROM r.review_date) as year,
    cp.priority as company_priority,
    p.company,
    p.name as product_name,
    COUNT(r.id) as total_reviews,
    COUNT(CASE WHEN r.processed_at IS NULL THEN 1 END) as unprocessed_reviews,
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as ai_processed_reviews,
    ROUND(
        COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) * 100.0 / 
        COUNT(r.id), 2
    ) as processing_percentage
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
LEFT JOIN priority_years py ON EXTRACT(YEAR FROM r.review_date) = py.year
LEFT JOIN company_priority cp ON p.company ILIKE '%' || cp.company_pattern || '%'
WHERE p.id IN (21, 22, 23)
AND r.review_date IS NOT NULL
GROUP BY py.priority, EXTRACT(YEAR FROM r.review_date), cp.priority, p.company, p.name
ORDER BY 
    COALESCE(py.priority, 999), -- Prioritized years first, then others
    COALESCE(cp.priority, 999), -- McAfee → Norton → Bitdefender
    p.name;

-- ============================================================================
-- 5. MONTHLY BREAKDOWN FOR RECENT YEARS (2023-2025)
-- ============================================================================

SELECT 
    p.company,
    p.name as product_name,
    EXTRACT(YEAR FROM r.review_date) as year,
    EXTRACT(MONTH FROM r.review_date) as month,
    TO_CHAR(r.review_date, 'YYYY-MM') as year_month,
    COUNT(r.id) as total_reviews,
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as ai_processed,
    ROUND(AVG(r.rating), 2) as avg_rating,
    ROUND(AVG(r.sentiment_score), 3) as avg_sentiment
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND EXTRACT(YEAR FROM r.review_date) >= 2023
GROUP BY p.company, p.name, EXTRACT(YEAR FROM r.review_date), EXTRACT(MONTH FROM r.review_date), TO_CHAR(r.review_date, 'YYYY-MM')
ORDER BY p.company, p.name, year DESC, month DESC;

-- ============================================================================
-- 6. AI COLUMN COMPLETENESS BY YEAR
-- ============================================================================

SELECT 
    p.company,
    p.name as product_name,
    EXTRACT(YEAR FROM r.review_date) as year,
    COUNT(r.id) as total_reviews,
    
    -- AI processing status
    COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) as processed_count,
    ROUND(
        COUNT(CASE WHEN r.processed_at IS NOT NULL THEN 1 END) * 100.0 / 
        COUNT(r.id), 1
    ) as processing_percentage,
    
    -- AI column completeness (for processed reviews only)
    COUNT(CASE WHEN r.sentiment_score IS NOT NULL THEN 1 END) as has_sentiment_score,
    COUNT(CASE WHEN r.sentiment_label IS NOT NULL THEN 1 END) as has_sentiment_label,
    COUNT(CASE WHEN r.confidence_score IS NOT NULL THEN 1 END) as has_confidence_score,
    COUNT(CASE WHEN r.key_topics IS NOT NULL AND r.key_topics != '[]' THEN 1 END) as has_key_topics,
    COUNT(CASE WHEN r.issues_mentioned IS NOT NULL AND r.issues_mentioned != '[]' THEN 1 END) as has_issues_mentioned,
    COUNT(CASE WHEN r.priority_level IS NOT NULL THEN 1 END) as has_priority_level,
    
    -- AI model tracking
    STRING_AGG(DISTINCT r.ai_model_used, ', ') as ai_models_used,
    STRING_AGG(DISTINCT r.processing_version, ', ') as processing_versions_used
    
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.review_date IS NOT NULL
GROUP BY p.company, p.name, EXTRACT(YEAR FROM r.review_date)
ORDER BY p.company, p.name, year DESC;

-- ============================================================================
-- 7. UNPROCESSED REVIEWS PRIORITIZED FOR AI PROCESSING
-- ============================================================================

SELECT 
    'PRIORITY_' || 
    CASE 
        WHEN EXTRACT(YEAR FROM r.review_date) = 2025 THEN '1_2025'
        WHEN EXTRACT(YEAR FROM r.review_date) = 2024 THEN '2_2024'
        WHEN EXTRACT(YEAR FROM r.review_date) = 2023 THEN '3_2023'
        ELSE '4_OTHER'
    END ||
    CASE 
        WHEN p.company ILIKE '%McAfee%' THEN '_A_McAfee'
        WHEN p.company ILIKE '%Norton%' OR p.company ILIKE '%NorTech%' OR p.company ILIKE '%Broadcom%' THEN '_B_Norton'
        WHEN p.company ILIKE '%Bitdefender%' THEN '_C_Bitdefender'
        ELSE '_D_Other'
    END as processing_priority,
    
    p.company,
    p.name as product_name,
    EXTRACT(YEAR FROM r.review_date) as year,
    COUNT(r.id) as unprocessed_count,
    MIN(r.review_date) as oldest_unprocessed,
    MAX(r.review_date) as newest_unprocessed
    
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.processed_at IS NULL
AND r.review_date IS NOT NULL
GROUP BY 
    p.company, 
    p.name, 
    EXTRACT(YEAR FROM r.review_date),
    CASE 
        WHEN EXTRACT(YEAR FROM r.review_date) = 2025 THEN '1_2025'
        WHEN EXTRACT(YEAR FROM r.review_date) = 2024 THEN '2_2024'
        WHEN EXTRACT(YEAR FROM r.review_date) = 2023 THEN '3_2023'
        ELSE '4_OTHER'
    END,
    CASE 
        WHEN p.company ILIKE '%McAfee%' THEN '_A_McAfee'
        WHEN p.company ILIKE '%Norton%' OR p.company ILIKE '%NorTech%' OR p.company ILIKE '%Broadcom%' THEN '_B_Norton'
        WHEN p.company ILIKE '%Bitdefender%' THEN '_C_Bitdefender'
        ELSE '_D_Other'
    END
ORDER BY processing_priority, unprocessed_count DESC;

-- ============================================================================
-- 8. RECENT AI PROCESSING ACTIVITY (LAST 7 DAYS)
-- ============================================================================

SELECT 
    p.company,
    p.name as product_name,
    DATE(r.processed_at) as processing_date,
    COUNT(r.id) as reviews_processed,
    ROUND(AVG(r.sentiment_score), 3) as avg_sentiment,
    ROUND(AVG(r.confidence_score), 3) as avg_confidence,
    r.ai_model_used,
    r.processing_version
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.processed_at >= NOW() - INTERVAL '7 days'
GROUP BY p.company, p.name, DATE(r.processed_at), r.ai_model_used, r.processing_version
ORDER BY processing_date DESC, p.company, p.name;

-- ============================================================================
-- 9. SENTIMENT TRENDS BY YEAR AND PRODUCT
-- ============================================================================

SELECT 
    p.company,
    p.name as product_name,
    EXTRACT(YEAR FROM r.review_date) as year,
    COUNT(CASE WHEN r.sentiment_label = 'positive' THEN 1 END) as positive_count,
    COUNT(CASE WHEN r.sentiment_label = 'negative' THEN 1 END) as negative_count,
    COUNT(CASE WHEN r.sentiment_label = 'neutral' THEN 1 END) as neutral_count,
    ROUND(
        COUNT(CASE WHEN r.sentiment_label = 'positive' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(CASE WHEN r.sentiment_label IS NOT NULL THEN 1 END), 0), 1
    ) as positive_percentage,
    ROUND(AVG(r.sentiment_score), 3) as avg_sentiment_score,
    ROUND(AVG(r.rating), 2) as avg_user_rating
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.processed_at IS NOT NULL
AND r.sentiment_label IS NOT NULL
GROUP BY p.company, p.name, EXTRACT(YEAR FROM r.review_date)
ORDER BY p.company, p.name, year DESC;

-- ============================================================================
-- 10. PROCESSING QUEUE STATUS (NEXT REVIEWS TO PROCESS)
-- ============================================================================

SELECT 
    'Next_' || ROW_NUMBER() OVER (ORDER BY 
        CASE EXTRACT(YEAR FROM r.review_date)
            WHEN 2025 THEN 1
            WHEN 2024 THEN 2  
            WHEN 2023 THEN 3
            ELSE 4
        END,
        CASE 
            WHEN p.company ILIKE '%McAfee%' THEN 1
            WHEN p.company ILIKE '%Norton%' OR p.company ILIKE '%NorTech%' OR p.company ILIKE '%Broadcom%' THEN 2
            WHEN p.company ILIKE '%Bitdefender%' THEN 3
            ELSE 4
        END,
        r.review_date DESC
    ) as queue_position,
    r.id as review_id,
    p.company,
    p.name as product_name,
    EXTRACT(YEAR FROM r.review_date) as year,
    r.review_date,
    r.rating,
    LEFT(r.content, 100) || '...' as content_preview
FROM products p 
INNER JOIN reviews r ON p.id = r.product_id 
WHERE p.id IN (21, 22, 23)
AND r.processed_at IS NULL
AND r.content IS NOT NULL
AND r.content != ''
ORDER BY 
    CASE EXTRACT(YEAR FROM r.review_date)
        WHEN 2025 THEN 1
        WHEN 2024 THEN 2  
        WHEN 2023 THEN 3
        ELSE 4
    END,
    CASE 
        WHEN p.company ILIKE '%McAfee%' THEN 1
        WHEN p.company ILIKE '%Norton%' OR p.company ILIKE '%NorTech%' OR p.company ILIKE '%Broadcom%' THEN 2
        WHEN p.company ILIKE '%Bitdefender%' THEN 3
        ELSE 4
    END,
    r.review_date DESC
LIMIT 50;
