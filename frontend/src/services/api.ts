import axios from 'axios';

export const api = axios.create({
  baseURL: 'https://takatrack-mlbj.onrender.com',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});
