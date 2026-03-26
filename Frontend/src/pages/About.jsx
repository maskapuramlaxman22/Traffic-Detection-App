import React from 'react';

const About = () => {
  return (
    <div className="container">
      <div className="card" style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#333' }}>
          🚗 Road Traffic Conditions Detection using Environmental Audio Signals
        </h1>
        <p style={{ fontSize: '1.1em', color: '#666', marginBottom: 0 }}>
          An innovative solution to predict real-time traffic conditions using advanced audio signal processing and machine learning
        </p>
      </div>

      {/* Project Purpose */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', color: '#2c3e50', borderBottom: '3px solid #3498db', paddingBottom: '10px' }}>
          🎯 Project Purpose
        </h2>
        <p style={{ fontSize: '1em', lineHeight: '1.8', color: '#555' }}>
          Traffic congestion is one of the major challenges in urban areas, causing economic losses, environmental pollution, 
          and reduced quality of life. Traditional traffic monitoring systems rely on cameras, sensors, or paid APIs that are expensive 
          and hard to scale.
        </p>
        <p style={{ fontSize: '1em', lineHeight: '1.8', color: '#555' }}>
          <strong>TrafficDetect</strong> takes a novel approach: <strong>using audio signals to detect traffic conditions</strong>. 
          Different traffic densities produce distinctly different audio patterns (horn frequency, noise levels, vehicle sounds). 
          By analyzing these environmental audio signals with machine learning, we can accurately predict traffic status without 
          expensive infrastructure.
        </p>
        <div style={{ background: '#e8f4f8', padding: '15px', borderRadius: '5px', marginTop: '15px', borderLeft: '4px solid #3498db' }}>
          <strong>✨ Key Innovation:</strong> Convert environmental sound patterns → ML model → Real-time traffic prediction
        </div>
      </div>

      {/* How It Works */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', color: '#2c3e50', borderBottom: '3px solid #27ae60', paddingBottom: '10px' }}>
          🔧 How Audio-Based Traffic Detection Works
        </h2>
        
        <div style={{ marginTop: '20px' }}>
          <h4 style={{ color: '#2c3e50', fontSize: '1.2em' }}>📊 Step-by-Step Process:</h4>
          <ol style={{ lineHeight: '2', color: '#555' }}>
            <li>
              <strong>Audio Capture:</strong> Traffic camera microphones or IoT sensors continuously capture ambient sound from roads
            </li>
            <li>
              <strong>Feature Extraction:</strong> Advanced audio processing extracts distinctive patterns:
              <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                <li><strong>MFCC</strong> (Mel-Frequency Cepstral Coefficients) - Human auditory perception</li>
                <li><strong>ZCR</strong> (Zero Crossing Rate) - Sound complexity indicator</li>
                <li><strong>Spectral Centroid</strong> - Frequency distribution of noise</li>
                <li><strong>Energy/Amplitude</strong> - Sound intensity levels</li>
              </ul>
            </li>
            <li>
              <strong>Machine Learning Model:</strong> A trained Decision Tree model analyzes these features and classifies traffic:
              <ul style={{ marginLeft: '20px', marginTop: '8px' }}>
                <li>🟢 <strong>Free Flow:</strong> Light traffic, smooth vehicle movement</li>
                <li>🟡 <strong>Moderate:</strong> Normal congestion, slower speeds</li>
                <li>🔴 <strong>Heavy:</strong> Severe congestion, frequent honks/braking</li>
              </ul>
            </li>
            <li>
              <strong>Real-Time Prediction:</strong> Results are sent to users instantly with confidence scores
            </li>
            <li>
              <strong>History & Analytics:</strong> Historical data tracked, analyzed, and visualized for trends
            </li>
          </ol>
        </div>

        <div style={{ background: '#fff3cd', padding: '15px', borderRadius: '5px', marginTop: '15px', borderLeft: '4px solid #f39c12' }}>
          <strong>💡 Why This Works:</strong> Traffic patterns create unique audio signatures. Heavy traffic = more honks, 
          engine noise, and brake sounds. Light traffic = quiet roads. Our ML model learns these patterns to predict traffic accurately!
        </div>
      </div>

      {/* Technologies Used */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', color: '#2c3e50', borderBottom: '3px solid #e74c3c', paddingBottom: '10px' }}>
          💻 Technologies & Architecture
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' }}>
          <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '5px' }}>
            <h4 style={{ color: '#e74c3c' }}>🎨 Frontend</h4>
            <ul style={{ marginLeft: '20px', color: '#555' }}>
              <li><strong>React 18</strong> - Modern UI with Hooks</li>
              <li><strong>Axios</strong> - API communication</li>
              <li><strong>Chart.js</strong> - Traffic trend visualization</li>
              <li><strong>Leaflet</strong> - Interactive mapping</li>
              <li><strong>CSS Grid/Flexbox</strong> - Responsive design</li>
            </ul>
          </div>

          <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '5px' }}>
            <h4 style={{ color: '#27ae60' }}>🔌 Backend API</h4>
            <ul style={{ marginLeft: '20px', color: '#555' }}>
              <li><strong>Python Flask</strong> - REST API framework</li>
              <li><strong>SQLite</strong> - History & location storage</li>
              <li><strong>Flask-SocketIO</strong> - Real-time updates</li>
              <li><strong>CORS & Middleware</strong> - Security & optimization</li>
            </ul>
          </div>

          <div style={{ background: '#f5f5f5', padding: '15px', borderRadius: '5px' }}>
            <h4 style={{ color: '#3498db' }}>🧠 ML & Audio Processing</h4>
            <ul style={{ marginLeft: '20px', color: '#555' }}>
              <li><strong>Librosa</strong> - Audio feature extraction</li>
              <li><strong>scikit-learn</strong> - Decision Tree classifier</li>
              <li><strong>NumPy/SciPy</strong> - Signal processing</li>
              <li><strong>PyAudio</strong> - Real-time audio capture</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Free APIs Used */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', color: '#2c3e50', borderBottom: '3px solid #f39c12', paddingBottom: '10px' }}>
          🌐 100% FREE APIs (Zero Cost!)
        </h2>
        <p style={{ fontSize: '1em', lineHeight: '1.8', color: '#555', marginBottom: '20px' }}>
          <strong>TrafficDetect uses only open-source and completely free APIs.</strong> No subscription costs, no API keys needed, 
          no hidden charges. Built for accessibility and scalability!
        </p>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '15px' }}>
          <div style={{ background: '#f0f8ff', padding: '15px', borderRadius: '5px', border: '2px solid #3498db' }}>
            <h4 style={{ color: '#3498db', marginTop: 0 }}>📍 Nominatim (OpenStreetMap)</h4>
            <p style={{ color: '#555', marginBottom: '8px' }}>
              <strong>Purpose:</strong> Location geocoding & reverse geocoding
            </p>
            <p style={{ color: '#666', fontSize: '0.95em' }}>
              Converts location names to coordinates and vice versa. Completely free with no API key required!
            </p>
          </div>

          <div style={{ background: '#eff8f0', padding: '15px', borderRadius: '5px', border: '2px solid #27ae60' }}>
            <h4 style={{ color: '#27ae60', marginTop: 0 }}>🛣️ OSRM (Open Source Routing)</h4>
            <p style={{ color: '#555', marginBottom: '8px' }}>
              <strong>Purpose:</strong> Route planning & distance calculation
            </p>
            <p style={{ color: '#666', fontSize: '0.95em' }}>
              Provides routing, distance matrix, and duration estimates. Completely open-source and free to use!
            </p>
          </div>

          <div style={{ background: '#fff8f0', padding: '15px', borderRadius: '5px', border: '2px solid #e67e22' }}>
            <h4 style={{ color: '#e67e22', marginTop: 0 }}>🌤️ Open-Meteo</h4>
            <p style={{ color: '#555', marginBottom: '8px' }}>
              <strong>Purpose:</strong> Weather data integration
            </p>
            <p style={{ color: '#666', fontSize: '0.95em' }}>
              Real-time weather data that impacts traffic. FREE tier with no API key required!
            </p>
          </div>

          <div style={{ background: '#f5f0ff', padding: '15px', borderRadius: '5px', border: '2px solid #9b59b6' }}>
            <h4 style={{ color: '#9b59b6', marginTop: 0 }}>🚨 OpenStreetMap Overpass</h4>
            <p style={{ color: '#555', marginBottom: '8px' }}>
              <strong>Purpose:</strong> Traffic incidents detection
            </p>
            <p style={{ color: '#666', fontSize: '0.95em' }}>
              Identifies road blocks, accidents, and construction zones. Completely free and open-source!
            </p>
          </div>
        </div>

        <div style={{ background: '#e8f8f5', padding: '15px', borderRadius: '5px', marginTop: '20px', borderLeft: '4px solid #16a085' }}>
          <strong>✨ Why Free APIs?</strong>
          <ul style={{ marginLeft: '20px', color: '#555', marginTop: '10px' }}>
            <li>✅ <strong>No Costs:</strong> 100% free, no subscription needed</li>
            <li>✅ <strong>Scalable:</strong> Can handle millions of requests</li>
            <li>✅ <strong>Reliable:</strong> Community-maintained, battle-tested</li>
            <li>✅ <strong>Open Source:</strong> No vendor lock-in, full transparency</li>
            <li>✅ <strong>Global:</strong> Works worldwide, perfect for international expansion</li>
          </ul>
        </div>
      </div>

      {/* Real-World Applications */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', color: '#2c3e50', borderBottom: '3px solid #9b59b6', paddingBottom: '10px' }}>
          🌍 Real-World Applications
        </h2>
        <ul style={{ fontSize: '1em', lineHeight: '2', color: '#555', marginLeft: '20px' }}>
          <li><strong>🚦 Smart City Traffic Management:</strong> City traffic control systems can optimize signal timing</li>
          <li><strong>🗺️ Navigation Apps:</strong> Integration with Google Maps, Waze for real-time route suggestions</li>
          <li><strong>📱 Commuter Apps:</strong> Help users choose best travel times and routes</li>
          <li><strong>🏢 Urban Planning:</strong> Understand traffic patterns for infrastructure development</li>
          <li><strong>🚨 Emergency Response:</strong> Ambulances/Fire departments get optimal route recommendations</li>
          <li><strong>📊 Government Analytics:</strong> Track congestion trends, identify traffic hotspots</li>
          <li><strong>🌱 Environmental Impact:</strong> Reduce emissions by optimizing traffic flow</li>
          <li><strong>💰 Cost Reduction:</strong> No expensive infrastructure, just audio sensors + AI</li>
        </ul>
      </div>

      {/* Design Philosophy */}
      <div className="card">
        <h2 style={{ fontSize: '2rem', color: '#2c3e50', borderBottom: '3px solid #16a085', paddingBottom: '10px' }}>
          ✨ Design Philosophy
        </h2>
        <p style={{ fontSize: '1em', lineHeight: '1.8', color: '#555' }}>
          <strong>User-Centric Design:</strong> We believe technology should be simple, intuitive, and helpful. That's why:
        </p>
        <ul style={{ fontSize: '1em', lineHeight: '2', color: '#555', marginLeft: '20px' }}>
          <li>✅ <strong>One-Click Search:</strong> Type location → Get traffic instantly</li>
          <li>✅ <strong>Visual Feedback:</strong> Color-coded status (Green/Yellow/Red)</li>
          <li>✅ <strong>Smart Suggestions:</strong> Auto-complete for faster search</li>
          <li>✅ <strong>Historical Insights:</strong> See traffic trends over time</li>
          <li>✅ <strong>Route Planning:</strong> Analyze multiple points on a route</li>
          <li>✅ <strong>Mobile-Friendly:</strong> Works seamlessly on all devices</li>
        </ul>
      </div>

      {/* Future Enhancements */}
      <div className="card" style={{ background: '#e8f8f5' }}>
        <h2 style={{ fontSize: '2rem', color: '#16a085', borderBottom: '3px solid #16a085', paddingBottom: '10px' }}>
          🚀 Future Roadmap
        </h2>
        <ul style={{ fontSize: '1em', lineHeight: '2', color: '#555', marginLeft: '20px' }}>
          <li>📡 <strong>Real-Time Streaming:</strong> Live audio feed from 100+ traffic cameras</li>
          <li>🤖 <strong>Advanced ML:</strong> Neural networks for even better predictions</li>
          <li>🌐 <strong>Multi-City Coverage:</strong> Expand to 50+ cities</li>
          <li>📱 <strong>Mobile Apps:</strong> iOS & Android native applications</li>
          <li>🛵 <strong>Multi-Transport:</strong> Support for buses, bikes, public transport</li>
          <li>🔔 <strong>Smart Alerts:</strong> Predictive alerts before traffic happens</li>
          <li>🌍 <strong>API for Developers:</strong> Open API for third-party integrations</li>
        </ul>
      </div>

      {/* Contact Information */}
      <div className="card">
        <h3 style={{ color: '#2c3e50' }}>📧 Contact & Feedback</h3>
        <p style={{ color: '#666' }}>
          Have suggestions? Found a bug? Want to collaborate? We'd love to hear from you!
        </p>
        <p style={{ color: '#555' }}>
          This project is part of academic research in traffic management and audio signal processing.
          Your feedback helps us improve the system.
        </p>
      </div>
    </div>
  );
};

export default About;