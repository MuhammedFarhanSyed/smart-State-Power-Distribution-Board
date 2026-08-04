import axios from 'axios';

const axiosClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

axiosClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorMsg = error.response?.data?.message || error.response?.data?.error || error.message || 'API request failed';
    return Promise.reject(new Error(errorMsg));
  }
);

export default axiosClient;
