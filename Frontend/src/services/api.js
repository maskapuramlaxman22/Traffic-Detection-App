import axios from 'axios';
import io from 'socket.io-client';

// Get API URL - try env var first, fallback to localhost
const getAPIBaseURL = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  // For production/serve, always use localhost:5000
  return 'http://localhost:5000';
};

const API_BASE_URL = getAPIBaseURL();
console.log('API Base URL:', API_BASE_URL);

// Initialize HTTP client
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Add response interceptor to handle errors
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status >= 400) {
      console.error(`API Error [${error.response.status}]:`, error.response.data);
    } else if (error.message === 'Network Error' || !error.response) {
      console.error('Network Error - Backend may not be running on ' + API_BASE_URL);
    }
    return Promise.reject(error);
  }
);

// Initialize WebSocket connection for real-time updates
let socket = null;

const initializeSocket = () => {
  if (!socket) {
    socket = io(API_BASE_URL, {
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5
    });
    
    socket.on('connect', () => {
      console.log('Connected to real-time traffic updates');
    });
    
    socket.on('disconnect', () => {
      console.log('Disconnected from real-time updates');
    });
    
    socket.on('error', (error) => {
      console.error('Socket error:', error);
    });
  }
  return socket;
};

// API Health Check
export const healthCheck = async () => {
  try {
    const response = await api.get('/api/v1/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    return { status: 'unavailable' };
  }
};

// Location Search - Real Geocoding
export const searchLocations = async (query) => {
  try {
    if (!query || query.length < 2) {
      return [];
    }
    
    const response = await api.get('/api/v1/search_locations', {
      params: { q: query }
    });
    return Array.isArray(response.data) ? response.data : [];
  } catch (error) {
    console.error('Error searching locations:', error);
    return [];
  }
};

// Get Real-Time Traffic for a Location
export const getTrafficStatus = async (location) => {
  try {
    const response = await api.get('/api/v1/traffic/current', {
      params: { location }
    });
    return response.data || { traffic_status: 'Unknown', congestion_level: 0 };
  } catch (error) {
    console.error('Error fetching traffic status:', error);
    return { traffic_status: 'Unknown', congestion_level: 0 };
  }
};

export const getTrafficByCoordinates = async (lat, lng) => {
  try {
    const response = await api.get('/api/v1/traffic/current', {
      params: { lat, lng }
    });
    return response.data || { traffic_status: 'Unknown', congestion_level: 0 };
  } catch (error) {
    console.error('Error fetching traffic by coordinates:', error);
    return { traffic_status: 'Unknown', congestion_level: 0 };
  }
};

// Get Route Traffic
export const getRouteTraffic = async (origin, destination) => {
  try {
    const response = await api.post('/api/v1/route', {
      origin,
      destination
    });
    return response.data;
  } catch (error) {
    console.error('Error getting route traffic:', error);
    return null;
  }
};

// Get Incidents in an Area
export const getIncidents = async (lat, lng, radiusKm = 5) => {
  try {
    const response = await api.get('/api/v1/incidents', {
      params: {
        lat,
        lng,
        radius_km: radiusKm
      }
    });
    return response.data || { incidents: [], count: 0 };
  } catch (error) {
    console.error('Error fetching incidents:', error);
    return { incidents: [], count: 0 };
  }
};

// Get Traffic History
export const getTrafficHistory = async (location, hours = 24) => {
  try {
    const response = await api.get('/api/v1/traffic/history', {
      params: { limit: 20 }
    });
    return response.data || { history: [], total: 0 };
  } catch (error) {
    console.error('Error fetching traffic history:', error);
    return { history: [], total: 0 };
  }
};

// Get Settings
export const getSettings = async () => {
  try {
    const response = await api.get('/api/v1/settings');
    return response.data || {
      refresh_interval: 30,
      alerts_enabled: true,
      cache_enabled: false
    };
  } catch (error) {
    console.error('Error fetching settings:', error);
    return {
      refresh_interval: 30,
      alerts_enabled: true,
      cache_enabled: false
    };
  }
};

// Update Settings
export const updateSettings = async (settings) => {
  try {
    const response = await api.post('/api/v1/settings', settings);
    return response.data;
  } catch (error) {
    console.error('Error updating settings:', error);
    throw error;
  }
};

// Save a search (history) entry
export const saveSearch = async (payload) => {
  try {
    const response = await api.post('/api/v1/search_history', payload);
    return response.data || { success: true };
  } catch (error) {
    console.error('Error saving search:', error);
    return { success: false };
  }
};

// Predict Traffic (Deprecated - use getTrafficStatus instead)
// Kept for backward compatibility
export const predictTraffic = async (location) => {
  return getTrafficStatus(location);
};

// Real-Time WebSocket API

// Export the initialized socket function
export { initializeSocket };

/**
 * Subscribe to real-time traffic updates for a location
 * @param {string} location - Location name to subscribe to
 * @param {function} onUpdate - Callback function for updates
 */
export const subscribeToLocation = (location, onUpdate) => {
  const sock = initializeSocket();
  
  sock.emit('subscribe_location', { location });
  sock.on(`traffic_update:${location}`, (data) => {
    onUpdate(data);
  });
  
  return () => {
    sock.off(`traffic_update:${location}`);
  };
};

/**
 * Subscribe to incident alerts in an area
 * @param {number} lat - Latitude
 * @param {number} lng - Longitude
 * @param {function} onIncident - Callback function for new incidents
 */
export const subscribeToIncidents = (lat, lng, onIncident) => {
  const sock = initializeSocket();
  
  sock.emit('subscribe_incidents', { lat, lng });
  sock.on(`incidents:${lat}:${lng}`, (data) => {
    onIncident(data);
  });
  
  return () => {
    sock.off(`incidents:${lat}:${lng}`);
  };
};

/**
 * Disconnect from real-time updates
 */
export const disconnectSocket = () => {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
};

// Utility function to get traffic color based on congestion level
export const getTrafficColor = (congestionLevel) => {
  if (congestionLevel < 0.3) return '#4CAF50'; // Green
  if (congestionLevel < 0.6) return '#FFC107'; // Yellow
  if (congestionLevel < 0.8) return '#FF9800'; // Orange
  return '#F44336'; // Red
};

// Utility function to get traffic status text
export const getTrafficStatusText = (congestionLevel) => {
  if (congestionLevel < 0.3) return 'Low Traffic';
  if (congestionLevel < 0.6) return 'Moderate Traffic';
  if (congestionLevel < 0.8) return 'Heavy Traffic';
  return 'Severe Traffic';
};