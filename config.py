import os
import json
from typing import Dict, Any

class Config:
    def __init__(self, env: str = None):
        self.env = env or os.getenv('APP_ENV', 'development')
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration based on environment"""
        base_config = {
            'app_name': 'Facebook Middleman',
            'debug': True,
            'host': '0.0.0.0',
            'port': 8000,
            'database': 'data.db'
        }
        
        if self.env == 'production':
            base_config.update({
                'debug': False,
                'database': '/data/app.db'
            })
        elif self.env == 'testing':
            base_config.update({
                'database': ':memory:'
            })
        
        # Load proxy configuration from environment variables
        base_config['proxy'] = {
            'host': os.getenv('PROXY_HOST', ''),
            'port': int(os.getenv('PROXY_PORT', '0')),
            'username': os.getenv('PROXY_USERNAME', ''),
            'password': os.getenv('PROXY_PASSWORD', '')
        }
        
        return base_config
    
    def get(self, key: str, default=None):
        """Get config value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def __getitem__(self, key):
        return self.get(key)
