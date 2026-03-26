import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    DEBUG = os.getenv('DEBUG', False)
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///database/traffic.db')
    
    # Cache
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', 300))  # 5 minutes
    
    # API Keys for Traffic Data
    TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY')
    HERE_API_KEY = os.getenv('HERE_API_KEY')
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    MAPBOX_API_KEY = os.getenv('MAPBOX_API_KEY')
    
    # Geocoding APIs
    NOMINATIM_USER_AGENT = os.getenv('NOMINATIM_USER_AGENT', 'traffic-detection-app')
    
    # OpenWeatherMap for Weather Impact
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
    
    # API Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', 3600))  # 1 hour
    
    # Real-time Updates
    WEBSOCKET_ENABLED = os.getenv('WEBSOCKET_ENABLED', True)
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 30))  # seconds
    
    # Audio Processing
    AUDIO_ENABLED = os.getenv('AUDIO_ENABLED', False)
    AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
    AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
