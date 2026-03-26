import React, { useState, useRef } from 'react';
import { getRouteTraffic, searchLocations, saveSearch } from '../services/api';

// ─── Default sample data shown when route is not found or inputs are missing ───
const DEFAULT_SOURCE = 'Hyderabad';
const DEFAULT_DEST   = 'Bangalore';
const DEFAULT_ROUTE  = {
  source: DEFAULT_SOURCE,
  destination: DEFAULT_DEST,
  distance_km: 570,
  traffic_duration_minutes: 540, // 9 hours
  normal_duration_minutes: 480,
  delay_minutes: 60,
  nodes: [
    { name: 'Hyderabad',   traffic_level: 'Moderate' },
    { name: 'Kurnool',     traffic_level: 'Low'      },
    { name: 'Anantapur',   traffic_level: 'Low'      },
    { name: 'Bangalore',   traffic_level: 'High'     },
  ],
  isSample: true,
};

const levelColor = (level) => {
  if (!level) return '#ff9800';
  const l = level.toLowerCase();
  if (l === 'low')  return '#4caf50';
  if (l === 'high') return '#f44336';
  return '#ff9800';
};

const RouteSearch = ({ onSearch, onAlert }) => {
  const [source, setSource] = useState('');
  const [destination, setDestination] = useState('');
  const [sourceSuggestions, setSourceSuggestions] = useState([]);
  const [destSuggestions, setDestSuggestions] = useState([]);
  const [selectedSource, setSelectedSource] = useState(null);
  const [selectedDest, setSelectedDest] = useState(null);
  const [routeData, setRouteData] = useState(DEFAULT_ROUTE);   // ← show default immediately
  const [loading, setLoading] = useState(false);
  const [hoveredSourceIdx, setHoveredSourceIdx] = useState(-1);
  const [hoveredDestIdx, setHoveredDestIdx] = useState(-1);
  const sourceTimer = useRef(null);
  const destTimer   = useRef(null);

  // ── Autocomplete helpers ──────────────────────────────────────────────────
  const handleSourceChange = (value) => {
    setSource(value);
    if (sourceTimer.current) clearTimeout(sourceTimer.current);
    if (value.length < 2) { setSourceSuggestions([]); return; }
    sourceTimer.current = setTimeout(async () => {
      try { setSourceSuggestions((await searchLocations(value)) || []); } catch { setSourceSuggestions([]); }
    }, 300);
  };

  const handleDestChange = (value) => {
    setDestination(value);
    if (destTimer.current) clearTimeout(destTimer.current);
    if (value.length < 2) { setDestSuggestions([]); return; }
    destTimer.current = setTimeout(async () => {
      try { setDestSuggestions((await searchLocations(value)) || []); } catch { setDestSuggestions([]); }
    }, 300);
  };

  const selectSource = (loc) => { setSelectedSource(loc); setSource(loc.name || loc.address || ''); setSourceSuggestions([]); };
  const selectDest   = (loc) => { setSelectedDest(loc);   setDestination(loc.name || loc.address || '');   setDestSuggestions([]);   };

  // ── Main search ───────────────────────────────────────────────────────────
  const handleSearch = async () => {
    const srcName  = selectedSource ? (selectedSource.name || selectedSource.address) : source  || DEFAULT_SOURCE;
    const destName = selectedDest   ? (selectedDest.name   || selectedDest.address)   : destination || DEFAULT_DEST;

    setLoading(true);
    try {
      const result = await getRouteTraffic(srcName, destName);

      if (result && result.distance_km) {
        setRouteData({ ...result, isSample: false });
        if (result.high_traffic_detected) onAlert?.('🚨 Heavy traffic detected on your route!');
        try { await saveSearch({ query: `${srcName} to ${destName}`, type: 'route', result }); } catch { /* silent */ }
        onSearch?.(result);
      } else {
        // API gave nothing useful — show friendly sample
        setRouteData({ ...DEFAULT_ROUTE, source: srcName, destination: destName, isSample: true });
        onSearch?.({ traffic_level: 'Moderate' });
      }
    } catch {
      setRouteData({ ...DEFAULT_ROUTE, source: srcName, destination: destName, isSample: true });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setSource(''); setDestination('');
    setSelectedSource(null); setSelectedDest(null);
    setRouteData(DEFAULT_ROUTE);
  };

  const handleViewOnMap = () => {
    const src  = routeData?.source      || DEFAULT_SOURCE;
    const dest = routeData?.destination || DEFAULT_DEST;
    window.open(
      `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(src)}&destination=${encodeURIComponent(dest)}`,
      '_blank'
    );
  };

  // ── Suggestion Dropdown ───────────────────────────────────────────────────
  const Dropdown = ({ items, onSelect, hoveredIdx, setHoveredIdx }) => {
    if (!items || items.length === 0) return null;
    return (
      <ul style={{
        position: 'absolute', top: '100%', left: 0, right: 0,
        border: '1px solid #ddd', borderTop: 'none', maxHeight: '240px',
        overflowY: 'auto', background: '#fff', zIndex: 1000,
        listStyle: 'none', padding: 0, margin: 0,
        borderRadius: '0 0 4px 4px', boxShadow: '0 4px 8px rgba(0,0,0,0.15)'
      }}>
        {items.map((loc, idx) => (
          <li key={idx} onClick={() => onSelect(loc)}
            onMouseEnter={() => setHoveredIdx(idx)} onMouseLeave={() => setHoveredIdx(-1)}
            style={{
              padding: '10px 14px', cursor: 'pointer',
              borderBottom: idx < items.length - 1 ? '1px solid #eee' : 'none',
              background: hoveredIdx === idx ? '#f5f5f5' : '#fff', transition: 'background 0.15s'
            }}>
            <span style={{ marginRight: '6px' }}>📍</span>{loc.name || loc.address}
          </li>
        ))}
      </ul>
    );
  };

  const durationHours = routeData ? Math.floor(routeData.traffic_duration_minutes / 60) : 0;
  const durationMins  = routeData ? Math.round(routeData.traffic_duration_minutes % 60) : 0;

  return (
    <div className="card">
      <h3 className="card-title">🗺️ Search Route Traffic</h3>

      {/* Source Input */}
      <div className="input-group" style={{ marginBottom: '12px' }}>
        <label>Source Location</label>
        <div style={{ position: 'relative' }}>
          <input type="text" value={source} onChange={(e) => handleSourceChange(e.target.value)}
            placeholder="Starting point (e.g., Hyderabad)"
            style={{ width: '100%', padding: '10px 12px', fontSize: '1em', border: '1px solid #ddd', borderRadius: '4px' }}
          />
          <Dropdown items={sourceSuggestions} onSelect={selectSource} hoveredIdx={hoveredSourceIdx} setHoveredIdx={setHoveredSourceIdx} />
        </div>
      </div>

      {/* Destination Input */}
      <div className="input-group" style={{ marginBottom: '12px' }}>
        <label>Destination Location</label>
        <div style={{ position: 'relative' }}>
          <input type="text" value={destination} onChange={(e) => handleDestChange(e.target.value)}
            placeholder="Destination (e.g., Bangalore)"
            style={{ width: '100%', padding: '10px 12px', fontSize: '1em', border: '1px solid #ddd', borderRadius: '4px' }}
          />
          <Dropdown items={destSuggestions} onSelect={selectDest} hoveredIdx={hoveredDestIdx} setHoveredIdx={setHoveredDestIdx} />
        </div>
      </div>

      {/* Selected route preview */}
      {(selectedSource || selectedDest) && (
        <div style={{
          padding: '8px 12px', marginBottom: '12px',
          background: '#f0f8ff', border: '1px solid #80bfff',
          borderRadius: '4px', fontSize: '0.9em', color: '#0055aa'
        }}>
          ✓ Route: <strong>{selectedSource?.name || source || DEFAULT_SOURCE}</strong>
          {' → '}
          <strong>{selectedDest?.name || destination || DEFAULT_DEST}</strong>
        </div>
      )}

      {/* Action buttons */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '4px' }}>
        <button className="btn btn-primary" onClick={handleSearch} disabled={loading} style={{ flex: 1 }}>
          {loading ? '⏳ Calculating...' : '📍 Get Route Traffic'}
        </button>
        {(selectedSource || selectedDest || source || destination) && (
          <button className="btn btn-secondary" onClick={handleClear} style={{ flex: 1 }}>✕ Clear</button>
        )}
      </div>

      {/* ── Route Result ─────────────────────────────────────────────────── */}
      {routeData && (
        <div style={{ marginTop: '20px' }}>
          {routeData.isSample && (
            <div style={{
              padding: '6px 12px', marginBottom: '10px',
              background: '#fff8e1', border: '1px solid #ffe082',
              borderRadius: '4px', fontSize: '0.85em', color: '#795548'
            }}>
              ℹ️ Showing sample data — enter source & destination for live results
            </div>
          )}

          {/* Stats row */}
          <div style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px', marginBottom: '16px'
          }}>
            {[
              { label: '📏 Distance',      value: `${routeData.distance_km} km`,               color: '#2196F3' },
              { label: '⏱️ Est. Time',    value: durationHours > 0 ? `${durationHours}h ${durationMins}m` : `${durationMins} min`, color: '#ff9800' },
              { label: '🚦 Traffic',       value: 'Moderate',                                  color: '#ff9800' },
            ].map((s, i) => (
              <div key={i} style={{
                padding: '12px', textAlign: 'center',
                background: '#f9f9f9', border: '1px solid #eee', borderRadius: '6px'
              }}>
                <div style={{ fontSize: '0.8em', color: '#666', marginBottom: '4px' }}>{s.label}</div>
                <div style={{ fontWeight: 700, color: s.color, fontSize: '1.1em' }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* Route node visualization */}
          {routeData.nodes && routeData.nodes.length > 0 && (
            <div style={{
              padding: '16px', background: '#f8f9fa',
              border: '1px solid #e0e0e0', borderRadius: '8px', marginBottom: '14px'
            }}>
              <div style={{ fontSize: '0.85em', color: '#666', marginBottom: '14px', fontWeight: 600 }}>
                📍 Route Checkpoints
              </div>
              <div style={{ display: 'flex', alignItems: 'center', overflowX: 'auto', paddingBottom: '6px' }}>
                {routeData.nodes.map((node, idx) => (
                  <React.Fragment key={idx}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '80px' }}>
                      {/* Traffic badge */}
                      <span style={{
                        padding: '3px 8px', borderRadius: '12px', fontSize: '0.7em',
                        fontWeight: 700, background: levelColor(node.traffic_level),
                        color: '#fff', marginBottom: '8px', whiteSpace: 'nowrap'
                      }}>
                        {node.traffic_level || 'OK'}
                      </span>
                      {/* Circle */}
                      <div style={{
                        width: '20px', height: '20px', borderRadius: '50%',
                        background: levelColor(node.traffic_level),
                        boxShadow: `0 0 6px ${levelColor(node.traffic_level)}`
                      }} />
                      {/* Label */}
                      <div style={{
                        fontSize: '0.75em', color: '#444', textAlign: 'center',
                        marginTop: '6px', maxWidth: '75px', wordBreak: 'break-word'
                      }}>
                        {node.name.length > 10 ? node.name.substring(0, 10) + '…' : node.name}
                      </div>
                    </div>
                    {idx < routeData.nodes.length - 1 && (
                      <div style={{ flex: 1, height: '2px', background: '#ccc', minWidth: '16px', margin: '0 2px' }} />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>
          )}

          {/* View on Map button */}
          <button
            onClick={handleViewOnMap}
            style={{
              width: '100%', padding: '11px',
              background: '#2196F3', color: '#fff',
              border: 'none', borderRadius: '6px',
              fontWeight: 600, cursor: 'pointer', fontSize: '0.95em'
            }}
          >
            🗺️ View on Map (Opens Google Maps)
          </button>
        </div>
      )}
    </div>
  );
};

export default RouteSearch;