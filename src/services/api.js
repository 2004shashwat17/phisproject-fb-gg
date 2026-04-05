import axios from 'axios';

// The Google/Facebook automation endpoints can take a while to complete
// since they drive a browser; the default 10‑second axios timeout is too low
// and was causing `timeout of 10000ms exceeded` errors in the UI.  Use a
// much larger value (60s) or 0 for no timeout.
// The automation endpoints may take arbitrarily long; we don't set
// a client timeout so the browser can wait for the server to finish.
// (axios uses 0 = no timeout when the option is omitted.)
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if exists
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add session ID if exists
    const sessionId = sessionStorage.getItem('sessionId');
    if (sessionId) {
      config.headers['X-Session-ID'] = sessionId;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Handle specific status codes
      switch (error.response.status) {
        case 401:
          // Unauthorized - redirect to login
          window.location.href = '/login';
          break;
        case 429:
          // Too many requests
          console.log('Rate limited. Please wait.');
          break;
        default:
          console.log('API error:', error.response.data);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
