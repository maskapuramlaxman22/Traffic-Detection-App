import os
import logging
import queue
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom services
from config import config
from database.models import setup_database, DatabaseManager
from services.free_traffic_service import FreeTrafficDataAggregator  # Use FREE APIs
from services.cache_service import CacheService
from services.queue_system import create_queue_manager, RequestType, QueuePriority
from services.audio_producer import AudioProducer, AudioPacket
from services.audio_consumer import AudioConsumer
from services.ml_prediction_service import TrafficPredictionModel
from services.error_handling import APIError, ValidationError, create_error_response, create_success_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Enable CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize services
db = DatabaseManager()
cache = CacheService(app.config.get('REDIS_URL', 'redis://localhost:6379/0'))
queue_manager = create_queue_manager(os.getenv('REDIS_URL', None))
traffic_aggregator = FreeTrafficDataAggregator()

logger.info("=" * 60)
logger.info("🎉 Using 100% FREE APIs - No Costs!")
logger.info("=" * 60)
logger.info("Geocoding: OpenStreetMap (Nominatim) - FREE")
logger.info("Routing: OSRM (Open Source) - FREE")
logger.info("Audio ML: PyAudio + Librosa - FREE")
logger.info("=" * 60)

# Global variables for audio producer/consumer
audio_queue = queue.Queue(maxsize=100)
audio_producer = None
audio_consumer = None
ml_model = None

def init_app():
    """Initialize application and database"""
    global audio_producer, audio_consumer, ml_model
    
    # Setup database with new schema
    setup_database('database/traffic.db')
    logger.info("✓ Database initialized")
    
    # Initialize ML model
    model_path = os.getenv('MODEL_PATH', None)
    ml_model = TrafficPredictionModel(model_path=model_path)
    logger.info(f"✓ ML Model initialized: {ml_model.model_version}")
    
    # Initialize audio producer-consumer system
    logger.info("\n" + "="*60)
    logger.info("🎤 Initializing Audio Producer-Consumer System...")
    logger.info("="*60)
    
    try:
        audio_source = os.getenv('AUDIO_SOURCE', 'synthetic')  # Default to synthetic for demo
        audio_file = os.getenv('AUDIO_FILE', None)
        
        logger.info(f"🎙️ Audio Source: {audio_source}")
        
        # Create producer
        audio_producer = AudioProducer(
            audio_queue=audio_queue,
            sample_rate=16000,
            chunk_duration=2.0,
            source=audio_source,
            audio_file=audio_file
        )
        audio_producer.start()
        logger.info("✓ Audio Producer started")
        
        # Create consumer
        audio_consumer = AudioConsumer(
            audio_queue=audio_queue,
            model_path=model_path,
            sample_rate=16000
        )
        
        # Set callback to emit predictions via WebSocket
        original_on_prediction = audio_consumer.on_prediction
        def emit_prediction(prediction):
            """Callback to emit predictions to clients"""
            if prediction:
                logger.info(f"🔊 Audio Prediction: {prediction.traffic_class} (confidence: {prediction.confidence:.2%})")
                socketio.emit('audio_prediction_update', 
                             prediction.to_dict(),
                             broadcast=True)
                
                # Save to database
                db.save_traffic_data(f"Audio-Chunk-{prediction.chunk_id}", {
                    'source': 'audio_sensor',
                    'traffic_class': prediction.traffic_class,
                    'confidence': float(prediction.confidence),
                    'scores': prediction.raw_scores,
                    'timestamp': prediction.timestamp.isoformat()
                })
        
        audio_consumer.on_prediction = emit_prediction
        audio_consumer.start()
        logger.info("✓ Audio Consumer started")
        
    except Exception as e:
        logger.error(f"❌ Audio system initialization failed: {e}")
        logger.warning("⚠️ System will continue without audio, using API-based traffic only")
            logger.info("✓ Audio Traffic Detection System started\n")
        except Exception as e:
            logger.warning(f"⚠️  Audio system failed to start: {e}")
            logger.info("System will run without audio detection\n")
    
    except Exception as e:
        logger.warning(f"⚠️  Audio system initialization error: {e}")
        logger.info("System will run without audio detection. Backend API still operational.\n")
    
    # Preload major Indian locations for geocoding cache
    major_locations = [
        # Hyderabad areas
        ("Hyderabad - Banjara Hills", "Hyderabad", "Telangana", 17.4132, 78.4226, "Banjara Hills, Hyderabad, Telangana, India"),
        ("Hyderabad - Jubilee Hills", "Hyderabad", "Telangana", 17.4320, 78.4082, "Jubilee Hills, Hyderabad, Telangana, India"),
        ("Hyderabad - Hitech City", "Hyderabad", "Telangana", 17.4469, 78.3732, "Hi-tech City, Hyderabad, Telangana, India"),
        ("Hyderabad - Gachibowli", "Hyderabad", "Telangana", 17.4401, 78.3489, "Gachibowli, Hyderabad, Telangana, India"),
        ("Hyderabad - Secunderabad", "Hyderabad", "Telangana", 17.4399, 78.4983, "Secunderabad, Hyderabad, Telangana, India"),
        ("Hyderabad - Kukatpally", "Hyderabad", "Telangana", 17.4845, 78.4079, "Kukatpally, Hyderabad, Telangana, India"),
        ("Hyderabad - Ameerpet", "Hyderabad", "Telangana", 17.4325, 78.4489, "Ameerpet, Hyderabad, Telangana, India"),
        ("Hyderabad - Madhapur", "Hyderabad", "Telangana", 17.4481, 78.3904, "Madhapur, Hyderabad, Telangana, India"),
        
        # Telangana cities
        ("Warangal", "Warangal", "Telangana", 17.9784, 79.5937, "Warangal, Telangana, India"),
        ("Karimnagar", "Karimnagar", "Telangana", 18.4386, 79.1288, "Karimnagar, Telangana, India"),
        ("Nizamabad", "Nizamabad", "Telangana", 18.6725, 78.0941, "Nizamabad, Telangana, India"),
        
        # Major Indian cities
        ("Mumbai", "Mumbai", "Maharashtra", 19.0760, 72.8777, "Mumbai, Maharashtra, India"),
        ("Delhi", "Delhi", "Delhi", 28.7041, 77.1025, "Delhi, India"),
        ("Bangalore", "Bangalore", "Karnataka", 12.9716, 77.5946, "Bangalore, Karnataka, India"),
        ("Chennai", "Chennai", "Tamil Nadu", 13.0827, 80.2707, "Chennai, Tamil Nadu, India"),
        ("Kolkata", "Kolkata", "West Bengal", 22.5726, 88.3639, "Kolkata, West Bengal, India"),
    ]
    
    for loc_name, city, state, lat, lng, address in major_locations:
        db.add_location(loc_name, city, state, lat, lng, address)
    
    logger.info("Application initialized successfully")

# API Endpoints

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "message": "Real-Time Traffic Detection API",
        "version": "2.0.0",
        "status": "running",
        "cache_available": cache.is_available(),
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Detailed health check with service status"""
    return jsonify({
        "status": "healthy",
        "services": {
            "database": "operational",
            "cache": "operational" if cache.is_available() else "unavailable",
            "apis": "configured"
        },
        "timestamp": datetime.now().isoformat()
    })


@app.route('/api/v1/search_locations', methods=['GET'])
def search_locations():
    """
    Search for locations
    Query params: q (search query)
    """
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({"error": "Query must be at least 2 characters"}), 400
    
    try:
        # Geocode the location using real API
        geo_data = traffic_aggregator.geocoder.geocode_location(query)
        
        if geo_data:
            # Cache the result
            if cache:
                cache.cache_geocoding(query, geo_data)
            
            # Log search
            db.log_search('location_search', query, result_status='success')
            
            return jsonify([{
                "name": geo_data['name'],
                "address": geo_data.get('address'),
                "latitude": geo_data['latitude'],
                "longitude": geo_data['longitude']
            }])
        
        return jsonify([])
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        db.log_search('location_search', query, result_status='error')
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/traffic/current', methods=['GET'])
def get_current_traffic():
    """
    Get real-time traffic at a location
    Query params: location (location name) OR lat, lng (coordinates)
    """
    try:
        location = request.args.get('location')
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        
        if not location and (lat is None or lng is None):
            return jsonify({"error": "Provide 'location' OR 'lat' and 'lng'"}), 400
        
        # Validate coordinate ranges
        if lat is not None and lng is not None:
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                return jsonify({"error": "Invalid coordinates. Latitude must be between -90 and 90, Longitude between -180 and 180"}), 400
        
        # Try cache first
        if lat and lng and cache:
            cached = cache.get_cached_traffic(lat, lng)
            if cached:
                return jsonify(cached)
        
        # Get real traffic data
        if location:
            traffic_data = traffic_aggregator.get_location_traffic(location)
        else:
            # Get traffic for coordinates
            reverse_loc = traffic_aggregator.geocoder.reverse_geocode(lat, lng)
            if not reverse_loc:
                reverse_loc = f"Location ({lat}, {lng})"
            
            # Get weather impact
            weather_data = traffic_aggregator.weather.get_weather(lat, lng)
            weather_impact = weather_data.get('traffic_impact', 'none') if weather_data else 'none'
            
            # Generate traffic data
            traffic_sim = traffic_aggregator.traffic_simulator.generate_realistic_traffic(
                reverse_loc, lat, lng, weather_impact
            )
            
            # Get incidents in area
            incidents = traffic_aggregator.get_area_incidents(lat, lng, radius_km=5)
            
            traffic_data = {
                "location": reverse_loc,
                "coordinates": {
                    "latitude": lat,
                    "longitude": lng
                },
                "traffic": traffic_sim,
                "weather_impact": weather_data if weather_data else None,
                "incidents": incidents,
                "data_sources": {
                    "geocoding": "OpenStreetMap (FREE)",
                    "traffic": "Simulated (LOCAL)",
                    "weather": "Open-Meteo (FREE, No Key)",
                    "incidents": "OpenStreetMap (FREE)"
                }
            }
        
        if traffic_data:
            # Save to database
            db.save_traffic_data(traffic_data.get('location', location), traffic_data)
            
            # Cache result
            if cache and 'coordinates' in traffic_data:
                coords = traffic_data['coordinates']
                cache.cache_traffic(coords['latitude'], coords['longitude'], traffic_data)
            
            # Log search
            db.log_search('traffic_query', location or f"{lat},{lng}", result_status='success')
            
            return jsonify(traffic_data)
        
        return jsonify({"error": "Unable to fetch traffic data"}), 404
    
    except Exception as e:
        logger.error(f"Traffic query error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/traffic/route', methods=['POST'])
def get_route_traffic():
    """
    Get traffic data for a route between two locations
    POST body: {"source": str, "destination": str}
    """
    try:
        data = request.get_json()
        source = data.get('source')
        destination = data.get('destination')
        
        if not source or not destination:
            return jsonify({"error": "Source and destination required"}), 400
        
        # Check cache
        if cache:
            cached = cache.get_cached_route(source, destination)
            if cached:
                return jsonify(cached)
        
        # Get real route traffic data
        route_data = traffic_aggregator.get_route_traffic(source, destination)
        
        if route_data:
            # Save to database
            db.save_route_traffic(source, destination, route_data)
            
            # Cache result
            if cache:
                cache.cache_route(source, destination, route_data)
            
            # Log search
            db.log_search('route_search', source=source, destination=destination, result_status='success')
            
            return jsonify(route_data)
        
        return jsonify({"error": "Unable to fetch route traffic data"}), 404
    
    except Exception as e:
        logger.error(f"Route traffic error: {e}")
        db.log_search('route_search', source=data.get('source'), 
                     destination=data.get('destination'), result_status='error')
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/incidents', methods=['GET'])
def get_incidents():
    """
    Get traffic incidents in an area
    Query params: lat, lng, radius_km (optional, default 5)
    """
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius_km = request.args.get('radius_km', 5, type=int)
        
        if lat is None or lng is None:
            return jsonify({"error": "Latitude and longitude required"}), 400
        
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({"error": "Invalid coordinates. Latitude must be between -90 and 90, Longitude between -180 and 180"}), 400
        
        # Check cache
        if cache:
            cached = cache.get_cached_incidents(lat, lng)
            if cached:
                return jsonify({"incidents": cached})
        
        # Get real incident data
        incidents = traffic_aggregator.get_area_incidents(lat, lng, radius_km)
        
        # Save to database
        if incidents:
            db.save_incidents(incidents)
            
            # Cache result
            if cache:
                cache.cache_incidents(lat, lng, incidents)
        
        return jsonify({
            "latitude": lat,
            "longitude": lng,
            "incidents": incidents,
            "count": len(incidents),
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Incidents query error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/traffic/history', methods=['GET'])
def get_traffic_history():
    """
    Get historical traffic data
    Query params: location (optional), hours (optional, default 24)
    If no location provided, returns recent search history
    """
    try:
        location = request.args.get('location')
        hours = request.args.get('hours', 24, type=int)
        
        # If no location, return all recent searches (from search log)
        if not location:
            recent_searches = db.get_recent_searches(limit=100)
            return jsonify({
                "type": "all_searches",
                "hours": hours,
                "data_points": len(recent_searches) if recent_searches else 0,
                "history": recent_searches or [],
                "total": len(recent_searches) if recent_searches else 0
            })
        
        # Else return traffic history for specific location
        history = db.get_traffic_history(location, hours)
        
        return jsonify({
            "location": location,
            "hours": hours,
            "data_points": len(history) if history else 0,
            "history": [
                {
                    "speed_kmh": h[0],
                    "congestion_level": h[1],
                    "delay_minutes": h[2],
                    "timestamp": h[3]
                }
                for h in (history or [])
            ]
        })
    
    except Exception as e:
        logger.error(f"History query error: {e}")
        return jsonify({"error": str(e), "history": [], "total": 0}), 500


@app.route('/api/v1/settings', methods=['GET', 'POST'])
def settings():
    """Get or update application settings"""
    if request.method == 'GET':
        return jsonify({
            "refresh_interval": 30,
            "alerts_enabled": True,
            "cache_enabled": cache.is_available(),
            "max_search_results": 20
        })
    
    elif request.method == 'POST':
        data = request.get_json()
        # Update settings logic here
        return jsonify({"message": "Settings updated"})


# ============================================================
# AUDIO-BASED TRAFFIC DETECTION ENDPOINTS (Producer-Consumer)
# ============================================================

@app.route('/api/v1/audio/status', methods=['GET'])
def get_audio_status():
    """
    Get current status of audio traffic detection system
    """
    try:
        audio_system = get_audio_system()
        
        if audio_system:
            status = {
                'status': 'active',
                'latest_prediction': None,
                'queue_stats': audio_system.get_queue_stats()
            }
            
            latest = audio_system.get_latest_traffic_status()
            if latest and latest.get('status') != 'no_prediction_yet':
                status['latest_prediction'] = latest
            
            return jsonify(status)
        else:
            return jsonify({'status': 'not_initialized'}), 503
    
    except Exception as e:
        logger.error(f"Audio status error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/audio/latest', methods=['GET'])
def get_latest_audio_prediction():
    """
    Get the latest traffic prediction from audio analysis
    """
    try:
        audio_system = get_audio_system()
        
        if audio_system:
            prediction = audio_system.get_latest_traffic_status()
            return jsonify(prediction)
        else:
            return jsonify({'error': 'Audio system not initialized'}), 503
    
    except Exception as e:
        logger.error(f"Audio prediction error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/audio/history', methods=['GET'])
def get_audio_prediction_history():
    """
    Get history of recent audio predictions
    Query params: limit (optional, default 10)
    """
    try:
        limit = request.args.get('limit', 10, type=int)
        audio_system = get_audio_system()
        
        if audio_system:
            history = audio_system.get_prediction_history(limit)
            return jsonify({
                'count': len(history),
                'predictions': history
            })
        else:
            return jsonify({'error': 'Audio system not initialized'}), 503
    
    except Exception as e:
        logger.error(f"Audio history error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/audio/stats', methods=['GET'])
def get_audio_system_stats():
    """
    Get detailed statistics about the audio processing system
    """
    try:
        audio_system = get_audio_system()
        
        if audio_system:
            stats = {
                'queue': audio_system.get_queue_stats(),
                'total_predictions': len(audio_system.consumer.predictions),
                'latest_prediction': None
            }
            
            latest = audio_system.consumer.get_latest_prediction()
            if latest:
                stats['latest_prediction'] = latest.to_dict()
            
            return jsonify(stats)
        else:
            return jsonify({'error': 'Audio system not initialized'}), 503
    
    except Exception as e:
        logger.error(f"Audio stats error: {e}")
        return jsonify({"error": str(e)}), 500


# WebSocket Events for Real-Time Updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected")
    emit('connect_response', {'data': 'Connected to real-time traffic updates'})


@socketio.on('subscribe_location')
def handle_subscribe(data):
    """Subscribe to real-time traffic updates for a location"""
    location = data.get('location')
    if location:
        # TODO: Implement real-time updates using a background task
        emit('subscribed', {'location': location, 'status': 'subscribed'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialize application
    init_app()
    
    # Run Flask-SocketIO server
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"Starting Traffic Detection API Server on port {port}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Cache available: {cache.is_available()}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode, allow_unsafe_werkzeug=True)