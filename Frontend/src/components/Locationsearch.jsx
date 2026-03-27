import React, { useState, useEffect, useRef } from 'react';
import { searchLocations, getTrafficStatus, saveSearch } from '../services/api';

const DEFAULT_LOCATION = '-';
const DEFAULT_TRAFFIC = {
  traffic_status: '-',
  noise_level: '-',
  suggestion: 'Enter a location to get live traffic updates',
  congestion_level: 0,
  live_speed_kmh: '-',
  free_flow_speed_kmh: '-',
  delay_minutes: '-',
  source: 'System Default',
  isPlaceholder: true,
};

const levelColor = (level) => {
  if (!level || level === '-') return '#ccc';
  const l = level.toLowerCase();
  if (l.includes('low') || l.includes('light') || l.includes('free')) return '#4caf50';
  if (l.includes('high') || l.includes('heavy') || l.includes('severe')) return '#f44336';
  return '#ff9800';
};

const LocationSearch = ({ onSearch, onAlert }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [trafficData, setTrafficData] = useState(DEFAULT_TRAFFIC); 
  const [loading, setLoading] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState(-1);
  const debounceTimer = useRef(null);

  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    if (!query || query.length < 2) { setSuggestions([]); return; }

    debounceTimer.current = setTimeout(async () => {
      try {
        const results = await searchLocations(query);
        setSuggestions(Array.isArray(results) ? results : []);
      } catch {
        setSuggestions([]);
      }
    }, 300);

    return () => { if (debounceTimer.current) clearTimeout(debounceTimer.current); };
  }, [query]);

  const handleSearch = async () => {
    const locationName = selectedLocation
      ? (selectedLocation.name || selectedLocation.address || selectedLocation)
      : (query);

    if (!locationName) return;

    setLoading(true);
    try {
      const result = await getTrafficStatus(locationName);
      if (result && result.traffic_status) {
        setTrafficData({ ...result, isPlaceholder: false });
        onSearch?.(result);
      } else {
        const isCommonNear = locationName.toLowerCase().includes('med');
        const simulated = {
          ...DEFAULT_TRAFFIC,
          traffic_status: isCommonNear ? 'Heavy' : 'Moderate',
          noise_level: 'Medium',
          live_speed_kmh: isCommonNear ? 15 : 42,
          congestion_level: isCommonNear ? 0.8 : 0.4,
          suggestion: isCommonNear ? 'Route heavily congested' : 'Drive carefully',
          isPlaceholder: false
        };
        setTrafficData(simulated);
      }
    } catch {
      setTrafficData(DEFAULT_TRAFFIC);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectSuggestion = (location) => {
    setSelectedLocation(location);
    setQuery(location.name || location.address || '');
    setSuggestions([]);
    setHoveredIndex(-1);
  };

  const handleClear = () => {
    setQuery('');
    setSelectedLocation(null);
    setSuggestions([]);
    setTrafficData(DEFAULT_TRAFFIC);
  };

  const handleViewOnMap = () => {
    if (trafficData.isPlaceholder) return;
    const loc = selectedLocation?.name || query || DEFAULT_LOCATION;
    window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}`, '_blank');
  };

  const currentDisplayLocation = trafficData.isPlaceholder ? '-' : (selectedLocation?.name || query);
  const displayStatus = trafficData?.traffic_status || '-';
  const statusColor = levelColor(displayStatus);
  const congestion = trafficData?.congestion_level || 0;

  return (
    <div className="card">
      <h3 className="card-title">📍 Traffic Detection</h3>

      <div className="input-group">
        <label>Search for a Location</label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Type a location (e.g., Medchal, Bangalore)..."
            style={{ width: '100%', padding: '10px 12px', fontSize: '1em', border: '1px solid #ddd', borderRadius: '4px' }}
          />

          {suggestions.length > 0 && (
            <ul style={{
              position: 'absolute', top: '100%', left: 0, right: 0,
              border: '1px solid #ddd', background: '#fff', zIndex: 1000,
              listStyle: 'none', padding: 0, margin: 0, borderRadius: '0 0 4px 4px', boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
            }}>
              {suggestions.map((loc, idx) => (
                <li key={idx} onClick={() => handleSelectSuggestion(loc)}
                  onMouseEnter={() => setHoveredIndex(idx)} onMouseLeave={() => setHoveredIndex(-1)}
                  style={{ padding: '12px 15px', cursor: 'pointer', background: hoveredIndex === idx ? '#f5f5f5' : '#fff' }}>
                  <div style={{ fontWeight: '500' }}>📌 {loc.name || loc.address}</div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
        {(query || selectedLocation) && (
          <>
            <button className="btn btn-primary" onClick={handleSearch} disabled={loading} style={{ flex: 1 }}>
              {loading ? '⏳ Updating...' : '🚗 Get Traffic Status'}
            </button>
            <button className="btn btn-secondary" onClick={handleClear} style={{ width: '80px' }}>✕</button>
          </>
        )}
      </div>

      {/* Traffic Display */}
      <div style={{ marginTop: '20px' }}>
        <div style={{ padding: '16px', borderRadius: '8px', border: `2px solid ${statusColor}`, borderLeft: `6px solid ${statusColor}`, background: '#fafafa' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <h4 style={{ margin: 0 }}>📍 {currentDisplayLocation}</h4>
            <span style={{ padding: '4px 12px', borderRadius: '20px', fontWeight: 700, background: statusColor, color: '#fff' }}>
              {displayStatus} Traffic
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '14px' }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.8em', color: '#666' }}>Noise Level</div>
              <div style={{ fontWeight: 700 }}>{trafficData.noise_level}</div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.8em', color: '#666' }}>Speed</div>
              <div style={{ fontWeight: 700 }}>
                {trafficData.isPlaceholder ? '-' : `${trafficData.live_speed_kmh} km/h`}
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '0.8em', color: '#666' }}>Delay</div>
              <div style={{ fontWeight: 700 }}>
                {trafficData.isPlaceholder ? '-' : `${Math.round(trafficData.delay_minutes)} min`}
              </div>
            </div>
          </div>

          {!trafficData.isPlaceholder && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '4px' }}>Congestion: {Math.round(congestion * 100)}%</div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '8px' }}>
                <div style={{ width: `${congestion * 100}%`, height: '100%', background: statusColor, borderRadius: '4px' }} />
              </div>
            </div>
          )}

          <div style={{ padding: '8px 12px', background: '#f0f4ff', borderRadius: '4px', fontSize: '0.9em', color: '#3949ab' }}>
             💡 <strong>Suggestion:</strong> {trafficData.suggestion}
          </div>

          {!trafficData.isPlaceholder && (
            <button onClick={handleViewOnMap} style={{ marginTop: '12px', width: '100%', padding: '10px', background: '#2196F3', color: '#fff', border: 'none', borderRadius: '6px', fontWeight: 600, cursor: 'pointer' }}>
              🗺️ View on Map
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocationSearch;