import React, { useState, useEffect } from 'react';
import './Trafficcard.css';
import { getTrafficStatus, getTrafficColor, getTrafficStatusText } from '../services/api';

/**
 * TrafficCard Component
 * Displays real-time traffic information for a location
 */
const TrafficCard = ({ location, latitude, longitude, onDataUpdate }) => {
  const [trafficData, setTrafficData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchTrafficData();
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchTrafficData, 30000);
    return () => clearInterval(interval);
  }, [location, latitude, longitude]);

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

      setTrafficData(data);
      setLastUpdated(new Date());
      onDataUpdate?.(data);
    } catch (err) {
      console.error('Error fetching traffic data:', err);
      setError('Failed to load traffic data');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !trafficData) {
    return (
      <div className="traffic-card loading">
        <div className="loader"></div>
        <p>Loading traffic data...</p>
      </div>
    );
  }

  if (error && !trafficData) {
    return (
      <div className="traffic-card error">
        <p className="error-text">{error}</p>
        <button onClick={fetchTrafficData} className="retry-btn">
          Retry
        </button>
      </div>
    );
  }

  if (!trafficData) {
    return (
      <div className="traffic-card">
        <p>No traffic data available</p>
      </div>
    );
  }

  const traffic = trafficData.traffic || {};
  const weather = trafficData.weather_impact || {};
  const address = trafficData.address || location;
  const congestionLevel = traffic.congestion_level || 0;
  const statusColor = getTrafficColor(congestionLevel);
  const statusText = getTrafficStatusText(congestionLevel);

  return (
    <div className="traffic-card" style={{ borderLeftColor: statusColor }}>
      <div className="card-header">
        <h3 className="location-name">{address}</h3>
        <span className="traffic-status" style={{ backgroundColor: statusColor }}>
          {statusText}
        </span>
      </div>

      <div className="card-body">
        {/* Main Traffic Metrics */}
        <div className="metrics-grid">
          <div className="metric">
            <span className="metric-label">Current Speed</span>
            <span className="metric-value">{traffic.live_speed_kmh || 'N/A'} km/h</span>
            <span className="metric-sublabel">
              (Free flow: {traffic.free_flow_speed_kmh || 'N/A'} km/h)
            </span>
          </div>

          <div className="metric">
            <span className="metric-label">Congestion</span>
            <div className="congestion-bar">
              <div 
                className="congestion-fill" 
                style={{ 
                  width: `${congestionLevel * 100}%`,
                  backgroundColor: statusColor 
                }}
              ></div>
            </div>
            <span className="metric-sublabel">
              {(congestionLevel * 100).toFixed(0)}%
            </span>
          </div>

          <div className="metric">
            <span className="metric-label">Travel Time</span>
            <span className="metric-value">
              {Math.round(traffic.travel_time_minutes || 0)} min
            </span>
            {traffic.delay_minutes > 0 && (
              <span className="metric-sublabel delay">
                +{Math.round(traffic.delay_minutes)} min delay
              </span>
            )}
          </div>
        </div>

        {/* Weather Impact */}
        {weather.main && (
          <div className="weather-section">
            <span className="section-title">Weather Impact</span>
            <div className="weather-info">
              <span className="weather-condition">
                {weather.main.charAt(0).toUpperCase() + weather.main.slice(1)}
              </span>
              {weather.temperature && (
                <span className="temperature">{weather.temperature}°C</span>
              )}
              <span className={`impact-badge impact-${weather.traffic_impact}`}>
                {weather.traffic_impact}
              </span>
            </div>
          </div>
        )}

        {/* Data Source & Update Time */}
        <div className="footer">
          <span className="data-source">
            Source: {traffic.source || 'Multiple APIs'}
          </span>
          {lastUpdated && (
            <span className="last-updated">
              Updated {getTimeAgo(lastUpdated)}
            </span>
          )}
        </div>
      </div>

      {/* Refresh Button */}
      <button 
        onClick={fetchTrafficData} 
        className="refresh-btn"
        disabled={loading}
        title="Refresh traffic data"
      >
        {loading ? '⟳ Updating...' : '⟳ Refresh'}
      </button>
    </div>
  );
};

/**
 * Utility function to display relative time
 */
function getTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

export default TrafficCard;