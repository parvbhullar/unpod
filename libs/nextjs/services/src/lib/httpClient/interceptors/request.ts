/**
 * Request interceptor for adding checksum to outgoing HTTP requests
 */

import { InternalAxiosRequestConfig } from 'axios';
import { generateChecksum, getCurrentTimestamp } from '@unpod/helpers';
import { getChecksumSecret, getRelativeUrl, isChecksumEnabled, shouldSkipChecksum } from '../utils/checksum';
import { serializeRequestData } from '../utils/serialization';

/**
 * Check if a value is an empty object {}
 * @param value - Value to check
 * @returns True if value is an empty object
 */
const isEmptyObject = (value: unknown): boolean => {
  return (
    value !== null &&
    typeof value === 'object' &&
    !Array.isArray(value) &&
    Object.keys(value as object).length === 0
  );
};

/**
 * Check if a value is empty for query params purposes
 * This includes both empty objects {} and stringified empty objects "{}"
 * @param value - Value to check
 * @returns True if value should be filtered from query params
 */
const isEmptyQueryParam = (value: unknown): boolean => {
  // Check for stringified empty object "{}" (common in table sort params)
  if (value === '{}') {
    return true;
  }

  return isEmptyObject(value);
};

/**
 * Remove empty objects from params to prevent backend validation errors
 * (e.g., sort={} fails schema validation expecting field/order properties)
 * @param params - Query parameters object
 * @returns Cleaned params without empty objects
 */
const cleanParams = (
  params: Record<string, unknown> | undefined,
): Record<string, unknown> | undefined => {
  if (!params || typeof params !== 'object') {
    return params;
  }

  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(params)) {
    if (!isEmptyQueryParam(value)) {
      cleaned[key] = value;
    } else if (process.env.NODE_ENV !== 'production') {
      console.log(`[Request] Removing empty object param: ${key}`);
    }
  }
  return cleaned;
};

/**
 * Parse query string value and convert to appropriate type
 * @param value - Query string value
 * @returns Parsed value
 */
const parseQueryValue = (value: string): unknown => {
  if (value === 'true') return true;
  if (value === 'false') return false;
  if (value === 'null') return null;
  if (value !== '' && !isNaN(Number(value))) return Number(value);

  // Try to parse JSON arrays/objects
  if (value.startsWith('[') || value.startsWith('{')) {
    try {
      return JSON.parse(value);
    } catch {
      // Keep as string if parsing fails
    }
  }

  return value;
};

/**
 * Clean URL by removing empty object params from query string
 * @param url - URL that may contain query string
 * @returns Cleaned URL
 */
const cleanUrlParams = (url: string | undefined): string | undefined => {
  if (!url || !url.includes('?')) {
    return url;
  }

  const [basePath, queryString] = url.split('?');
  if (!queryString) {
    return url;
  }

  const urlParams = new URLSearchParams(queryString);
  const cleanedParams = new URLSearchParams();
  let hasRemovedParams = false;

  urlParams.forEach((value, key) => {
    const parsedValue = parseQueryValue(value);

    if (!isEmptyQueryParam(parsedValue)) {
      cleanedParams.append(key, value);
    } else {
      hasRemovedParams = true;
      if (process.env.NODE_ENV !== 'production') {
        console.log(`[Request] Removing empty object param from URL: ${key}`);
      }
    }
  });

  if (!hasRemovedParams) {
    return url;
  }

  const cleanedQueryString = cleanedParams.toString();
  return cleanedQueryString ? `${basePath}?${cleanedQueryString}` : basePath;
};

/**
 * Create a request interceptor that adds checksum headers
 * @param clientName - Name for logging (e.g., 'httpClient', 'httpLocalClient')
 * @returns Request interceptor function
 */
export const createRequestInterceptor =
  (clientName: string) =>
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    try {
      // Clean empty objects from params (prevents backend validation errors)
      if (config.params) {
        config.params = cleanParams(config.params as Record<string, unknown>);
      }

      // Clean empty objects from URL query string (e.g., ?sort={})
      if (config.url) {
        config.url = cleanUrlParams(config.url);
      }

      // Skip checksum for specific endpoints
      if (shouldSkipChecksum(config.url)) {
        if (process.env.NODE_ENV !== 'production') {
          console.log(`[${clientName}] Skipping checksum for:`, config.url);
        }
        return config;
      }

      // Only add checksum if feature is enabled
      if (isChecksumEnabled()) {
        const timestamp = getCurrentTimestamp();
        const { serializedData, dataType } = serializeRequestData(config);

        // Normalize URL to relative format (strip API prefix) to match backend
        const relativeUrl = getRelativeUrl(config.url);

        // Generate checksum including method and url
        const checksum = generateChecksum(
          config.method || 'get',
          relativeUrl,
          serializedData,
          timestamp,
          getChecksumSecret(),
        );

        // Add headers
        config.headers['UP-Checksum'] = checksum;
        config.headers['UP-Timestamp'] = timestamp;

        if (process.env.NODE_ENV !== 'production') {
          console.log(
            `[${clientName}] ==================== CHECKSUM CALCULATION ====================`,
          );
          console.log(`[${clientName}] Method:`, config.method?.toUpperCase());
          console.log(`[${clientName}] Original URL:`, config.url);
          console.log(`[${clientName}] Relative URL (used):`, relativeUrl);
          console.log(`[${clientName}] Data Type:`, dataType);
          console.log(
            `[${clientName}] Serialized Data:`,
            serializedData.length > 500
              ? serializedData.substring(0, 500) + '... (truncated)'
              : serializedData,
          );
          console.log(`[${clientName}] Timestamp:`, timestamp);
          console.log(
            `[${clientName}] Checksum Formula: ${config.method?.toUpperCase()} + "${relativeUrl}" + DATA + "${timestamp}" + SECRET`,
          );
          console.log(`[${clientName}] Generated Checksum:`, checksum);
          console.log(
            `[${clientName}] ==============================================================`,
          );
        }
      }
    } catch (error) {
      // Log error but don't block request (graceful degradation)
      console.error(
        `[${clientName}] Error generating request checksum:`,
        error,
      );
    }

    return config;
  };

/**
 * Request interceptor error handler
 * @param error
 * @returns Promise
 */
export const requestInterceptorError = (error: unknown): Promise<never> => {
  return Promise.reject(error);
};
