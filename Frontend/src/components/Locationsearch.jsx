import React, { useState, useEffect, useRef } from 'react';
import { searchLocations, getTrafficStatus, saveSearch } from '../services/api';

// ─── Default sample data shown when no location is selected or API fails ───
const DEFAULT_LOCATION = 'Hyderabad';
const DEFAULT_TRAFFIC = {
  traffic_status: 'Moderate',
  noise_level: 'Medium',
  suggestion: 'Drive carefully',
  congestion_level: 0.45,
  live_speed_kmh: 32,
  free_flow_speed_kmh: 50,
  delay_minutes: 8,
  source: 'Sample Data',
};

const levelColor = (level) => {
  if (!level) return '#ff9800';
  const l = level.toLowerCase();
  if (l.includes('low') || l.includes('light') || l.includes('free')) return '#4caf50';
  if (l.includes('high') || l.includes('heavy') || l.includes('severe')) return '#f44336';
  return '#ff9800';
};

const LocationSearch = ({ onSearch, onAlert }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [trafficData, setTrafficData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isSampleData, setIsSampleData] = useState(false);
  const [hoveredIndex, setHoveredIndex] = useState(-1);
  const debounceTimer = useRef(null);

  // Show sample data immediately on mount
  useEffect(() => {
    showSampleData();
  }, []);

  const showSampleData = () => {
    setTrafficData(DEFAULT_TRAFFIC);
    setIsSampleData(true);
  };

  // Debounced location autocomplete
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
    // If no location selected, use default
    const locationName = selectedLocation
      ? (selectedLocation.name || selectedLocation.address || selectedLocation)
      : DEFAULT_LOCATION;

    setLoading(true);
    setIsSampleData(false);

    try {
      const result = await getTrafficStatus(locationName);

      if (result && (result.traffic_status || result.traffic)) {
        setTrafficData(result.traffic || result);
        setIsSampleData(false);

        const level = result.traffic_status || '';
        if (level === 'High Traffic') {
          onAlert?.(`🚨 Heavy traffic detected at ${locationName}`);
        }

        try {
          await saveSearch({ query: locationName, type: 'location', result });
        } catch { /* silent */ }

        onSearch?.(result);
      } else {
        // API returned nothing useful — show sample
        setTrafficData({ ...DEFAULT_TRAFFIC, location: locationName });
        setIsSampleData(true);
        onSearch?.({ traffic_status: 'Moderate' });
      }
    } catch {
      // Network/API failure — show sample silently
      setTrafficData({ ...DEFAULT_TRAFFIC, location: locationName });
      setIsSampleData(true);
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
    showSampleData();
  };

  const handleViewOnMap = () => {
    const loc = selectedLocation?.name || query || DEFAULT_LOCATION;
    window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc)}`, '_blank');
  };

  const displayStatus = trafficData?.traffic_status || trafficData?.live_speed_kmh
    ? (trafficData.live_speed_kmh >= 40 ? 'Low' : trafficData.live_speed_kmh >= 20 ? 'Moderate' : 'High')
    : 'Moderate';

  const statusColor = levelColor(displayStatus);
  const congestion = trafficData?.congestion_level || 0.45;

  return (
    <div className="card">
      <h3 className="card-title">📍 Search Location Traffic</h3>

      {/* Input */}
      <div className="input-group">
        <label>Search for a Location</label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Type a location (e.g., Hyderabad, Bangalore)..."
            style={{
              width: '100%', padding: '10px 12px',
              fontSize: '1em', border: '1px solid #ddd', borderRadius: '4px'
            }}
          />

          {suggestions.length > 0 && (
            <ul style={{
              position: 'absolute', top: '100%', left: 0, right: 0,
              border: '1px solid #ddd', borderTop: 'none', marginTop: 0,
              maxHeight: '280px', overflowY: 'auto', background: '#fff',
              zIndex: 1000, listStyle: 'none', padding: 0, margin: 0,
              borderRadius: '0 0 4px 4px', boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
            }}>
              {suggestions.map((loc, idx) => (
                <li
                  key={idx}
                  onClick={() => handleSelectSuggestion(loc)}
                  onMouseEnter={() => setHoveredIndex(idx)}
                  onMouseLeave={() => setHoveredIndex(-1)}
                  style={{
                    padding: '12px 15px', cursor: 'pointer',
                    borderBottom: idx < suggestions.length - 1 ? '1px solid #eee' : 'none',
                    background: hoveredIndex === idx ? '#f5f5f5' : '#fff',
                    transition: 'background 0.2s'
                  }}
                >
                  <div style={{ fontWeight: '500', color: '#333' }}>📌 {loc.name || loc.address}</div>
                  {loc.address && <div style={{ fontSize: '0.85em', color: '#666', marginTop: '4px' }}>{loc.address}</div>}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {selectedLocation && (
        <div style={{
          marginTop: '12px', padding: '8px 12px',
          background: '#f0f8ff', border: '1px solid #80bfff',
          borderRadius: '4px', fontSize: '0.95em', color: '#0055aa'
        }}>
          ✓ Selected: <strong>{selectedLocation.name || selectedLocation.address}</strong>
        </div>
      )}

      {/* Buttons */}
      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
        <button
          className="btn btn-primary"
          onClick={handleSearch}
          disabled={loading}
          style={{ flex: 1 }}
        >
          {loading ? '⏳ Fetching...' : '🚗 Get Traffic Status'}
        </button>
        {(selectedLocation || query) && (
          <button className="btn btn-secondary" onClick={handleClear} style={{ flex: 1 }}>
            ✕ Clear
          </button>
        )}
      </div>

      {/* Traffic Result Card */}
      {trafficData && (
        <div style={{ marginTop: '20px' }}>
          {isSampleData && (
            <div style={{
              padding: '6px 12px', marginBottom: '10px',
              background: '#fff8e1', border: '1px solid #ffe082',
              borderRadius: '4px', fontSize: '0.85em', color: '#795548'
            }}>
              ℹ️ Showing sample data — enter a location above for live results
            </div>
          )}

          <div style={{
            padding: '16px', borderRadius: '8px', border: `2px solid ${statusColor}`,
            borderLeft: `6px solid ${statusColor}`, background: '#fafafa'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <h4 style={{ margin: 0, color: '#333' }}>
                📍 {selectedLocation?.name || query || DEFAULT_LOCATION}
              </h4>
              <span style={{
                padding: '4px 12px', borderRadius: '20px', fontWeight: 700,
                background: statusColor, color: '#fff', fontSize: '0.9em'
              }}>
                {displayStatus} Traffic
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '14px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '4px' }}>Traffic Level</div>
                <div style={{ fontWeight: 700, color: statusColor, fontSize: '1.1em' }}>{displayStatus}</div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '4px' }}>Noise Level</div>
                <div style={{ fontWeight: 700, color: '#555', fontSize: '1.1em' }}>
                  {trafficData.noise_level || 'Medium'}
                </div>
              </div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '4px' }}>Speed</div>
                <div style={{ fontWeight: 700, color: '#333', fontSize: '1.1em' }}>
                  {trafficData.live_speed_kmh || 32} km/h
                </div>
              </div>
            </div>

            {/* Congestion bar */}
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '4px' }}>
                Congestion: {Math.round(congestion * 100)}%
              </div>
              <div style={{ background: '#eee', borderRadius: '4px', height: '8px' }}>
                <div style={{
                  width: `${congestion * 100}%`, height: '100%',
                  background: statusColor, borderRadius: '4px',
                  transition: 'width 0.5s ease'
                }} />
              </div>
            </div>

            {/* Suggestion */}
            <div style={{
              padding: '8px 12px', background: '#f0f4ff',
              borderRadius: '4px', fontSize: '0.9em', color: '#3949ab'
            }}>
              💡 <strong>Suggestion:</strong> {trafficData.suggestion || 'Drive carefully'}
            </div>

            {/* View on Map */}
            <button
              onClick={handleViewOnMap}
              style={{
                marginTop: '12px', width: '100%', padding: '10px',
                background: '#2196F3', color: '#fff', border: 'none',
                borderRadius: '6px', fontWeight: 600, cursor: 'pointer', fontSize: '0.95em'
              }}
            >
              📍 View on Map
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default LocationSearch;