import axios from 'axios';

// Dynamically detect the backend URL based on where the frontend is being accessed from
const defaultHost = window.location.hostname || '127.0.0.1';
const defaultApiUrl = `${window.location.protocol}//${defaultHost}:5000`;
const API_URL = import.meta.env.VITE_API_URL || defaultApiUrl;

console.log('Frontend is running on:', window.location.hostname);
console.log('API URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true
});

// Add error logging
api.interceptors.response.use(
  response => response,
  error => {
    console.error('API Error:', error.config?.url, error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

export default api;
