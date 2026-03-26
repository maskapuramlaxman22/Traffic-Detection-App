"""
Enhanced Queue System for Producer-Consumer Architecture
Supports both Redis (production) and in-memory queue (development)
"""

import logging
import json
import time
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
from enum import Enum
from abc import ABC, abstractmethod
import threading

logger = logging.getLogger(__name__)


class QueuePriority(Enum):
    """Request priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


class RequestType(Enum):
    """Types of requests in the queue"""
    TRAFFIC_SEARCH = "traffic_search"
    ROUTE_SEARCH = "route_search"
    AUDIO_PREDICTION = "audio_prediction"
    LOCATION_GEOCODE = "location_geocode"
    CACHE_REFRESH = "cache_refresh"


class QueueMessage:
    """Standardized message format for queue"""
    
    def __init__(
        self,
        message_id: str,
        request_type: RequestType,
        payload: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL,
        retry_count: int = 0,
        max_retries: int = 3,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None
    ):
        self.message_id = message_id
        self.request_type = request_type
        self.payload = payload
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at or (datetime.utcnow() + timedelta(minutes=5))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "request_type": self.request_type.value,
            "payload": self.payload,
            "priority": self.priority.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict())
    
    def is_expired(self) -> bool:
        """Check if message has expired"""
        return datetime.utcnow() > self.expires_at
    
    def should_retry(self) -> bool:
        """Check if message should be retried"""
        return self.retry_count < self.max_retries and not self.is_expired()


class QueueBackend(ABC):
    """Abstract base class for queue implementations"""
    
    @abstractmethod
    def put(self, message: QueueMessage) -> bool:
        """Add message to queue"""
        pass
    
    @abstractmethod
    def get(self, timeout: int = 1) -> Optional[QueueMessage]:
        """Retrieve message from queue"""
        pass
    
    @abstractmethod
    def size(self) -> int:
        """Get queue size"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all messages"""
        pass
    
    @abstractmethod
    def exists(self, message_id: str) -> bool:
        """Check if message exists"""
        pass


class InMemoryQueue(QueueBackend):
    """In-memory queue for development/testing"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = []
        self.max_size = max_size
        self.lock = threading.RLock()
        self.processed = {}  # Track processed messages
    
    def put(self, message: QueueMessage) -> bool:
        """Add message to queue with priority"""
        with self.lock:
            if len(self.queue) >= self.max_size:
                logger.warning(f"Queue full, dropping message: {message.message_id}")
                return False
            
            # Insert based on priority (lower value = higher priority)
            inserted = False
            for idx, existing_msg in enumerate(self.queue):
                if message.priority.value < existing_msg.priority.value:
                    self.queue.insert(idx, message)
                    inserted = True
                    break
            
            if not inserted:
                self.queue.append(message)
            
            logger.debug(f"📥 Message queued: {message.message_id} (priority: {message.priority.name})")
            return True
    
    def get(self, timeout: int = 1) -> Optional[QueueMessage]:
        """Retrieve message from queue (blocking)"""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            with self.lock:
                # Remove expired messages
                self.queue = [m for m in self.queue if not m.is_expired()]
                
                if self.queue:
                    message = self.queue.pop(0)
                    self.processed[message.message_id] = datetime.utcnow()
                    logger.debug(f"📤 Message retrieved: {message.message_id}")
                    return message
            
            time.sleep(0.1)
        
        return None
    
    def size(self) -> int:
        """Get queue size"""
        with self.lock:
            return len(self.queue)
    
    def clear(self) -> None:
        """Clear all messages"""
        with self.lock:
            self.queue.clear()
            logger.info("Queue cleared")
    
    def exists(self, message_id: str) -> bool:
        """Check if message exists in queue"""
        with self.lock:
            return any(m.message_id == message_id for m in self.queue)


class RedisQueue(QueueBackend):
    """Redis-backed queue for production"""
    
    def __init__(self, redis_client, queue_name: str = "traffic_queue"):
        self.redis = redis_client
        self.queue_name = queue_name
        self.processed_key = f"{queue_name}:processed"
    
    def put(self, message: QueueMessage) -> bool:
        """Add message to Redis queue"""
        try:
            # Store with score = priority.value for sorted processing
            score = (message.priority.value * 1000) + (datetime.utcnow().timestamp() % 1000)
            
            self.redis.zadd(
                self.queue_name,
                {message.to_json(): score}
            )
            
            # Set TTL for message expiration
            self.redis.expire(self.queue_name, 300)  # 5 minutes
            
            logger.debug(f"📥 Message queued in Redis: {message.message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to queue message in Redis: {e}")
            return False
    
    def get(self, timeout: int = 1) -> Optional[QueueMessage]:
        """Retrieve message from Redis queue"""
        try:
            # Get highest priority message (lowest score)
            messages = self.redis.zrange(self.queue_name, 0, 0)
            
            if not messages:
                return None
            
            message_json = messages[0]
            self.redis.zrem(self.queue_name, message_json)
            
            message_dict = json.loads(message_json)
            message = QueueMessage(
                message_id=message_dict["message_id"],
                request_type=RequestType(message_dict["request_type"]),
                payload=message_dict["payload"],
                priority=QueuePriority(message_dict["priority"]),
                retry_count=message_dict["retry_count"],
                max_retries=message_dict["max_retries"]
            )
            
            # Track processed message
            self.redis.hset(self.processed_key, message.message_id, time.time())
            
            logger.debug(f"📤 Message retrieved from Redis: {message.message_id}")
            return message
        except Exception as e:
            logger.error(f"Failed to get message from Redis: {e}")
            return None
    
    def size(self) -> int:
        """Get queue size"""
        try:
            return self.redis.zcard(self.queue_name)
        except:
            return 0
    
    def clear(self) -> None:
        """Clear queue"""
        try:
            self.redis.delete(self.queue_name)
            logger.info("Redis queue cleared")
        except Exception as e:
            logger.error(f"Failed to clear Redis queue: {e}")
    
    def exists(self, message_id: str) -> bool:
        """Check if message exists"""
        try:
            return self.redis.hexists(self.processed_key, message_id)
        except:
            return False


class QueueManager:
    """Unified queue management interface"""
    
    def __init__(self, backend: QueueBackend):
        self.backend = backend
        self.message_counter = 0
        self.lock = threading.Lock()
    
    def create_message(
        self,
        request_type: RequestType,
        payload: Dict[str, Any],
        priority: QueuePriority = QueuePriority.NORMAL
    ) -> str:
        """Create and queue a message, return message_id"""
        with self.lock:
            self.message_counter += 1
            message_id = f"msg_{self.message_counter}_{int(time.time()*1000)}"
        
        message = QueueMessage(
            message_id=message_id,
            request_type=request_type,
            payload=payload,
            priority=priority
        )
        
        success = self.backend.put(message)
        if success:
            return message_id
        raise RuntimeError(f"Failed to queue message: {message_id}")
    
    def get_message(self, timeout: int = 1) -> Optional[QueueMessage]:
        """Get next message from queue"""
        return self.backend.get(timeout)
    
    def acknowledge(self, message_id: str) -> None:
        """Mark message as processed"""
        logger.info(f"✓ Message acknowledged: {message_id}")
    
    def nack(self, message: QueueMessage) -> bool:
        """Negative acknowledge - retry message"""
        if message.should_retry():
            message.retry_count += 1
            logger.warning(f"⚠️ Retrying message {message.message_id} (attempt {message.retry_count}/{message.max_retries})")
            return self.backend.put(message)
        else:
            logger.error(f"❌ Message failed after {message.max_retries} retries: {message.message_id}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get queue status"""
        return {
            "queue_size": self.backend.size(),
            "backend_type": self.backend.__class__.__name__,
            "message_counter": self.message_counter,
            "timestamp": datetime.utcnow().isoformat()
        }


# Convenience factory function
def create_queue_manager(redis_url: Optional[str] = None) -> QueueManager:
    """
    Create appropriate queue manager
    
    Args:
        redis_url: Redis connection URL. If None, uses in-memory queue.
    
    Returns:
        QueueManager instance
    """
    try:
        if redis_url:
            import redis as redis_lib
            redis_client = redis_lib.from_url(redis_url)
            redis_client.ping()
            logger.info("✓ Connected to Redis queue")
            return QueueManager(RedisQueue(redis_client))
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Using in-memory queue.")
    
    logger.info("✓ Using in-memory queue")
    return QueueManager(InMemoryQueue())
