#!/usr/bin/env python3
"""
Enhanced wrapper script that provides a cleaner interface and parses results
"""

import subprocess
import sys
import os
import logging
import re
from typing import Dict, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the script path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENHANCED_SCRIPT = os.path.join(SCRIPT_DIR, "data_collection", "enhanced_fetch_reviews.py")

def parse_collection_output(output: str) -> Dict[str, Any]:
    """Parse the collection script output to extract key metrics"""
    
    metrics = {
        'reviews_collected': 0,
        'total_found': 0,
        'job_id': None,
        'success': False
    }
    
    if not output:
        return metrics
    
    # Look for completion message
    if "Collection completed successfully!" in output:
        metrics['success'] = True
    
    # Extract job ID - look for both formats
    job_match = re.search(r'Job ID: (\d+)', output)
    if not job_match:
        job_match = re.search(r'collection job (\d+) for', output)
    if job_match:
        metrics['job_id'] = int(job_match.group(1))
    
    # Extract reviews collected - look for the final summary line
    collected_match = re.search(r'Reviews Collected: (\d+)', output)
    if collected_match:
        metrics['reviews_collected'] = int(collected_match.group(1))
    
    # Extract total found
    found_match = re.search(r'Total Found: (\d+)', output)
    if found_match:
        metrics['total_found'] = int(found_match.group(1))
    
    # Alternative parsing for "Job X completed: Y reviews inserted"
    if metrics['reviews_collected'] == 0:
        inserted_match = re.search(r'Job \d+ completed: (\d+) reviews inserted', output)
        if inserted_match:
            metrics['reviews_collected'] = int(inserted_match.group(1))
            # If we found inserted count, use it for total_found too if not already set
            if metrics['total_found'] == 0:
                metrics['total_found'] = metrics['reviews_collected']
    
    return metrics

def fetch(platform: str, app_id: str, country: Optional[str] = None, 
          max_reviews: Optional[int] = None, site: Optional[str] = None, 
          max_pages: Optional[int] = None, product_name: Optional[str] = None,
          company: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Enhanced fetch function that integrates with Supabase database
    
    Args:
        platform: Platform to fetch from ('apple', 'google', 'amazon')
        app_id: App/Product ID on the platform
        country: Country code (default: 'us')
        max_reviews: Maximum number of reviews to fetch (default: 1000)
        site: Amazon site (default: 'com') - only for Amazon
        max_pages: Max pages for Amazon (default: 10) - only for Amazon
        product_name: Product name for database lookup (e.g., "Norton 360")
        company: Company name for database lookup (e.g., "NorTech")
        **kwargs: Additional parameters
    
    Returns:
        Dictionary with collection results including parsed metrics
    """
    
    # Validate inputs
    if platform not in ['apple', 'google', 'amazon']:
        raise ValueError(f"Unsupported platform: {platform}. Supported: apple, google, amazon")
    
    if not app_id:
        raise ValueError("app_id is required")
    
    # Set defaults
    country = country or 'us'
    max_reviews = max_reviews or 1000
    
    # Build command
    cmd = [
        sys.executable, 
        ENHANCED_SCRIPT,
        "--platform", platform,
        "--app_id", app_id,
        "--max_reviews", str(max_reviews),
        "--country", country
    ]
    
    # Add product information if provided
    if product_name:
        cmd.extend(["--product_name", product_name])
    if company:
        cmd.extend(["--company", company])
    
    # Add platform-specific parameters
    if platform == "amazon":
        if site:
            cmd.extend(["--site", site])
        if max_pages:
            cmd.extend(["--max_pages", str(max_pages)])
    
    # Add any additional parameters
    for key, value in kwargs.items():
        if value is not None:
            cmd.extend([f"--{key}", str(value)])
    
    logger.info(f"🛠 Running collection: {platform}/{app_id} (target: {max_reviews})")
    
    try:
        # Run the enhanced script
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Parse the output (check both stdout and stderr since logs go to stderr)
        combined_output = result.stdout + "\n" + result.stderr
        metrics = parse_collection_output(combined_output)
        
        logger.info(f"✅ Collection completed: {metrics['reviews_collected']} reviews collected")
        
        # Return enhanced result with parsed metrics
        return {
            'success': True,
            'return_code': result.returncode,
            'output': result.stdout,
            'error': result.stderr,
            'platform': platform,
            'app_id': app_id,
            'max_reviews': max_reviews,
            'reviews_collected': metrics['reviews_collected'],
            'total_found': metrics['total_found'],
            'job_id': metrics['job_id']
        }
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Collection failed: {e}")
        
        # Try to parse partial results (check both stdout and stderr)
        combined_output = (e.stdout or "") + "\n" + (e.stderr or "")
        metrics = parse_collection_output(combined_output) if combined_output.strip() else {'reviews_collected': 0, 'success': False}
        
        return {
            'success': False,
            'return_code': e.returncode,
            'output': e.stdout,
            'error': e.stderr,
            'platform': platform,
            'app_id': app_id,
            'max_reviews': max_reviews,
            'reviews_collected': metrics['reviews_collected'],
            'total_found': metrics.get('total_found', 0),
            'job_id': metrics.get('job_id')
        }
    
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return {
            'success': False,
            'return_code': -1,
            'output': '',
            'error': str(e),
            'platform': platform,
            'app_id': app_id,
            'max_reviews': max_reviews,
            'reviews_collected': 0,
            'total_found': 0,
            'job_id': None
        }

# Keep all the convenience functions from the original...
def fetch_norton_360():
    """Convenience function to fetch Norton 360 reviews from both platforms"""
    results = {}
    
    # Norton 360 on Apple Store
    logger.info("📱 Fetching Norton 360 reviews from Apple Store...")
    results['apple'] = fetch(
        platform="apple", 
        app_id="724596345", 
        country="us", 
        max_reviews=10000,
        product_name="Norton 360",
        company="NorTech (Broadcom)"
    )
    
    # Norton 360 on Google Play
    logger.info("🤖 Fetching Norton 360 reviews from Google Play...")
    results['google'] = fetch(
        platform="google", 
        app_id="com.symantec.mobilesecurity", 
        country="us", 
        max_reviews=10000,
        product_name="Norton 360",
        company="NorTech (Broadcom)"
    )
    
    return results

def fetch_mcafee():
    """Convenience function to fetch McAfee reviews from both platforms"""
    results = {}
    
    # McAfee on Apple Store
    logger.info("📱 Fetching McAfee reviews from Apple Store...")
    results['apple'] = fetch(
        platform="apple", 
        app_id="520234411", 
        country="us", 
        max_reviews=10000,
        product_name="McAfee Total Protection",
        company="McAfee"
    )
    
    # McAfee on Google Play
    logger.info("🤖 Fetching McAfee reviews from Google Play...")
    results['google'] = fetch(
        platform="google", 
        app_id="com.wsandroid.suite", 
        country="us", 
        max_reviews=30000,
        product_name="McAfee Total Protection",
        company="McAfee"
    )
    
    return results

def fetch_bitdefender():
    """Convenience function to fetch Bitdefender reviews from both platforms"""
    results = {}
    
    # Bitdefender on Apple Store
    logger.info("📱 Fetching Bitdefender reviews from Apple Store...")
    results['apple'] = fetch(
        platform="apple", 
        app_id="1127716399", 
        country="us", 
        max_reviews=10000,
        product_name="Bitdefender Total Security",
        company="Bitdefender"
    )
    
    # Bitdefender on Google Play
    logger.info("🤖 Fetching Bitdefender reviews from Google Play...")
    results['google'] = fetch(
        platform="google", 
        app_id="com.bitdefender.security", 
        country="us", 
        max_reviews=30000,
        product_name="Bitdefender Total Security",
        company="Bitdefender"
    )
    
    return results

if __name__ == "__main__":
    # Test the enhanced wrapper
    print("✅ Enhanced fetch wrapper with result parsing is ready!")
    print("\n🔧 Usage examples:")
    print('result = fetch("apple", "724596345", max_reviews=100, product_name="Norton 360")')
    print('print(f"Collected: {result[\"reviews_collected\"]} reviews")')
