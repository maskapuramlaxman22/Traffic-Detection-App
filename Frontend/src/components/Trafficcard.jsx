import React from 'react';

const TrafficCard = ({ data }) => {
  const getStatusClass = (status) => {
    if (status.includes('Low')) return 'traffic-low';
    if (status.includes('Moderate')) return 'traffic-moderate';
    if (status.includes('High')) return 'traffic-high';
    return '';
  };

  const getIcon = (status) => {
    if (status.includes('Low')) return '🟢';
    if (status.includes('Moderate')) return '🟡';
    if (status.includes('High')) return '🔴';
    return '⚪';
  };

  return (
    <div className="card" style={{ marginTop: '20px', background: '#f9f9f9' }}>
      <h4>Traffic Analysis Result</h4>
      <div style={{ textAlign: 'center', padding: '20px' }}>
        <div style={{ fontSize: '3rem' }}>{getIcon(data.traffic_status)}</div>
        <div style={{ fontSize: '1.2rem', marginTop: '10px' }}>
          <strong>{data.location}</strong>
        </div>
        <div className={getStatusClass(data.traffic_status)} style={{ fontSize: '1.5rem', marginTop: '10px' }}>
          {data.traffic_status}
        </div>
        <div style={{ marginTop: '10px', fontSize: '0.9rem', color: '#666' }}>
          Analyzed at: {new Date(data.timestamp).toLocaleString()}
        </div>
      </div>
    </div>
  );
};

export default TrafficCard;