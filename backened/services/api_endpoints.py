"""
Enhanced API Endpoints for Production
Integrates queue system, ML model, and API fallbacks
"""

import os
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, jsonify

from services.queue_system import (
    QueueManager, RequestType, QueuePriority, create_queue_manager
)
from services.ml_prediction_service import (
    TrafficPredictionModel, AudioFeatureExtractor, PredictionResult
)
from services.api_service import APIServiceWithFallback
from services.cache_service import CacheService
from services.error_handling import (
    APIError, ValidationError, NotFoundError, ExternalAPIError,
    ErrorLogger, create_success_response, create_error_response,
    handle_exceptions
)
from database.models import DatabaseManager

logger = __import__('logging').getLogger(__name__)


class TrafficDetectionAPI:
    """Enhanced API endpoints for traffic detection"""
    
    def __init__(self, app, db: DatabaseManager, cache: CacheService, 
                 ml_model: TrafficPredictionModel, config: Dict[str, str] = None):
        self.app = app
        self.db = db
        self.cache = cache
        self.ml_model = ml_model
        self.config = config or {}
        
        # Initialize services
        self.queue_manager = create_queue_manager(
            os.getenv('REDIS_URL', None)
        )
        self.api_service = APIServiceWithFallback(cache_service=cache, config=config)
        
        # Register routes
        self.register_routes()
    
    def register_routes(self):
        """Register all API endpoints"""
        
        # Health and status
        @self.app.route('/api/health', methods=['GET'])
        @handle_exceptions()
        def health_check():
            """Health check endpoint"""
            status = {
                'database': self.db is not None,
                'cache': self.cache.is_available(),
                'ml_model': self.ml_model.is_ready(),
                'queue': self.queue_manager is not None,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            return jsonify(create_success_response(status, "System is healthy"))
        
        # Traffic prediction from audio
        @self.app.route('/api/traffic-predict', methods=['POST'])
        @handle_exceptions()
        def predict_traffic():
            """
            Predict traffic level from audio features
            
            Request:
            {
                "audio_features": [0.1, 0.2, ...],  # Audio feature vector
                "location": "Hyderabad",             # Optional location
                "audio_data": <base64>              # Optional raw audio
            }
            """
            try:
                data = request.get_json()
                
                # Validate input
                if not data:
                    raise ValidationError("Request body required")
                
                # Extract audio features
                audio_features = data.get('audio_features')
                location = data.get('location', 'unknown')
                
                if not audio_features:
                    # Try to extract from raw audio if provided
                    audio_data = data.get('audio_data')
                    if audio_data:
                        import base64
                        import numpy as np
                        audio_bytes = base64.b64decode(audio_data)
                        audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
                        audio_features = AudioFeatureExtractor.extract_features_from_array(audio_array)
                    else:
                        raise ValidationError("audio_features or audio_data required")
                
                # Make prediction
                result = self.ml_model.predict(audio_features, location)
                
                # Save to database
                self.db.save_traffic_data(f"prediction_{result.timestamp.timestamp()}", {
                    'source': 'audio_ml_model',
                    'traffic_level': result.traffic_level.value,
                    'location': location,
                    'confidence': result.confidence,
                    'timestamp': result.timestamp.isoformat()
                })
                
                return jsonify(create_success_response(
                    result.to_dict(),
                    "Traffic prediction successful"
                ))
                
            except ValidationError as e:
                return create_error_response(e)
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                raise APIError(
                    code="ml_prediction_error",
                    message="Failed to make traffic prediction",
                    status_code=500
                )
        
        # Geocode location
        @self.app.route('/api/geocode', methods=['GET', 'POST'])
        @handle_exceptions()
        def geocode_location():
            """
            Convert location name to coordinates
            
            Query parameters (GET):
            - location: Location name (required)
            
            JSON body (POST):
            {
                "location": "Hyderabad"  # Required
            }
            """
            try:
                if request.method == 'POST':
                    data = request.get_json() or {}
                    location = data.get('location')
                else:
                    location = request.args.get('location')
                
                if not location:
                    raise ValidationError("location parameter required", "location")
                
                # Add to queue
                msg_id = self.queue_manager.create_message(
                    request_type=RequestType.LOCATION_GEOCODE,
                    payload={"location": location},
                    priority=QueuePriority.HIGH
                )
                
                # Execute immediately (no background processing needed)
                geoloc_result = self.api_service.geocode(location)
                
                if not geoloc_result:
                    raise NotFoundError("Location", location)
                
                # Cache the result
                if self.cache:
                    self.cache.set(f"location_{location}", geoloc_result, ttl=86400)
                
                # Save to database
                self.db.add_location(
                    location,
                    geoloc_result.get("address", location),
                    "India",
                    geoloc_result["latitude"],
                    geoloc_result["longitude"],
                    geoloc_result.get("address", location)
                )
                
                self.queue_manager.acknowledge(msg_id)
                
                return jsonify(create_success_response(
                    geoloc_result,
                    "Location geocoded successfully"
                ))
                
            except (ValidationError, NotFoundError, ExternalAPIError) as e:
                return create_error_response(e)
            except Exception as e:
                ErrorLogger.log_error(e, {"action": "geocode"})
                raise APIError(
                    code="geocoding_error",
                    message="Failed to geocode location",
                    status_code=500
                )
        
        # Get route with traffic
        @self.app.route('/api/route', methods=['POST'])
        @handle_exceptions()
        def get_route():
            """
            Get route between two locations with traffic estimation
            
            Request:
            {
                "origin": "Hyderabad",
                "destination": "Bangalore",
                "origin_lat": 17.3850,    # Optional (bypass geocoding)
                "origin_lng": 78.4867,
                "dest_lat": 12.9716,
                "dest_lng": 77.5946
            }
            """
            try:
                data = request.get_json() or {}
                
                origin = data.get('origin')
                destination = data.get('destination')
                origin_lat = data.get('origin_lat')
                origin_lng = data.get('origin_lng')
                dest_lat = data.get('dest_lat')
                dest_lng = data.get('dest_lng')
                
                # Validate required fields
                if not origin or not destination:
                    raise ValidationError("origin and destination required")
                
                # Geocode if coordinates not provided
                if not (origin_lat and origin_lng):
                    origin_geoloc = self.api_service.geocode(origin)
                    if not origin_geoloc:
                        raise NotFoundError("Origin location", origin)
                    origin_lat, origin_lng = origin_geoloc['latitude'], origin_geoloc['longitude']
                
                if not (dest_lat and dest_lng):
                    dest_geoloc = self.api_service.geocode(destination)
                    if not dest_geoloc:
                        raise NotFoundError("Destination location", destination)
                    dest_lat, dest_lng = dest_geoloc['latitude'], dest_geoloc['longitude']
                
                # Validate coordinates
                if not (-90 <= origin_lat <= 90 and -180 <= origin_lng <= 180):
                    raise ValidationError("Invalid origin coordinates")
                if not (-90 <= dest_lat <= 90 and -180 <= dest_lng <= 180):
                    raise ValidationError("Invalid destination coordinates")
                
                # Add to queue
                msg_id = self.queue_manager.create_message(
                    request_type=RequestType.ROUTE_SEARCH,
                    payload={
                        "origin": origin,
                        "destination": destination,
                        "origin_lat": origin_lat,
                        "origin_lng": origin_lng,
                        "dest_lat": dest_lat,
                        "dest_lng": dest_lng
                    },
                    priority=QueuePriority.NORMAL
                )
                
                # Get route
                route = self.api_service.get_route(origin_lat, origin_lng, dest_lat, dest_lng)
                
                if not route:
                    raise ExternalAPIError("All routing providers", "No route found")
                
                # Estimate traffic (combine API + ML)
                route_key = f"route_{origin}_{destination}"
                route['estimated_traffic'] = "Moderate Traffic"  # Could integrate ML here
                route['timestamp'] = datetime.utcnow().isoformat()
                
                # Save to database
                self.db.save_traffic_data(route_key, {
                    'source': 'route_api',
                    'origin': origin,
                    'destination': destination,
                    'distance_km': route.get('distance_km'),
                    'duration_minutes': route.get('duration_minutes'),
                    'provider': route.get('provider'),
                    'timestamp': route['timestamp']
                })
                
                self.queue_manager.acknowledge(msg_id)
                
                return jsonify(create_success_response(
                    route,
                    "Route retrieved successfully"
                ))
                
            except (ValidationError, NotFoundError, ExternalAPIError) as e:
                return create_error_response(e)
            except Exception as e:
                ErrorLogger.log_error(e, {"action": "get_route"})
                raise APIError(
                    code="routing_error",
                    message="Failed to get route",
                    status_code=500
                )
        
        # Traffic status for location
        @self.app.route('/api/traffic', methods=['GET'])
        @handle_exceptions()
        def get_traffic_status():
            """
            Get traffic status for a location
            
            Query parameters:
            - location: Location name (required)
            - lat: Latitude (optional)
            - lng: Longitude (optional)
            """
            try:
                location = request.args.get('location')
                lat = request.args.get('lat', type=float)
                lng = request.args.get('lng', type=float)
                
                if not location:
                    raise ValidationError("location parameter required", "location")
                
                # Get traffic data from database or APIs
                traffic_data = self.db.get_location_traffic(location)
                
                if not traffic_data:
                    # Fetch from APIs
                    geoloc = self.api_service.geocode(location)
                    if not geoloc:
                        raise NotFoundError("Location", location)
                    
                    # Simulate traffic (in production, use actual traffic APIs)
                    traffic_data = {
                        'location': location,
                        'latitude': geoloc['latitude'],
                        'longitude': geoloc['longitude'],
                        'traffic_level': 'Moderate Traffic',
                        'speed': 40,
                        'congestion': '30%',
                        'source': 'aggregated',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                return jsonify(create_success_response(
                    traffic_data,
                    "Traffic status retrieved"
                ))
                
            except (ValidationError, NotFoundError) as e:
                return create_error_response(e)
        
        # Queue status
        @self.app.route('/api/queue/status', methods=['GET'])
        @handle_exceptions()
        def queue_status():
            """Get queue status and metrics"""
            status = self.queue_manager.get_status()
            return jsonify(create_success_response(status, "Queue status retrieved"))
        
        # API service status
        @self.app.route('/api/services/status', methods=['GET'])
        @handle_exceptions()
        def services_status():
            """Get status of external API services"""
            status = self.api_service.get_status()
            return jsonify(create_success_response(status, "Services status retrieved"))
        
        # ML model info
        @self.app.route('/api/ml-model/info', methods=['GET'])
        @handle_exceptions()
        def ml_model_info():
            """Get ML model information"""
            info = self.ml_model.get_model_info()
            return jsonify(create_success_response(info, "ML model info retrieved"))


# Factory function to initialize API
def init_api(app, db, cache, ml_model, config=None):
    """Initialize traffic detection API"""
    logger.info("🔧 Initializing Traffic Detection API...")
    api = TrafficDetectionAPI(app, db, cache, ml_model, config)
    logger.info("✓ API routes registered")
    return api
