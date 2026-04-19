import axios from 'axios';

// More robust API URL detection for multi-device access
const getApiUrl = () => {
  // If VITE_API_URL is set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // For multi-device access, we need to determine the server IP
  // When accessed from another device, window.location.hostname will be the server's IP
  const currentHost = window.location.hostname;

  // If it's localhost or 127.0.0.1, assume development
  if (currentHost === 'localhost' || currentHost === '127.0.0.1') {
    return `${window.location.protocol}//${currentHost}:5000`;
  }

  // For other devices accessing via IP, use the same host but backend port
  return `${window.location.protocol}//${currentHost}:5000`;
};

const API_URL = getApiUrl();

console.log('Frontend accessed from:', window.location.hostname);
console.log('API URL detected as:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  }
});

// Enhanced error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.config?.url, error.response?.status, error.response?.data);
    if (error.code === 'NETWORK_ERROR') {
      console.error('Network error - check if backend is running on:', API_URL);
    }
    return Promise.reject(error);
  }
);

export default api;
