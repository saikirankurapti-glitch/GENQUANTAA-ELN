import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT session token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('eln_access_token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for automatic token refresh and safe error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (!error.response) {
      return Promise.reject(error);
    }

    const requestUrl = originalRequest?.url || '';
    const isAuthEndpoint = 
      requestUrl.includes('/auth/login') || 
      requestUrl.includes('/auth/register') || 
      requestUrl.includes('/auth/refresh');

    // Only attempt token refresh for 401 Unauthorized errors on non-auth endpoints
    if (error.response.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('eln_refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token available');
        }

        const refreshResponse = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken
        });

        const { access_token, refresh_token } = refreshResponse.data;

        localStorage.setItem('eln_access_token', access_token);
        if (refresh_token) {
          localStorage.setItem('eln_refresh_token', refresh_token);
        }

        // Update header and retry original request
        originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
        return apiClient(originalRequest);

      } catch (refreshError) {
        // Refresh token is invalid or expired: clear tokens
        localStorage.removeItem('eln_access_token');
        localStorage.removeItem('eln_refresh_token');

        window.dispatchEvent(new Event('auth:unauthorized'));
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
