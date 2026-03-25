import React, { useState, useEffect } from 'react';

const Alerts = ({ message, onClose }) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false);
      if (onClose) onClose();
    }, 5000);
    
    return () => clearTimeout(timer);
  }, [onClose]);

  if (!visible || !message) return null;

  return (
    <div className="alert-banner">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>⚠️ {message}</span>
        <button 
          onClick={() => setVisible(false)}
          style={{ background: 'none', border: 'none', fontSize: '1.2rem', cursor: 'pointer' }}
        >
          ×
        </button>
      </div>
    </div>
  );
};

export default Alerts;