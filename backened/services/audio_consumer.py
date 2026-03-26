"""
Audio Consumer Module - Preprocessing, Feature Extraction, and ML Inference
Part of the Producer-Consumer architecture for traffic detection
"""

import numpy as np
import librosa
import threading
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class PredictionResult:
    """ML prediction output"""
    timestamp: datetime
    traffic_class: str          # 'heavy', 'medium', 'light', 'free'
    confidence: float           # 0.0 to 1.0
    raw_scores: dict            # {class: probability}
    processing_time_ms: float   # How long inference took
    chunk_id: int
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'traffic_class': self.traffic_class,
            'confidence': float(self.confidence),
            'raw_scores': self.raw_scores,
            'processing_time_ms': float(self.processing_time_ms),
            'chunk_id': self.chunk_id
        }
    
    def __repr__(self):
        return (f"Prediction(class={self.traffic_class}, "
                f"confidence={self.confidence:.2%}, "
                f"time={self.processing_time_ms:.1f}ms)")


class AudioPreprocessor:
    """
    Preprocesses audio: noise removal, normalization, etc.
    """
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
    
    def normalize(self, audio: np.ndarray) -> np.ndarray:
        """
        Normalize audio amplitude to [-1, 1] range
        
        Args:
            audio: Audio samples
            
        Returns:
            Normalized audio
        """
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio / max_val
        return audio
    
    def remove_silence(self, audio: np.ndarray, 
                       threshold_db: float = -40.0) -> np.ndarray:
        """
        Remove silent portions of audio
        
        Args:
            audio: Audio samples
            threshold_db: Silence threshold in dB
            
        Returns:
            Audio with silence removed
        """
        try:
            audio_trimmed, _ = librosa.effects.trim(
                audio, 
                top_db=-threshold_db
            )
            return audio_trimmed
        except Exception as e:
            logger.warning(f"Silence removal error: {e}, returning original")
            return audio
    
    def apply_bandpass_filter(self, audio: np.ndarray,
                             low_freq: int = 100,
                             high_freq: int = 8000) -> np.ndarray:
        """
        Apply bandpass filter to remove very low/high frequencies
        (Traffic noise is typically in 100Hz - 8000Hz range)
        
        Args:
            audio: Audio samples
            low_freq: Low cutoff frequency
            high_freq: High cutoff frequency
            
        Returns:
            Filtered audio
        """
        try:
            D = librosa.stft(audio)
            magnitude = np.abs(D)
            phase = np.angle(D)
            
            # Create frequency mask
            freqs = librosa.fft_frequencies(sr=self.sample_rate)
            mask = (freqs > low_freq) & (freqs < high_freq)
            
            # Apply mask
            magnitude_filtered = magnitude.copy()
            magnitude_filtered[~mask, :] = 0
            
            # Reconstruct
            S_filtered = magnitude_filtered * np.exp(1j * phase)
            audio_filtered = librosa.istft(S_filtered)
            
            return audio_filtered
        except Exception as e:
            logger.warning(f"Bandpass filter error: {e}, returning original")
            return audio
    
    def preprocess(self, audio: np.ndarray) -> np.ndarray:
        """
        Complete preprocessing pipeline
        
        Args:
            audio: Raw audio samples
            
        Returns:
            Preprocessed audio ready for feature extraction
        """
        # Step 1: Normalize
        audio = self.normalize(audio)
        
        # Step 2: Remove silence
        audio = self.remove_silence(audio, threshold_db=-35)
        
        # Step 3: Apply bandpass filter
        audio = self.apply_bandpass_filter(audio)
        
        return audio


class FeatureExtractor:
    """
    Extracts MFCC and other features from audio
    """
    
    def __init__(self, sample_rate: int = 16000, n_mfcc: int = 13):
        self.sample_rate = sample_rate
        self.n_mfcc = n_mfcc
    
    def extract_mfcc(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract MFCC (Mel-Frequency Cepstral Coefficients)
        
        Args:
            audio: Audio samples
            
        Returns:
            MFCC matrix shape (n_mfcc, time_steps)
        """
        try:
            # Compute MFCC
            mfcc = librosa.feature.mfcc(
                y=audio,
                sr=self.sample_rate,
                n_mfcc=self.n_mfcc,
                n_fft=2048,
                hop_length=512
            )
            return mfcc
        except Exception as e:
            logger.error(f"MFCC extraction error: {e}")
            # Return dummy MFCC
            return np.zeros((self.n_mfcc, 100))
    
    def extract_spectral_features(self, audio: np.ndarray) -> dict:
        """
        Extract additional spectral features
        
        Args:
            audio: Audio samples
            
        Returns:
            Dictionary of spectral features
        """
        try:
            # Zero Crossing Rate (speech indicator)
            zcr = librosa.feature.zero_crossing_rate(audio)[0]
            
            # Spectral Centroid (brightness)
            spec_cent = librosa.feature.spectral_centroid(y=audio, sr=self.sample_rate)[0]
            
            # Spectral Rolloff
            spec_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=self.sample_rate)[0]
            
            return {
                'spectral_centroid': float(spec_cent.mean()),
                'spectral_rolloff': float(spec_rolloff.mean()),
                'zero_crossing_rate': float(zcr.mean())
            }
        except Exception as e:
            logger.warning(f"Spectral features extraction error: {e}")
            return {
                'spectral_centroid': 0.0,
                'spectral_rolloff': 0.0,
                'zero_crossing_rate': 0.0
            }
    
    def extract_features(self, audio: np.ndarray) -> np.ndarray:
        """
        Extract all features and prepare for ML model
        
        Args:
            audio: Preprocessed audio
            
        Returns:
            Feature matrix ready for model input
        """
        # Extract MFCC
        mfcc = self.extract_mfcc(audio)
        
        # Extract spectral features
        spectral = self.extract_spectral_features(audio)
        
        # Normalize MFCC
        mfcc_normalized = (mfcc - mfcc.mean(axis=1, keepdims=True)) / (
            mfcc.std(axis=1, keepdims=True) + 1e-8
        )
        
        # Transpose for model input: (time_steps, features)
        features = mfcc_normalized.T
        
        logger.debug(f"[FEATURE_EXTRACTOR] Final shape: {features.shape}")
        
        return features


class TrafficPredictor:
    """
    Loads trained ML model and makes predictions
    For demo purposes, uses a simple statistical model
    """
    
    # Class mapping
    CLASSES = ['heavy', 'medium', 'light', 'free']
    CLASS_MAPPING = {0: 'heavy', 1: 'medium', 2: 'light', 3: 'free'}
    
    def __init__(self, model_path: str = None):
        """
        Initialize predictor
        
        Args:
            model_path: Path to .h5 or .keras model file (optional)
        """
        self.model = None
        self.model_path = model_path
        
        if model_path:
            try:
                import tensorflow as tf
                logger.info(f"[PREDICTOR] Loading model from {model_path}...")
                self.model = tf.keras.models.load_model(model_path)
                logger.info("[PREDICTOR] ✓ Model loaded successfully")
            except Exception as e:
                logger.warning(f"[PREDICTOR] Could not load model: {e}")
                logger.info("[PREDICTOR] Using fallback statistical model")
    
    def predict(self, features: np.ndarray) -> PredictionResult:
        """
        Make traffic prediction from audio features
        
        Args:
            features: Feature matrix from FeatureExtractor
            
        Returns:
            PredictionResult with class and confidence
        """
        inference_start = time.time()
        
        if self.model is not None:
            # Use trained model
            try:
                import tensorflow as tf
                
                # Prepare input
                max_steps = self.model.input_shape[1] if len(self.model.input_shape) > 1 else 100
                
                if len(features) > max_steps:
                    features = features[:max_steps]
                elif len(features) < max_steps:
                    pad_amount = max_steps - len(features)
                    features = np.pad(features, ((0, pad_amount), (0, 0)))
                
                # Add batch dimension
                features_batch = np.expand_dims(features, axis=0)
                
                # Predict
                predictions = self.model.predict(features_batch, verbose=0)[0]
            except Exception as e:
                logger.error(f"[PREDICTOR] Prediction error: {e}")
                # Fallback to statistical model
                predictions = self._statistical_predict(features)
        else:
            # Use fallback statistical model based on feature statistics
            predictions = self._statistical_predict(features)
        
        inference_time = (time.time() - inference_start) * 1000
        
        # Get class
        class_idx = np.argmax(predictions)
        traffic_class = self.CLASS_MAPPING[class_idx]
        confidence = float(predictions[class_idx])
        
        # Create result
        result = PredictionResult(
            timestamp=datetime.now(),
            traffic_class=traffic_class,
            confidence=confidence,
            raw_scores=dict(zip(self.CLASSES, [float(p) for p in predictions])),
            processing_time_ms=inference_time,
            chunk_id=0
        )
        
        return result
    
    def _statistical_predict(self, features: np.ndarray) -> np.ndarray:
        """
        Fallback statistical prediction based on feature statistics
        This is used when no trained model is available
        
        Args:
            features: Feature matrix
            
        Returns:
            Prediction scores for each class
        """
        try:
            # Simple heuristic based on feature statistics
            feature_mean = features.mean()
            feature_std = features.std()
            feature_energy = np.sum(features ** 2)
            
            # Normalize scores
            scores = np.array([
                max(0, feature_std / 2),           # heavy - high variance
                max(0, feature_mean / 2),          # medium - mid-level
                max(0, 1 - feature_std / 2),       # light
                max(0, 1 - feature_energy / 100)   # free
            ])
            
            # Softmax to get probabilities
            scores = np.exp(scores) / np.sum(np.exp(scores))
            
            return scores
        except Exception as e:
            logger.error(f"Statistical prediction error: {e}")
            # Return uniform distribution
            return np.array([0.25, 0.25, 0.25, 0.25])


class AudioConsumer(threading.Thread):
    """
    Main consumer: Gets audio from queue, processes, predicts
    Runs in separate thread for concurrent operation
    """
    
    def __init__(self, audio_queue, model_path: str = None, 
                 sample_rate: int = 16000):
        """
        Initialize consumer
        
        Args:
            audio_queue: Queue to get audio packets
            model_path: Path to trained ML model
            sample_rate: Audio sample rate
        """
        super().__init__()
        self.daemon = True
        self.audio_queue = audio_queue
        self.sample_rate = sample_rate
        self.running = False
        
        # Initialize components
        self.preprocessor = AudioPreprocessor(sample_rate)
        self.feature_extractor = FeatureExtractor(sample_rate)
        self.predictor = TrafficPredictor(model_path)
        
        # Store predictions history
        self.predictions = []
        self.max_history = 100
    
    def process_and_predict(self, audio_packet) -> PredictionResult:
        """
        Process audio packet and make prediction
        
        Args:
            audio_packet: AudioPacket from queue
            
        Returns:
            PredictionResult
        """
        logger.debug(f"[CONSUMER] Processing {audio_packet}...")
        
        try:
            # Step 1: Preprocess
            audio = self.preprocessor.preprocess(audio_packet.data)
            
            # Step 2: Extract features
            features = self.feature_extractor.extract_features(audio)
            
            # Step 3: Predict
            prediction = self.predictor.predict(features)
            prediction.chunk_id = audio_packet.chunk_id
            
            logger.info(f"[CONSUMER] 🎯 {prediction}")
            
            return prediction
            
        except Exception as e:
            logger.error(f"[CONSUMER] Processing error: {e}")
            return None
    
    def run(self):
        """Run consumer in thread"""
        self.running = True
        logger.info("[CONSUMER] Started")
        
        while self.running:
            try:
                # Try to get packet from queue
                packet = self.audio_queue.get(timeout=2.0)
                
                if packet is None:
                    continue
                
                # Process and predict
                prediction = self.process_and_predict(packet)
                
                if prediction:
                    # Store in history
                    self.predictions.append(prediction)
                    if len(self.predictions) > self.max_history:
                        self.predictions.pop(0)
                    
                    # Trigger callback
                    self.on_prediction(prediction)
                    
                    self.audio_queue.task_done()
            
            except:
                continue
    
    def on_prediction(self, prediction: PredictionResult):
        """
        Callback when prediction is ready
        Override this method to handle predictions
        """
        pass
    
    def stop(self):
        """Stop consuming"""
        self.running = False
        logger.info("[CONSUMER] Stopped")
    
    def get_latest_prediction(self) -> PredictionResult:
        """Get most recent prediction"""
        return self.predictions[-1] if self.predictions else None
    
    def get_prediction_history(self, limit: int = 10) -> List[PredictionResult]:
        """Get recent prediction history"""
        return self.predictions[-limit:]
