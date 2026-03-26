import os
import logging
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
from services.traffic_service import TrafficDataAggregator
from services.cache_service import CacheService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Load configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Enable CORS
CORS(app)

# Initialize WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
db = DatabaseManager()
cache = CacheService(app.config.get('REDIS_URL', 'redis://localhost:6379/0'))

# Initialize traffic data aggregator
traffic_config = {
    'TOMTOM_API_KEY': app.config.get('TOMTOM_API_KEY'),
    'HERE_API_KEY': app.config.get('HERE_API_KEY'),
    'GOOGLE_MAPS_API_KEY': app.config.get('GOOGLE_MAPS_API_KEY'),
    'OPENWEATHER_API_KEY': app.config.get('OPENWEATHER_API_KEY')
}
traffic_aggregator = TrafficDataAggregator(traffic_config)

# Application initialization
def init_app():
    """Initialize application and database"""
    # Setup database with new schema
    setup_database('database/traffic.db')
    
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
            traffic_data = {
                "traffic": traffic_aggregator.tomtom.get_traffic_flow(lat, lng) or
                           traffic_aggregator.here.get_traffic_flow(lat, lng),
                "weather_impact": traffic_aggregator.weather.get_weather_impact(lat, lng)
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
    """Get historical traffic data"""
    try:
        location = request.args.get('location')
        hours = request.args.get('hours', 24, type=int)
        
        if not location:
            return jsonify({"error": "Location required"}), 400
        
        history = db.get_traffic_history(location, hours)
        
        return jsonify({
            "location": location,
            "hours": hours,
            "data_points": len(history),
            "history": [
                {
                    "speed_kmh": h[0],
                    "congestion_level": h[1],
                    "delay_minutes": h[2],
                    "timestamp": h[3]
                }
                for h in history
            ]
        })
    
    except Exception as e:
        logger.error(f"History query error: {e}")
        return jsonify({"error": str(e)}), 500


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