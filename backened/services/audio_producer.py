"""
Audio Producer Module - Captures audio from microphone, file, or synthetic signals
Part of the Producer-Consumer architecture for traffic detection
Supports both real and synthetic audio for zero-dependency operation
"""

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except (ImportError, Exception):
    PYAUDIO_AVAILABLE = False
    class FakePyAudio:
        paFloat32 = 0x00000001 # Standard value
    pyaudio = FakePyAudio()

import numpy as np
import queue
import threading
import time
from dataclasses import dataclass
from datetime import datetime
import librosa
import logging

logger = logging.getLogger(__name__)


@dataclass
class AudioPacket:
    """Audio data packet with metadata"""
    data: np.ndarray           # Audio samples
    timestamp: datetime        # When captured
    sample_rate: int          # Hz
    source: str               # 'microphone' or 'file'
    chunk_id: int             # Sequence number
    
    def __repr__(self):
        return f"AudioPacket(id={self.chunk_id}, duration={len(self.data)/self.sample_rate:.2f}s)"


class AudioProducer(threading.Thread):
    """
    Reads audio from microphone or file and produces packets to queue
    Runs in separate thread for concurrent operation
    """
    
    def __init__(self, audio_queue: queue.Queue, 
                 sample_rate: int = 16000,
                 chunk_duration: float = 2.0,
                 source: str = 'microphone',
                 audio_file: str = None):
        """
        Initialize producer
        
        Args:
            audio_queue: Queue to put audio packets
            sample_rate: Sampling rate in Hz (default 16kHz)
            chunk_duration: Duration of each chunk in seconds
            source: 'microphone' or 'file'
            audio_file: Path to audio file (if source='file')
        """
        super().__init__()
        self.daemon = True
        self.audio_queue = audio_queue
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.source = source
        self.audio_file = audio_file
        self.running = False
        self.chunk_id = 0
        
    def from_microphone(self):
        """Capture audio from microphone with fallback"""
        logger.info(f"[PRODUCER] Initializing microphone (sample_rate={self.sample_rate}Hz)")
        
        if not PYAUDIO_AVAILABLE:
            logger.warning("[PRODUCER] PyAudio not installed/available. Skipping microphone mode.")
            return
        
        try:
            p = pyaudio.PyAudio()
        except Exception as e:
            logger.error(f"[PRODUCER] ❌ PyAudio initialization failed: {e}")
            logger.warning("[PRODUCER] Microphone will not be available. Using simulation mode.")
            return
        
        try:
            # Find a valid audio input device
            device_index = None
            device_count = p.get_device_count()
            
            if device_count == 0:
                logger.warning("[PRODUCER] No audio devices found. Running in simulation mode.")
                p.terminate()
                return
            
            for i in range(min(device_count, 10)):  # Check first 10 devices
                try:
                    info = p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        device_index = i
                        logger.info(f"[PRODUCER] Using device: {info['name']}")
                        break
                except:
                    continue
            
            if device_index is None:
                logger.warning("[PRODUCER] No microphone devices found. Running in simulation mode.")
                p.terminate()
                return
            
            # Open microphone stream
            try:
                stream = p.open(
                    format=pyaudio.paFloat32,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=self.chunk_size
                )
            except Exception as e:
                logger.error(f"[PRODUCER] ❌ Failed to open audio stream: {e}")
                p.terminate()
                return
            
            logger.info("[PRODUCER] Microphone stream opened. Starting capture...")
            stream.start_stream()
            
            while self.running:
                try:
                    # Read audio chunk from microphone
                    audio_bytes = stream.read(self.chunk_size, exception_on_overflow=False)
                    audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
                    
                    # Create packet
                    packet = AudioPacket(
                        data=audio_data,
                        timestamp=datetime.now(),
                        sample_rate=self.sample_rate,
                        source='microphone',
                        chunk_id=self.chunk_id
                    )
                    
                    # Put into queue (non-blocking, max timeout 2 seconds)
                    try:
                        self.audio_queue.put(packet, timeout=2.0)
                        logger.debug(f"[PRODUCER] {packet} → Queue (size={self.audio_queue.qsize()})")
                        self.chunk_id += 1
                    except queue.Full:
                        logger.warning(f"[PRODUCER] Queue full! Dropping old packet")
                        try:
                            self.audio_queue.get_nowait()
                            self.audio_queue.put(packet, timeout=0.1)
                        except queue.Empty:
                            pass
                    
                except Exception as e:
                    logger.error(f"[PRODUCER] Error reading from microphone: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            logger.info("[PRODUCER] Microphone stream closed")
            
        except Exception as e:
            logger.error(f"[PRODUCER] Error initializing microphone: {e}")
        finally:
            p.terminate()
    
    def from_file(self, filepath: str):
        """
        Read audio from file and stream like real-time
        
        Args:
            filepath: Path to audio file (.wav, .mp3, .flac)
        """
        logger.info(f"[PRODUCER] Loading audio file: {filepath}")
        
        try:
            # Load entire audio file
            audio_data, sr = librosa.load(filepath, sr=self.sample_rate, mono=True)
            logger.info(f"[PRODUCER] Loaded audio: duration={len(audio_data)/sr:.2f}s, sr={sr}Hz")
            
            # Stream in chunks
            num_chunks = len(audio_data) // self.chunk_size
            
            for i in range(num_chunks):
                if not self.running:
                    break
                
                # Extract chunk
                start_idx = i * self.chunk_size
                end_idx = start_idx + self.chunk_size
                chunk = audio_data[start_idx:end_idx]
                
                # Create packet
                packet = AudioPacket(
                    data=chunk,
                    timestamp=datetime.now(),
                    sample_rate=self.sample_rate,
                    source='file',
                    chunk_id=self.chunk_id
                )
                
                # Put into queue
                try:
                    self.audio_queue.put(packet, timeout=2.0)
                    logger.debug(f"[PRODUCER] {packet} → Queue")
                    self.chunk_id += 1
                except queue.Full:
                    logger.warning(f"[PRODUCER] Queue full, dropping data")
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put(packet, timeout=0.1)
                    except queue.Empty:
                        pass
                
                # Sleep to simulate real-time streaming
                time.sleep(self.chunk_duration * 0.9)
            
            logger.info(f"[PRODUCER] File streaming complete ({num_chunks} chunks)")
            
        except Exception as e:
            logger.error(f"[PRODUCER] Error reading file: {e}")
    
    def from_synthetic(self):
        """Generate synthetic traffic audio signals without any real audio input"""
        logger.info(f"[PRODUCER] Using SYNTHETIC AUDIO MODE (sample_rate={self.sample_rate}Hz)")
        logger.info("[PRODUCER] 🎵 Generating traffic-like audio signals...")
        
        # Traffic class probabilities - more high traffic than low traffic (realistic)
        traffic_classes = {
            'light': 0.25,      # 25% light traffic
            'moderate': 0.45,   # 45% moderate traffic  
            'heavy': 0.30       # 30% heavy traffic
        }
        
        chunk_count = 0
        attempt = 0
        
        while self.running:  # Run indefinitely while producer is active
            try:
                # Randomly select traffic class based on realistic distribution
                traffic_class = np.random.choice(
                    list(traffic_classes.keys()),
                    p=list(traffic_classes.values())
                )
                
                # Generate synthetic audio based on traffic class
                # Features vary by traffic: frequency, amplitude, noise complexity
                if traffic_class == 'light':
                    # Light traffic: Low energy, simple signals
                    base_freq = 200  # Lower frequency
                    amplitude = 0.3
                    num_harmonics = 1
                    
                elif traffic_class == 'moderate':
                    # Moderate traffic: Mid-range frequency and complexity
                    base_freq = 500
                    amplitude = 0.6
                    num_harmonics = 2
                    
                else:  # heavy
                    # Heavy traffic: High energy, complex harmonics (engine/horn noise)
                    base_freq = 800
                    amplitude = 0.85
                    num_harmonics = 4
                
                # Generate audio signal
                t = np.linspace(0, self.chunk_duration, self.chunk_size, endpoint=False)
                
                # Start with base signal
                signal = amplitude * np.sin(2 * np.pi * base_freq * t)
                
                # Add harmonics to simulate engine noise
                for harmonic in range(2, num_harmonics + 1):
                    signal += (amplitude / harmonic) * np.sin(2 * np.pi * base_freq * harmonic * t)
                
                # Add traffic-specific features
                if traffic_class == 'heavy':
                    # Heavy traffic: Add horn bursts and acceleration
                    horn_indices = np.random.choice(self.chunk_size, size=np.random.randint(0, 5), replace=False)
                    for idx in horn_indices:
                        horn_freq = np.random.choice([600, 800, 1000])
                        duration = np.random.randint(100, 300)
                        if idx + duration < self.chunk_size:
                            signal[idx:idx+duration] += 0.4 * np.sin(2 * np.pi * horn_freq * t[:duration])
                
                # Add ambient noise
                noise = np.random.normal(0, amplitude * 0.1, self.chunk_size)
                signal = signal + noise
                
                # Normalize to [-1, 1] range
                max_val = np.max(np.abs(signal))
                if max_val > 0:
                    signal = signal / max_val
                
                # Convert to float32
                audio_data = signal.astype(np.float32)
                
                # Create packet with traffic class metadata
                packet = AudioPacket(
                    data=audio_data,
                    timestamp=datetime.now(),
                    sample_rate=self.sample_rate,
                    source='synthetic',
                    chunk_id=chunk_count
                )
                
                # Put into queue
                try:
                    self.audio_queue.put(packet, timeout=2.0)
                    logger.debug(f"[PRODUCER] {packet} [{traffic_class.upper()}] → Queue (size={self.audio_queue.qsize()})")
                    chunk_count += 1
                except queue.Full:
                    logger.warning(f"[PRODUCER] Queue full! Dropping packet")
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put(packet, timeout=0.1)
                    except queue.Empty:
                        pass
                
                # Sleep to simulate real-time
                time.sleep(self.chunk_duration * 0.8)
                attempt += 1
                
            except Exception as e:
                logger.error(f"[PRODUCER] Error generating synthetic audio: {e}")
                break
        
        logger.info(f"[PRODUCER] Synthetic audio generation complete ({chunk_count} chunks)")
    
    def run(self):
        """Run the producer in thread with fallback to synthetic audio"""
        self.running = True
        
        if self.source == 'microphone':
            # Try microphone first, fallback to synthetic
            self.from_microphone()
            if self.running:
                # Microphone failed, use synthetic 
                logger.info("[PRODUCER] Falling back to synthetic audio generation...")
                self.from_synthetic()
                
        elif self.source == 'file':
            # Try file first, fallback to synthetic
            if self.audio_file:
                self.from_file(self.audio_file)
            if self.running:
                logger.info("[PRODUCER] Falling back to synthetic audio generation...")
                self.from_synthetic()
                
        elif self.source == 'synthetic':
            # Direct synthetic mode
            self.from_synthetic()
        else:
            # Default: use synthetic
            logger.info(f"[PRODUCER] Unknown source '{self.source}', using synthetic mode")
            self.from_synthetic()
    
    def stop(self):
        """Stop producing audio packets"""
        self.running = False
        logger.info("[PRODUCER] Stopping...")
