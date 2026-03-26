"""
Enhanced Database Models and Initialization
Supports real-time traffic data storage and analysis
"""

import sqlite3
import json
from datetime import datetime
import os

def setup_database(db_path: str = "database/traffic.db"):
    """Initialize database with enhanced schema for real traffic data"""
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Locations table with geocoding cache
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            city TEXT,
            state TEXT,
            country TEXT DEFAULT 'India',
            latitude REAL,
            longitude REAL,
            address TEXT,
            cached_at DATETIME,
            last_traffic_check DATETIME
        )
    ''')
    
    # Real-time traffic data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS traffic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_id INTEGER,
            location_name TEXT,
            latitude REAL,
            longitude REAL,
            live_speed_kmh REAL,
            free_flow_speed_kmh REAL,
            congestion_level REAL,
            travel_time_minutes REAL,
            delay_minutes REAL,
            data_source TEXT,
            weather_condition TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
        )
    ''')
    
    # Route traffic data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS route_traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            source_lat REAL,
            source_lng REAL,
            dest_lat REAL,
            dest_lng REAL,
            distance_km REAL,
            normal_duration_minutes REAL,
            traffic_duration_minutes REAL,
            delay_minutes REAL,
            data_sources TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Traffic incidents/accidents
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT,
            incident_type TEXT,
            description TEXT,
            latitude REAL,
            longitude REAL,
            delay_minutes INTEGER,
            severity TEXT,
            start_time DATETIME,
            end_time DATETIME,
            data_source TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Search history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_type TEXT,
            query TEXT,
            source TEXT,
            destination TEXT,
            latitude REAL,
            longitude REAL,
            result_status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            user_ip TEXT
        )
    ''')
    
    # User alerts and notifications
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location_name TEXT,
            alert_type TEXT,
            message TEXT,
            congestion_threshold REAL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            triggered_count INTEGER DEFAULT 0
        )
    ''')
    
    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE,
            setting_value TEXT,
            setting_type TEXT,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_location ON traffic_data(location_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_traffic_time ON traffic_data(recorded_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents(latitude, longitude)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_time ON search_history(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_route_source_dest ON route_traffic(source, destination)')
    
    conn.commit()
    conn.close()


class DatabaseManager:
    """Helper class for database operations"""
    
    def __init__(self, db_path: str = "database/traffic.db"):
        self.db_path = db_path
    
    def add_location(self, name: str, city: str, state: str, latitude: float, 
                    longitude: float, address: str = None) -> int:
        """Add a location to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO locations 
                (name, city, state, latitude, longitude, address, cached_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, city, state, latitude, longitude, address, datetime.now()))
            
            conn.commit()
            location_id = cursor.lastrowid
            return location_id
        finally:
            conn.close()
    
    def save_traffic_data(self, location_name: str, traffic_data: dict) -> bool:
        """Save real-time traffic data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO traffic_data
                (location_name, latitude, longitude, live_speed_kmh, free_flow_speed_kmh,
                 congestion_level, travel_time_minutes, delay_minutes, data_source,
                 weather_condition, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                location_name,
                traffic_data.get('coordinates', {}).get('latitude'),
                traffic_data.get('coordinates', {}).get('longitude'),
                traffic_data.get('traffic', {}).get('live_speed_kmh'),
                traffic_data.get('traffic', {}).get('free_flow_speed_kmh'),
                traffic_data.get('traffic', {}).get('congestion_level'),
                traffic_data.get('traffic', {}).get('travel_time_minutes'),
                traffic_data.get('traffic', {}).get('delay_minutes'),
                traffic_data.get('traffic', {}).get('source'),
                traffic_data.get('weather_impact', {}).get('main'),
                datetime.now()
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving traffic data: {e}")
            return False
        finally:
            conn.close()
    
    def save_route_traffic(self, source: str, destination: str, route_data: dict) -> bool:
        """Save route traffic data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO route_traffic
                (source, destination, distance_km, normal_duration_minutes,
                 traffic_duration_minutes, delay_minutes, data_sources, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                source,
                destination,
                route_data.get('distance_km'),
                route_data.get('normal_duration_minutes'),
                route_data.get('traffic_duration_minutes'),
                route_data.get('delay_minutes'),
                route_data.get('api_source'),
                datetime.now()
            ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving route traffic data: {e}")
            return False
        finally:
            conn.close()
    
    def save_incidents(self, incidents: list) -> bool:
        """Save traffic incidents"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for incident in incidents:
                cursor.execute('''
                    INSERT OR REPLACE INTO incidents
                    (incident_id, incident_type, description, latitude, longitude,
                     delay_minutes, severity, start_time, data_source, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    incident.get('id'),
                    incident.get('type'),
                    incident.get('description'),
                    incident.get('latitude'),
                    incident.get('longitude'),
                    incident.get('delay_minutes'),
                    incident.get('magnitude'),
                    incident.get('start_time'),
                    incident.get('source'),
                    datetime.now()
                ))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving incidents: {e}")
            return False
        finally:
            conn.close()
    
    def log_search(self, search_type: str, query: str = None, source: str = None,
                  destination: str = None, result_status: str = 'success',
                  traffic_status: str = 'Moderate Traffic') -> bool:
        """Log search history with traffic status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO search_history
                (search_type, query, source, destination, result_status, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (search_type, query, source, destination, traffic_status, datetime.now()))
            
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging search: {e}")
            return False
        finally:
            conn.close()
    
    def get_traffic_history(self, location_name: str, hours: int = 24) -> list:
        """Get historical traffic data for a location"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT live_speed_kmh, congestion_level, delay_minutes, recorded_at
                FROM traffic_data
                WHERE location_name = ? AND recorded_at > datetime('now', '-' || ? || ' hours')
                ORDER BY recorded_at ASC
            ''', (location_name, hours))
            
            return cursor.fetchall()
        finally:
            conn.close()
    
    def get_recent_searches(self, limit: int = 100, hours: int = 24) -> list:
        """Get recent search history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT search_type, query, source, destination, result_status, timestamp
                FROM search_history
                WHERE timestamp > datetime('now', '-' || ? || ' hours')
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (hours, limit))
            
            results = cursor.fetchall()
            return [
                {
                    "type": "route" if row[0] == "route_search" else "single",
                    "location": row[1],
                    "source": row[2],
                    "destination": row[3],
                    "traffic_status": "Unknown",
                    "timestamp": row[5]
                }
                for row in results
            ] if results else []
        except Exception as e:
            print(f"Error getting recent searches: {e}")
            return []
        finally:
            conn.close()

    def get_search_history(self, limit: int = 20) -> list:
        """Alias used by api_handler — returns recent searches formatted for frontend"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT search_type, query, source, destination, result_status, timestamp
                FROM search_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [
                {
                    "type": "route" if (row[0] or '').lower() in ('route', 'route_search') else "single",
                    "location": row[1] or '',
                    "source": row[2] or '',
                    "destination": row[3] or '',
                    "traffic_status": row[4] or 'Moderate Traffic',
                    "timestamp": row[5]
                }
                for row in rows
            ]
        except Exception as e:
            print(f"Error in get_search_history: {e}")
            return []
        finally:
            conn.close()
