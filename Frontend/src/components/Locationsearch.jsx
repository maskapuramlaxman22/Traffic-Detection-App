import React, { useState, useEffect } from 'react';
import { predictTraffic, searchLocations } from '../services/api';
import TrafficCard from './Trafficcard';

const LocationSearch = ({ onSearch, onAlert }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState('');
  const [trafficData, setTrafficData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length > 1) {
        const results = await searchLocations(query);
        setSuggestions(results);
      } else {
        setSuggestions([]);
      }
    };
    
    const timeoutId = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(timeoutId);
  }, [query]);

  const handleSearch = async () => {
    if (!selectedLocation) return;
    
    setLoading(true);
    const result = await predictTraffic(selectedLocation);
    setTrafficData(result);
    
    // Trigger alert if high traffic
    if (result.traffic_status === 'High Traffic') {
      onAlert('Heavy traffic detected at ' + selectedLocation);
    }
    
    onSearch(result);
    setLoading(false);
  };

  return (
    <div className="card">
      <h3 className="card-title">Single Location Search</h3>
      <div className="input-group">
        <label>Search Location</label>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter location name..."
        />
        {suggestions.length > 0 && (
          <ul style={{ border: '1px solid #ddd', marginTop: '5px', maxHeight: '200px', overflowY: 'auto' }}>
            {suggestions.map((loc, idx) => (
              <li
                key={idx}
                onClick={() => {
                  setSelectedLocation(loc.name);
                  setQuery(loc.name);
                  setSuggestions([]);
                }}
                style={{ padding: '8px', cursor: 'pointer', borderBottom: '1px solid #eee' }}
              >
                {loc.name} ({loc.city}, {loc.state})
              </li>
            ))}
          </ul>
        )}
      </div>
      
      <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
        {loading ? 'Analyzing Audio...' : 'Predict Traffic'}
      </button>
      
      {trafficData && <TrafficCard data={trafficData} />}
    </div>
  );
};

export default LocationSearch;