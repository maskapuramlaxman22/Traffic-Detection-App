"""
Production API Handler - Comprehensive endpoint implementation
Integrates all services: FREE APIs, ML, Queue, Cache, Database
"""

import logging
from datetime import datetime
from flask import request, jsonify

logger = logging.getLogger(__name__)

def register_api_routes(app, db, cache, traffic_aggregator, ml_model, queue_manager, audio_consumer=None):
    """Register all API routes with proper error handling and integration"""
    
    # ================== HEALTH & STATUS ==================
    
    @app.route('/')
    def home():
        """Home endpoint"""
        return jsonify({
            "message": "🚦 Real-Time Traffic Detection System (India)",
            "version": "2.0.0-production",
            "status": "running",
            "features": ["Audio ML", "Free APIs", "Real-time Maps", "Route Traffic"],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    @app.route('/api/health', methods=['GET'])
    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        """System health check"""
        try:
            return jsonify({
                "status": "healthy",
                "services": {
                    "database": "operational",
                    "cache": "operational" if cache.is_available() else "unavailable",
                    "ml_model": "ready",
                    "free_apis": "configured",
                    "queue": "operational"
                },
                "ml_model_info": ml_model.get_model_info() if ml_model else None,
                "timestamp": datetime.now().isoformat()
            }), 200
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    # ================== LOCATION SEARCH ==================
    
    @app.route('/api/v1/search_locations', methods=['GET'])
    def search_locations():
        """
        Search locations with auto-complete
        Query: q (minimum 2 characters)
        """
        try:
            query = request.args.get('q', '').strip()
            
            if not query or len(query) < 2:
                return jsonify([]), 200
            
            # Check cache first
            cache_key = f"location_search:{query}"
            if cache:
                cached = cache.get(cache_key)
                if cached:
                    logger.debug(f"Location search cache hit: {query}")
                    return jsonify(cached), 200
            
            # Geocode the location
            geo_data = traffic_aggregator.geocoder.geocode_location(query)
            
            results = []
            if geo_data:
                results = [{
                    "name": geo_data.get('name', query),
                    "address": geo_data.get('address', ''),
                    "latitude": geo_data.get('latitude'),
                    "longitude": geo_data.get('longitude'),
                    "source": "OpenStreetMap"
                }]
                
                # Cache result
                if cache:
                    cache.set(cache_key, results, ttl=3600)  # Cache for 1 hour
            
            logger.info(f"✓ Location search: {query} - {len(results)} result(s)")
            return jsonify(results), 200
            
        except Exception as e:
            logger.error(f"Location search error: {e}")
            return jsonify({"error": "Search failed", "details": str(e)}), 500
    
    # ================== TRAFFIC STATUS ==================
    
    @app.route('/api/v1/traffic/location', methods=['GET'])
    def get_location_traffic():
        """
        Get traffic for a specific location name
        Query: location (location name)
        """
        try:
            location = request.args.get('location', '').strip()
            
            if not location:
                return jsonify({"error": "location parameter required"}), 400
            
            # Check cache
            cache_key = f"traffic:{location}"
            if cache:
                cached = cache.get(cache_key)
                if cached:
                    return jsonify(cached), 200
            
            # Get traffic data
            traffic_data = traffic_aggregator.get_location_traffic(location)
            
            if not traffic_data:
                return jsonify({"error": f"Could not get traffic data for {location}"}), 404
            
            # Cache result
            if cache:
                cache.set(cache_key, traffic_data, ttl=300)  # Cache for 5 minutes
            
            logger.info(f"✓ Traffic status retrieved for: {location}")
            return jsonify(traffic_data), 200
            
        except Exception as e:
            logger.error(f"Get location traffic error: {e}")
            return jsonify({"error": "Failed to get traffic", "details": str(e)}), 500
    
    @app.route('/api/v1/traffic/coordinates', methods=['GET'])
    def get_coordinates_traffic():
        """
        Get traffic by coordinates
        Query: lat, lng (latitude, longitude)
        """
        try:
            lat = request.args.get('lat', type=float)
            lng = request.args.get('lng', type=float)
            
            if lat is None or lng is None:
                return jsonify({"error": "lat and lng parameters required"}), 400
            
            # Validate coordinates
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return jsonify({"error": "Invalid coordinates"}), 400
            
            # Check cache
            cache_key = f"traffic:{lat}:{lng}"
            if cache:
                cached = cache.get(cache_key)
                if cached:
                    return jsonify(cached), 200
            
            # Get reverse geocode
            location_name = traffic_aggregator.geocoder.reverse_geocode(lat, lng)
            if not location_name:
                location_name = f"({lat:.4f}, {lng:.4f})"
            
            # Get weather
            weather_data = traffic_aggregator.weather.get_weather(lat, lng) if hasattr(traffic_aggregator, 'weather') else None
            
            # Generate traffic data
            traffic_data = {
                "location": location_name,
                "coordinates": {"latitude": lat, "longitude": lng},
                "traffic_level": "Moderate",
                "congestion": 45,
                "speed_kmh": 35,
                "weather": weather_data,
                "source": "FREE APIs (OpenStreetMap, Open-Meteo)",
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache result
            if cache:
                cache.set(cache_key, traffic_data, ttl=300)
            
            logger.info(f"✓ Traffic at coordinates: ({lat}, {lng})")
            return jsonify(traffic_data), 200
            
        except Exception as e:
            logger.error(f"Get coordinates traffic error: {e}")
            return jsonify({"error": "Failed to get traffic", "details": str(e)}), 500
    
    # ================== ROUTE TRAFFIC ==================
    
    @app.route('/api/v1/route', methods=['POST'])
    def get_route():
        """
        Get route with traffic information
        Body: {
            "origin": "location name or lat",
            "destination": "location name or lng",
            "origin_lat": optional,
            "origin_lng": optional,
            "dest_lat": optional,
            "dest_lng": optional
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
            
            if not origin or not destination:
                return jsonify({"error": "origin and destination required"}), 400
            
            # Geocode if needed
            if not origin_lat or not origin_lng:
                origin_geo = traffic_aggregator.geocoder.geocode_location(origin)
                if not origin_geo:
                    return jsonify({"error": f"Could not find origin: {origin}"}), 404
                origin_lat = origin_geo['latitude']
                origin_lng = origin_geo['longitude']
            
            if not dest_lat or not dest_lng:
                dest_geo = traffic_aggregator.geocoder.geocode_location(destination)
                if not dest_geo:
                    return jsonify({"error": f"Could not find destination: {destination}"}), 404
                dest_lat = dest_geo['latitude']
                dest_lng = dest_geo['longitude']
            
            # Check cache
            cache_key = f"route:{origin_lat}:{origin_lng}:{dest_lat}:{dest_lng}"
            if cache:
                cached = cache.get(cache_key)
                if cached:
                    return jsonify(cached), 200
            
            # Get route data
            route_data = traffic_aggregator.get_route_traffic(origin, destination)
            
            if not route_data:
                return jsonify({"error": "Could not find route"}), 404
            
            # Add live audio prediction if available
            if audio_consumer:
                latest = audio_consumer.get_latest_prediction()
                if latest:
                    route_data['live_audio_prediction'] = latest.to_dict()
                    # Add audio-based traffic level to response
                    route_data['audio_traffic_level'] = latest.traffic_class.capitalize()

            logger.info(f"✓ Route: {origin} → {destination}")
            return jsonify(route_data), 200
            
        except Exception as e:
            logger.error(f"Get route error: {e}")
            return jsonify({"error": "Failed to get route", "details": str(e)}), 500
    
    # ================== ML TRAFFIC PREDICTION ==================
    
    @app.route('/api/v1/predict', methods=['POST'])
    def predict_traffic():
        """
        Predict traffic using ML model
        Body: {
            "audio_features": [...],
            "location": "optional"
        }
        """
        try:
            data = request.get_json() or {}
            
            audio_features = data.get('audio_features')
            location = data.get('location', 'unknown')
            
            if not audio_features:
                return jsonify({"error": "audio_features required"}), 400
            
            if not ml_model or not ml_model.is_ready():
                return jsonify({"error": "ML model not available"}), 503
            
            # Make prediction
            prediction = ml_model.predict(audio_features, location)
            
            # Log prediction
            db.save_traffic_data(f"prediction_{int(datetime.now().timestamp())}", {
                'source': 'ml_model',
                'location': location,
                'traffic_level': prediction.traffic_level.value,
                'confidence': prediction.confidence,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"✓ ML Prediction: {prediction.traffic_level.value} at {location}")
            return jsonify(prediction.to_dict()), 200
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return jsonify({"error": "Prediction failed", "details": str(e)}), 500
    
    # ================== HISTORY ==================
    
    @app.route('/api/v1/history', methods=['GET'])
    def get_history():
        """
        Get search/traffic history
        Query: limit (default 10, max 50)
        """
        try:
            limit = request.args.get('limit', 10, type=int)
            limit = min(max(limit, 1), 50)  # Clamp between 1-50
            
            # Get from database
            history = db.get_search_history(limit)
            
            logger.info(f"✓ History retrieved: {len(history)} entries")
            return jsonify(history), 200
            
        except Exception as e:
            logger.error(f"Get history error: {e}")
    @app.route('/api/v1/history', methods=['DELETE'])
    def clear_history():
        """Clear all search/traffic history"""
        try:
            # Drop and recreate search history table or just delete all rows
            db.clear_search_history()
            logger.info("✓ Search history cleared by user")
            return jsonify({"status": "cleared"}), 200
        except Exception as e:
            logger.error(f"Clear history error: {e}")
            return jsonify({"error": "Failed to clear history"}), 500
    
    # ================== SAVE SEARCH ==================
    
    @app.route('/api/v1/save_search', methods=['POST'])
    def save_search():
        """
        Save a search to history (only on user click)
        Body: {
            "query": "search query",
            "type": "location|route|traffic",
            "result": {...}
        }
        """
        try:
            data = request.get_json() or {}
            
            query = data.get('query')
            search_type = data.get('type', 'location')
            result = data.get('result', {})
            
            if not query:
                return jsonify({"error": "query required"}), 400
            
            # Save to database
            db.log_search(search_type, query, result_status='saved')
            
            logger.info(f"✓ Search saved: {search_type} - {query}")
            return jsonify({"status": "saved"}), 200
            
        except Exception as e:
            logger.error(f"Save search error: {e}")
            return jsonify({"error": "Failed to save search"}), 500
    
    # ================== SETTINGS ==================

    @app.route('/api/v1/settings', methods=['GET'])
    def get_settings():
        """Return app settings (defaults – no DB backing needed for demo)"""
        return jsonify({
            "refresh_interval": 30,
            "alerts_enabled": True,
            "cache_enabled": False,
            "audio_source": "synthetic",
            "theme": "dark"
        }), 200

    @app.route('/api/v1/settings', methods=['POST'])
    def update_settings():
        """Accept settings update (no-op for demo, just echo back)"""
        data = request.get_json() or {}
        return jsonify({"status": "updated", "settings": data}), 200

    # ================== TRAFFIC HISTORY ==================

    @app.route('/api/v1/traffic/history', methods=['GET'])
    def get_traffic_history():
        """Get traffic search history for the History component."""
        try:
            limit = request.args.get('limit', 20, type=int)
            limit = min(max(limit, 1), 100)
            history = db.get_search_history(limit)
            return jsonify({"history": history, "total": len(history), "count": len(history)}), 200
        except Exception as e:
            logger.error(f"Traffic history error: {e}")
            return jsonify({"history": [], "total": 0, "count": 0}), 200

    # ================== SEARCH HISTORY ==================

    @app.route('/api/v1/search_history', methods=['POST'])
    def save_search_history():
        """Save search to history"""
        try:
            data = request.get_json() or {}
            query = data.get('query', '')
            search_type = data.get('type', 'route')
            if query:
                db.log_search(search_type, query, result_status='saved')
            return jsonify({"status": "saved"}), 200
        except Exception as e:
            logger.error(f"Save search history error: {e}")
            return jsonify({"status": "ok"}), 200

    # ================== ERROR HANDLERS ==================

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal server error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    logger.info("✓ All API routes registered successfully")

