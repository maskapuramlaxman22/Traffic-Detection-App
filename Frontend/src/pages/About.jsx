import React from 'react';

const About = () => {
  return (
    <div className="container">
      <div className="card">
        <h3 className="card-title">About the Project</h3>
        
        <div style={{ marginTop: '20px' }}>
          <h4>Project Overview</h4>
          <p>
            This Road Traffic Conditions Detection system uses advanced audio analysis and machine learning
            to predict traffic conditions in real-time. By analyzing audio features such as MFCC,
            zero-crossing rate, and spectral centroids, the system can accurately determine traffic density.
          </p>
        </div>
        
        <div style={{ marginTop: '20px' }}>
          <h4>Technology Stack</h4>
          <ul style={{ marginLeft: '20px', marginTop: '10px' }}>
            <li><strong>Frontend:</strong> React.js with modern Hooks and functional components</li>
            <li><strong>Backend:</strong> Python Flask REST API</li>
            <li><strong>Database:</strong> SQLite for location and history storage</li>
            <li><strong>ML & Audio:</strong> scikit-learn (Decision Tree), librosa for audio analysis</li>
            <li><strong>Visualization:</strong> Chart.js for traffic trend graphs</li>
          </ul>
        </div>
        
        <div style={{ marginTop: '20px' }}>
          <h4>Features</h4>
          <ul style={{ marginLeft: '20px', marginTop: '10px' }}>
            <li>✅ Single location search with autocomplete</li>
            <li>✅ Route-based traffic analysis with intermediate points</li>
            <li>✅ Audio feature extraction for accurate predictions</li>
            <li>✅ ML-powered Decision Tree model</li>
            <li>✅ Search history with statistics and graphs</li>
            <li>✅ Smart alert system for heavy traffic</li>
            <li>✅ Customizable settings (refresh interval, alerts)</li>
            <li>✅ Responsive design for all devices</li>
          </ul>
        </div>
        
        <div style={{ marginTop: '20px' }}>
          <h4>How It Works</h4>
          <ol style={{ marginLeft: '20px', marginTop: '10px' }}>
            <li>Audio is captured from traffic cameras/sensors</li>
            <li>Librosa extracts audio features (MFCC, ZCR, Spectral)</li>
            <li>Decision Tree model analyzes patterns</li>
            <li>Traffic status (Low/Moderate/High) is predicted</li>
            <li>Results are displayed with color-coded indicators</li>
            <li>Alerts are triggered for high traffic conditions</li>
          </ol>
        </div>
        
        <div style={{ marginTop: '20px', padding: '15px', background: '#f5f5f5', borderRadius: '5px' }}>
          <h4>Future Enhancements</h4>
          <p>
            • Real-time audio streaming from traffic cameras<br/>
            • Integration with GPS and mapping services<br/>
            • Historical trend analysis with predictive forecasting<br/>
            • Mobile app development<br/>
            • Multi-city traffic comparison<br/>
            • Traffic optimization suggestions
          </p>
        </div>
      </div>
    </div>
  );
};

export default About;