import axios from 'axios';

export const api = axios.create({
  baseURL: 'https://takatrack-mlbj.onrender.com',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Automatically attach the Bearer token on every outgoing request (for mobile browsers)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('takatrack_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Automatically save the token from the response header on login/register
api.interceptors.response.use((response) => {
  const token = response.headers['x-access-token'] || response.data?.access_token;
  if (token) {
    localStorage.setItem('takatrack_token', token);
  }
  if (response.config.url?.includes('/auth/logout')) {
    localStorage.removeItem('takatrack_token');
  }
  return response;
});