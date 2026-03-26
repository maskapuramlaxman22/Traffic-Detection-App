import React, { useState, useEffect } from 'react';
import TrafficMap from '../components/TrafficMap';
import LocationSearch from '../components/Locationsearch';
import './Map.css';

const Map = () => {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [coordinates, setCoordinates] = useState({
    latitude: 17.3850, // Default to Hyderabad
    longitude: 78.4867,
  });
  const [routeCoordinates, setRouteCoordinates] = useState([]);
  const [showIncidents, setShowIncidents] = useState(true);
  const [showTraffic, setShowTraffic] = useState(true);

  /**
   * Handle location search selection
   */
  const handleLocationSelect = (location) => {
    setSelectedLocation(location.name);
    setCoordinates({
      latitude: location.latitude,
      longitude: location.longitude,
    });
    setRouteCoordinates([]); // Clear any existing route
  };

  /**
   * Handle route search
   */
  const handleRouteSearch = (routeData) => {
    if (routeData && routeData.route_geometry) {
      // Parse route coordinates from geometry
      const coords = routeData.route_geometry.map((point) => [
        point[1],
        point[0],
      ]);
      setRouteCoordinates(coords);
    }
  };

  return (
    <div className="map-page-container">
      <div className="map-header">
        <h1>🗺️ Traffic Map</h1>
        <p>Real-time traffic visualization with incidents and routing</p>
      </div>

      <div className="map-layout">
        {/* Sidebar Controls */}
        <aside className="map-sidebar">
          <div className="sidebar-section">
            <h3>Search Location</h3>
            <LocationSearch onSearch={handleLocationSelect} />
          </div>

          <div className="sidebar-section">
            <h3>Map Options</h3>
            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showIncidents}
                  onChange={(e) => setShowIncidents(e.target.checked)}
                />
                <span>Show Incidents (🚨🚧)</span>
              </label>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={showTraffic}
                  onChange={(e) => setShowTraffic(e.target.checked)}
                />
                <span>Show Traffic Zones</span>
              </label>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>Legend</h3>
            <div className="mini-legend">
              <div className="legend-row">
                <span
                  className="color-box"
                  style={{ backgroundColor: '#22c55e' }}
                ></span>
                <span>Free Flow</span>
              </div>
              <div className="legend-row">
                <span
                  className="color-box"
                  style={{ backgroundColor: '#eab308' }}
                ></span>
                <span>Moderate</span>
              </div>
              <div className="legend-row">
                <span
                  className="color-box"
                  style={{ backgroundColor: '#f97316' }}
                ></span>
                <span>Congested</span>
              </div>
              <div className="legend-row">
                <span
                  className="color-box"
                  style={{ backgroundColor: '#dc2626' }}
                ></span>
                <span>Heavy</span>
              </div>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>Current View</h3>
            {selectedLocation && (
              <div className="current-location">
                <p>
                  <strong>{selectedLocation}</strong>
                </p>
                <small>
                  Lat: {coordinates.latitude.toFixed(4)}
                  <br />
                  Lng: {coordinates.longitude.toFixed(4)}
                </small>
              </div>
            )}
            {!selectedLocation && (
              <p className="info-text">Select a location to view details</p>
            )}
          </div>

          <div className="sidebar-section tips">
            <h3>💡 Tips</h3>
            <ul>
              <li>Click markers for details</li>
              <li>Use controls to refresh data</li>
              <li>Enable live updates for real-time</li>
              <li>Zoom in/out as needed</li>
            </ul>
          </div>
        </aside>

        {/* Main Map Area */}
        <main className="map-main">
          {showTraffic && (
            <TrafficMap
              location={selectedLocation}
              latitude={coordinates.latitude}
              longitude={coordinates.longitude}
              routeCoordinates={routeCoordinates}
              showIncidents={showIncidents}
              showTrafficCircles={showTraffic}
              zoom={13}
            />
          )}
          {!showTraffic && (
            <div className="map-disabled">
              <p>Map is disabled. Enable "Show Traffic Zones" to view.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Map;
