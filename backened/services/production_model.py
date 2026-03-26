import threading
import queue
import time
import logging
from datetime import datetime
from services.free_traffic_service import FreeTrafficDataAggregator

logger = logging.getLogger(__name__)

class TrafficProducer(threading.Thread):
    """
    Producer: Fetches traffic data for a list of locations at regular intervals.
    In a real production system, this could be fetching from a camera stream 
    or a high-frequency sensor network.
    """
    def __init__(self, data_queue, locations, interval=60):
        super().__init__()
        self.data_queue = data_queue
        self.locations = locations
        self.interval = interval
        self.running = True
        self.aggregator = FreeTrafficDataAggregator()
        self.daemon = True

    def run(self):
        logger.info(f"🚀 Traffic Producer started. Monitoring {len(self.locations)} locations.")
        while self.running:
            for loc_name in self.locations:
                try:
                    logger.info(f"Producing data for: {loc_name}")
                    traffic_data = self.aggregator.get_location_traffic(loc_name)
                    if traffic_data:
                        # Put data into the queue for the consumer
                        self.data_queue.put({
                            'type': 'traffic_update',
                            'payload': traffic_data,
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.error(f"Producer error for {loc_name}: {e}")
            
            # Wait for next cycle
            time.sleep(self.interval)

    def stop(self):
        self.running = False


class TrafficConsumer(threading.Thread):
    """
    Consumer: Processes data from the queue.
    Performs analysis, updates databases, and triggers alerts.
    """
    def __init__(self, data_queue, socketio_instance, db_manager):
        super().__init__()
        self.data_queue = data_queue
        self.socketio = socketio_instance
        self.db = db_manager
        self.running = True
        self.daemon = True

    def run(self):
        logger.info("🎯 Traffic Consumer started. Waiting for data...")
        while self.running:
            try:
                # Blocks for 1 second waiting for data
                item = self.data_queue.get(timeout=1)
                
                if item['type'] == 'traffic_update':
                    data = item['payload']
                    
                    # 1. Logic Analysis: Detect Heavy Congestion
                    congestion = data.get('traffic', {}).get('congestion_level', 0)
                    is_alert = congestion > 0.7
                    
                    # 2. Database Action: Save processed result
                    self.db.save_traffic_data(data['location'], data)
                    
                    # 3. Real-time Notification: Emit via SocketIO
                    self.socketio.emit('realtime_traffic_update', {
                        'location': data['location'],
                        'congestion': congestion,
                        'speed': data.get('traffic', {}).get('live_speed_kmh'),
                        'alert': is_alert,
                        'timestamp': item['timestamp']
                    })
                    
                    logger.info(f"Consumed data for {data['location']}. Congestion: {congestion}")

                # Mark task as done
                self.data_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Consumer error: {e}")

    def stop(self):
        self.running = False

def start_production_pipeline(socketio, db):
    """
    Helper to initialize the Producer-Consumer model
    """
    shared_queue = queue.Queue(maxsize=100)
    
    # Locations to monitor
    monitored_locations = [
        "Banjara Hills, Hyderabad",
        "Hitech City, Hyderabad",
        "Gachibowli, Hyderabad",
        "Secunderabad, Hyderabad"
    ]
    
    producer = TrafficProducer(shared_queue, monitored_locations, interval=30)
    consumer = TrafficConsumer(shared_queue, socketio, db)
    
    producer.start()
    consumer.start()
    
    return producer, consumer
