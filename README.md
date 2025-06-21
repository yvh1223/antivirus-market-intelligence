# 🛡️ Consumer Security Analysis Platform

**AI-Powered Competitive Intelligence for Antivirus Products**

[![Processing Status](https://img.shields.io/badge/AI%20Processing-Active-brightgreen)](/) [![Data Quality](https://img.shields.io/badge/Data%20Quality-Excellent-brightgreen)](/) [![Success Rate](https://img.shields.io/badge/Success%20Rate-100%25-brightgreen)](/)

> **Enterprise-grade competitive intelligence platform analyzing 200K+ antivirus product reviews using OpenAI GPT-4o-mini for comprehensive market insights.**

---

## 🚀 **Quick Start**

```bash
# 1. Check current data status
python check_data_simple.py

# 2. Start AI processing (recommended)
python parallel_processor.py

# 3. Monitor progress (optional - separate terminal)
python progress_monitor.py
```

---

## 📊 **Comprehensive Data Collection**

### **All Major Antivirus Products - Complete Platform Coverage**

| Product | Company | Apple Store ID | Google Play ID |
|---------|---------|----------------|----------------|
| **Norton 360** | NorTech (Broadcom) | `724596345` | `com.symantec.mobilesecurity` |
| **McAfee Total Protection** | McAfee | `520234411` | `com.wsandroid.suite` |
| **Bitdefender Total Security** | Bitdefender | `1127716399` | `com.bitdefender.security` |
| **Kaspersky Internet Security** | Kaspersky | `1430738996` | `com.kms.free` |
| **AVG AntiVirus** | AVG (Avast) | `519235025` | `com.antivirus` |
| **Avast Free Antivirus** | Avast | `793096595` | `com.avast.android.mobilesecurity` |
| **ESET Internet Security** | ESET | `1091665828` | `com.eset.ems2.gp` |
| **Trend Micro Maximum Security** | Trend Micro | `1006214921` | `com.trendmicro.tmmms` |
| **Malwarebytes Premium** | Malwarebytes | `1327105431` | `org.malwarebytes.antimalware` |
| **F-Secure SAFE** | F-Secure | `771097804` | `com.fsecure.ms.dc` |
| **Sophos Intercept X** | Sophos | `1168395491` | `com.sophos.smsec` |

### **Complete Cross-Platform Data Collection**

```bash
# Extract ALL major products from BOTH platforms
python -c "
from src.enhanced_wrapper import fetch

# All major products with both platform IDs
all_products = [
    ('Norton 360', 'NorTech (Broadcom)', '724596345', 'com.symantec.mobilesecurity'),
    ('McAfee Total Protection', 'McAfee', '520234411', 'com.wsandroid.suite'),
    ('Bitdefender Total Security', 'Bitdefender', '1127716399', 'com.bitdefender.security'),
    ('Kaspersky Internet Security', 'Kaspersky', '1430738996', 'com.kms.free'),
    ('AVG AntiVirus', 'AVG (Avast)', '519235025', 'com.antivirus'),
    ('Avast Free Antivirus', 'Avast', '793096595', 'com.avast.android.mobilesecurity'),
    ('ESET Internet Security', 'ESET', '1091665828', 'com.eset.ems2.gp'),
    ('Trend Micro Maximum Security', 'Trend Micro', '1006214921', 'com.trendmicro.tmmms'),
    ('Malwarebytes Premium', 'Malwarebytes', '1327105431', 'org.malwarebytes.antimalware'),
    ('F-Secure SAFE', 'F-Secure', '771097804', 'com.fsecure.ms.dc'),
    ('Sophos Intercept X', 'Sophos', '1168395491', 'com.sophos.smsec')
]

print('🌐 COMPLETE CROSS-PLATFORM DATA EXTRACTION')
print('=' * 60)
grand_total = 0

for product_name, company, apple_id, google_id in all_products:
    print(f'🛡️ {product_name} by {company}')
    
    # Apple Store
    apple_result = fetch('apple', apple_id, max_reviews=5000, 
                         product_name=product_name, company=company, country='us')
    apple_count = apple_result['reviews_collected']
    
    # Google Play
    google_result = fetch('google', google_id, max_reviews=10000, 
                          product_name=product_name, company=company, country='us')
    google_count = google_result['reviews_collected']
    
    product_total = apple_count + google_count
    grand_total += product_total
    
    print(f'   📱 Apple: {apple_count:,} | 🤖 Google: {google_count:,} | 🎯 Total: {product_total:,}')

print(f'🏆 GRAND TOTAL: {grand_total:,} reviews collected across all products and platforms')
"
```

### **Apple Store - All Products**

```bash
# Extract from Apple App Store for all major products
python -c "
from src.enhanced_wrapper import fetch

products_apple = [
    ('724596345', 'Norton 360', 'NorTech (Broadcom)'),
    ('520234411', 'McAfee Total Protection', 'McAfee'),
    ('1127716399', 'Bitdefender Total Security', 'Bitdefender'),
    ('1430738996', 'Kaspersky Internet Security', 'Kaspersky'),
    ('519235025', 'AVG AntiVirus', 'AVG (Avast)'),
    ('793096595', 'Avast Free Antivirus', 'Avast'),
    ('1091665828', 'ESET Internet Security', 'ESET'),
    ('1006214921', 'Trend Micro Maximum Security', 'Trend Micro'),
    ('1327105431', 'Malwarebytes Premium', 'Malwarebytes'),
    ('771097804', 'F-Secure SAFE', 'F-Secure'),
    ('1168395491', 'Sophos Intercept X', 'Sophos')
]

print('📱 APPLE APP STORE - ALL PRODUCTS')
print('=' * 50)
total_collected = 0

for app_id, product_name, company in products_apple:
    print(f'🔄 Collecting {product_name}...')
    result = fetch('apple', app_id, max_reviews=5000, 
                   product_name=product_name, company=company, country='us')
    collected = result['reviews_collected']
    total_collected += collected
    print(f'   ✅ {product_name}: {collected:,} reviews')
    
print(f'🎯 APPLE TOTAL: {total_collected:,} reviews')
"
```

### **Google Play - All Products**

```bash
# Extract from Google Play Store for all major products
python -c "
from src.enhanced_wrapper import fetch

products_google = [
    ('com.symantec.mobilesecurity', 'Norton 360', 'NorTech (Broadcom)'),
    ('com.wsandroid.suite', 'McAfee Total Protection', 'McAfee'),
    ('com.bitdefender.security', 'Bitdefender Total Security', 'Bitdefender'),
    ('com.kms.free', 'Kaspersky Internet Security', 'Kaspersky'),
    ('com.antivirus', 'AVG AntiVirus', 'AVG (Avast)'),
    ('com.avast.android.mobilesecurity', 'Avast Free Antivirus', 'Avast'),
    ('com.eset.ems2.gp', 'ESET Internet Security', 'ESET'),
    ('com.trendmicro.tmmms', 'Trend Micro Maximum Security', 'Trend Micro'),
    ('org.malwarebytes.antimalware', 'Malwarebytes Premium', 'Malwarebytes'),
    ('com.fsecure.ms.dc', 'F-Secure SAFE', 'F-Secure'),
    ('com.sophos.smsec', 'Sophos Intercept X', 'Sophos')
]

print('🤖 GOOGLE PLAY STORE - ALL PRODUCTS')
print('=' * 50)
total_collected = 0

for app_id, product_name, company in products_google:
    print(f'🔄 Collecting {product_name}...')
    result = fetch('google', app_id, max_reviews=10000, 
                   product_name=product_name, company=company, country='us')
    collected = result['reviews_collected']
    total_collected += collected
    print(f'   ✅ {product_name}: {collected:,} reviews')
    
print(f'🎯 GOOGLE TOTAL: {total_collected:,} reviews')
"
```

### **Regional Market Collection**

```bash
# Collect reviews from multiple countries for market analysis
python -c "
from src.enhanced_wrapper import fetch

# Target countries for analysis
countries = ['us', 'gb', 'ca', 'au', 'de', 'fr', 'jp']
country_names = {'us': 'United States', 'gb': 'United Kingdom', 'ca': 'Canada', 
                'au': 'Australia', 'de': 'Germany', 'fr': 'France', 'jp': 'Japan'}

# Focus on top 3 products for regional analysis
top_products = [
    ('724596345', 'Norton 360', 'NorTech (Broadcom)'),
    ('520234411', 'McAfee Total Protection', 'McAfee'),
    ('1127716399', 'Bitdefender Total Security', 'Bitdefender')
]

print('🌍 REGIONAL MARKET DATA EXTRACTION')
print('=' * 50)

for app_id, product_name, company in top_products:
    print(f'🛡️ {product_name} - Regional Collection')
    product_total = 0
    
    for country in countries:
        result = fetch('apple', app_id, max_reviews=1000, 
                      product_name=f'{product_name} ({country_names[country]})', 
                      company=company, country=country)
        collected = result['reviews_collected']
        product_total += collected
        print(f'   🌐 {country_names[country]}: {collected:,} reviews')
    
    print(f'   🎯 {product_name} Total: {product_total:,} reviews')
"
```

### **Quick Start - Top 3 Products**

```bash
# Quick setup: Load reviews for the top 3 antivirus products
python -c "
from src.enhanced_wrapper import fetch

# Top 3 products for quick start
quick_products = [
    ('Norton 360', 'NorTech (Broadcom)', '724596345', 'com.symantec.mobilesecurity'),
    ('McAfee Total Protection', 'McAfee', '520234411', 'com.wsandroid.suite'),
    ('Bitdefender Total Security', 'Bitdefender', '1127716399', 'com.bitdefender.security')
]

print('🚀 QUICK START - TOP 3 ANTIVIRUS PRODUCTS')
print('=' * 60)

for product_name, company, apple_id, google_id in quick_products:
    print(f'🛡️ {product_name} by {company}')
    
    # Apple Store
    apple_result = fetch('apple', apple_id, max_reviews=3000, 
                        product_name=product_name, company=company)
    
    # Google Play
    google_result = fetch('google', google_id, max_reviews=7000, 
                         product_name=product_name, company=company)
    
    total = apple_result['reviews_collected'] + google_result['reviews_collected']
    print(f'   📱 Apple: {apple_result["reviews_collected"]:,} | 🤖 Google: {google_result["reviews_collected"]:,} | 🎯 Total: {total:,}')
"
```

### **Verify Data Collection**

```bash
# Check what data was successfully loaded
python -c "
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

print('📊 DATA COLLECTION VERIFICATION')
print('=' * 50)

# Get all products and their review counts
products = supabase.table('products').select('id, name, company').execute().data
total_reviews = 0

for product in products:
    count_result = supabase.table('reviews').select('id', count='exact').eq('product_id', product['id']).execute()
    count = count_result.count
    total_reviews += count
    
    if count > 0:
        print(f'✅ {product["name"]} by {product["company"]}: {count:,} reviews')
    else:
        print(f'⭕ {product["name"]} by {product["company"]}: No reviews yet')

print(f'🎯 TOTAL REVIEWS IN DATABASE: {total_reviews:,}')

# Platform breakdown
platforms_result = supabase.table('platforms').select('id, display_name').execute()
for platform in platforms_result.data:
    platform_count = supabase.table('reviews').select('id', count='exact').eq('platform_id', platform['id']).execute()
    print(f'📱 {platform["display_name"]}: {platform_count.count:,} reviews')
"
```

---

## 🤖 **AI Data Processing**

### **Parallel Processing by Product (Recommended)**

Process reviews efficiently using the parallel processor that allows you to focus on specific products:

```bash
# Process specific products in parallel (run in separate terminals for maximum speed)
python parallel_processor.py

# Available options:
# 1. Norton
# 2. Bitdefender  
# 3. Kaspersky
# 4. AVG
# 5. Avast
# 6. ESET
# 7. Trend Micro
# 8. Malwarebytes

# Processing size options:
# 1. Test run (250 reviews) - ~10 minutes
# 2. Small run (1,000 reviews) - ~30 minutes  
# 3. Medium run (5,000 reviews) - ~2-3 hours
# 4. Large run (25,000 reviews) - ~10-12 hours
# 5. Full processing (all reviews for that product) - varies by product size
```

### **Multi-Terminal Parallel Processing**

For maximum processing speed, run multiple instances in separate terminals:

```bash
# Terminal 1: Process Norton reviews
python parallel_processor.py
# Choose: 1 (Norton) → 5 (Full processing)

# Terminal 2: Process McAfee reviews  
python parallel_processor.py
# Choose: 2 (Bitdefender) → 5 (Full processing)

# Terminal 3: Process Bitdefender reviews
python parallel_processor.py
# Choose: 3 (Kaspersky) → 5 (Full processing)

# This approach processes multiple products simultaneously for faster completion
```

### **Processing Features**
- ✅ **Year Priority**: Processes 2025 → 2024 → 2023 → older reviews
- ✅ **Real AI Analysis**: Uses OpenAI GPT-4o-mini for sentiment analysis
- ✅ **Progress Tracking**: Shows real-time progress and success rates
- ✅ **Error Handling**: Robust retry logic and quality validation
- ✅ **Resumable**: Can stop and restart processing at any time

### **Monitor Processing Progress**

```bash
# Real-time progress monitoring (run in separate terminal)
python progress_monitor.py

# Quick status check
python check_data_simple.py
```

---

## 📊 **Current Status**

### **Dataset Coverage**
- **Norton 360** (NorTech/Broadcom) - 100,000 reviews
- **McAfee Total Protection** (McAfee) - 100,000 reviews  
- **Bitdefender Total Security** (Bitdefender) - Reviews loaded
- **Kaspersky Internet Security** (Kaspersky) - 500 reviews
- **AVG, Avast, ESET, Trend Micro, Malwarebytes** - Reviews loaded

### **Data Quality Metrics**
- ✅ **200,272 reviews** collected and cleaned
- ✅ **1,000+ reviews** processed with AI analysis
- ✅ **100% processing success rate**
- ✅ **0.832 confidence average** (excellent quality)

### **Sentiment Distribution** (Current Sample)
- **Positive**: 869 reviews (86.9%)
- **Negative**: 68 reviews (6.8%)
- **Neutral**: 35 reviews (3.5%)
- **Mixed/Other**: 28 reviews (2.8%)

---

## 🗄️ **Database Schema**

### **Review Collection Columns**
```sql
content              TEXT    -- Review text content (main AI input)
rating               INTEGER -- User rating (1-5 stars)
review_date          DATE    -- When review was posted
product_id           INTEGER -- Links to products table
platform_id          INTEGER -- Links to platforms table
platform_review_id   TEXT    -- Unique ID from source platform
author_name          TEXT    -- Reviewer name (if available)
```

### **AI Analysis Columns**
```sql
sentiment_score      FLOAT   -- -1.0 to 1.0 sentiment rating
sentiment_label      TEXT    -- positive/negative/neutral
confidence_score     FLOAT   -- 0.0 to 1.0 AI confidence
key_topics          JSON    -- ["performance", "ui", "support"]
issues_mentioned    JSON    -- ["slow_scanning", "false_positives"]
priority_level      TEXT    -- low/medium/high business impact
processed_at        TIMESTAMP -- When AI analysis completed
ai_model_used       TEXT    -- "gpt-4o-mini"
processing_version  TEXT    -- "3.0"
```

---

## 🛠️ **Setup & Configuration**

### **Environment Setup**
```bash
# Clone and setup
cd consumer-security-analysis-v3

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your credentials
```

### **Required Configuration**
```bash
# Database (Supabase)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

# AI Processing (OpenAI)
OPENAI_API_KEY=your_openai_api_key
```

---

## 📈 **Business Intelligence**

### **AI Analysis Features**
- **Sentiment Analysis**: -1.0 to 1.0 sentiment scoring with labels
- **Content Intelligence**: Key topics and issues extraction
- **Priority Assessment**: Business impact evaluation (low/medium/high)
- **Quality Assurance**: 0.832 average confidence score

### **Competitive Insights**
- Product sentiment comparison across competitors
- Feature satisfaction benchmarking
- Customer pain point identification
- Market positioning analysis

---

## 🔄 **Project Status: Production Ready**

This platform is currently **actively processing** with:
- ✅ **Proven reliability** (100% success rate)
- ✅ **Production-grade quality** (enterprise-level AI analysis)
- ✅ **Scalable architecture** (handles 200K+ reviews)
- ✅ **Real-time insights** (continuous competitive intelligence)

**The system is generating actual business intelligence from antivirus market data!** 🚀

---

*Last Updated: June 20, 2025 | Status: Active Production Processing*