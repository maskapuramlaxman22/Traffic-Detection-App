# Traffic Detection System - Setup & Deployment Guide

## 🚀 Quick Start

### Phase 1: Environment Configuration

#### 1.1 Backend Setup (.env)
```bash
# Navigate to backend directory
cd backened

# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required minimum:
# - TOMTOM_API_KEY or HERE_API_KEY (for traffic data)
# - GOOGLE_MAPS_API_KEY (for route planning)
# - MAPBOX_API_KEY (for frontend maps)
```

#### 1.2 Frontend Setup (.env)
```bash
# Navigate to frontend directory
cd Frontend

# Copy the example environment file
cp .env.example .env

# Edit .env and add configuration
REACT_APP_API_URL=http://localhost:5000
REACT_APP_MAPBOX_TOKEN=your_mapbox_token
```

### Phase 2: Install Dependencies

#### Backend
```bash
cd backened

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirement.txt
```

#### Frontend
```bash
cd Frontend

# Install Node packages
npm install
```

### Phase 3: Run Application

#### Start Redis Cache (Optional but Recommended)
```bash
# Using Docker:
docker run -d -p 6379:6379 redis:latest

# Or install locally and run:
redis-server
```

#### Start Backend
```bash
cd backened

# Activate venv first (if using it)
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run Flask server
python app.py

# Server will start on http://localhost:5000
```

#### Start Frontend (in new terminal)
```bash
cd Frontend
npm start

# Frontend will start on http://localhost:3000
```

---

## 📋 API Endpoints

### Real-Time Traffic APIs

#### 1. Get Current Traffic for a Location
```http
GET /api/v1/traffic/current?location=Secunderabad
```

**Response:**
```json
{
  "location": "Secunderabad",
  "coordinates": {
    "latitude": 17.4399,
    "longitude": 78.4983
  },
  "traffic": {
    "source": "TomTom Traffic API",
    "live_speed_kmh": 18,
    "free_flow_speed_kmh": 45,
    "congestion_level": 0.65,
    "travel_time_minutes": 12,
    "delay_minutes": 5,
    "last_updated": "2026-03-26T10:30:00Z"
  },
  "weather_impact": {
    "main": "rain",
    "traffic_impact": "moderate",
    "temperature": 28.5
  }
}
```

#### 2. Get Route Traffic
```http
POST /api/v1/traffic/route
Content-Type: application/json

{
  "source": "Secunderabad",
  "destination": "Warangal"
}
```

**Response:**
```json
{
  "source": "Secunderabad",
  "destination": "Warangal",
  "distance_km": 142,
  "normal_duration_minutes": 180,
  "traffic_duration_minutes": 210,
  "delay_minutes": 30,
  "weather_impact": {
    "main": "clear",
    "traffic_impact": "none"
  }
}
```

#### 3. Get Incidents in Area
```http
GET /api/v1/incidents?lat=17.4399&lng=78.4983&radius_km=5
```

**Response:**
```json
{
  "latitude": 17.4399,
  "longitude": 78.4983,
  "incidents": [
    {
      "type": "accident",
      "description": "Accident near Paradise Circle",
      "delay_minutes": 10,
      "latitude": 17.4380,
      "longitude": 78.4950,
      "severity": "high"
    }
  ],
  "count": 1
}
```

#### 4. Search Locations
```http
GET /api/v1/search_locations?q=hyderabad
```

#### 5. Get Traffic History
```http
GET /api/v1/traffic/history?location=Secunderabad&hours=24
```

---

## 🔑 Getting API Keys

### TomTom Traffic API
1. Sign up: https://developer.tomtom.com/
2. Create an API key
3. Add to .env: `TOMTOM_API_KEY=your_key`
4. **Cost**: $100-300/month (depends on usage)

### Google Maps API
1. Go to: https://console.cloud.google.com/
2. Create a new project
3. Enable: Maps API, Distance Matrix API, Places API
4. Create API key
5. Add to .env: `GOOGLE_MAPS_API_KEY=your_key`
6. **Cost**: $200-500/month (with traffic layer)

### HERE Traffic API
1. Sign up: https://developer.here.com/
2. Create credentials
3. Add to .env: `HERE_API_KEY=your_key`
4. **Cost**: $100-300/month

### Mapbox GL JS
1. Sign up: https://www.mapbox.com/
2. Create access token
3. Add to Frontend .env: `REACT_APP_MAPBOX_TOKEN=your_token`
4. **Cost**: $0-100+/month (free tier available)

### OpenWeatherMap
1. Sign up: https://openweathermap.org/api
2. Get API key
3. Add to .env: `OPENWEATHER_API_KEY=your_key`
4. **Cost**: Free to $100+/month

---

## 🏗️ Architecture Components

### Backend Services

#### 1. Traffic Service (`services/traffic_service.py`)
- **GeocodingService**: Converts location names to coordinates (OpenStreetMap/Nominatim)
- **TomTomTrafficService**: Real-time traffic flow and incidents
- **HereTrafficService**: Fallback traffic data provider
- **GoogleMapsTrafficService**: Route-based traffic analysis
- **WeatherService**: Weather impact on traffic
- **TrafficDataAggregator**: Combines multiple data sources

#### 2. Cache Service (`services/cache_service.py`)
- Redis-based caching
- Reduces API calls by 70-80%
- Configurable TTL for different data types

#### 3. Database (`database/models.py`)
- SQLite for local development
- Ready for PostgreSQL + PostGIS migration
- Tables: locations, traffic_data, route_traffic, incidents, search_history

### Frontend Components

#### Key Features
- Real-time map display with Mapbox GL JS
- Live traffic layer overlay
- Route planning with traffic predictions
- Incident alerts and notifications
- Historical traffic graphs
- WebSocket for real-time updates

---

## 📊 Database Schema

### traffic_data Table
Stores real-time traffic observations:
```
- location_name (TEXT)
- latitude, longitude (REAL)
- live_speed_kmh, free_flow_speed_kmh (REAL)
- congestion_level (REAL 0-1)
- delay_minutes (REAL)
- data_source (TEXT - TomTom, HERE, etc)
- recorded_at (DATETIME)
```

### route_traffic Table
Stores calculated route information:
```
- source, destination (TEXT)
- distance_km (REAL)
- normal_duration_minutes (REAL)
- traffic_duration_minutes (REAL)
- delay_minutes (REAL)
- recorded_at (DATETIME)
```

### incidents Table
Stores traffic incidents:
```
- incident_id, incident_type (TEXT)
- description (TEXT)
- latitude, longitude (REAL)
- delay_minutes (INTEGER)
- severity (TEXT)
- start_time, end_time (DATETIME)
- recorded_at (DATETIME)
```

---

## 🔄 Real-Time Updates (WebSocket)

### Client-Side Example
```javascript
import { subscribeToLocation, disconnectSocket } from './services/api';

// Subscribe to updates for a location
const unsubscribe = subscribeToLocation('Secunderabad', (trafficData) => {
  console.log('Traffic update:', trafficData);
  // Update UI with new data
});

// Cleanup on unmount
componentWillUnmount(() => {
  unsubscribe();
  disconnectSocket();
});
```

---

## 📈 Performance Optimization

### 1. Caching Strategy
- **Geocoding**: 24 hours (locations rarely change)
- **Traffic Data**: 5 minutes (updates every 5 min)
- **Route Data**: 10 minutes
- **Incidents**: 2 minutes (most volatile)
- **Weather**: 10 minutes

### 2. Rate Limiting
- API requests are cached to stay under provider limits
- TomTom: 5 req/sec after caching
- Google: 150 req/second
- HERE: Variable limits

### 3. Database Indexes
```sql
- traffic_data(location_name)
- traffic_data(recorded_at)
- incidents(latitude, longitude)
- route_traffic(source, destination)
```

---

## 🚢 Deployment Options

### Option 1: AWS (Recommended)
```
Frontend: CloudFront + S3
Backend: EC2 + RDS (PostgreSQL)
Cache: ElastiCache (Redis)
Maps: Mapbox hosted
Cost: $50-150/month
```

### Option 2: Vercel (Frontend) + Heroku (Backend)
```
Frontend: Vercel (already configured)
Backend: Heroku dyno
Cache: Redis Cloud (free tier)
Cost: $20-50/month
```

### Option 3: Docker + GCP
```
Docker containers for both
Google Cloud Run + Cloud SQL
Cloud Memorystore for Redis
Cost: $30-100/month
```

---

## 🔐 Security Checklist

- [ ] API keys in .env (not in code)
- [ ] CORS configured properly
- [ ] Rate limiting enabled
- [ ] HTTPS enforced in production
- [ ] Redis password configured
- [ ] Database encrypted
- [ ] Sensitive data logged appropriately

---

## 🐛 Troubleshooting

### Backend Issues
```bash
# Check if port 5000 is in use
netstat -an | grep 5000

# Clear Redis cache
redis-cli FLUSHALL

# Check database
sqlite3 database/traffic.db ".tables"
```

### Frontend Issues
```bash
# Clear Node cache
rm -rf node_modules package-lock.json
npm install

# Check if backend is running
curl http://localhost:5000/api/v1/health
```

### API Key Issues
- Verify keys in .env
- Check API quotas
- Ensure keys have required permissions
- Test with curl:
  ```bash
  curl "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?point=17.4399,78.4983&key=YOUR_KEY"
  ```

---

## 📚 References

- TomTom API Docs: https://developer.tomtom.com/traffic-api/
- HERE API Docs: https://developer.here.com/
- Google Maps API: https://developers.google.com/maps/documentation
- Mapbox GL JS: https://docs.mapbox.com/mapbox-gl-js/
- OpenStreetMap Nominatim: https://nominatim.org/

---

## 🛣️ Next Steps

1. **Get API Keys** (see above)
2. **Configure .env files** in both backend and frontend
3. **Install dependencies** (pip + npm)
4. **Start Redis** (optional but recommended)
5. **Run backend** on port 5000
6. **Run frontend** on port 3000
7. **Test endpoints** using Postman or curl
8. **Enable real-time updates** (WebSocket)
9. **Deploy to production** (see Deployment Options)

---

## 💡 Tips

- Start with a single API provider (TomTom is recommended)
- Use Redis to reduce API costs
- Monitor API usage in provider dashboards
- Set up alerts for quota limits
- Test with development/staging keys first
- Consider free tier options while developing

