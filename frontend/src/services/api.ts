import axios from 'axios';
import type { ChatRequest, ChatResponse, Unit, ApiError } from '../types';

const API_BASE_URL = 'http://127.0.0.1:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url, config.data);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.data);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    
    let errorMessage = 'An error occurred';
    
    // Handle specific error types
    if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
      errorMessage = 'Unable to connect to the server. Please check if the backend is running.';
    } else if (error.response) {
      // Server responded with error status
      errorMessage = error.response.data?.detail || error.response.data?.message || `Server error: ${error.response.status}`;
    } else if (error.request) {
      // Request made but no response received
      errorMessage = 'No response from server. Please check your internet connection.';
    } else {
      // Something else happened
      errorMessage = error.message || 'An unexpected error occurred';
    }
    
    const apiError: ApiError = {
      message: errorMessage,
      status: error.response?.status,
    };
    return Promise.reject(apiError);
  }
);

export const chatApi = {
  // Send message to chat endpoint
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    try {
      const response = await api.post<ChatResponse>('/chat', request);
      return response.data;
    } catch (error) {
      console.error('Error sending message:', error);
      throw error;
    }
  },

  // Get units (for testing/debugging)
  getUnits: async (filters?: {
    bedrooms?: number;
    max_price?: number;
    location?: string;
  }): Promise<Unit[]> => {
    try {
      const response = await api.get<Unit[]>('/units', {
        params: filters,
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching units:', error);
      throw error;
    }
  },

  // Health check
  healthCheck: async (): Promise<{ status: string }> => {
    try {
      await api.get('/');
      return { status: 'ok' };
    } catch (error) {
      console.error('Health check failed:', error);
      throw error;
    }
  },
};

export default api;