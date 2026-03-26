"""
Audio Traffic Detection System - Integration Module
Main orchestrator for Producer-Consumer architecture
"""

import queue
import threading
import time
from datetime import datetime
import logging

from services.audio_producer import AudioProducer
from services.audio_consumer import AudioConsumer

logger = logging.getLogger(__name__)


class AudioTrafficDetectionSystem:
    """
    Main system orchestrator
    Coordinates producer, queue, and consumer for audio-based traffic detection
    """
    
    def __init__(self, model_path: str = None, 
                 audio_source: str = 'microphone',
                 audio_file: str = None,
                 buffer_size: int = 10):
        """
        Initialize audio traffic detection system
        
        Args:
            model_path: Path to trained ML model
            audio_source: 'microphone' or 'file'
            audio_file: Path to audio file (if source='file')
            buffer_size: Maximum buffer size
        """
        # Create queue
        self.audio_buffer = queue.Queue(maxsize=buffer_size)
        
        # Create producer
        self.producer = AudioProducer(
            audio_queue=self.audio_buffer,
            sample_rate=16000,
            chunk_duration=2.0,
            source=audio_source,
            audio_file=audio_file
        )
        
        # Create consumer
        self.consumer = AudioConsumer(
            audio_queue=self.audio_buffer,
            model_path=model_path,
            sample_rate=16000
        )
        
        self.running = False
        self.producer_thread = None
        self.consumer_thread = None
        
        # Prediction callback (for integration with Flask/WebSocket)
        self.prediction_callback = None
    
    def set_prediction_callback(self, callback):
        """
        Set callback function to be called when prediction is ready
        
        Args:
            callback: Function that receives PredictionResult
        """
        self.prediction_callback = callback
        # Override consumer's on_prediction method
        self.consumer.on_prediction = callback
    
    def start(self):
        """Start the entire system"""
        logger.info("="*60)
        logger.info("🎤 AUDIO TRAFFIC DETECTION SYSTEM STARTING...")
        logger.info("="*60)
        
        self.running = True
        
        # Start producer thread
        self.producer_thread = threading.Thread(
            target=self.producer.run,
            daemon=True,
            name="AudioProducer-Thread"
        )
        self.producer_thread.start()
        logger.info("[SYSTEM] ✓ Producer thread started")
        
        # Start consumer thread
        self.consumer_thread = threading.Thread(
            target=self.consumer.run,
            daemon=True,
            name="AudioConsumer-Thread"
        )
        self.consumer_thread.start()
        logger.info("[SYSTEM] ✓ Consumer thread started")
        
        logger.info("="*60)
        logger.info("🎯 System ready. Processing audio...\n")
    
    def get_latest_traffic_status(self) -> dict:
        """
        Get current traffic status (for API)
        
        Returns:
            Dictionary with latest prediction
        """
        prediction = self.consumer.get_latest_prediction()
        if prediction:
            return {
                'status': 'success',
                'timestamp': prediction.timestamp.isoformat(),
                'traffic_class': prediction.traffic_class,
                'confidence': float(prediction.confidence),
                'scores': prediction.raw_scores,
                'processing_time_ms': float(prediction.processing_time_ms)
            }
        return {'status': 'no_prediction_yet'}
    
    def get_prediction_history(self, limit: int = 10) -> list:
        """
        Get recent predictions
        
        Returns:
            List of recent predictions
        """
        predictions = self.consumer.get_prediction_history(limit)
        return [p.to_dict() for p in predictions]
    
    def get_queue_stats(self) -> dict:
        """
        Get queue statistics
        
        Returns:
            Dictionary with queue health information
        """
        return {
            'queue_size': self.audio_buffer.qsize(),
            'max_size': self.audio_buffer.maxsize,
            'fill_percentage': (self.audio_buffer.qsize() / self.audio_buffer.maxsize) * 100
        }
    
    def stop(self):
        """Stop the entire system"""
        logger.info("\n[SYSTEM] Stopping...")
        
        self.running = False
        self.producer.stop()
        self.consumer.stop()
        
        # Wait for threads to finish
        if self.producer_thread:
            self.producer_thread.join(timeout=5)
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)
        
        logger.info("[SYSTEM] ✓ Stopped")


# Global instance
audio_system = None


def initialize_audio_system(model_path: str = None,
                           audio_source: str = 'microphone',
                           audio_file: str = None):
    """
    Initialize the global audio traffic detection system
    
    Args:
        model_path: Path to trained ML model
        audio_source: 'microphone' or 'file'
        audio_file: Path to audio file
        
    Returns:
        AudioTrafficDetectionSystem instance
    """
    global audio_system
    
    audio_system = AudioTrafficDetectionSystem(
        model_path=model_path,
        audio_source=audio_source,
        audio_file=audio_file
    )
    
    return audio_system


def start_audio_system():
    """Start the global audio system"""
    global audio_system
    if audio_system:
        audio_system.start()
    else:
        logger.error("Audio system not initialized. Call initialize_audio_system first.")


def get_audio_system():
    """Get the global audio system instance"""
    return audio_system
