"""
Redis Caching Service
Handles caching of traffic data to reduce API calls and improve performance
"""

import redis
import json
import logging
from typing import Any, Optional
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching for traffic data"""
    
    # Cache key prefixes
    LOCATION_CACHE = "location:"
    TRAFFIC_CACHE = "traffic:"
    ROUTE_CACHE = "route:"
    INCIDENT_CACHE = "incidents:"
    WEATHER_CACHE = "weather:"
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", default_ttl: int = 300):
        """
        Initialize Redis cache connection
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Cache disabled.")
            self.redis = None
        
        self.default_ttl = default_ttl
    
    def is_available(self) -> bool:
        """Check if Redis cache is available"""
        return self.redis is not None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (uses default if None)
        """
        if not self.redis:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            data = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            return None
        
        try:
            value = self.redis.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        if not self.redis:
            return False
        
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    def clear(self, pattern: str = "*") -> int:
        """Clear all cache entries matching pattern"""
        if not self.redis:
            return 0
        
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    # Location caching
    def cache_geocoding(self, location_name: str, geo_data: dict, ttl: int = 86400) -> bool:
        """Cache geocoding result (24 hours by default)"""
        key = f"{self.LOCATION_CACHE}{location_name.lower()}"
        return self.set(key, geo_data, ttl)
    
    def get_cached_geocoding(self, location_name: str) -> Optional[dict]:
        """Get cached geocoding result"""
        key = f"{self.LOCATION_CACHE}{location_name.lower()}"
        return self.get(key)
    
    # Traffic data caching
    def cache_traffic(self, lat: float, lng: float, traffic_data: dict, ttl: int = 300) -> bool:
        """Cache traffic data (5 minutes by default)"""
        key = f"{self.TRAFFIC_CACHE}{lat:.4f}:{lng:.4f}"
        return self.set(key, traffic_data, ttl)
    
    def get_cached_traffic(self, lat: float, lng: float) -> Optional[dict]:
        """Get cached traffic data"""
        key = f"{self.TRAFFIC_CACHE}{lat:.4f}:{lng:.4f}"
        return self.get(key)
    
    # Route caching
    def cache_route(self, source: str, destination: str, route_data: dict, ttl: int = 600) -> bool:
        """Cache route data (10 minutes by default)"""
        route_key = f"{source.lower()}|{destination.lower()}"
        key_hash = hashlib.md5(route_key.encode()).hexdigest()
        key = f"{self.ROUTE_CACHE}{key_hash}"
        return self.set(key, route_data, ttl)
    
    def get_cached_route(self, source: str, destination: str) -> Optional[dict]:
        """Get cached route data"""
        route_key = f"{source.lower()}|{destination.lower()}"
        key_hash = hashlib.md5(route_key.encode()).hexdigest()
        key = f"{self.ROUTE_CACHE}{key_hash}"
        return self.get(key)
    
    # Incident caching
    def cache_incidents(self, lat: float, lng: float, incidents: list, ttl: int = 120) -> bool:
        """Cache incident data (2 minutes by default)"""
        key = f"{self.INCIDENT_CACHE}{lat:.4f}:{lng:.4f}"
        return self.set(key, incidents, ttl)
    
    def get_cached_incidents(self, lat: float, lng: float) -> Optional[list]:
        """Get cached incidents"""
        key = f"{self.INCIDENT_CACHE}{lat:.4f}:{lng:.4f}"
        return self.get(key)
    
    # Weather caching
    def cache_weather(self, lat: float, lng: float, weather_data: dict, ttl: int = 600) -> bool:
        """Cache weather data (10 minutes by default)"""
        key = f"{self.WEATHER_CACHE}{lat:.4f}:{lng:.4f}"
        return self.set(key, weather_data, ttl)
    
    def get_cached_weather(self, lat: float, lng: float) -> Optional[dict]:
        """Get cached weather data"""
        key = f"{self.WEATHER_CACHE}{lat:.4f}:{lng:.4f}"
        return self.get(key)


def cache_result(cache_key_prefix: str, ttl: int = 300):
    """
    Decorator for caching function results
    
    Usage:
        @cache_result(cache_service, "my_cache_key", ttl=600)
        def my_function(param1, param2):
            return expensive_operation()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Build cache key from function name and arguments
            cache_key = f"{cache_key_prefix}:{':'.join(str(a) for a in args)}"
            
            # Try to get from cache
            if self.cache:
                cached = self.cache.get(cache_key)
                if cached is not None:
                    logger.debug(f"Cache hit for {cache_key}")
                    return cached
            
            # Execute function if not cached
            result = func(self, *args, **kwargs)
            
            # Store in cache
            if result and self.cache:
                self.cache.set(cache_key, result, ttl)
                logger.debug(f"Cached {cache_key} for {ttl}s")
            
            return result
        
        return wrapper
    return decorator
