import React, { useState, useEffect } from 'react';
import { getSettings, updateSettings } from '../services/api';

const Settings = () => {
  const [settings, setSettings] = useState({
    refresh_interval: 30,
    alerts_enabled: true
  });
  const [message, setMessage] = useState('');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    const data = await getSettings();
    setSettings(data);
  };

  const handleSave = async () => {
    await updateSettings(settings);
    setMessage('Settings saved successfully!');
    setTimeout(() => setMessage(''), 3000);
  };

  return (
    <div className="card">
      <h3 className="card-title">Settings</h3>
      
      <div className="input-group">
        <label>Auto-refresh Interval (seconds)</label>
        <select
          value={settings.refresh_interval}
          onChange={(e) => setSettings({ ...settings, refresh_interval: parseInt(e.target.value) })}
        >
          <option value="15">15 seconds</option>
          <option value="30">30 seconds</option>
          <option value="60">1 minute</option>
          <option value="300">5 minutes</option>
        </select>
      </div>
      
      <div className="input-group">
        <label>
          <input
            type="checkbox"
            checked={settings.alerts_enabled}
            onChange={(e) => setSettings({ ...settings, alerts_enabled: e.target.checked })}
            style={{ width: 'auto', marginRight: '10px' }}
          />
          Enable Alerts
        </label>
      </div>
      
      <button className="btn btn-primary" onClick={handleSave}>
        Save Settings
      </button>
      
      {message && (
        <div style={{ marginTop: '10px', color: 'green' }}>
          {message}
        </div>
      )}
      
      <div style={{ marginTop: '15px', fontSize: '0.9rem', color: '#666' }}>
        <strong>Note:</strong> Auto-refresh will automatically fetch traffic updates every {settings.refresh_interval} seconds.
      </div>
    </div>
  );
};

export default Settings;