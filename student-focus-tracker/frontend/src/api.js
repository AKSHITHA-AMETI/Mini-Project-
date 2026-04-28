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
  timeout: 30000, // Increased to 30 seconds for slower connections
  headers: {
    'Content-Type': 'application/json',
  }
});

// Add Authorization token to requests
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = token;
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Enhanced error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.config?.url, error.response?.status, error.response?.data);
    if (error.code === 'ECONNABORTED' || error.code === 'ENOTFOUND') {
      console.error('Network error - check if backend is running on:', API_URL);
    }
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export default api;
