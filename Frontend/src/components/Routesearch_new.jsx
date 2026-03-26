import React, { useState, useRef } from 'react';
import { getRouteTraffic, searchLocations, saveSearch } from '../services/api';
import RouteVisualization from './RouteVisualization';

/**
 * RouteSearch Component
 * =====================
 * 
 * Allows users to search for routes and view:
 * - Source and destination location inputs with autocomplete
 * - Route traffic information
 * - Traffic indicators via RouteVisualization
 * 
 * Does NOT embed a map - instead provides "View on Map" button
 * that opens Google Maps/OpenStreetMap in a new tab
 */
const RouteSearch = ({ onSearch, onAlert }) => {
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destSuggestions, setDestSuggestions] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [selectedDest, setSelectedDest] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hoveredSourceIdx, setHoveredSourceIdx] = useState(-1);
  const [hoveredDestIdx, setHoveredDestIdx] = useState(-1);
  const sourceDebounceTimer = useRef(null);
  const destDebounceTimer = useRef(null);

  // Debounced source search
  const handleSourceChange = (value) => {
    setSource(value);
    setError(null);
    
    if (sourceDebounceTimer.current) {
      clearTimeout(sourceDebounceTimer.current);
    }
    
    if (value.length < 2) {
      setSourceSuggestions([]);
      return;
    }
    
    sourceDebounceTimer.current = setTimeout(async () => {
      try {
        const results = await searchLocations(value);
        setSourceSuggestions(Array.isArray(results) ? results : []);
      } catch (err) {
        console.error('Source search error:', err);
        setSourceSuggestions([]);
      }
    }, 300);
  };

  // Debounced destination search
  const handleDestChange = (value) => {
    setDestination(value);
    setError(null);
    
    if (destDebounceTimer.current) {
      clearTimeout(destDebounceTimer.current);
    }
    
    if (value.length < 2) {
      setDestSuggestions([]);
      return;
    }
    
    destDebounceTimer.current = setTimeout(async () => {
      try {
        const results = await searchLocations(value);
        setDestSuggestions(Array.isArray(results) ? results : []);
      } catch (err) {
        console.error('Destination search error:', err);
        setDestSuggestions([]);
      }
    }, 300);
  };

  const handleSelectSource = (location) => {
    setSelectedSource(location);
    setSource(location.name || location.address || '');
    setSourceSuggestions([]);
    setHoveredSourceIdx(-1);
  };

  const handleSelectDest = (location) => {
    setSelectedDest(location);
    setDestination(location.name || location.address || '');
    setDestSuggestions([]);
    setHoveredDestIdx(-1);
  };

  const handleSearch = async () => {
    if (!selectedSource || !selectedDest) {
      setError('Please select both source and destination');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await getRouteTraffic(
        selectedSource.name || selectedSource,
        selectedDest.name || selectedDest
      );
      
      if (!result) {
        setError('Could not find route. Please try different locations.');
        setLoading(false);
        return;
      }
      
      setRouteData(result);
      
      // Alert if high traffic detected
      if (result.high_traffic_detected) {
        onAlert?.('🚨 Heavy traffic detected on your route!');
      }
      
      // Save to history
      try {
        await saveSearch({
          query: `${selectedSource.name || selectedSource} to ${selectedDest.name || selectedDest}`,
          type: 'route',
          result: result
        });
      } catch (e) {
        console.warn('Could not save search:', e);
      }
      
      onSearch?.(result);
    } catch (error) {
      console.error('Route search error:', error);
      setError('Failed to get route. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Suggestion dropdown component
  const SuggestionDropdown = ({ items, onSelect, hoveredIdx, setHoveredIdx }) => {
    if (items.length === 0) return null;
    
    return (
      <ul style={{
        position: 'absolute',
        top: '100%',
        left: 0,
        right: 0,
        border: '1px solid #ddd',
        borderTop: 'none',
        marginTop: 0,
        maxHeight: '280px',
        overflowY: 'auto',
        background: '#fff',
        zIndex: 1000,
        listStyle: 'none',
        padding: 0,
        margin: 0,
        borderRadius: '0 0 4px 4px',
        boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
      }}>
        {items.map((loc, idx) => (
          <li
            key={idx}
            onClick={() => onSelect(loc)}
            onMouseEnter={() => setHoveredIdx(idx)}
            onMouseLeave={() => setHoveredIdx(-1)}
            style={{
              padding: '12px 15px',
              cursor: 'pointer',
              borderBottom: idx < items.length - 1 ? '1px solid #eee' : 'none',
              background: hoveredIdx === idx ? '#f5f5f5' : '#fff',
              transition: 'background 0.2s ease'
            }}
          >
            <div style={{ fontWeight: '500', color: '#333' }}>
              📌 {loc.name || loc.address}
            </div>
            {loc.address && (
              <div style={{ fontSize: '0.85em', color: '#666', marginTop: '4px' }}>
                {loc.address}
              </div>
            )}
          </li>
        ))}
      </ul>
    );
  };

  const handleClear = () => {
    setSource('');
    setDestination('');
    setSelectedSource(null);
    setSelectedDest(null);
    setRouteData(null);
    setError(null);
  };

  return (
    <div className="card">
      <h3 className="card-title">🗺️ Search Route Traffic</h3>
      
      {/* Error Message */}
      {error && (
        <div style={{
          padding: '10px 15px',
          marginBottom: '15px',
          background: '#fee',
          border: '1px solid #f99',
          borderRadius: '4px',
          color: '#c33',
          fontSize: '0.9em'
        }}>
          ⚠️ {error}
        </div>
      )}
      
      {/* Source Location Input */}
      <div className="input-group">
        <label>📍 Source Location</label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={source}
            onChange={(e) => handleSourceChange(e.target.value)}
            placeholder="Where are you starting from? (e.g., Secunderabad)"
            style={{
              width: '100%',
              padding: '10px 12px',
              fontSize: '1em',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'inherit'
            }}
          />
          <SuggestionDropdown 
            items={sourceSuggestions} 
            onSelect={handleSelectSource}
            hoveredIdx={hoveredSourceIdx}
            setHoveredIdx={setHoveredSourceIdx}
          />
        </div>
      </div>
      
      {/* Destination Location Input */}
      <div className="input-group">
        <label>🎯 Destination Location</label>
        <div style={{ position: 'relative' }}>
          <input
            type="text"
            value={destination}
            onChange={(e) => handleDestChange(e.target.value)}
            placeholder="Where do you want to go? (e.g., Medchal)"
            style={{
              width: '100%',
              padding: '10px 12px',
              fontSize: '1em',
              border: '1px solid #ddd',
              borderRadius: '4px',
              fontFamily: 'inherit'
            }}
          />
          <SuggestionDropdown 
            items={destSuggestions} 
            onSelect={handleSelectDest}
            hoveredIdx={hoveredDestIdx}
            setHoveredIdx={setHoveredDestIdx}
          />
        </div>
      </div>

      {/* Selected Route Summary */}
      {selectedSource && selectedDest && (
        <div style={{
          marginTop: '12px',
          padding: '10px 15px',
          background: '#f0f8ff',
          border: '1px solid #80bfff',
          borderRadius: '4px',
          fontSize: '0.95em',
          color: '#0055aa',
          fontWeight: '500'
        }}>
          ✓ Route: <strong>{selectedSource.name || selectedSource}</strong> 
          {' → '} 
          <strong>{selectedDest.name || selectedDest}</strong>
        </div>
      )}
      
      {/* Action Buttons */}
      <div style={{ marginTop: '15px', display: 'flex', gap: '10px' }}>
        <button 
          className="btn btn-primary"
          onClick={handleSearch}
          disabled={loading || !selectedSource || !selectedDest}
          style={{ flex: 1 }}
        >
          {loading ? '⏳ Calculating...' : '📍 Get Route Traffic'}
        </button>
        
        {(selectedSource || selectedDest) && (
          <button 
            className="btn btn-secondary"
            onClick={handleClear}
            style={{ flex: 1 }}
          >
            ✕ Clear
          </button>
        )}
      </div>
      
      {/* Route Visualization (includes map button) */}
      {routeData && (
        <RouteVisualization 
          source={selectedSource}
          destination={selectedDest}
          routeData={routeData}
        />
      )}
    </div>
  );
};

export default RouteSearch;
