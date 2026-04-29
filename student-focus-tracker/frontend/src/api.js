import axios from 'axios';

// Use explicit URL when provided, otherwise go through Vite proxy.
// This avoids HTTPS/HTTP mismatch errors (ERR_SSL_PROTOCOL_ERROR).
const API_URL = import.meta.env.VITE_API_URL || '/api';

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
