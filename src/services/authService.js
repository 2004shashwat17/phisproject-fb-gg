import api from './api';

export const authService = {
  login: (credentials) => api.post('/auth/login', credentials).then(res => res.data),
  register: (data) => api.post('/auth/register', data).then(res => res.data),
  googleLogin: (token) => api.post('/auth/google', { token }).then(res => res.data),
  facebookLogin: (token) => api.post('/auth/facebook', { token }).then(res => res.data),
};
