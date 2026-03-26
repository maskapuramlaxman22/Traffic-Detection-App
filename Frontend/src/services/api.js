import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const predictTraffic = async (location) => {
  try {
    const response = await api.post('/predict', { location });
    return response.data;
  } catch (error) {
    console.error('Error predicting traffic:', error);
    throw error;
  }
};

export const getRouteTraffic = async (source, destination) => {
  try {
    const response = await api.post('/route_traffic', { source, destination });
    return response.data;
  } catch (error) {
    console.error('Error getting route traffic:', error);
    throw error;
  }
};

export const getHistory = async () => {
  try {
    const response = await api.get('/history');
    return response.data;
  } catch (error) {
    console.error('Error fetching history:', error);
    return { total: 0, history: [] };
  }
};

export const searchLocations = async (query) => {
  try {
    const response = await api.get('/search_locations', {
      params: { q: query }
    });
    return response.data;
  } catch (error) {
    console.error('Error searching locations:', error);
    return [];
  }
};

export const getSettings = async () => {
  try {
    const response = await api.get('/settings');
    return response.data;
  } catch (error) {
    console.error('Error fetching settings:', error);
    return { refresh_interval: 30, alerts_enabled: true };
  }
};

export const updateSettings = async (settings) => {
  try {
    const response = await api.post('/settings', settings);
    return response.data;
  } catch (error) {
    console.error('Error updating settings:', error);
    throw error;
  }
};