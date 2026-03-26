"""
API Service with Fallback and Retry Logic
Provides resilient API calls with automatic failover to alternative providers
"""

import logging
import requests
import time
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from datetime import datetime, timedelta
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Supported API providers"""
    NOMINATIM = "nominatim"
    OSRM = "osrm"
    GOOGLE_MAPS = "google_maps"
    OPENROUTE_SERVICE = "openroute_service"
    OPEN_METEO = "open_meteo"
    TOMTOM = "tomtom"
    HERE = "here_maps"
    MAPBOX = "mapbox"


class APIStatus(Enum):
    """API health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"


@staticmethod
def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 1.0, 
                       exceptions: tuple = (requests.RequestException,)):
    """
    Decorator for retry logic with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Multiplier for backoff duration (backoff = backoff_factor ** attempt)
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(f"✓ {func.__name__} succeeded on attempt {attempt + 1}")
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = backoff_factor ** attempt
                        logger.warning(f"⚠️ {func.__name__} attempt {attempt + 1} failed: {str(e)}")
                        logger.info(f"   Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_retries + 1} attempts")
            
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern for API calls
    Prevents cascading failures by temporarily disabling failing APIs
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = APIStatus.HEALTHY  # HEALTHY, DEGRADED, DOWN
        self.lock = threading.RLock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self.lock:
            # Check if circuit should be closed (recovery attempt)
            if self.state == APIStatus.DOWN:
                if (time.time() - self.last_failure_time.timestamp()) > self.recovery_timeout:
                    logger.info(f"🔄 Attempting to recover circuit...")
                    self.state = APIStatus.DEGRADED
                    self.failure_count = 0
                else:
                    raise Exception(f"Circuit breaker is OPEN. Recovering in "
                                  f"{self.recovery_timeout - (time.time() - self.last_failure_time.timestamp()):.0f}s")
            
            # Execute function
            try:
                result = func(*args, **kwargs)
                # Reset on success
                if self.state != APIStatus.HEALTHY:
                    logger.info(f"✓ Circuit recovered to HEALTHY")
                self.state = APIStatus.HEALTHY
                self.failure_count = 0
                return result
            
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = datetime.utcnow()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = APIStatus.DOWN
                    logger.error(f"🔴 Circuit breaker OPENED after {self.failure_count} failures")
                else:
                    self.state = APIStatus.DEGRADED
                    logger.warning(f"⚠️ Circuit breaker DEGRADED ({self.failure_count}/{self.failure_threshold})")
                
                raise
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        with self.lock:
            return self.state == APIStatus.DOWN or self.state == APIStatus.DEGRADED
    
    def get_status(self) -> Dict[str, Any]:
        """Get circuit status"""
        with self.lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
            }


class APIServiceWithFallback:
    """
    Unified API service with fallback logic
    Automatically switches to alternative providers on failure
    """
    
    def __init__(self, cache_service=None, config: Dict[str, str] = None):
        """
        Args:
            cache_service: Cache service for memoizing responses
            config: Configuration dictionary with API keys
        """
        self.cache = cache_service
        self.config = config or {}
        self.circuit_breakers = {}
        self.request_counter = 0
        self.error_counter = 0
        self.lock = threading.RLock()
    
    def _get_circuit_breaker(self, provider: APIProvider) -> CircuitBreaker:
        """Get or create circuit breaker for provider"""
        if provider not in self.circuit_breakers:
            self.circuit_breakers[provider] = CircuitBreaker()
        return self.circuit_breakers[provider]
    
    @retry_with_backoff(max_retries=2, backoff_factor=0.5)
    def geocode(self, location: str, preferred_providers: List[APIProvider] = None) -> Optional[Dict[str, Any]]:
        """
        Geocode location name to coordinates with fallback
        
        Fallback chain: Nominatim → Google Maps → OpenRouteService
        """
        cache_key = f"geocode_{location}"
        
        # Check cache
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info(f"✓ Cache hit for geocode: {location}")
                return cached
        
        providers = preferred_providers or [
            APIProvider.NOMINATIM,
            APIProvider.GOOGLE_MAPS,
            APIProvider.OPENROUTE_SERVICE
        ]
        
        for provider in providers:
            try:
                cb = self._get_circuit_breaker(provider)
                
                if provider == APIProvider.NOMINATIM:
                    result = cb.call(self._geocode_nominatim, location)
                elif provider == APIProvider.GOOGLE_MAPS:
                    result = cb.call(self._geocode_google_maps, location)
                elif provider == APIProvider.OPENROUTE_SERVICE:
                    result = cb.call(self._geocode_openroute, location)
                else:
                    continue
                
                if result:
                    # Cache result
                    if self.cache:
                        self.cache.set(cache_key, result, ttl=3600)  # 1 hour
                    return result
                    
            except Exception as e:
                logger.warning(f"⚠️ {provider.value} geocoding failed: {str(e)}")
                continue
        
        logger.error(f"❌ All geocoding providers failed for: {location}")
        return None
    
    def _geocode_nominatim(self, location: str) -> Optional[Dict[str, Any]]:
        """Geocode using Nominatim (OpenStreetMap) - FREE"""
        try:
            from geopy.geocoders import Nominatim as NominatimGeocoder
            from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
            
            geocoder = NominatimGeocoder(user_agent='traffic-detection-app')
            geoloc = geocoder.geocode(location, timeout=5)
            
            if geoloc:
                return {
                    "name": location,
                    "latitude": geoloc.latitude,
                    "longitude": geoloc.longitude,
                    "address": geoloc.address,
                    "provider": "nominatim",
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except Exception as e:
            raise requests.RequestException(f"Nominatim error: {e}")
    
    def _geocode_google_maps(self, location: str) -> Optional[Dict[str, Any]]:
        """Geocode using Google Maps API"""
        try:
            api_key = self.config.get('GOOGLE_MAPS_API_KEY')
            if not api_key:
                raise ValueError("Google Maps API key not configured")
            
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {"address": location, "key": api_key}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                loc = result["geometry"]["location"]
                
                return {
                    "name": location,
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                    "address": result.get("formatted_address", location),
                    "provider": "google_maps",
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except Exception as e:
            raise requests.RequestException(f"Google Maps error: {e}")
    
    def _geocode_openroute(self, location: str) -> Optional[Dict[str, Any]]:
        """Geocode using OpenRouteService - FREE"""
        try:
            url = "https://api.openrouteservice.org/geocode/search"
            params = {"text": location}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if data.get("features"):
                feature = data["features"][0]
                coords = feature["geometry"]["coordinates"]
                
                return {
                    "name": location,
                    "latitude": coords[1],
                    "longitude": coords[0],
                    "address": feature["properties"].get("label", location),
                    "provider": "openroute_service",
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except Exception as e:
            raise requests.RequestException(f"OpenRouteService error: {e}")
    
    def get_route(self, origin_lat: float, origin_lng: float, 
                 dest_lat: float, dest_lng: float,
                 preferred_providers: List[APIProvider] = None) -> Optional[Dict[str, Any]]:
        """
        Get route between two points with fallback
        
        Fallback chain: OSRM → Google Maps → OpenRouteService
        """
        cache_key = f"route_{origin_lat:.4f}_{origin_lng:.4f}_{dest_lat:.4f}_{dest_lng:.4f}"
        
        # Check cache
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                logger.info("✓ Cache hit for route")
                return cached
        
        providers = preferred_providers or [
            APIProvider.OSRM,
            APIProvider.GOOGLE_MAPS,
            APIProvider.OPENROUTE_SERVICE
        ]
        
        for provider in providers:
            try:
                cb = self._get_circuit_breaker(provider)
                
                if provider == APIProvider.OSRM:
                    result = cb.call(self._route_osrm, origin_lat, origin_lng, dest_lat, dest_lng)
                elif provider == APIProvider.GOOGLE_MAPS:
                    result = cb.call(self._route_google_maps, origin_lat, origin_lng, dest_lat, dest_lng)
                elif provider == APIProvider.OPENROUTE_SERVICE:
                    result = cb.call(self._route_openroute, origin_lat, origin_lng, dest_lat, dest_lng)
                else:
                    continue
                
                if result:
                    if self.cache:
                        self.cache.set(cache_key, result, ttl=1800)  # 30 minutes
                    return result
                    
            except Exception as e:
                logger.warning(f"⚠️ {provider.value} routing failed: {str(e)}")
                continue
        
        logger.error("❌ All routing providers failed")
        return None
    
    def _route_osrm(self, origin_lat: float, origin_lng: float, 
                    dest_lat: float, dest_lng: float) -> Optional[Dict[str, Any]]:
        """Get route from OSRM - FREE"""
        try:
            url = f"http://router.project-osrm.org/route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
            params = {"overview": "full", "steps": "true", "annotations": "duration,distance"}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("code") == "Ok" and data.get("routes"):
                route = data["routes"][0]
                
                return {
                    "distance_km": route.get("distance", 0) / 1000,
                    "duration_minutes": route.get("duration", 0) / 60,
                    "geometry": route.get("geometry"),
                    "provider": "osrm",
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except Exception as e:
            raise requests.RequestException(f"OSRM error: {e}")
    
    def _route_google_maps(self, origin_lat: float, origin_lng: float,
                          dest_lat: float, dest_lng: float) -> Optional[Dict[str, Any]]:
        """Get route from Google Maps"""
        try:
            api_key = self.config.get('GOOGLE_MAPS_API_KEY')
            if not api_key:
                raise ValueError("Google Maps API key not configured")
            
            origin = f"{origin_lat},{origin_lng}"
            destination = f"{dest_lat},{dest_lng}"
            
            url = "https://maps.googleapis.com/maps/api/directions/json"
            params = {"origin": origin, "destination": destination, "key": api_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("routes"):
                route = data["routes"][0]
                leg = route["legs"][0]
                
                return {
                    "distance_km": leg["distance"]["value"] / 1000,
                    "duration_minutes": leg["duration"]["value"] / 60,
                    "geometry": route.get("overview_polyline", {}).get("points"),
                    "provider": "google_maps",
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except Exception as e:
            raise requests.RequestException(f"Google Maps error: {e}")
    
    def _route_openroute(self, origin_lat: float, origin_lng: float,
                        dest_lat: float, dest_lng: float) -> Optional[Dict[str, Any]]:
        """Get route from OpenRouteService - FREE"""
        try:
            url = "https://api.openrouteservice.org/v2/directions/driving-car"
            params = {
                "start": f"{origin_lng},{origin_lat}",
                "end": f"{dest_lng},{dest_lat}"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("features"):
                route = data["features"][0]
                props = route["properties"]["summary"]
                
                return {
                    "distance_km": props.get("distance", 0) / 1000,
                    "duration_minutes": props.get("duration", 0) / 60,
                    "geometry": route.get("geometry"),
                    "provider": "openroute_service",
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except Exception as e:
            raise requests.RequestException(f"OpenRouteService error: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get API service status"""
        with self.lock:
            provider_status = {
                provider.value: cb.get_status()
                for provider, cb in self.circuit_breakers.items()
            }
            
            return {
                "total_requests": self.request_counter,
                "total_errors": self.error_counter,
                "providers": provider_status,
                "timestamp": datetime.utcnow().isoformat()
            }
