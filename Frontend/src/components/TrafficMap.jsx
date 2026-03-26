import React, { useState, useEffect, useRef } from 'react';
import {
  MapContainer,
  TileLayer,
  Marker,
  Popup,
  Polyline,
  Circle,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import './TrafficMap.css';
import {
  getTrafficStatus,
  getIncidents,
  getTrafficColor,
  getTrafficStatusText,
  initializeSocket,
} from '../services/api';

// Fix for default markers in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

/**
 * Custom marker icons for traffic status
 */
const createTrafficIcon = (congestionLevel) => {
  const color = getTrafficColor(congestionLevel);
  const colors = {
    '#22c55e': '#10b981', // green
    '#eab308': '#f59e0b', // yellow
    '#f97316': '#ea580c', // orange
    '#dc2626': '#991b1b', // red
  };

  return L.divIcon({
    html: `
      <div class="traffic-marker" style="background-color: ${color}; border: 3px solid ${colors[color] || color};">
        <div class="traffic-marker-inner"></div>
      </div>
    `,
    className: 'traffic-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

const createIncidentIcon = (type) => {
  const icons = {
    accident: '🚨',
    construction: '🚧',
    roadwork: '🛠️',
    incident: '⚠️',
    default: '📍',
  };

  return L.divIcon({
    html: `<div class="incident-marker">${icons[type] || icons.default}</div>`,
    className: 'incident-icon',
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16],
  });
};

/**
 * RecenterButton Component - Provides a button to reset map view
 */
const RecenterButton = ({ position, zoom }) => {
  const map = useMap();

  const handleRecenter = () => {
    if (position) {
      map.setView(position, zoom);
    }
  };

  return null;
};

/**
 * TrafficMap Component
 * Displays real-time traffic on an interactive Leaflet map
 */
const TrafficMap = ({
  location,
  latitude,
  longitude,
  routeCoordinates,
  showIncidents = true,
  showTrafficCircles = true,
  zoom = 12,
}) => {
  // Default to Hyderabad if no location provided
  const defaultLat = 17.3850;
  const defaultLng = 78.4867;

  const mapLat = latitude || defaultLat;
  const mapLng = longitude || defaultLng;

  const [mapCenter, setMapCenter] = useState([mapLat, mapLng]);
  const [trafficData, setTrafficData] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [realTimeUpdates, setRealTimeUpdates] = useState(false);
  const socketRef = useRef(null);

  /**
   * Fetch traffic data for current location
   */
  useEffect(() => {
    if (latitude && longitude) {
      fetchTrafficData();
      if (showIncidents) {
        fetchIncidents();
      }
    }
  }, [latitude, longitude, showIncidents]);

  const fetchTrafficData = async () => {
    try {
      setLoading(true);
      setError(null);

      let data;
      if (location) {
        data = await getTrafficStatus(location);
      } else if (latitude && longitude) {
        const { getTrafficByCoordinates } = await import('../services/api');
        data = await getTrafficByCoordinates(latitude, longitude);
      }

      if (data) {
        setTrafficData(data);
        // Update map center if we got coordinates
        if (data.latitude && data.longitude) {
          setMapCenter([data.latitude, data.longitude]);
        }
      }
    } catch (err) {
      console.error('Error fetching traffic data:', err);
      setError('Failed to load traffic data');
    } finally {
      setLoading(false);
    }
  };

  const fetchIncidents = async () => {
    try {
      const data = await getIncidents(latitude, longitude, 10);
      if (data && data.incidents) {
        setIncidents(data.incidents);
      }
    } catch (err) {
      console.error('Error fetching incidents:', err);
    }
  };

  /**
   * Setup real-time updates via WebSocket
   */
  useEffect(() => {
    if (realTimeUpdates && latitude && longitude) {
      try {
        const socket = initializeSocket();
        socketRef.current = socket;

        // Subscribe to location updates
        socket.emit('subscribe_location', {
          latitude,
          longitude,
          radius_km: 5,
        });

        // Subscribe to incident updates
        socket.emit('subscribe_incidents', {
          latitude,
          longitude,
          radius_km: 10,
        });

        // Listen for traffic updates
        socket.on('traffic_update', (data) => {
          setTrafficData(data);
        });

        // Listen for incident updates
        socket.on('incident_update', (data) => {
          if (data && data.incidents) {
            setIncidents(data.incidents);
          }
        });

        return () => {
          socket.off('traffic_update');
          socket.off('incident_update');
        };
      } catch (err) {
        console.error('Error setting up real-time updates:', err);
        setError('Failed to connect to real-time updates');
      }
    }
  }, [realTimeUpdates, latitude, longitude]);

  // Auto-refresh traffic data every 30 seconds if not using real-time updates
  useEffect(() => {
    if (!realTimeUpdates && (latitude || longitude)) {
      const interval = setInterval(() => {
        fetchTrafficData();
        if (showIncidents) {
          fetchIncidents();
        }
      }, 30000);

      return () => clearInterval(interval);
    }
  }, [realTimeUpdates, latitude, longitude, showIncidents]);

  /**
   * Toggle real-time updates
   */
  const toggleRealTimeUpdates = () => {
    setRealTimeUpdates(!realTimeUpdates);
  };

  /**
   * Refresh data manually
   */
  const handleRefresh = () => {
    fetchTrafficData();
    if (showIncidents) {
      fetchIncidents();
    }
  };

  return (
    <div className="traffic-map-container">
      <div className="map-controls">
        <div className="control-group">
          <button
            className={`control-btn ${realTimeUpdates ? 'active' : ''}`}
            onClick={toggleRealTimeUpdates}
            title={realTimeUpdates ? 'Disable real-time' : 'Enable real-time'}
          >
            {realTimeUpdates ? '🔴 Live' : '⚪ Live'}
          </button>
          <button className="control-btn" onClick={handleRefresh} title="Refresh">
            🔄 Refresh
          </button>
          {error && <span className="error-badge">{error}</span>}
        </div>

        {trafficData && (
          <div className="traffic-info-mini">
            <div className="traffic-status">
              <span className="status-dot" style={{
                backgroundColor: getTrafficColor(trafficData.traffic?.congestion_level || 0),
              }}></span>
              <span className="status-text">
                {getTrafficStatusText(trafficData.traffic?.congestion_level || 0)}
              </span>
            </div>
            <div className="traffic-speed">
              {trafficData.traffic?.live_speed_kmh?.toFixed(1)}
              <span className="unit">km/h</span>
            </div>
          </div>
        )}
      </div>

      <MapContainer
        center={mapCenter}
        zoom={zoom}
        className="traffi-map"
        style={{ height: '500px', width: '100%' }}
      >
        {/* OpenStreetMap Tile Layer (Free!) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Current Location Marker */}
        {mapCenter && (
          <Marker
            position={mapCenter}
            icon={createTrafficIcon(trafficData?.traffic?.congestion_level || 0)}
          >
            <Popup className="traffic-popup">
              <div className="popup-content">
                <h4>{trafficData?.address || location || 'Current Location'}</h4>
                <div className="popup-info">
                  <p>
                    <strong>Speed:</strong>{' '}
                    {trafficData?.traffic?.live_speed_kmh?.toFixed(1) || 'N/A'} km/h
                  </p>
                  <p>
                    <strong>Status:</strong>{' '}
                    {getTrafficStatusText(
                      trafficData?.traffic?.congestion_level || 0
                    )}
                  </p>
                  <p>
                    <strong>Congestion:</strong>{' '}
                    {((trafficData?.traffic?.congestion_level || 0) * 100).toFixed(0)}%
                  </p>
                  {trafficData?.weather_impact && (
                    <p>
                      <strong>Weather:</strong> {trafficData.weather_impact.temperature}°C
                    </p>
                  )}
                  <p className="data-source">
                    {trafficData?.traffic?.source || 'No data'}
                  </p>
                </div>
              </div>
            </Popup>
          </Marker>
        )}

        {/* Search Radius Circle */}
        {showTrafficCircles && mapCenter && (
          <Circle
            center={mapCenter}
            radius={5000}
            pathOptions={{
              color: 'rgba(100, 200, 255, 0.3)',
              fillColor: 'rgba(100, 200, 255, 0.1)',
              weight: 2,
              filling: true,
              fillOpacity: 0.1,
            }}
          />
        )}

        {/* Route Visualization */}
        {routeCoordinates && routeCoordinates.length > 0 && (
          <Polyline
            positions={routeCoordinates}
            pathOptions={{
              color: '#3b82f6',
              weight: 4,
              opacity: 0.8,
              dashArray: '5, 10',
            }}
          />
        )}

        {/* Incident Markers */}
        {showIncidents &&
          incidents.map((incident, idx) => (
            <Marker
              key={`incident-${idx}`}
              position={[incident.latitude || incident.lat, incident.longitude || incident.lng]}
              icon={createIncidentIcon(incident.type || 'incident')}
            >
              <Popup className="incident-popup">
                <div className="popup-content">
                  <h4>{incident.type || 'Incident'}</h4>
                  <p>{incident.description || incident.name || 'Traffic incident'}</p>
                  {incident.severity && (
                    <p>
                      <strong>Severity:</strong>{' '}
                      <span className={`severity-${incident.severity}`}>
                        {incident.severity}
                      </span>
                    </p>
                  )}
                  {incident.distance_km !== undefined && (
                    <p>
                      <strong>Distance:</strong> {incident.distance_km.toFixed(2)} km
                    </p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}

        {/* Recenter button trigger */}
        <RecenterButton position={mapCenter} zoom={zoom} />
      </MapContainer>

      {/* Map Legend */}
      <div className="map-legend">
        <h4>Legend</h4>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#22c55e' }}></span>
          <span>Free Flow (&lt; 20 km/h)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#eab308' }}></span>
          <span>Moderate (20-35 km/h)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#f97316' }}></span>
          <span>Congested (35-50 km/h)</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#dc2626' }}></span>
          <span>Heavily Congested (&gt; 50 km/h)</span>
        </div>
        <div className="legend-item">
          <span className="legend-emoji">🚨</span>
          <span>Accident</span>
        </div>
        <div className="legend-item">
          <span className="legend-emoji">🚧</span>
          <span>Construction</span>
        </div>
        <div className="legend-item">
          <span className="legend-emoji">⚠️</span>
          <span>Other Incident</span>
        </div>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div className="map-loading">
          <div className="loader"></div>
          <p>Loading traffic data...</p>
        </div>
      )}
    </div>
  );
};

export default TrafficMap;
