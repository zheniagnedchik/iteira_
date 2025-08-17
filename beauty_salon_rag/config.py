"""
Configuration module for Beauty Salon RAG System
Manages application settings and environment variables
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for managing application settings"""
    
    def __init__(self):
        self._config = self._load_default_config()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration settings"""
        return {
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
                'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '1000')),
                'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
            },
            'data': {
                'services_file': os.getenv('SERVICES_FILE', 'services.json'),
                'services_no_staff_file': os.getenv('SERVICES_NO_STAFF_FILE', 'services_no_staff.json')
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            },
            'app': {
                'debug': os.getenv('DEBUG', 'False').lower() == 'true',
                'mode': os.getenv('APP_MODE', 'production'),  # development, testing, production
                'performance_mode': os.getenv('PERFORMANCE_MODE', 'balanced'),  # speed, quality, balanced
                'enable_caching': os.getenv('ENABLE_CACHING', 'True').lower() == 'true',
                'cache_ttl': int(os.getenv('CACHE_TTL', '300')),  # Cache TTL in seconds
                'max_retries': int(os.getenv('MAX_RETRIES', '3')),
                'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
                'interactive_mode': os.getenv('INTERACTIVE_MODE', 'True').lower() == 'true'
            },
            'telegram': {
                'bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
                'max_message_length': int(os.getenv('TELEGRAM_MAX_MESSAGE_LENGTH', '4096')),
                'context_ttl_hours': int(os.getenv('TELEGRAM_CONTEXT_TTL_HOURS', '24')),
                'max_context_messages': int(os.getenv('TELEGRAM_MAX_CONTEXT_MESSAGES', '20')),
                'enable_buttons': os.getenv('TELEGRAM_ENABLE_BUTTONS', 'True').lower() == 'true'
            },
            'performance': {
                'speed': {
                    'max_tokens': 500,
                    'temperature': 0.3,
                    'cache_ttl': 600,
                    'min_request_interval': 0.05
                },
                'quality': {
                    'max_tokens': 1500,
                    'temperature': 0.7,
                    'cache_ttl': 180,
                    'min_request_interval': 0.2
                },
                'balanced': {
                    'max_tokens': 1000,
                    'temperature': 0.5,
                    'cache_ttl': 300,
                    'min_request_interval': 0.1
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key using dot notation"""
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_openai_key(self) -> str:
        """Get OpenAI API key"""
        api_key = self.get('openai.api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return api_key
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration"""
        return self.get('openai', {})
    
    def get_data_files(self) -> Dict[str, str]:
        """Get data file paths"""
        return self.get('data', {})
    
    def get_app_mode(self) -> str:
        """Get application mode"""
        return self.get('app.mode', 'production')
    
    def get_performance_mode(self) -> str:
        """Get performance mode"""
        return self.get('app.performance_mode', 'balanced')
    
    def get_performance_settings(self, mode: str = None) -> Dict[str, Any]:
        """Get performance settings for specified mode"""
        if mode is None:
            mode = self.get_performance_mode()
        return self.get(f'performance.{mode}', self.get('performance.balanced', {}))
    
    def is_caching_enabled(self) -> bool:
        """Check if caching is enabled"""
        return self.get('app.enable_caching', True)
    
    def is_interactive_mode(self) -> bool:
        """Check if interactive mode is enabled"""
        return self.get('app.interactive_mode', True)
    
    def is_debug_mode(self) -> bool:
        """Check if debug mode is enabled"""
        return self.get('app.debug', False)
    
    def get_retry_settings(self) -> Dict[str, int]:
        """Get retry settings"""
        return {
            'max_retries': self.get('app.max_retries', 3),
            'request_timeout': self.get('app.request_timeout', 30)
        }
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """Get Telegram bot configuration"""
        return self.get('telegram', {})
    
    def get_telegram_token(self) -> str:
        """Get Telegram bot token"""
        token = self.get('telegram.bot_token')
        if not token:
            raise ValueError("Telegram bot token not found. Please set TELEGRAM_BOT_TOKEN environment variable.")
        return token


# Global configuration instance
config = Config()


def load_config() -> Config:
    """Load and return configuration instance"""
    return config