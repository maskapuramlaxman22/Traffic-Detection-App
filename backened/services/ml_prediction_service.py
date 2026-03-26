"""
ML Traffic Prediction Service
Loads and manages ML model for traffic classification
Uses: Decision Tree Classifier trained on audio features (MFCC, ZCR, Spectral Centroid, etc.)
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import threading
from dataclasses import dataclass
from enum import Enum
import os

logger = logging.getLogger(__name__)


class TrafficLevel(Enum):
    """Traffic classification levels"""
    LOW = "Low Traffic"
    MODERATE = "Moderate Traffic"
    HIGH = "High Traffic"


@dataclass
class PredictionResult:
    """Standard prediction result"""
    traffic_level: TrafficLevel
    confidence: float  # 0-1
    raw_scores: Dict[str, float]  # Confidence for each class
    features_used: List[str]
    model_version: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "traffic_level": self.traffic_level.value,
            "confidence": float(self.confidence),
            "raw_scores": {k: float(v) for k, v in self.raw_scores.items()},
            "features_used": self.features_used,
            "model_version": self.model_version,
            "timestamp": self.timestamp.isoformat()
        }


class MockMLModel:
    """Mock model for development/testing when sklearn model is not available"""
    
    def __init__(self):
        self.model_version = "mock_v1.0"
        self.feature_names = ['mfcc_mean', 'mfcc_std', 'zcr_mean', 'centroid_mean', 
                             'rolloff_mean', 'energy_mean', 'spectral_bandwidth_mean']
    
    def predict_proba(self, features: np.ndarray) -> np.ndarray:
        """
        Mock prediction - in production, this would be sklearn Decision Tree
        Returns probabilities for: [Low, Moderate, High]
        """
        # In production, these would come from a trained model
        # For demo, we use heuristic based on feature values
        
        if len(features) == 0:
            return np.array([0.33, 0.33, 0.34])
        
        # Simple heuristic: use mean values
        feature_mean = np.mean(features)
        
        # Map to traffic level (this is a mock, real model would be trained)
        if feature_mean < 0.3:
            probs = np.array([0.70, 0.20, 0.10])  # Low traffic
        elif feature_mean < 0.6:
            probs = np.array([0.20, 0.60, 0.20])  # Moderate traffic
        else:
            probs = np.array([0.10, 0.20, 0.70])  # High traffic
        
        return probs
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Get class prediction"""
        probs = self.predict_proba(features)
        return np.argmax(probs, axis=1) if len(features.shape) > 1 else np.array([np.argmax(probs)])


class TrafficPredictionModel:
    """
    Production ML model wrapper
    Handles model loading, caching, and predictions
    """
    
    def __init__(self, model_path: Optional[str] = None, use_mock: bool = False):
        """
        Initialize ML model
        
        Args:
            model_path: Path to trained sklearn model file (.pkl)
            use_mock: If True, use mock model for testing
        """
        self.model = None
        self.scaler = None
        self.model_version = "unknown"
        self.feature_names = []
        self.classes = [TrafficLevel.LOW, TrafficLevel.MODERATE, TrafficLevel.HIGH]
        self.lock = threading.RLock()  # Thread-safe loading
        self.load_time = None
        self.predictions_made = 0
        
        # Try to load real model
        if not use_mock and model_path:
            self._load_model(model_path)
        else:
            self._load_mock_model()
    
    def _load_model(self, model_path: str) -> None:
        """Load sklearn model from file"""
        try:
            import joblib
            
            # Load model
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                logger.info(f"✓ Loaded ML model from: {model_path}")
            else:
                logger.warning(f"Model file not found: {model_path}. Using mock model.")
                self._load_mock_model()
                return
            
            # Load scaler if available
            scaler_path = model_path.replace('.pkl', '_scaler.pkl')
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✓ Loaded feature scaler")
            
            self.load_time = datetime.utcnow()
            self.model_version = f"sklearn_{self.model.__class__.__name__}"
            
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}. Using mock model.")
            self._load_mock_model()
    
    def _load_mock_model(self) -> None:
        """Load mock model for development"""
        self.model = MockMLModel()
        self.model_version = "mock_v1.0"
        self.load_time = datetime.utcnow()
        logger.info("✓ Loaded mock ML model (development mode)")
    
    def predict(self, audio_features: np.ndarray, location: Optional[str] = None) -> PredictionResult:
        """
        Make traffic prediction from audio features
        
        Args:
            audio_features: numpy array of audio features
                           Expected: [mfcc_mean, mfcc_std, zcr_mean, centroid_mean, 
                                     rolloff_mean, energy_mean, spectral_bandwidth_mean, ...]
            location: Optional location name for context
        
        Returns:
            PredictionResult with traffic level and confidence
        """
        with self.lock:
            try:
                if audio_features is None or len(audio_features) == 0:
                    raise ValueError("No features provided")
                
                # Ensure features are numpy array
                features = np.array(audio_features).reshape(1, -1) if len(audio_features.shape) == 1 else audio_features
                
                # Scale features if scaler available
                if self.scaler:
                    features = self.scaler.transform(features)
                
                # Get probabilities
                probs = self.model.predict_proba(features)[0]  # Get first sample
                
                # Get class prediction
                class_idx = np.argmax(probs)
                traffic_level = self.classes[class_idx]
                confidence = float(probs[class_idx])
                
                # Build raw scores dict
                raw_scores = {
                    "low": float(probs[0]),
                    "moderate": float(probs[1]),
                    "high": float(probs[2])
                }
                
                result = PredictionResult(
                    traffic_level=traffic_level,
                    confidence=confidence,
                    raw_scores=raw_scores,
                    features_used=self._get_feature_names(),
                    model_version=self.model_version,
                    timestamp=datetime.utcnow()
                )
                
                self.predictions_made += 1
                logger.info(f"🔮 Prediction: {traffic_level.value} "
                          f"(confidence: {confidence:.2%}) "
                          f"at {location or 'unknown location'}")
                
                return result
                
            except Exception as e:
                logger.error(f"Prediction error: {e}")
                # Return low confidence neutral prediction
                return PredictionResult(
                    traffic_level=TrafficLevel.MODERATE,
                    confidence=0.33,
                    raw_scores={"low": 0.33, "moderate": 0.34, "high": 0.33},
                    features_used=self._get_feature_names(),
                    model_version=self.model_version,
                    timestamp=datetime.utcnow()
                )
    
    def predict_from_dict(self, features_dict: Dict[str, float], location: Optional[str] = None) -> PredictionResult:
        """
        Make prediction from feature dictionary
        
        Args:
            features_dict: Dictionary of feature names to values
                          Expected keys: mfcc_mean, mfcc_std, zcr_mean, etc.
        """
        # Convert dict to array in expected order
        feature_order = ['mfcc_mean', 'mfcc_std', 'zcr_mean', 'centroid_mean',
                        'rolloff_mean', 'energy_mean', 'spectral_bandwidth_mean']
        
        features = np.array([features_dict.get(fname, 0.0) for fname in feature_order])
        return self.predict(features, location)
    
    def batch_predict(self, features_list: List[np.ndarray]) -> List[PredictionResult]:
        """Make predictions for multiple samples"""
        return [self.predict(features) for features in features_list]
    
    def _get_feature_names(self) -> List[str]:
        """Get list of feature names used by model"""
        return ['mfcc_mean', 'mfcc_std', 'zcr_mean', 'spectral_centroid', 
               'spectral_rolloff', 'energy', 'spectral_bandwidth']
    
    def get_model_info(self) -> Dict:
        """Get model metadata"""
        return {
            "model_version": self.model_version,
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "predictions_made": self.predictions_made,
            "feature_names": self._get_feature_names(),
            "classes": [cls.value for cls in self.classes],
            "has_scaler": self.scaler is not None
        }
    
    def is_ready(self) -> bool:
        """Check if model is ready for predictions"""
        return self.model is not None


class AudioFeatureExtractor:
    """Extract audio features for ML model"""
    
    @staticmethod
    def extract_features(audio_data: np.ndarray, sr: int = 22050) -> Dict[str, float]:
        """
        Extract MFCC and spectral features from audio
        
        Args:
            audio_data: Raw audio samples
            sr: Sample rate (Hz)
        
        Returns:
            Dictionary of extracted features
        """
        try:
            import librosa
            
            features = {}
            
            # MFCC Features (Mel-Frequency Cepstral Coefficients)
            try:
                mfccs = librosa.feature.mfcc(y=audio_data, sr=sr, n_mfcc=13)
                features['mfcc_mean'] = float(np.mean(mfccs))
                features['mfcc_std'] = float(np.std(mfccs))
            except:
                features['mfcc_mean'] = 0.0
                features['mfcc_std'] = 0.0
            
            # Zero Crossing Rate (ZCR)
            try:
                zcr = librosa.feature.zero_crossing_rate(audio_data)
                features['zcr_mean'] = float(np.mean(zcr))
            except:
                features['zcr_mean'] = 0.0
            
            # Spectral Centroid
            try:
                centroid = librosa.feature.spectral_centroid(y=audio_data, sr=sr)
                features['centroid_mean'] = float(np.mean(centroid))
            except:
                features['centroid_mean'] = 0.0
            
            # Spectral Rolloff
            try:
                rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=sr)
                features['rolloff_mean'] = float(np.mean(rolloff))
            except:
                features['rolloff_mean'] = 0.0
            
            # Energy
            try:
                energy = np.sum(audio_data ** 2)
                features['energy_mean'] = float(energy)
            except:
                features['energy_mean'] = 0.0
            
            # Spectral Bandwidth
            try:
                bandwidth = librosa.feature.spectral_bandwidth(y=audio_data, sr=sr)
                features['spectral_bandwidth_mean'] = float(np.mean(bandwidth))
            except:
                features['spectral_bandwidth_mean'] = 0.0
            
            return features
            
        except ImportError:
            logger.warning("librosa not installed. Returning dummy features.")
            # Return dummy features if librosa not available
            return {
                'mfcc_mean': 0.0,
                'mfcc_std': 0.0,
                'zcr_mean': 0.0,
                'centroid_mean': 0.0,
                'rolloff_mean': 0.0,
                'energy_mean': 0.0,
                'spectral_bandwidth_mean': 0.0
            }
    
    @staticmethod
    def extract_features_from_array(audio_array: np.ndarray, sr: int = 22050) -> np.ndarray:
        """Extract features and return as numpy array"""
        features_dict = AudioFeatureExtractor.extract_features(audio_array, sr)
        feature_order = ['mfcc_mean', 'mfcc_std', 'zcr_mean', 'centroid_mean',
                        'rolloff_mean', 'energy_mean', 'spectral_bandwidth_mean']
        return np.array([features_dict.get(fname, 0.0) for fname in feature_order])
