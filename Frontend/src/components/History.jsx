import React, { useState, useEffect } from 'react';
import { getTrafficHistory, clearHistory } from '../services/api';

const History = ({ refreshTrigger }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAllLoc, setShowAllLoc] = useState(false);
  const [showAllRoute, setShowAllRoute] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, [refreshTrigger]);

  const fetchHistory = async () => {
    const data = await getTrafficHistory(undefined, 100);
    setHistory(data.history || []);
    setLoading(false);
  };

  const locationHistory = history.filter(item => item.type === 'location' || item.type === 'single' || item.location);
  const routeHistory = history.filter(item => item.type === 'route' || item.source);

  const getStats = (list) => {
    const counts = { low: 0, moderate: 0, high: 0 };
    list.forEach(item => {
      const status = (item.traffic_status || '').toLowerCase();
      if (status.includes('low')) counts.low++;
      else if (status.includes('high') || status.includes('heavy')) counts.high++;
      else counts.moderate++;
    });
    return counts;
  };

  const locStats = getStats(locationHistory);
  const routeStats = getStats(routeHistory);

  if (loading) return <div style={{ padding: '20px', textAlign: 'center' }}>⏳ Loading History...</div>;

  const Table = ({ data, isRoute, showAll, onToggle }) => (
    <div style={{ marginTop: '20px', border: '1px solid #eee', borderRadius: '8px', padding: '15px', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h4 style={{ margin: 0 }}>{isRoute ? '🗺️ Recent Route Searches' : '📍 Recent Location Searches'}</h4>
        {data.length > 5 && (
          <button onClick={onToggle} style={{ background: 'none', border: 'none', color: '#007bff', cursor: 'pointer', fontWeight: 600 }}>
            {showAll ? 'Show Less' : `View All (${data.length})`}
          </button>
        )}
      </div>

      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9em' }}>
        <thead>
          <tr style={{ background: '#f8f9fa', borderBottom: '2px solid #eee' }}>
            <th style={{ padding: '10px', textAlign: 'left' }}>{isRoute ? 'Route' : 'Location'}</th>
            <th style={{ padding: '10px', textAlign: 'left' }}>Status</th>
            <th style={{ padding: '10px', textAlign: 'left' }}>Date</th>
          </tr>
        </thead>
        <tbody>
          {data.length > 0 ? (
            (showAll ? data : data.slice(0, 5)).map((item, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid #f2f2f2' }}>
                <td style={{ padding: '10px' }}>
                   {isRoute ? `${item.source || '-'} → ${item.destination || '-'}` : (item.location || item.query || '-')}
                </td>
                <td style={{ padding: '10px' }}>
                  <span style={{ 
                    padding: '2px 8px', borderRadius: '10px', fontSize: '0.8em', fontWeight: 600,
                    background: (item.traffic_status || '').toLowerCase().includes('high') ? '#ffebee' : (item.traffic_status || '').toLowerCase().includes('low') ? '#e8f5e9' : '#fff3e0',
                    color: (item.traffic_status || '').toLowerCase().includes('high') ? '#c62828' : (item.traffic_status || '').toLowerCase().includes('low') ? '#2e7d32' : '#ef6c00'
                  }}>
                    {item.traffic_status || 'Moderate'}
                  </span>
                </td>
                <td style={{ padding: '10px', color: '#888' }}>
                  {new Date(item.timestamp).toLocaleDateString()}
                </td>
              </tr>
            ))
          ) : (
            <tr><td colSpan="3" style={{ padding: '20px', textAlign: 'center', color: '#999' }}>No history yet.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear ALL search history? This cannot be undone.')) {
      await clearHistory();
      setHistory([]);
    }
  };

  return (
    <div className="card" style={{ background: '#fcfcfc' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
        <h3 className="card-title" style={{ margin: 0 }}>📊 Search Statistics & History</h3>
        {history.length > 0 && (
          <button 
            onClick={handleClearHistory}
            style={{ padding: '8px 15px', background: '#dc3545', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 600, fontSize: '0.85em' }}
          >
            🗑️ Clear History
          </button>
        )}
      </div>
      
      <div className="grid-2">
        {/* Location Stats */}
        <div style={{ padding: '15px', background: '#fff', borderRadius: '8px', border: '1px solid #f0f0f0' }}>
          <h4 style={{ marginBottom: '12px' }}>📍 Location Totals</h4>
          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.9em' }}>🟢 Low: <strong>{locStats.low}</strong></span>
            <span style={{ fontSize: '0.9em' }}>🟡 Mod: <strong>{locStats.moderate}</strong></span>
            <span style={{ fontSize: '0.9em' }}>🔴 High: <strong>{locStats.high}</strong></span>
            <span style={{ fontSize: '0.9em', marginLeft: 'auto' }}>Total: <strong>{locationHistory.length}</strong></span>
          </div>
          <Table data={locationHistory} isRoute={false} showAll={showAllLoc} onToggle={() => setShowAllLoc(!showAllLoc)} />
        </div>

        {/* Route Stats */}
        <div style={{ padding: '15px', background: '#fff', borderRadius: '8px', border: '1px solid #f0f0f0' }}>
          <h4 style={{ marginBottom: '12px' }}>🗺️ Route Totals</h4>
          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.9em' }}>🟢 Low: <strong>{routeStats.low}</strong></span>
            <span style={{ fontSize: '0.9em' }}>🟡 Mod: <strong>{routeStats.moderate}</strong></span>
            <span style={{ fontSize: '0.9em' }}>🔴 High: <strong>{routeStats.high}</strong></span>
            <span style={{ fontSize: '0.9em', marginLeft: 'auto' }}>Total: <strong>{routeHistory.length}</strong></span>
          </div>
          <Table data={routeHistory} isRoute={true} showAll={showAllRoute} onToggle={() => setShowAllRoute(!showAllRoute)} />
        </div>
      </div>
    </div>
  );
};

export default History;