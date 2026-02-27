/**
 * API Hooks
 * 
 * React Query hooks for API calls with caching and state management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from '../services/api';

/**
 * Health Check
 */
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.checkHealth,
    refetchInterval: 30000, // Check every 30 seconds
    retry: 3,
  });
};

/**
 * Upload Prescription
 */
export const useUploadPrescription = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ imageFile, userId, telegramChatId }) =>
      api.uploadPrescription(imageFile, userId, telegramChatId),
    onSuccess: (data) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

/**
 * Validate Prescription
 */
export const useValidatePrescription = () => {
  return useMutation({
    mutationFn: api.validatePrescription,
  });
};

/**
 * Get Prescription Status
 */
export const usePrescriptionStatus = (prescriptionId, options = {}) => {
  return useQuery({
    queryKey: ['prescription', prescriptionId],
    queryFn: () => api.getPrescriptionStatus(prescriptionId),
    enabled: !!prescriptionId,
    ...options,
  });
};

/**
 * Get Order
 */
export const useOrder = (orderId, options = {}) => {
  return useQuery({
    queryKey: ['order', orderId],
    queryFn: () => api.getOrder(orderId),
    enabled: !!orderId,
    ...options,
  });
};

/**
 * Get Order Summary
 */
export const useOrderSummary = (orderId, options = {}) => {
  return useQuery({
    queryKey: ['orderSummary', orderId],
    queryFn: () => api.getOrderSummary(orderId),
    enabled: !!orderId,
    ...options,
  });
};

/**
 * Get User Orders
 */
export const useUserOrders = (userId, options = {}) => {
  return useQuery({
    queryKey: ['orders', 'user', userId],
    queryFn: () => api.getUserOrders(userId),
    enabled: !!userId,
    ...options,
  });
};

/**
 * Check Inventory
 */
export const useInventory = (options = {}) => {
  return useQuery({
    queryKey: ['inventory'],
    queryFn: api.checkInventory,
    ...options,
  });
};

/**
 * Check Medicine Availability
 */
export const useCheckAvailability = () => {
  return useMutation({
    mutationFn: api.checkMedicineAvailability,
  });
};

/**
 * Search Medicines
 */
export const useSearchMedicines = (query, options = {}) => {
  return useQuery({
    queryKey: ['medicines', 'search', query],
    queryFn: () => api.searchMedicines(query),
    enabled: !!query && query.length > 2,
    ...options,
  });
};

/**
 * Get Low Stock Items
 */
export const useLowStockItems = (options = {}) => {
  return useQuery({
    queryKey: ['inventory', 'low-stock'],
    queryFn: api.getLowStockItems,
    ...options,
  });
};
