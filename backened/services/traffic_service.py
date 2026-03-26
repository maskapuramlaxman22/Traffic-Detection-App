"""
Traffic Data Service Layer
Integrates with real-time traffic APIs from multiple providers
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import os

logger = logging.getLogger(__name__)

class GeocodingService:
    """Handle location geocoding using Nominatim (OpenStreetMap)"""
    
    def __init__(self, user_agent='traffic-detection-app'):
        self.geocoder = Nominatim(user_agent=user_agent)
    
    def geocode_location(self, location_name: str) -> Optional[Dict]:
        """
        Convert location name to coordinates
        Returns: {"name": str, "lat": float, "lng": float, "full_address": str}
        """
        try:
            location = self.geocoder.geocode(location_name, timeout=5)
            if location:
                return {
                    "name": location_name,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "address": location.address,
                    "timestamp": datetime.utcnow().isoformat()
                }
            return None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding failed for {location_name}: {str(e)}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Convert coordinates to location name"""
        try:
            location = self.geocoder.reverse(f"{lat}, {lng}", timeout=5)
            return location.address if location else None
        except (GeocoderTimedOut, GeocoderUnavailable):
            return None


class TomTomTrafficService:
    """TomTom Real-time Traffic API Integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.tomtom.com/traffic/services/4"
    
    def get_traffic_flow(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Get real-time traffic flow at a specific location
        Uses TomTom Traffic Flow API v4
        """
        if not self.api_key:
            logger.warning("TomTom API key not configured")
            return None
        
        try:
            # TomTom Traffic Flow API endpoint
            url = f"{self.base_url}/flowSegmentData/absolute/10/json"
            params = {
                "point": f"{lat},{lng}",
                "key": self.api_key,
                "thickness": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('flowSegmentData'):
                flow = data['flowSegmentData']
                return {
                    "source": "TomTom Traffic API",
                    "latitude": lat,
                    "longitude": lng,
                    "live_speed_kmh": flow.get('currentSpeed'),
                    "free_flow_speed_kmh": flow.get('freeFlowSpeed'),
                    "congestion_level": self._calculate_congestion(
                        flow.get('currentSpeed', 0),
                        flow.get('freeFlowSpeed', 1)
                    ),
                    "travel_time_minutes": flow.get('currentTravelTime', 0) / 60,
                    "confidence": flow.get('confidence'),
                    "last_updated": datetime.utcnow().isoformat()
                }
            return None
        
        except requests.RequestException as e:
            logger.error(f"TomTom API error: {str(e)}")
            return None
    
    def get_traffic_incidents(self, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """
        Get traffic incidents in a bounding box
        bbox: (min_lat, min_lng, max_lat, max_lng)
        """
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/incidentDetails/1/json"
            params = {
                "boundingBox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
                "key": self.api_key,
                "trafficModelId": "urprtall"
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            incidents = []
            
            for incident in data.get('incidents', []):
                incidents.append({
                    "id": incident.get('id'),
                    "type": incident.get('incidentType'),
                    "description": incident.get('description'),
                    "delay_minutes": incident.get('delay'),
                    "latitude": incident.get('position', {}).get('lat'),
                    "longitude": incident.get('position', {}).get('lng'),
                    "magnitude": incident.get('magnitude'),
                    "start_time": incident.get('startTime'),
                    "source": "TomTom"
                })
            
            return incidents
        
        except requests.RequestException as e:
            logger.error(f"TomTom incidents API error: {str(e)}")
            return []
    
    @staticmethod
    def _calculate_congestion(current_speed: float, free_flow_speed: float) -> float:
        """Calculate congestion level (0-1)"""
        if free_flow_speed == 0:
            return 0
        ratio = current_speed / free_flow_speed
        # Inverse relationship: higher speed = lower congestion
        return max(0, min(1, 1 - ratio))


class HereTrafficService:
    """HERE Real-time Traffic API Integration"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://traffic.ls.hereapi.com/traffic/6.3"
    
    def get_traffic_flow(self, lat: float, lng: float, radius: int = 500) -> Optional[Dict]:
        """Get real-time traffic flow using HERE API"""
        if not self.api_key:
            logger.warning("HERE API key not configured")
            return None
        
        try:
            url = f"{self.base_url}/flow.json"
            params = {
                "apiKey": self.api_key,
                "at": f"{lat},{lng}",
                "radius": radius
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('RWS'):
                rws = data['RWS'][0]
                if rws.get('FIS'):
                    flow = rws['FIS'][0]
                    current_flow = flow.get('FF', {})
                    
                    current_speed = current_flow.get('SP', 0)
                    free_flow_speed = current_flow.get('FU', 0)
                    
                    return {
                        "source": "HERE Traffic API",
                        "latitude": lat,
                        "longitude": lng,
                        "live_speed_kmh": current_speed,
                        "free_flow_speed_kmh": free_flow_speed,
                        "congestion_level": self._calculate_congestion(
                            current_speed, free_flow_speed
                        ),
                        "road_closure": flow.get('CR', 0),
                        "last_updated": datetime.utcnow().isoformat()
                    }
            return None
        
        except requests.RequestException as e:
            logger.error(f"HERE API error: {str(e)}")
            return None
    
    @staticmethod
    def _calculate_congestion(current_speed: float, free_flow_speed: float) -> float:
        """Calculate congestion level (0-1)"""
        if free_flow_speed == 0:
            return 0
        return max(0, min(1, 1 - (current_speed / free_flow_speed)))


class GoogleMapsTrafficService:
    """Google Maps Distance Matrix API for traffic-aware routing"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    
    def get_route_traffic(self, origin: str, destination: str) -> Optional[Dict]:
        """
        Get traffic-aware distance and duration between two locations
        """
        if not self.api_key:
            logger.warning("Google Maps API key not configured")
            return None
        
        try:
            params = {
                "origins": origin,
                "destinations": destination,
                "key": self.api_key,
                "mode": "driving",
                "departure_time": "now"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data['status'] == 'OK' and data.get('rows'):
                elements = data['rows'][0].get('elements', [])
                if elements:
                    element = elements[0]
                    
                    if 'duration_in_traffic' in element:
                        return {
                            "source": origin,
                            "destination": destination,
                            "distance_km": element['distance']['value'] / 1000,
                            "normal_duration_minutes": element['duration']['value'] / 60,
                            "traffic_duration_minutes": element['duration_in_traffic']['value'] / 60,
                            "delay_minutes": (
                                element['duration_in_traffic']['value'] - 
                                element['duration']['value']
                            ) / 60,
                            "api_source": "Google Maps",
                            "last_updated": datetime.utcnow().isoformat()
                        }
            return None
        
        except requests.RequestException as e:
            logger.error(f"Google Maps API error: {str(e)}")
            return None


class WeatherService:
    """OpenWeatherMap for weather impact on traffic"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
    
    def get_weather_impact(self, lat: float, lng: float) -> Optional[Dict]:
        """Get weather conditions affecting traffic"""
        if not self.api_key:
            return None
        
        try:
            params = {
                "lat": lat,
                "lon": lng,
                "appid": self.api_key,
                "units": "metric"
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            weather = data.get('weather', [{}])[0]
            weather_main = weather.get('main', '').lower()
            
            # Map to traffic impact categories
            impact_map = {
                'clear': 'none',
                'clouds': 'light',
                'rain': 'moderate' if data['rain'] and data['rain'].get('1h', 0) < 5 else 'heavy',
                'snow': 'heavy',
                'thunderstorm': 'severe',
                'mist': 'light',
                'smoke': 'light',
                'haze': 'light',
                'dust': 'moderate',
                'fog': 'moderate',
                'sand': 'heavy',
                'ash': 'heavy',
                'squall': 'moderate',
                'tornado': 'severe'
            }
            
            return {
                "main": weather_main,
                "description": weather.get('description'),
                "temperature": data.get('main', {}).get('temp'),
                "visibility": data.get('visibility'),
                "wind_speed": data.get('wind', {}).get('speed'),
                "traffic_impact": impact_map.get(weather_main, 'light'),
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except requests.RequestException as e:
            logger.error(f"Weather API error: {str(e)}")
            return None


class TrafficDataAggregator:
    """
    Aggregates traffic data from multiple sources
    Provides fallback mechanisms and intelligent caching
    """
    
    def __init__(self, config):
        self.geocoder = GeocodingService()
        self.tomtom = TomTomTrafficService(config.get('TOMTOM_API_KEY'))
        self.here = HereTrafficService(config.get('HERE_API_KEY'))
        self.google_maps = GoogleMapsTrafficService(config.get('GOOGLE_MAPS_API_KEY'))
        self.weather = WeatherService(config.get('OPENWEATHER_API_KEY'))
    
    def get_location_traffic(self, location_name: str) -> Optional[Dict]:
        """Get comprehensive traffic data for a location"""
        # Step 1: Geocode location
        geo_data = self.geocoder.geocode_location(location_name)
        if not geo_data:
            logger.error(f"Failed to geocode: {location_name}")
            return None
        
        lat, lng = geo_data['latitude'], geo_data['longitude']
        
        # Step 2: Fetch traffic from primary source (TomTom)
        traffic_data = self.tomtom.get_traffic_flow(lat, lng)
        
        # Step 3: Fallback to HERE if TomTom fails
        if not traffic_data:
            traffic_data = self.here.get_traffic_flow(lat, lng)
        
        # Step 4: Add weather impact
        weather_data = self.weather.get_weather_impact(lat, lng)
        
        if traffic_data:
            result = {
                "location": location_name,
                "coordinates": {
                    "latitude": lat,
                    "longitude": lng
                },
                "traffic": traffic_data,
                "address": geo_data.get('address')
            }
            
            if weather_data:
                result["weather_impact"] = weather_data
            
            return result
        
        return None
    
    def get_route_traffic(self, source: str, destination: str) -> Optional[Dict]:
        """Get traffic data for a route between two locations"""
        try:
            route_data = self.google_maps.get_route_traffic(source, destination)
            
            if route_data:
                # Add weather data for origin
                source_geo = self.geocoder.geocode_location(source)
                if source_geo:
                    weather = self.weather.get_weather_impact(
                        source_geo['latitude'],
                        source_geo['longitude']
                    )
                    route_data['weather_impact'] = weather
            
            return route_data
        
        except Exception as e:
            logger.error(f"Route traffic error: {str(e)}")
            return None
    
    def get_area_incidents(self, lat: float, lng: float, radius_km: int = 5) -> List[Dict]:
        """Get incidents in an area"""
        # Convert radius in km to degrees (rough approximation)
        lat_offset = radius_km / 111.0
        lng_offset = radius_km / (111.0 * abs(__import__('math').cos(__import__('math').radians(lat))))
        
        bbox = (lat - lat_offset, lng - lng_offset, lat + lat_offset, lng + lng_offset)
        
        incidents = self.tomtom.get_traffic_incidents(bbox)
        return incidents
