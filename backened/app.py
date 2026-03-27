"""
Production Traffic Detection System - Main Flask Application
Real-time intelligent traffic monitoring using Audio ML and FREE APIs
India-focused implementation with zero dependencies on paid services
"""

import os
import logging
import queue
import threading
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

# Import custom services
from config import config
from database.models import setup_database, DatabaseManager
from services.free_traffic_service import FreeTrafficDataAggregator
from services.cache_service import CacheService
from services.queue_system import create_queue_manager
from services.audio_producer import AudioProducer
from services.audio_consumer import AudioConsumer
from services.ml_prediction_service import TrafficPredictionModel
from services.api_handler import register_api_routes

# ===== FLASK APP SETUP =====

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Load environment configuration
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Enable CORS for frontend communication
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Initialize WebSocket for real-time updates
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25
)

# ===== SERVICE INITIALIZATION =====

logger.info("=" * 70)
logger.info("🚦 TRAFFIC DETECTION SYSTEM - PRODUCTION INITIALIZATION")
logger.info("=" * 70)

# Core services
db = DatabaseManager()
cache = CacheService(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
queue_manager = create_queue_manager(os.getenv('REDIS_URL', None))
traffic_aggregator = FreeTrafficDataAggregator()

logger.info("✓ Core services initialized")
logger.info(f"  ├─ Database: SQLite")
logger.info(f"  ├─ Cache: {'Redis' if cache.is_available() else 'Disabled (Redis unavailable)'}")
logger.info(f"  ├─ Queue: {'Redis-backed' if queue_manager.backend.__class__.__name__ == 'RedisQueue' else 'In-memory'}")
logger.info(f"  └─ Traffic APIs: 100% FREE")

# ML Model
ml_model = None
audio_producer = None
audio_consumer = None
audio_queue = None

def initialize_ml_and_audio():
    """Initialize ML model and audio producer-consumer system"""
    global ml_model, audio_producer, audio_consumer, audio_queue
    
    logger.info("\n" + "=" * 70)
    logger.info("🤖 ML MODEL INITIALIZATION")
    logger.info("=" * 70)
    
    model_path = os.getenv('MODEL_PATH', None)
    ml_model = TrafficPredictionModel(model_path=model_path)
    logger.info(f"✓ ML Model: {ml_model.model_version}")
    logger.info(f"  └─ Status: {'Training ready' if ml_model.model else 'Using mock model (demo mode)'}")
    
    logger.info("\n" + "=" * 70)
    logger.info("🎤 AUDIO PRODUCER-CONSUMER SYSTEM")
    logger.info("=" * 70)
    
    try:
        audio_queue = queue.Queue(maxsize=100)
        audio_source = os.getenv('AUDIO_SOURCE', 'synthetic')
        audio_file = os.getenv('AUDIO_FILE', None)
        
        logger.info(f"📡 Audio Source: {audio_source.upper()}")
        
        # Initialize producer
        audio_producer = AudioProducer(
            audio_queue=audio_queue,
            sample_rate=16000,
            chunk_duration=2.0,
            source=audio_source,
            audio_file=audio_file
        )
        audio_producer.start()
        logger.info("✓ Audio Producer: STARTED")
        
        # Initialize consumer
        audio_consumer = AudioConsumer(
            audio_queue=audio_queue,
            model_path=model_path,
            sample_rate=16000
        )
        
        # Override on_prediction callback
        def broadcast_prediction(prediction):
            if prediction:
                logger.info(f"🎯 Audio Prediction: {prediction.traffic_class.upper()} " +
                          f"({prediction.confidence*100:.1f}% confidence)")
                
                # Emit to connected clients
                socketio.emit('audio_update', prediction.to_dict(), broadcast=True)
                
                # Save to database
                try:
                    db.save_traffic_data(f"audio_chunk_{prediction.chunk_id}", {
                        'source': 'audio_ml',
                        'traffic_class': prediction.traffic_class,
                        'confidence': float(prediction.confidence),
                        'timestamp': prediction.timestamp.isoformat()
                    })
                except Exception as e:
                    logger.warning(f"Could not save prediction to DB: {e}")
        
        audio_consumer.on_prediction = broadcast_prediction
        audio_consumer.start()
        logger.info("✓ Audio Consumer: STARTED")
        
    except Exception as e:
        logger.warning(f"⚠️ Audio system setup failed: {e}")
        logger.info("   System will continue with API-based traffic detection only")

def init_app():
    """Initialize application: database, services, and routes"""
    
    logger.info("\n" + "=" * 70)
    logger.info("📁 DATABASE INITIALIZATION")
    logger.info("=" * 70)
    
    try:
        setup_database('database/traffic.db')
        logger.info("✓ Database: Ready")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Initialize ML and audio
    try:
        initialize_ml_and_audio()
    except Exception as e:
        logger.error(f"⚠️ ML/Audio initialization error: {e}")
    
    # Register API routes
    logger.info("\n" + "=" * 70)
    logger.info("🔗 API ROUTES REGISTRATION")
    logger.info("=" * 70)
    
    try:
        register_api_routes(app, db, cache, traffic_aggregator, ml_model, queue_manager, audio_consumer)
        logger.info("✓ API Routes: Registered")
    except Exception as e:
        logger.error(f"❌ Route registration failed: {e}")
        raise
    
    logger.info("\n" + "=" * 70)
    logger.info("✅ APPLICATION READY FOR PRODUCTION")
    logger.info("=" * 70)
    logger.info(f"Environment: {env}")
    logger.info(f"Start time: {datetime.now().isoformat()}")
    logger.info("=" * 70 + "\n")

# ===== WEBSOCKET EVENTS =====

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket client connection"""
    logger.info(f"👤 Client connected: {request.sid}")
    socketio.emit('connection_response', {'status': 'Connected to traffic system'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket client disconnection"""
    logger.info(f"👤 Client disconnected: {request.sid}")

@socketio.on('request_audio_update')
def handle_audio_request():
    """Handle client request for latest audio prediction"""
    if audio_consumer:
        latest = audio_consumer.get_latest_prediction()
        if latest:
            socketio.emit('audio_update', latest.to_dict())

# ===== SHUTDOWN HANDLERS =====

def shutdown():
    """Graceful shutdown"""
    logger.info("\n" + "=" * 70)
    logger.info("🛑 SHUTTING DOWN SYSTEM")
    logger.info("=" * 70)
    
    if audio_producer:
        audio_producer.stop()
        logger.info("✓ Audio Producer: Stopped")
    
    if audio_consumer:
        audio_consumer.stop()
        logger.info("✓ Audio Consumer: Stopped")
    
    logger.info("✓ System shutdown complete")

# Register shutdown handler
import atexit
atexit.register(shutdown)

# ===== ENTRY POINT =====

# ===== INITIALIZE ON IMPORT =====
# This ensures routes and services are ready when running with Gunicorn
init_app()

# ===== ENTRY POINT =====

if __name__ == '__main__':
    # Run server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Starting server on port {port} (debug={debug})")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)
