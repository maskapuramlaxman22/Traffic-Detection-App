import React, { useState, useEffect, useRef } from 'react';
import LocationSearch from '../components/Locationsearch';
import RouteSearch from '../components/Routesearch';
import History from '../components/History';
import Alerts from '../components/Alerts';
import Settings from '../components/Settings';
import { getSettings } from '../services/api';

const Dashboard = () => {
  const [alertMessage, setAlertMessage] = useState('');
  const [settings, setSettings] = useState({ refresh_interval: 30, alerts_enabled: true });
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const refreshInterval = useRef(null);

  useEffect(() => {
    loadSettings();
    return () => {
      if (refreshInterval.current) {
        clearInterval(refreshInterval.current);
      }
    };
  }, []);

  const loadSettings = async () => {
    const data = await getSettings();
    setSettings(data);
    
    if (refreshInterval.current) {
      clearInterval(refreshInterval.current);
    }
    
    if (data.refresh_interval > 0) {
      refreshInterval.current = setInterval(() => {
        setRefreshTrigger(prev => prev + 1);
      }, data.refresh_interval * 1000);
    }
  };

  const showAlert = (message) => {
    if (settings.alerts_enabled) {
      setAlertMessage(message);
    }
  };

  const handleSearchComplete = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="container">
      <Alerts message={alertMessage} onClose={() => setAlertMessage('')} />
      
      <div className="grid-2">
        <LocationSearch onSearch={handleSearchComplete} onAlert={showAlert} />
        <RouteSearch onSearch={handleSearchComplete} onAlert={showAlert} />
      </div>
      
      <History refreshTrigger={refreshTrigger} />
      <Settings />
    </div>
  );
};

export default Dashboard;