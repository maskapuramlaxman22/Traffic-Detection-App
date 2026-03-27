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
    
    # ============================================================
    # FREE APIS ONLY - NO API KEYS REQUIRED!
    # ============================================================
    
    # Geocoding: OpenStreetMap Nominatim (COMPLETELY FREE)
    NOMINATIM_USER_AGENT = os.getenv('NOMINATIM_USER_AGENT', 'traffic-detection-app')
    
    # Weather: Open-Meteo (COMPLETELY FREE, NO API KEY NEEDED!)
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', None)  # Optional, if you want OpenWeatherMap free tier
    
    # Routing: OSRM - Open Source Routing Machine (FREE, SELF-HOSTED AVAILABLE)
    OSRM_URL = os.getenv('OSRM_URL', 'http://router.project-osrm.org')
    
    # Incidents: OpenStreetMap Overpass API (COMPLETELY FREE)
    OVERPASS_API_URL = os.getenv('OVERPASS_API_URL', 'https://overpass-api.de/api/interpreter')
    
    # Maps Frontend: Leaflet with OpenStreetMap tiles (COMPLETELY FREE)
    # Mapbox requires API key, but we use Leaflet instead
    
    # ============================================================
    # NOTE: Paid API keys below are NOT USED in free tier
    # They are kept for reference but not required
    # ============================================================
    
    # API Keys (Optional - only if you want paid services)
    TOMTOM_API_KEY = os.getenv('TOMTOM_API_KEY', None)  # Optional paid service
    HERE_API_KEY = os.getenv('HERE_API_KEY', None)      # Optional paid service
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', None)  # Optional paid service
    MAPBOX_API_KEY = os.getenv('MAPBOX_API_KEY', None)  # Optional paid service
    
    # API Rate Limiting
    RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', 100))
    RATE_LIMIT_PERIOD = int(os.getenv('RATE_LIMIT_PERIOD', 3600))  # 1 hour
    
    # Real-time Updates
    WEBSOCKET_ENABLED = os.getenv('WEBSOCKET_ENABLED', True)
    UPDATE_INTERVAL = int(os.getenv('UPDATE_INTERVAL', 30))  # seconds
    
    # Audio Processing
    AUDIO_ENABLED = os.getenv('AUDIO_ENABLED', False)

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
