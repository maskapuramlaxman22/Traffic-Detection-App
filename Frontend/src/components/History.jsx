import React, { useState, useEffect } from 'react';
import { getTrafficHistory } from '../services/api';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const History = ({ refreshTrigger }) => {
  const [history, setHistory] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    fetchHistory();
  }, [refreshTrigger]);

  const fetchHistory = async () => {
    const data = await getTrafficHistory(undefined, 24);
    setHistory(data.history || []);
    setTotalCount(data.total || data.count || (data.history || []).length);
    setLoading(false);
  };

  const getTrafficCount = () => {
    const counts = { 'Low Traffic': 0, 'Moderate Traffic': 0, 'High Traffic': 0 };
    history.forEach(item => {
      if (item.traffic_status in counts) {
        counts[item.traffic_status]++;
      }
    });
    return counts;
  };

  // Display only last 5 by default, or all if "View All" is clicked
  const displayedHistory = showAll ? history : history.slice(0, 5);
  const itemsToShow = showAll ? 15 : 5;

  const chartData = {
    labels: history.slice(0, 10).reverse().map(item => 
      new Date(item.timestamp).toLocaleDateString()
    ),
    datasets: [
      {
        label: 'Traffic Status',
        data: history.slice(0, 10).reverse().map(item => {
          const status = item.traffic_status;
          if (status === 'Low Traffic') return 1;
          if (status === 'Moderate Traffic') return 2;
          if (status === 'High Traffic') return 3;
          return 0;
        }),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.1
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
      title: {
        display: true,
        text: 'Recent Traffic Trends'
      }
    },
    scales: {
      y: {
        ticks: {
          callback: function(value) {
            if (value === 1) return 'Low';
            if (value === 2) return 'Moderate';
            if (value === 3) return 'High';
            return '';
          }
        }
      }
    }
  };

  if (loading) return <div>Loading history...</div>;

  const trafficCounts = getTrafficCount();

  return (
    <div className="card">
      <h3 className="card-title">📊 Search History</h3>
      
      <div className="grid-2">
        <div>
          <h4>Statistics</h4>
          <div style={{ marginTop: '10px' }}>
            <p>🟢 Low Traffic: {trafficCounts['Low Traffic']}</p>
            <p>🟡 Moderate Traffic: {trafficCounts['Moderate Traffic']}</p>
            <p>🔴 High Traffic: {trafficCounts['High Traffic']}</p>
            <p>📊 Total Searches: {totalCount}</p>
          </div>
        </div>
        
        <div>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
      
      <div style={{ marginTop: '30px', overflowX: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
          <h4 style={{ margin: 0 }}>Recent Searches ({displayedHistory.length} of {totalCount})</h4>
          {!showAll && history.length > 5 && (
            <button
              onClick={() => setShowAll(true)}
              style={{
                background: '#007bff',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                padding: '8px 16px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              View All ({totalCount})
            </button>
          )}
          {showAll && (
            <button
              onClick={() => setShowAll(false)}
              style={{
                background: '#6c757d',
                color: '#fff',
                border: 'none',
                borderRadius: '4px',
                padding: '8px 16px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              Show Less
            </button>
          )}
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f5f5' }}>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Type</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Location</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Status</th>
              <th style={{ padding: '12px', border: '1px solid #ddd', textAlign: 'left' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {displayedHistory.length > 0 ? (
              displayedHistory.map((item, idx) => (
                <tr key={idx}>
                  <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {item.type === 'single' ? '📍 Single' : '🗺️ Route'}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    {item.location || `${item.source} → ${item.destination}`}
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ddd' }}>
                    <span className={`traffic-${(item.traffic_status || 'moderate').toLowerCase().split(' ')[0]}`}>
                      {item.traffic_status || 'Moderate Traffic'}
                    </span>
                  </td>
                  <td style={{ padding: '10px', border: '1px solid #ddd', fontSize: '0.9em', color: '#666' }}>
                    {new Date(item.timestamp).toLocaleString()}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" style={{ padding: '20px', textAlign: 'center', color: '#999' }}>
                  No search history yet. Start by searching for a location or route!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default History;