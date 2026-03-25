import React, { useState, useEffect } from 'react';
import { getHistory } from '../services/api';
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

const History = () => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    const data = await getHistory();
    setHistory(data);
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
      <h3 className="card-title">Search History</h3>
      
      <div className="grid-2">
        <div>
          <h4>Statistics</h4>
          <div style={{ marginTop: '10px' }}>
            <p>🟢 Low Traffic: {trafficCounts['Low Traffic']}</p>
            <p>🟡 Moderate Traffic: {trafficCounts['Moderate Traffic']}</p>
            <p>🔴 High Traffic: {trafficCounts['High Traffic']}</p>
            <p>📊 Total Searches: {history.length}</p>
          </div>
        </div>
        
        <div>
          <Line data={chartData} options={chartOptions} />
        </div>
      </div>
      
      <div style={{ marginTop: '20px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#f5f5f5' }}>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Type</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Location</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Status</th>
              <th style={{ padding: '10px', border: '1px solid #ddd' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {history.map((item, idx) => (
              <tr key={idx}>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                  {item.type === 'single' ? '📍 Single' : '🗺️ Route'}
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                  {item.location || `${item.source} → ${item.destination}`}
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                  <span className={`traffic-${item.traffic_status.toLowerCase().split(' ')[0]}`}>
                    {item.traffic_status}
                  </span>
                </td>
                <td style={{ padding: '8px', border: '1px solid #ddd' }}>
                  {new Date(item.timestamp).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default History;