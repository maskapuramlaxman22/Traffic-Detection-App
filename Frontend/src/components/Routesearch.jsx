import React, { useState } from 'react';
import { getRouteTraffic, searchLocations } from '../services/api';

const RouteSearch = ({ onSearch, onAlert }) => {
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destSuggestions, setDestSuggestions] = useState([]);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSourceChange = async (value) => {
    setSource(value);
    if (value.length > 1) {
      const results = await searchLocations(value);
      setSourceSuggestions(results);
    } else {
      setSourceSuggestions([]);
    }
  };

  const handleDestChange = async (value) => {
    setDestination(value);
    if (value.length > 1) {
      const results = await searchLocations(value);
      setDestSuggestions(results);
    } else {
      setDestSuggestions([]);
    }
  };

  const handleSearch = async () => {
    if (!source || !destination) return;
    
    setLoading(true);
    const result = await getRouteTraffic(source, destination);
    setRouteData(result);
    
    if (result.high_traffic_detected) {
      onAlert('⚠️ Heavy traffic detected on your route!');
    }
    
    onSearch(result);
    setLoading(false);
  };

  return (
    <div className="card">
      <h3 className="card-title">Route Search</h3>
      <div className="input-group">
        <label>Source Location</label>
        <input
          type="text"
          value={source}
          onChange={(e) => handleSourceChange(e.target.value)}
          placeholder="Enter source location..."
        />
        {sourceSuggestions.length > 0 && (
          <ul style={{ border: '1px solid #ddd', marginTop: '5px', maxHeight: '150px', overflowY: 'auto' }}>
            {sourceSuggestions.map((loc, idx) => (
              <li
                key={idx}
                onClick={() => {
                  setSource(loc.name);
                  setSourceSuggestions([]);
                }}
                style={{ padding: '8px', cursor: 'pointer' }}
              >
                {loc.name}
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <div className="input-group">
        <label>Destination Location</label>
        <input
          type="text"
          value={destination}
          onChange={(e) => handleDestChange(e.target.value)}
          placeholder="Enter destination location..."
        />
        {destSuggestions.length > 0 && (
          <ul style={{ border: '1px solid #ddd', marginTop: '5px', maxHeight: '150px', overflowY: 'auto' }}>
            {destSuggestions.map((loc, idx) => (
              <li
                key={idx}
                onClick={() => {
                  setDestination(loc.name);
                  setDestSuggestions([]);
                }}
                style={{ padding: '8px', cursor: 'pointer' }}
              >
                {loc.name}
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
        {loading ? 'Analyzing Route...' : 'Get Route Traffic'}
      </button>
      
      {routeData && (
        <div style={{ marginTop: '20px' }}>
          <h4>Route Details:</h4>
          {routeData.traffic_data.map((point, idx) => (
            <div key={idx} style={{ padding: '10px', margin: '5px 0', background: '#f5f5f5', borderRadius: '5px' }}>
              <strong>{point.location}</strong>: 
              <span className={`traffic-${point.traffic_status.toLowerCase().split(' ')[0]}`}>
                {point.traffic_status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RouteSearch;