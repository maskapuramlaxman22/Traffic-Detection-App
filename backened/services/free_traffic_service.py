"""
Free Traffic Data Service Layer
Uses only free and open-source APIs - No costs!
"""

import requests
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import os

logger = logging.getLogger(__name__)

# Free API Endpoints
FREE_APIS = {
    'OSRM': 'http://router.project-osrm.org',  # Open Source Routing Machine
    'OPEN_METEO': 'https://api.open-meteo.com/v1',  # Free weather (no key needed)
    'OPENWEATHER_FREE': 'https://api.openweathermap.org/data/2.5',  # Free tier
}


class FreeGeocodingService:
    """Handle location geocoding using Nominatim (OpenStreetMap) - COMPLETELY FREE"""
    
    def __init__(self, user_agent='traffic-detection-app'):
        self.geocoder = Nominatim(user_agent=user_agent)
    
    def geocode_location(self, location_name: str) -> Optional[Dict]:
        """
        Convert location name to coordinates using OpenStreetMap
        COMPLETELY FREE - No API key required!
        """
        try:
            location = self.geocoder.geocode(location_name, timeout=5)
            if location:
                return {
                    "name": location_name,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "address": location.address,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "OpenStreetMap (Free)"
                }
            return None
        except (GeocoderTimedOut, GeocoderUnavailable) as e:
            logger.warning(f"Geocoding failed for {location_name}: {str(e)}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """Convert coordinates to location name - FREE"""
        try:
            location = self.geocoder.reverse(f"{lat}, {lng}", timeout=5)
            return location.address if location else None
        except (GeocoderTimedOut, GeocoderUnavailable):
            return None


class FreeRoutingService:
    """
    Open Source Routing Machine (OSRM) - Completely FREE
    No API key needed, self-hosted option available
    Provides: routing, directions, distance matrix
    """
    
    def __init__(self):
        self.base_url = "http://router.project-osrm.org/route/v1/driving"
    
    def get_route(self, origin_lat: float, origin_lng: float, 
                  dest_lat: float, dest_lng: float) -> Optional[Dict]:
        """
        Get route information using OSRM
        Returns: distance, duration, geometry
        """
        try:
            # OSRM format: coordinates;coordinates
            url = f"{self.base_url}/{origin_lng},{origin_lat};{dest_lng},{dest_lat}"
            params = {
                'overview': 'full',
                'steps': 'true',
                'annotations': 'duration,distance,speed'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 'Ok' and data.get('routes'):
                route = data['routes'][0]
                
                # Calculate estimated travel time
                duration_seconds = route.get('duration', 0)
                distance_meters = route.get('distance', 0)
                
                return {
                    "distance_km": distance_meters / 1000,
                    "duration_minutes": duration_seconds / 60,
                    "route_geometry": route.get('geometry'),
                    "steps": route.get('legs', [{}])[0].get('steps', []),
                    "api_source": "OSRM (Free/Open Source)",
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            return None
        
        except requests.RequestException as e:
            logger.error(f"OSRM error: {str(e)}")
            return None


class FreeWeatherService:
    """
    Open-Meteo Weather API - COMPLETELY FREE!
    No API key required
    Rate limit: None specified (free to use)
    Provides: temperature, precipitation, weather code
    """
    
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_weather(self, lat: float, lng: float) -> Optional[Dict]:
        """
        Get current weather conditions using Open-Meteo (FREE, no key needed)
        """
        try:
            params = {
                'latitude': lat,
                'longitude': lng,
                'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
                'timezone': 'auto'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('current'):
                current = data['current']
                weather_code = current.get('weather_code', 0)
                
                # Map WMO weather codes to traffic impact
                traffic_impact = self._get_weather_impact(weather_code)
                
                return {
                    "temperature": current.get('temperature_2m'),
                    "humidity": current.get('relative_humidity_2m'),
                    "wind_speed": current.get('wind_speed_10m'),
                    "weather_code": weather_code,
                    "traffic_impact": traffic_impact,
                    "source": "Open-Meteo (FREE - No Key Required)",
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            return None
        
        except requests.RequestException as e:
            logger.error(f"Weather API error: {str(e)}")
            return None
    
    @staticmethod
    def _get_weather_impact(wmo_code: int) -> str:
        """
        Map WMO weather codes to traffic impact
        WMO Code reference: https://open-meteo.com/en/docs
        """
        if wmo_code in [0, 1, 2]:  # Clear, Mainly clear, Partly cloudy
            return 'none'
        elif wmo_code in [3, 45, 48]:  # Overcast, Foggy
            return 'light'
        elif wmo_code in [51, 53, 55, 61, 63, 65]:  # Drizzle, Light rain
            return 'light'
        elif wmo_code in [71, 73, 75, 80, 82]:  # Snow, rain showers
            return 'moderate'
        elif wmo_code in [80, 81, 82]:  # Rain showers
            return 'moderate'
        elif wmo_code in [85, 86]:  # Snow showers
            return 'heavy'
        elif wmo_code in [80, 81, 82]:  # Showers
            return 'heavy'
        elif wmo_code in [95, 96, 99]:  # Thunderstorm
            return 'severe'
        else:
            return 'light'


class FreeIncidentService:
    """
    Free incident detection using various sources
    Options:
    1. Overpass API (OpenStreetMap) - For incidents tagged on map
    2. Crowd-sourced data from public datasets
    3. City open data portals
    """
    
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"
    
    def get_incidents_from_osm(self, lat: float, lng: float, radius_km: int = 5) -> List[Dict]:
        """
        Get incidents from OpenStreetMap using Overpass API
        Fetches: accidents, construction, road closures
        COMPLETELY FREE - No API key
        """
        try:
            # Overpass query format
            # Query radius in meters
            radius_meters = radius_km * 1000
            
            query = f"""
            [bbox:{lat-0.05},{lng-0.05},{lat+0.05},{lng+0.05}];
            (
              node["accident"](bbox);
              way["accident"](bbox);
              node["construction"](bbox);
              way["construction"](bbox);
              node["traffic_signals"](bbox);
            );
            out geom;
            """
            
            response = requests.post(
                self.overpass_url,
                data=query,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            incidents = []
            
            # Parse OSM elements
            for element in data.get('elements', []):
                if 'lat' in element and 'lon' in element:
                    tags = element.get('tags', {})
                    
                    if any(key in tags for key in ['accident', 'construction']):
                        incidents.append({
                            "type": next(
                                (v for k, v in tags.items() 
                                 if k in ['accident', 'construction']),
                                "incident"
                            ),
                            "description": tags.get('name', 'No description'),
                            "latitude": element.get('lat'),
                            "longitude": element.get('lon'),
                            "severity": "normal",
                            "source": "OpenStreetMap (Free)",
                            "recorded_at": datetime.utcnow().isoformat()
                        })
            
            return incidents
        
        except requests.RequestException as e:
            logger.error(f"OSM Overpass API error: {str(e)}")
            return []


class SimulatedTrafficData:
    """
    Generate realistic but not-real traffic data based on:
    - Time of day patterns
    - Weather conditions
    - Distance from city center
    - Road type assumptions
    
    This is for demonstration when real APIs aren't available
    """
    
    @staticmethod
    def generate_realistic_traffic(location_name: str, lat: float, lng: float, 
                                   weather_impact: str = 'none') -> Dict:
        """
        Generate traffic data based on realistic patterns
        Not real data, but useful for testing
        """
        import random
        from datetime import datetime
        
        # Time-based traffic patterns
        hour = datetime.now().hour
        
        # Base speeds (km/h) by time of day
        if 7 <= hour <= 9:  # Morning peak
            base_speed = random.randint(15, 25)
        elif 17 <= hour <= 19:  # Evening peak
            base_speed = random.randint(12, 22)
        elif 23 <= hour or hour <= 6:  # Night
            base_speed = random.randint(40, 60)
        else:  # Off-peak
            base_speed = random.randint(30, 50)
        
        # Weather impact modifier
        weather_modifiers = {
            'none': 1.0,
            'light': 0.85,
            'moderate': 0.65,
            'heavy': 0.45,
            'severe': 0.25
        }
        
        modified_speed = base_speed * weather_modifiers.get(weather_impact, 1.0)
        free_flow = 50  # Typical free-flow speed
        
        # Calculate congestion
        congestion = 1 - (modified_speed / free_flow)
        congestion = max(0, min(1, congestion))
        
        return {
            "location": location_name,
            "source": "Traffic Pattern Simulation (Not Real Data)",
            "live_speed_kmh": round(modified_speed, 1),
            "free_flow_speed_kmh": free_flow,
            "congestion_level": round(congestion, 2),
            "travel_time_minutes": None,  # Will be calculated from OSRM
            "delay_minutes": round((free_flow - modified_speed) / 10, 1) if modified_speed < free_flow else 0,
            "last_updated": datetime.utcnow().isoformat(),
            "note": "This is simulated traffic data for demonstration. Real data requires paid APIs."
        }


class FreeTrafficDataAggregator:
    """
    Aggregates traffic data from FREE sources only!
    
    Data sources:
    - Geocoding: OpenStreetMap/Nominatim (FREE)
    - Routing: OSRM - Open Source Routing Machine (FREE)
    - Weather: Open-Meteo (FREE, no key needed!)
    - Incidents: OpenStreetMap Overpass API (FREE)
    - Traffic patterns: Simulated based on time/weather (LOCAL)
    """
    
    def __init__(self):
        self.geocoder = FreeGeocodingService()
        self.routing = FreeRoutingService()
        self.weather = FreeWeatherService()
        self.incidents = FreeIncidentService()
        self.traffic_simulator = SimulatedTrafficData()
    
    def get_location_traffic(self, location_name: str) -> Optional[Dict]:
        """Get traffic data for a single location using FREE APIs"""
        try:
            # Step 1: Geocode location (FREE)
            geo_data = self.geocoder.geocode_location(location_name)
            if not geo_data:
                logger.error(f"Failed to geocode: {location_name}")
                return None
            
            lat, lng = geo_data['latitude'], geo_data['longitude']
            
            # Step 2: Get weather (FREE, no key needed)
            weather_data = self.weather.get_weather(lat, lng)
            weather_impact = weather_data.get('traffic_impact', 'none') if weather_data else 'none'
            
            # Step 3: Generate realistic traffic simulation (LOCAL)
            traffic_data = self.traffic_simulator.generate_realistic_traffic(
                location_name, lat, lng, weather_impact
            )
            
            result = {
                "location": location_name,
                "coordinates": {
                    "latitude": lat,
                    "longitude": lng
                },
                "traffic": traffic_data,
                "address": geo_data.get('address'),
                "data_sources": {
                    "geocoding": "OpenStreetMap (FREE)",
                    "traffic": "Simulated (LOCAL)",
                    "weather": "Open-Meteo (FREE, No Key)",
                    "incidents": "OpenStreetMap (FREE)"
                }
            }
            
            if weather_data:
                result["weather_impact"] = weather_data
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting location traffic: {e}")
            return None
    
    def get_route_traffic(self, source: str, destination: str) -> Optional[Dict]:
        """Get traffic data for a route using FREE APIs"""
        try:
            # Step 1: Geocode both locations
            source_geo = self.geocoder.geocode_location(source)
            dest_geo = self.geocoder.geocode_location(destination)
            
            if not source_geo or not dest_geo:
                return None
            
            source_lat, source_lng = source_geo['latitude'], source_geo['longitude']
            dest_lat, dest_lng = dest_geo['latitude'], dest_geo['longitude']
            
            # Step 2: Get route using OSRM (FREE)
            route_data = self.routing.get_route(source_lat, source_lng, dest_lat, dest_lng)
            
            if not route_data:
                return None
            
            # Step 3: Get weather for origin (FREE)
            weather_data = self.weather.get_weather(source_lat, source_lng)
            weather_impact = weather_data.get('traffic_impact', 'none') if weather_data else 'none'
            
            # Step 4: Estimate traffic impact on route
            base_duration = route_data.get('duration_minutes', 0)
            
            # Apply weather impact
            weather_factors = {
                'none': 1.0,
                'light': 1.1,
                'moderate': 1.25,
                'heavy': 1.5,
                'severe': 2.0
            }
            
            traffic_duration = base_duration * weather_factors.get(weather_impact, 1.0)
            delay = traffic_duration - base_duration
            
            return {
                "source": source,
                "destination": destination,
                "distance_km": route_data.get('distance_km'),
                "normal_duration_minutes": round(base_duration, 1),
                "traffic_duration_minutes": round(traffic_duration, 1),
                "delay_minutes": round(delay, 1),
                "weather_impact": weather_data if weather_data else None,
                "data_sources": {
                    "routing": "OSRM (FREE/Open Source)",
                    "weather": "Open-Meteo (FREE)",
                    "traffic_prediction": "Simulated (LOCAL)"
                },
                "note": "Route timing based on OSRM + weather simulation",
                "last_updated": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error getting route traffic: {e}")
            return None
    
    def get_area_incidents(self, lat: float, lng: float, radius_km: int = 5) -> List[Dict]:
        """Get incidents in an area using FREE APIs"""
        try:
            incidents = self.incidents.get_incidents_from_osm(lat, lng, radius_km)
            return incidents
        except Exception as e:
            logger.error(f"Error getting incidents: {e}")
            return []
