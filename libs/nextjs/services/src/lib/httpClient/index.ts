/**
 * HTTP Client Configuration
 * Main entry point for Axios HTTP clients with checksum validation
 */

import axios, { AxiosError, AxiosInstance } from 'axios';
import {
  createRequestInterceptor,
  requestInterceptorError,
} from './interceptors/request';
import {
  createResponseInterceptor,
  responseInterceptorError,
} from './interceptors/response';
import {
  AxiosResponseWithRaw,
  responseTransformer,
} from './utils/serialization';

// ============================================================================
// HTTP CLIENT INSTANCES
// ============================================================================

/**
 * Local HTTP client (no baseURL)
 * Used for local API calls like token generation
 */
export const httpLocalClient: AxiosInstance = axios.create({
  headers: {
    'Content-Type': 'application/json',
    AppType: process.env.appType,
    'Product-Id': process.env.productId,
  },
  // Use custom response transformer to capture raw data
  transformResponse: [responseTransformer],
});

/**
 * Main HTTP client (with baseURL)
 * Used for all backend API calls
 */
export const httpClient: AxiosInstance = axios.create({
  baseURL: process.env.apiUrl,
  headers: {
    'Content-Type': 'application/json',
    AppType: process.env.appType,
    'Product-Id': process.env.productId,
  },
  // Use custom response transformer to capture raw data
  transformResponse: [responseTransformer],
});

// ============================================================================
// HEADER MANAGEMENT
// ============================================================================

/**
 * Set or remove organization header
 * @param handle - Organization domain handle
 */
export const setOrgHeader = (handle: string | null | undefined): void => {
  if (handle) {
    httpClient.defaults.headers.common['Org-Handle'] = handle;
  } else {
    console.log('Delete Org Header');
    delete httpClient.defaults.headers.common['Org-Handle'];
  }
};

/**
 * Set or remove authentication token
 * @param token - JWT token
 */
export const setAuthToken = (token: string | null | undefined): void => {
  if (token) {
    httpClient.defaults.headers.common['Authorization'] = 'JWT ' + token;
    httpLocalClient.defaults.headers.common['Authorization'] = 'JWT ' + token;
  } else {
    delete httpClient.defaults.headers.common['Authorization'];
    delete httpLocalClient.defaults.headers.common['Authorization'];
  }
};

// ============================================================================
// APPLY INTERCEPTORS
// ============================================================================

// httpLocalClient interceptors
httpLocalClient.interceptors.request.use(
  createRequestInterceptor('httpLocalClient'),
  requestInterceptorError,
);

httpLocalClient.interceptors.response.use(
  createResponseInterceptor('httpLocalClient'),
  responseInterceptorError,
);

// httpClient interceptors
httpClient.interceptors.request.use(
  createRequestInterceptor('httpClient'),
  requestInterceptorError,
);

httpClient.interceptors.response.use(
  createResponseInterceptor('httpClient'),
  (error: AxiosError): Promise<never> => {
    // Keep existing 401 handling for httpClient
    if (error.response && error.response.status === 401) {
      window.location.href = '/auth/signin';
    }
    return Promise.reject(error);
  },
);

export default httpClient;

// Re-export types for consumers
export type { AxiosResponseWithRaw };
