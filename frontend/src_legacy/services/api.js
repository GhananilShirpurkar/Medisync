/**
 * API Service
 * 
 * Centralized API client for backend communication
 */

import axios from 'axios';

// Base API URL - update based on environment
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 seconds for OCR processing
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`[API] Response:`, response.status);
    return response;
  },
  (error) => {
    console.error('[API] Response error:', error.response?.data || error.message);

    // Format error for consistent handling
    const formattedError = {
      message: error.response?.data?.detail || error.message || 'An error occurred',
      status: error.response?.status,
      data: error.response?.data,
    };

    return Promise.reject(formattedError);
  }
);

/**
 * API Methods
 */

// Health check
export const checkHealth = async () => {
  const response = await apiClient.get('/health');
  return response.data;
};

/**
 * Prescription APIs
 */
export const uploadPrescription = async (file, sessionId) => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await apiClient.post(`/api/prescription/upload?session_id=${sessionId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

export const validatePrescription = async (prescriptionId) => {
  const response = await apiClient.get(`/api/v1/prescriptions/${prescriptionId}/validate`);
  return response.data;
};

/**
 * Order APIs
 */
export const getOrderById = async (orderId) => {
  const response = await apiClient.get(`/api/v1/orders/${orderId}`);
  return response.data;
};

export const getUserOrders = async (userId) => {
  const response = await apiClient.get(`/api/v1/orders/user/${userId}`);
  return response.data;
};

export const getOrderSummary = async (orderId) => {
  const response = await apiClient.get(`/api/v1/orders/${orderId}/summary`);
  return response.data;
};

/**
 * Inventory APIs
 */
export const searchMedicines = async (query, limit = 50) => {
  const response = await apiClient.get('/api/v1/inventory/search', {
    params: { q: query, limit },
  });
  return response.data;
};

export const getMedicineDetails = async (medicineName) => {
  const response = await apiClient.get(`/api/v1/inventory/medicine/${encodeURIComponent(medicineName)}`);
  return response.data;
};

export const getLowStockItems = async (threshold = 10) => {
  const response = await apiClient.get('/api/v1/inventory/low-stock', {
    params: { threshold },
  });
  return response.data;
};

export const checkAvailability = async (items) => {
  const response = await apiClient.post('/api/v1/inventory/check-availability', { items });
  return response.data;
};

/**
 * Conversation APIs
 */
export const sendMessage = async (sessionId, message, userId) => {
  const response = await apiClient.post('/api/conversation', {
    session_id: sessionId,
    user_input: message,
    user_id: userId,
  });
  return response.data;
};

export const createSession = async (userId) => {
  const response = await apiClient.post('/api/conversation/create', {
    user_id: userId,
  });
  return response.data;
};

export default apiClient;
