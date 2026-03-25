import React from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <div className="container">
      <div className="card" style={{ textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '20px' }}>
          🚦 Road Traffic Conditions Detection
        </h1>
        <p style={{ fontSize: '1.2rem', marginBottom: '30px' }}>
          Advanced traffic monitoring system using audio analysis and machine learning
        </p>
        
        <div className="grid-2" style={{ marginTop: '40px' }}>
          <div style={{ padding: '20px' }}>
            <div style={{ fontSize: '3rem' }}>🎵</div>
            <h3>Audio Analysis</h3>
            <p>Advanced audio feature extraction using MFCC, ZCR, and spectral analysis</p>
          </div>
          
          <div style={{ padding: '20px' }}>
            <div style={{ fontSize: '3rem' }}>🤖</div>
            <h3>Machine Learning</h3>
            <p>Decision Tree model for accurate traffic prediction</p>
          </div>
          
          <div style={{ padding: '20px' }}>
            <div style={{ fontSize: '3rem' }}>📊</div>
            <h3>Real-time Monitoring</h3>
            <p>Live traffic updates with auto-refresh capability</p>
          </div>
          
          <div style={{ padding: '20px' }}>
            <div style={{ fontSize: '3rem' }}>🔔</div>
            <h3>Smart Alerts</h3>
            <p>Instant notifications for heavy traffic conditions</p>
          </div>
        </div>
        
        <Link to="/dashboard">
          <button className="btn btn-primary" style={{ marginTop: '30px', fontSize: '1.2rem' }}>
            Get Started →
          </button>
        </Link>
      </div>
    </div>
  );
};

export default Home;