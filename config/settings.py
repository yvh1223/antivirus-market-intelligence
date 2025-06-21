"""
Configuration management for Consumer Security Analysis V3
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """Application configuration"""
    
    def __init__(self, env_file: str = '.env'):
        load_dotenv(env_file)
        
        # Database Configuration
        self.SUPABASE_URL = os.getenv('SUPABASE_URL', '')
        self.SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '')
        self.DB_HOST = os.getenv('DB_HOST', '')
        self.DB_PORT = int(os.getenv('DB_PORT', 5432))
        self.DB_NAME = os.getenv('DB_NAME', 'postgres')
        self.DB_USER = os.getenv('DB_USER', 'postgres')
        self.DB_PASSWORD = os.getenv('DB_PASSWORD', '')
        
        # AI Configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
        self.OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4.1-nano')
        
        # Rate Limiting
        self.RATE_LIMITS = {
            'apple': int(os.getenv('APPLE_RATE_LIMIT', 500)),
            'google': int(os.getenv('GOOGLE_RATE_LIMIT', 1000)),
            'amazon': int(os.getenv('AMAZON_RATE_LIMIT', 200)),
            'reddit': int(os.getenv('REDDIT_RATE_LIMIT', 600))
        }
        
        # Processing Configuration
        self.BATCH_SIZE = int(os.getenv('BATCH_SIZE', 50))
        self.MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', 5))
        self.PROCESSING_TIMEOUT = int(os.getenv('PROCESSING_TIMEOUT_SECONDS', 300))
        
        # Logging
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/consumer_security_analysis.log')
        
    def validate(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        errors = []
        warnings = []
        
        # Required fields
        if not self.SUPABASE_URL:
            errors.append("SUPABASE_URL is required")
        if not self.SUPABASE_ANON_KEY:
            errors.append("SUPABASE_ANON_KEY is required")
        if not self.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY is missing - AI analysis will be limited")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (excluding sensitive data)"""
        return {
            'supabase_url': self.SUPABASE_URL[:20] + "..." if self.SUPABASE_URL else None,
            'has_openai_key': bool(self.OPENAI_API_KEY),
            'openai_model': self.OPENAI_MODEL,
            'rate_limits': self.RATE_LIMITS,
            'batch_size': self.BATCH_SIZE,
            'max_concurrent_requests': self.MAX_CONCURRENT_REQUESTS,
            'log_level': self.LOG_LEVEL
        }

# Global config instance
config = Config()
