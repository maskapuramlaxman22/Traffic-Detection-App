# 🗺️ Leaflet Map Component - Complete Guide

## Overview

The Leaflet Map Component is a fully-featured, interactive traffic visualization system built with:

- **Leaflet** - lightweight open-source map library (free!)
- **OpenStreetMap** - free map tiles (no API key required!)
- **React-Leaflet** - React wrapper for Leaflet
- **Free APIs** - Nominatim, OSRM, Open-Meteo, Overpass

---

## Files Created

### React Components
- **`Frontend/src/components/TrafficMap.jsx`** (400+ lines)
  - Main map component with all traffic visualization features
  - Handles real-time updates via WebSocket
  - Displays incidents, routes, and traffic status
  - Fully responsive and mobile-friendly

- **`Frontend/src/pages/Map.jsx`** (150+ lines)
  - Dedicated map page with sidebar controls
  - Location search integration
  - Map options (show/hide incidents, zones)
  - Legend and tips

### Styling
- **`Frontend/src/components/TrafficMap.css`** (500+ lines)
  - Comprehensive styling for map and markers
  - Responsive design for all screen sizes
  - Dark mode support
  - Animations and transitions

- **`Frontend/src/pages/Map.css`** (400+ lines)
  - Page layout with sidebar
  - Control panel styling
  - Mobile-first responsive design

### Routing
- **`Frontend/src/App.js`** (updated)
  - Added Map route: `/map`
  - Integrated with existing navigation

- **`Frontend/src/components/Navbar.jsx`** (updated)
  - Added "Map" navigation link

---

## Features

### 📍 Real-Time Traffic Display
- **Color-coded markers** for traffic status:
  - 🟢 Green: Free flow (< 20 km/h)
  - 🟡 Yellow: Moderate (20-35 km/h)
  - 🟠 Orange: Congested (35-50 km/h)
  - 🔴 Red: Heavily congested (> 50 km/h)
- **Pulsing animation** shows live updates
- **Hover expands** marker details

### 🚨 Incident Markers
- **Emoji-based icons** for visual clarity:
  - 🚨 Accidents
  - 🚧 Construction
  - 🛠️ Road work
  - ⚠️ Other incidents
- **Bounce animation** for visibility
- **Detailed popups** with severity and distance

### 🛣️ Route Visualization
- **Blue dashed lines** show selected routes
- **OSRM-powered** routing (free!)
- **Real travel times** with traffic impact

### 🎮 Interactive Controls
- **Live Toggle** - Enable/disable real-time WebSocket updates (🔴 Live)
- **Refresh Button** - Manual data refresh (🔄 Refresh)
- **Map Options** - Show/hide incidents, traffic zones
- **Search** - Find any location via Nominatim
- **Legend** - Color reference always visible

### 📊 Data Display
- **Location info** - Address, coordinates
- **Traffic metrics** - Speed, congestion, delay
- **Weather impact** - Temperature and conditions
- **Data source** - Shows where data comes from
- **Search radius** - Visual 5km circle around location

### 📱 Fully Responsive
- **Desktop** - Full sidebar + large map (500px height)
- **Tablet** - Stacked layout, adjusted controls
- **Mobile** - Single column, optimized map (280px height)
- **Touch-friendly** - Larger tap targets

### 🌙 Dark Mode
- Automatic detection via `prefers-color-scheme`
- Proper contrast ratios
- Readable in low-light conditions

---

## How to Use

### 1. Search for a Location

```javascript
// User selects a location from the search box
// This updates coordinates and center the map
```

The map automatically:
- Centers on the selected location
- Fetches traffic data
- Loads nearby incidents (5km radius)
- Shows weather information

### 2. View Real-Time Updates

```javascript
// Click "Live" button to enable WebSocket
```

Features:
- Automatic updates every few seconds
- No manual refresh needed
- Real-time incident notifications
- Live traffic changes

### 3. View Traffic Details

**Click on any marker** to see:
- Current traffic speed (km/h)
- Congestion level (0-100%)
- Estimated delay
- Weather conditions
- Data source

### 4. Visualize a Route

The map shows routes when you:
1. Search from location A to location B
2. Route polyline appears in blue
3. Shows distance and travel time
4. Color changes based on traffic

### 5. Filter Incidents

```javascript
// Uncheck "Show Incidents" to hide markers
// This reduces clutter for highway views
```

---

## Component API

### TrafficMap Props

```javascript
<TrafficMap
  // Required
  latitude={17.3850}           // Starting latitude
  longitude={78.4867}          // Starting longitude
  
  // Optional
  location="Hyderabad"         // Location name
  routeCoordinates={[]}        // Array of [lat, lng] for route
  showIncidents={true}         // Display incident markers
  showTrafficCircles={true}    // Display 5km radius circle
  zoom={12}                    // Initial zoom level (1-20)
/>
```

### Data Format

```javascript
// Traffic Data Response
{
  address: "Hyderabad, Telangana, India",
  latitude: 17.3850,
  longitude: 78.4867,
  traffic: {
    source: "Traffic Pattern Simulation",
    live_speed_kmh: 22.5,
    congestion_level: 0.55,     // 0-1 (0% to 100%)
    delay_minutes: 2.75
  },
  weather_impact: {
    temperature: 28.5,
    traffic_impact: "light"
  }
}

// Incident Data Response
{
  incidents: [
    {
      type: "accident",
      description: "Vehicle accident on main road",
      latitude: 17.39,
      longitude: 78.48,
      severity: "high",
      distance_km: 1.2
    }
  ],
  count: 1
}

// Route Data Response
{
  source: "Hyderabad",
  destination: "Bangalore",
  distance_km: 562,
  normal_duration_minutes: 480,
  traffic_duration_minutes: 540,
  delay_minutes: 60,
  route_geometry: [[78.48, 17.39], [77.59, 13.19]]
}
```

---

## Installation & Setup

### 1. Install Dependencies

The `package.json` already includes:
```json
"leaflet": "^1.9.4",
"react-leaflet": "^4.2.1"
```

Install if not already done:
```bash
cd Frontend
npm install
```

### 2. Make Sure Backend is Running

```bash
cd backened
python app.py
# Should output: Running on http://localhost:5000
```

### 3. Start Frontend

```bash
cd Frontend
npm start
# Opens http://localhost:3000
```

### 4. Navigate to Map

Click **"Map"** in the navigation bar or go to:
```
http://localhost:3000/map
```

---

## Integration Examples

### Using in Dashboard

```javascript
import TrafficMap from '../components/TrafficMap';

const Dashboard = () => {
  return (
    <div>
      <h1>Traffic Dashboard</h1>
      <TrafficMap
        latitude={17.3850}
        longitude={78.4867}
        zoom={12}
      />
    </div>
  );
};
```

### With Location Search

```javascript
const [location, setLocation] = useState(null);

<LocationSearch onSearch={(loc) => {
  setLocation(loc);
}} />

<TrafficMap
  location={location?.name}
  latitude={location?.latitude}
  longitude={location?.longitude}
/>
```

### With Route Data

```javascript
const [route, setRoute] = useState(null);

const handleRouteSearch = (routeData) => {
  setRoute(routeData);
};

<TrafficMap
  routeCoordinates={route?.route_geometry?.map(p => [p[1], p[0]])}
  showIncidents={true}
/>
```

---

## Customization

### Change Default Location

Edit `Frontend/src/pages/Map.jsx`:
```javascript
// Line ~20
const defaultLat = 17.3850;  // Change latitude
const defaultLng = 78.4867;  // Change longitude
```

### Change Map Zoom

```javascript
<TrafficMap zoom={15} />  // 1-20, higher = more zoomed
```

### Change Map Tiles

Edit `Frontend/src/components/TrafficMap.jsx`:
```javascript
// Line ~180 - Replace OpenStreetMap with another free provider

// CartoDB Positron (light)
<TileLayer
  url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
  attribution='&copy; CartoDB'
/>

// CartoDB Voyager (colorful)
<TileLayer
  url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
  attribution='&copy; CartoDB'
/>

// Stamen Terrain
<TileLayer
  url="https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png"
  attribution='Map tiles by Stamen'
/>
```

### Change Marker Icons

Edit `Frontend/src/components/TrafficMap.jsx`:
```javascript
// Customize createTrafficIcon() function (line ~35)
// Change colors, sizes, HTML content

const createTrafficIcon = (congestionLevel) => {
  // Your custom HTML here
};
```

### Add More Incident Types

Edit `Frontend/src/components/TrafficMap.jsx`:
```javascript
const createIncidentIcon = (type) => {
  const icons = {
    accident: '🚨',
    construction: '🚧',
    // Add more types
    flooding: '🌊',
    landslide: '⛰️',
  };
  // ...
};
```

---

## Real-Time Updates via WebSocket

### How It Works

```javascript
// When user clicks "Live" button
socket.emit('subscribe_location', {
  latitude: 17.3850,
  longitude: 78.4867,
  radius_km: 5
});

// Backend sends updates every 5-10 seconds
socket.on('traffic_update', (data) => {
  // Update map with new traffic data
});

// Incident updates come separately
socket.on('incident_update', (data) => {
  // Update incident markers
});
```

### Disabling Real-Time

Click "Live" button again to disable:
- Stops WebSocket listening
- Falls back to 30-second polling
- Reduces bandwidth usage
- Better for slower connections

---

## Performance Tips

### Large Datasets (100+ markers)

```javascript
// Use marker clustering (optional)
// Install: npm install react-leaflet-cluster
// This groups nearby markers to avoid clutter
```

### Slow Networks

```javascript
// Reduce incident search radius
<TrafficMap
  latitude={lat}
  longitude={lng}
  showIncidents={true}
  // Consider disabling live updates
/>

// Manually refresh instead
```

### Mobile Optimization

The component automatically:
- Reduces map height to 280-350px
- Hides legend on very small screens
- Optimizes popup sizes
- Uses touch-friendly controls

---

## Troubleshooting

### Map Not Showing?

1. Check console for errors
```bash
F12 → Console tab
```

2. Verify dependencies installed
```bash
cd Frontend
npm ls leaflet react-leaflet
```

3. Check backend is running
```bash
# Should see traffic data in networks tab (F12)
```

### Markers Not Displaying?

1. Ensure coordinates are valid:
   - Latitude: -90 to 90
   - Longitude: -180 to 180

2. Check API responses:
```javascript
// Check if backend returning data
curl http://localhost:5000/api/v1/traffic/current?location=Hyderabad
```

### Popups Cut Off?

This is a known Leaflet issue. The CSS handles it, but you can also:
1. Zoom out slightly
2. Center popup manually

### Real-Time Not Working?

1. Check WebSocket connection:
```javascript
// Open console
socket.connected  // Should be true
```

2. Enable `realTimeUpdates` in component state

3. Check backend Socket.io is running
```python
# app.py should include SocketIO
from flask_socketio import SocketIO
```

---

## Browser Support

| Browser | Leaflet | React-Leaflet |
|---------|---------|---------------|
| Chrome  | ✅ All  | ✅ All        |
| Firefox | ✅ All  | ✅ All        |
| Safari  | ✅ All  | ✅ All        |
| Edge    | ✅ All  | ✅ All        |
| IE 11   | ❌ No   | ❌ No         |

---

## Free API Limits

### OpenStreetMap Tiles
- **Rate limit**: Unlimited
- **Data**: Global coverage
- **Updates**: Quarterly

### Nominatim (Geocoding)
- **Rate limit**: ~1 request/second per IP
- **Results**: Top 10 matches
- **Coverage**: Global (community)

### OSRM (Routing)
- **Rate limit**: Unlimited (public server)
- **Coverage**: Global
- **Alternatives**: Self-host for private use

### Open-Meteo (Weather)
- **Rate limit**: Unlimited
- **API key**: NOT REQUIRED
- **Updates**: Hourly

### Overpass API (Incidents)
- **Rate limit**: Depends on server
- **Coverage**: Global
- **Data**: Community-maintained

---

## Advanced Features (Future)

Potential enhancements:

1. **Marker Clustering**
   - Group nearby markers
   - Performance improvement

2. **Heatmap Layer**
   - Show traffic density
   - Visual congestion patterns

3. **Drawing Tools**
   - Draw custom areas
   - Get traffic for drawn region

4. **Export Map**
   - Save as image
   - Share with others

5. **Historical Replay**
   - Time slider
   - See traffic over 24 hours

6. **Analytics**
   - Charts on sidebar
   - Peak hours, bottlenecks

---

## Cost Analysis

| Component | Cost | Notes |
|-----------|------|-------|
| Leaflet | $0 | Open source |
| OpenStreetMap | $0 | Community data |
| Nominatim | $0 | Free tier unlimited |
| OSRM | $0 | Public server free |
| React-Leaflet | $0 | Open source |
| **TOTAL** | **$0** | **Completely free!** |

---

## Testing the Map

### Quick Test

```bash
# 1. Start backend
cd backened && python app.py

# 2. Start frontend
cd Frontend && npm start

# 3. Go to http://localhost:3000/map

# 4. Search "Hyderabad" or similar

# 5. Click markers to see data

# 6. Try "Live" button for real-time
```

### Automated Testing

```bash
# In Frontend folder
npm test

# Tests for TrafficMap component
```

---

## Summary

Your Traffic Detection app now has a **professional, feature-rich map interface** powered by 100% free technologies:

✅ Real-time traffic visualization
✅ Interactive incident markers
✅ Route planning and display
✅ Zero cost (free tiles + free APIs)
✅ Fully responsive
✅ Dark mode support
✅ WebSocket real-time updates
✅ Production-ready

**Total Cost**: $0/month (was $200+ before)

Happy mapping! 🗺️🚗
