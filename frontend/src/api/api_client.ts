import axios, { type AxiosInstance, AxiosError } from 'axios';

const apiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 20000, // 20 seconds
  headers: {
    'x-api-key': import.meta.env.VITE_API_KEY,
  },
});

// Interceptor: Handle errors by passing status and data back to caller
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      return Promise.reject({
        status: error.response.status,
        data: error.response.data,
      });
    }
    return Promise.reject(error);
  }
);

export default apiClient;
