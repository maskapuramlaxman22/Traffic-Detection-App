import os
import sqlite3
import json
import random
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import librosa
import soundfile as sf

app = Flask(__name__)
CORS(app)

# Database initialization
def init_database():
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    
    # Create locations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            city TEXT,
            state TEXT,
            latitude REAL,
            longitude REAL
        )
    ''')
    
    # Create history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            location TEXT,
            source TEXT,
            destination TEXT,
            traffic_status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            refresh_interval INTEGER DEFAULT 30,
            alerts_enabled INTEGER DEFAULT 1
        )
    ''')
    
    # Insert default settings if not exists
    cursor.execute('SELECT * FROM settings')
    if not cursor.fetchone():
        cursor.execute('INSERT INTO settings (refresh_interval, alerts_enabled) VALUES (30, 1)')
    
    # Insert locations if empty
    cursor.execute('SELECT COUNT(*) FROM locations')
    if cursor.fetchone()[0] == 0:
        insert_locations(cursor)
    
    conn.commit()
    conn.close()

def insert_locations(cursor):
    # Major cities in India
    locations = [
        # Hyderabad areas
        ("Hyderabad - Banjara Hills", "Hyderabad", "Telangana", 17.4132, 78.4226),
        ("Hyderabad - Jubilee Hills", "Hyderabad", "Telangana", 17.4320, 78.4082),
        ("Hyderabad - Hitech City", "Hyderabad", "Telangana", 17.4469, 78.3732),
        ("Hyderabad - Gachibowli", "Hyderabad", "Telangana", 17.4401, 78.3489),
        ("Hyderabad - Secunderabad", "Hyderabad", "Telangana", 17.4399, 78.4983),
        ("Hyderabad - Kukatpally", "Hyderabad", "Telangana", 17.4845, 78.4079),
        ("Hyderabad - Ameerpet", "Hyderabad", "Telangana", 17.4325, 78.4489),
        ("Hyderabad - Madhapur", "Hyderabad", "Telangana", 17.4481, 78.3904),
        
        # Telangana cities
        ("Warangal", "Warangal", "Telangana", 17.9784, 79.5937),
        ("Karimnagar", "Karimnagar", "Telangana", 18.4386, 79.1288),
        ("Nizamabad", "Nizamabad", "Telangana", 18.6725, 78.0941),
        ("Khammam", "Khammam", "Telangana", 17.2473, 80.1514),
        ("Nalgonda", "Nalgonda", "Telangana", 17.0572, 79.2672),
        ("Mahabubnagar", "Mahabubnagar", "Telangana", 16.7375, 77.9856),
        ("Adilabad", "Adilabad", "Telangana", 19.6642, 78.5320),
        
        # Major Indian cities
        ("Mumbai", "Mumbai", "Maharashtra", 19.0760, 72.8777),
        ("Delhi", "Delhi", "Delhi", 28.7041, 77.1025),
        ("Bangalore", "Bangalore", "Karnataka", 12.9716, 77.5946),
        ("Chennai", "Chennai", "Tamil Nadu", 13.0827, 80.2707),
        ("Kolkata", "Kolkata", "West Bengal", 22.5726, 88.3639),
        ("Pune", "Pune", "Maharashtra", 18.5204, 73.8567),
        ("Ahmedabad", "Ahmedabad", "Gujarat", 23.0225, 72.5714),
        ("Jaipur", "Jaipur", "Rajasthan", 26.9124, 75.7873),
        ("Lucknow", "Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
        ("Nagpur", "Nagpur", "Maharashtra", 21.1458, 79.0882),
        ("Indore", "Indore", "Madhya Pradesh", 22.7196, 75.8577),
    ]
    
    # Add more locations to reach 5000+ (simulated)
    for i in range(1, 5000):
        locations.append((f"Location_{i}", "Generic", "India", random.uniform(8.0, 37.0), random.uniform(68.0, 97.0)))
    
    for loc in locations:
        try:
            cursor.execute('INSERT INTO locations (name, city, state, latitude, longitude) VALUES (?, ?, ?, ?, ?)', loc)
        except:
            pass

# Audio feature extraction (simulated if real audio not available)
def extract_audio_features(audio_file=None):
    try:
        if audio_file and os.path.exists(audio_file):
            # Load audio file
            y, sr = librosa.load(audio_file, duration=3)
            
            # Extract MFCC features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_mean = np.mean(mfcc, axis=1)
            
            # Extract zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)
            zcr_mean = np.mean(zcr)
            
            # Extract spectral centroid
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_centroid_mean = np.mean(spectral_centroid)
            
            features = np.concatenate([mfcc_mean, [zcr_mean, spectral_centroid_mean]])
            return features
    except:
        pass
    
    # Return simulated features if no audio file
    return np.random.rand(15)

# ML Model (Decision Tree) for traffic prediction
class TrafficPredictor:
    def __init__(self):
        self.model = None
        self.load_model()
    
    def load_model(self):
        from sklearn.tree import DecisionTreeClassifier
        
        # Generate training data (simulated)
        X_train = []
        y_train = []
        
        # Low traffic patterns
        for _ in range(100):
            features = np.random.rand(15) * 0.3
            X_train.append(features)
            y_train.append(0)  # Low
        
        # Moderate traffic patterns
        for _ in range(100):
            features = np.random.rand(15) * 0.5 + 0.3
            X_train.append(features)
            y_train.append(1)  # Moderate
        
        # High traffic patterns
        for _ in range(100):
            features = np.random.rand(15) * 0.5 + 0.5
            X_train.append(features)
            y_train.append(2)  # High
        
        self.model = DecisionTreeClassifier(max_depth=3)
        self.model.fit(X_train, y_train)
    
    def predict(self, features):
        if self.model:
            prediction = self.model.predict([features])[0]
            return prediction
        return random.randint(0, 2)  # Fallback

predictor = TrafficPredictor()

def get_traffic_status(location):
    # Extract features (simulated)
    features = extract_audio_features()
    
    # Predict traffic
    prediction = predictor.predict(features)
    
    traffic_map = {0: "Low Traffic", 1: "Moderate Traffic", 2: "High Traffic"}
    return traffic_map[prediction]

@app.route('/')
def home():
    return jsonify({"message": "Traffic Detection API is running"})

@app.route('/search_locations', methods=['GET'])
def search_locations():
    query = request.args.get('q', '')
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, city, state FROM locations 
        WHERE name LIKE ? OR city LIKE ?
        LIMIT 20
    ''', (f'%{query}%', f'%{query}%'))
    
    locations = [{"name": row[0], "city": row[1], "state": row[2]} for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(locations)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    location = data.get('location')
    
    if not location:
        return jsonify({"error": "Location required"}), 400
    
    # Get traffic status
    traffic_status = get_traffic_status(location)
    
    # Save to history
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (type, location, traffic_status) 
        VALUES (?, ?, ?)
    ''', ('single', location, traffic_status))
    conn.commit()
    conn.close()
    
    return jsonify({
        "location": location,
        "traffic_status": traffic_status,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/route_traffic', methods=['POST'])
def route_traffic():
    data = request.json
    source = data.get('source')
    destination = data.get('destination')
    
    # Simulate intermediate locations
    intermediate_locations = []
    current = source
    locations_list = []
    
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    
    # Get random locations for route simulation
    cursor.execute('SELECT name FROM locations LIMIT 5')
    random_locs = cursor.fetchall()
    
    # Simulate 3-5 intermediate points
    num_intermediate = random.randint(3, 5)
    for i in range(num_intermediate):
        if i < len(random_locs):
            loc = random_locs[i][0]
            intermediate_locations.append(loc)
            locations_list.append(loc)
    
    # Add source and destination
    route = [source] + intermediate_locations + [destination]
    
    # Get traffic for each point
    route_traffic = []
    high_traffic_detected = False
    
    for loc in route:
        traffic = get_traffic_status(loc)
        route_traffic.append({
            "location": loc,
            "traffic_status": traffic
        })
        if traffic == "High Traffic":
            high_traffic_detected = True
    
    # Save to history
    cursor.execute('''
        INSERT INTO history (type, source, destination, traffic_status) 
        VALUES (?, ?, ?, ?)
    ''', ('route', source, destination, 'High' if high_traffic_detected else 'Normal'))
    conn.commit()
    conn.close()
    
    return jsonify({
        "route": route,
        "traffic_data": route_traffic,
        "high_traffic_detected": high_traffic_detected
    })

@app.route('/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT type, location, source, destination, traffic_status, timestamp 
        FROM history 
        ORDER BY timestamp DESC 
        LIMIT 50
    ''')
    
    history = []
    for row in cursor.fetchall():
        history.append({
            "type": row[0],
            "location": row[1],
            "source": row[2],
            "destination": row[3],
            "traffic_status": row[4],
            "timestamp": row[5]
        })
    
    conn.close()
    return jsonify(history)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    conn = sqlite3.connect('database/traffic.db')
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT refresh_interval, alerts_enabled FROM settings LIMIT 1')
        row = cursor.fetchone()
        conn.close()
        return jsonify({
            "refresh_interval": row[0],
            "alerts_enabled": bool(row[1])
        })
    
    elif request.method == 'POST':
        data = request.json
        refresh_interval = data.get('refresh_interval', 30)
        alerts_enabled = data.get('alerts_enabled', 1)
        
        cursor.execute('''
            UPDATE settings SET refresh_interval = ?, alerts_enabled = ?
        ''', (refresh_interval, alerts_enabled))
        conn.commit()
        conn.close()
        
        return jsonify({"message": "Settings updated"})

if __name__ == '__main__':
    # Create database directory
    os.makedirs('database', exist_ok=True)
    init_database()
    app.run(debug=True, port=5000)