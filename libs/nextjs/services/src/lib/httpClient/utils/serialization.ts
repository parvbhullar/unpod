/**
 * Serialization utilities for HTTP requests/responses
 * Handles different data types (FormData, JSON, query params) consistently for checksum generation
 */

import {
  AxiosRequestConfig,
  AxiosResponse,
  AxiosResponseHeaders,
  RawAxiosResponseHeaders,
} from 'axios'; // Symbol to store raw response data

// Symbol to store raw response data
export const RAW_RESPONSE_DATA: unique symbol = Symbol('rawResponseData');

// Type for response data with raw data symbol
export type ResponseDataWithRaw = {
  [RAW_RESPONSE_DATA]?: string;
  [key: string]: unknown;};

/**
 * Recursively sort object keys alphabetically to match backend behavior
 * This ensures consistent serialization for checksum generation
 * @param obj - Object to sort
 * @returns Object with sorted keys (recursively)
 */
const sortObjectKeysRecursively = <T>(obj: T): T => {
  // Return non-objects as-is
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  // Handle arrays - sort elements recursively but preserve order
  if (Array.isArray(obj)) {
    return obj.map(sortObjectKeysRecursively) as T;
  }

  // Sort object keys alphabetically and recurse into values
  return Object.keys(obj as object)
    .sort()
    .reduce((acc, key) => {
      (acc as Record<string, unknown>)[key] = sortObjectKeysRecursively(
        (obj as Record<string, unknown>)[key],
      );
      return acc;
    }, {} as T);
};

/**
 * Parse a form field name with bracket notation into nested object structure
 * Examples:
 *   "field" -> sets obj.field
 *   "field[0]" -> sets obj.field[0]
 *   "field[key]" -> sets obj.field.key
 * @param obj - Target object
 * @param key - Field name (may contain brackets)
 * @param value - Value to set
 */
const setNestedValue = (
  obj: Record<string, unknown>,
  key: string,
  value: unknown,
): void => {
  // Match bracket notation: field[0] or field[key]
  const bracketMatch = key.match(/^([^[]+)\[([^\]]+)\]$/);

  if (bracketMatch) {
    const [, fieldName, indexOrKey] = bracketMatch;

    // Check if it's a numeric index
    const isNumeric = /^\d+$/.test(indexOrKey);

    if (isNumeric) {
      // Array notation: field[0]
      if (!obj[fieldName]) {
        obj[fieldName] = [];
      }
      (obj[fieldName] as unknown[])[parseInt(indexOrKey)] = value;
    } else {
      // Object notation: field[key]
      if (!obj[fieldName]) {
        obj[fieldName] = {};
      }
      (obj[fieldName] as Record<string, unknown>)[indexOrKey] = value;
    }
  } else {
    // Simple key
    obj[key] = value;
  }
};

/**
 * File metadata for checksum calculation
 */
type FileMetadata = {
  name: string;
  size: number;
  type: string;};

/**
 * Serialize FormData for checksum generation
 * Extracts text fields and file metadata (not binary data)
 * Attempts to parse JSON values and handle bracket notation to match backend's parsing behavior
 * @param formData
 * @returns JSON string of form data
 */
const serializeFormData = (formData: FormData): string => {
  const formDataObj: Record<string, unknown> = {};

  for (const [key, value] of formData.entries()) {
    if (typeof value === 'string') {
      // Try to parse JSON values (arrays, objects, booleans, numbers)
      // This matches backend behavior which parses these from form data
      let parsedValue: unknown = value;

      // Try to parse as JSON if it looks like JSON
      if (
        value === 'true' ||
        value === 'false' ||
        value === 'null' ||
        value.startsWith('{') ||
        value.startsWith('[') ||
        (!isNaN(Number(value)) && value !== '')
      ) {
        try {
          parsedValue = JSON.parse(value);
        } catch {
          // If parsing fails, keep as string
          // But convert numeric strings to numbers
          if (!isNaN(Number(value)) && value !== '') {
            parsedValue = Number(value);
          }
        }
      }

      // Skip undefined values (they shouldn't be sent at all)
      if (parsedValue !== 'undefined' && parsedValue !== undefined) {
        // Handle bracket notation (e.g., field[0], field[key])
        setNestedValue(formDataObj, key, parsedValue);
      }
    } else {
      // For files (File extends Blob), include metadata only (name, size, type)
      const fileValue = value as File;
      const fileMetadata: FileMetadata = {
        name: fileValue.name || 'unknown',
        size: fileValue.size || 0,
        type: fileValue.type || 'unknown',
      };
      setNestedValue(formDataObj, key, fileMetadata);
    }
  }

  // Sort keys alphabetically (recursively) to match backend behavior
  const sortedObj = sortObjectKeysRecursively(formDataObj);

  if (process.env.NODE_ENV !== 'production') {
    console.log(
      '[Serialization] FormData parsed (sorted recursively):',
      sortedObj,
    );
  }

  return JSON.stringify(sortedObj);
};

/**
 * Check if a value is an empty object {}
 * Empty objects in query params can cause backend validation errors
 * (e.g., sort={} fails schema validation expecting field/order properties)
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
 * Convert a string value to its appropriate type
 * Matches backend's query parameter parsing behavior
 * @param value - Value to convert
 * @returns Converted value
 */
const convertQueryValue = (value: unknown): unknown => {
  if (typeof value !== 'string') {
    return value;
  }

  // Handle boolean strings
  if (value === 'true') return true;
  if (value === 'false') return false;

  // Handle null
  if (value === 'null') return null;

  // Handle numeric strings
  if (value !== '' && !isNaN(Number(value))) {
    // Check if it's an integer or float
    const num = Number(value);
    return num;
  }

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
 * Extract query parameters from a URL string
 * @param url - URL that may contain query string
 * @returns Parsed query parameters
 */
const extractQueryParamsFromUrl = (url: string): Record<string, unknown> => {
  if (!url || !url.includes('?')) {
    return {};
  }

  const queryString = url.split('?')[1];
  if (!queryString) {
    return {};
  }

  const params: Record<string, unknown> = {};
  const urlParams = new URLSearchParams(queryString);

  urlParams.forEach((value, key) => {
    // Convert value to appropriate type
    params[key] = convertQueryValue(value);
  });

  return params;
};

/**
 * Result of serializing request data
 */
export type SerializedRequestData = {
  serializedData: string;
  dataType: 'body' | 'formdata' | 'params';};

/**
 * Serialize request data for checksum generation
 * Handles GET params, POST body, FormData, etc.
 * For GET requests, merges params from both config.params AND URL query string
 * @param config - Axios request config
 * @returns Serialized data and data type
 */
export const serializeRequestData = (
  config: AxiosRequestConfig,
): SerializedRequestData => {
  let serializedData = '';
  let dataType: 'body' | 'formdata' | 'params' = 'body';

  // Handle FormData (file uploads)
  if (config.data instanceof FormData) {
    serializedData = serializeFormData(config.data);
    dataType = 'formdata';
  }
  // For GET requests, checksum the query parameters
  else if (config.method?.toLowerCase() === 'get') {
    // Extract params from URL query string (e.g., axios.get('url/?key=value'))
    const urlParams = extractQueryParamsFromUrl(config.url || '');

    // Get params from config.params (e.g., axios.get('url/', { params: {...} }))
    const configParams = (config.params || {}) as Record<string, unknown>;

    // Merge both sources - config.params takes precedence over URL params
    const mergedParams = { ...urlParams, ...configParams };

    if (Object.keys(mergedParams).length > 0) {
      // Filter out empty objects and convert values
      const filteredParams = Object.keys(mergedParams).reduce(
        (acc: Record<string, unknown>, key) => {
          // Convert values to appropriate types
          const convertedValue = convertQueryValue(mergedParams[key]);

          // Skip empty objects {} - they cause backend validation errors
          // (e.g., sort={} fails schema validation)
          if (!isEmptyObject(convertedValue)) {
            acc[key] = convertedValue;
          } else if (process.env.NODE_ENV !== 'production') {
            console.log(
              `[Serialization] Skipping empty object for key: ${key}`,
            );
          }

          return acc;
        },
        {},
      );

      // Only serialize if we have remaining params after filtering
      if (Object.keys(filteredParams).length > 0) {
        // Sort keys recursively to match backend behavior
        const sortedParams = sortObjectKeysRecursively(filteredParams);
        serializedData = JSON.stringify(sortedParams);

        if (process.env.NODE_ENV !== 'production') {
          console.log('[Serialization] GET params sources:', {
            fromUrl: urlParams,
            fromConfig: configParams,
            merged: mergedParams,
            sorted: sortedParams,
          });
        }
      } else {
        serializedData = '';
      }
    } else {
      serializedData = '';
    }
    dataType = 'params';
  }
  // For POST/PUT/PATCH, checksum the request body
  else {
    if (!config.data) {
      serializedData = '';
    } else if (typeof config.data === 'string') {
      serializedData = config.data;
    } else {
      // Sort keys recursively to match backend behavior
      const sortedData = sortObjectKeysRecursively(config.data);
      serializedData = JSON.stringify(sortedData);
    }
  }

  return { serializedData, dataType };
};

/**
 * Extended response type with raw data storage
 */
export type AxiosResponseWithRaw<T = unknown> = AxiosResponse<T> & {
  [RAW_RESPONSE_DATA]?: string;};

/**
 * Serialize response data for checksum validation
 * Uses raw response text if available, otherwise re-serializes parsed data
 * @param response - Axios response object
 * @returns Serialized response data
 */
export const serializeResponseData = (
  response: AxiosResponseWithRaw,
): string => {
  // Try to use raw response text stored during transformation
  if (response[RAW_RESPONSE_DATA]) {
    return response[RAW_RESPONSE_DATA];
  }

  // Try to get raw data from parsed response data
  const responseData = response.data as ResponseDataWithRaw | null;
  if (responseData && responseData[RAW_RESPONSE_DATA]) {
    return responseData[RAW_RESPONSE_DATA];
  }

  // Fallback: try responseText from XHR adapter
  const request = response.request as XMLHttpRequest | undefined;
  if (request?.responseText) {
    return request.responseText;
  }

  // Last resort: re-serialize parsed data (might not match original)
  if (typeof response.data === 'string') {
    return response.data;
  }

  return JSON.stringify(response.data);
};

/**
 * Response transformer that captures raw response data before parsing
 * This ensures we have the exact response string for checksum validation
 * @param data - Raw response data
 * @param headers - Response headers
 * @returns Parsed response data
 */
export const responseTransformer = (
  data: string | ArrayBuffer,
  headers?: AxiosResponseHeaders | RawAxiosResponseHeaders,
): unknown => {
  // Skip transformation for non-string data (ArrayBuffer, Blob, etc.)
  // These are binary responses like audio/video files
  if (typeof data !== 'string') {
    return data;
  }

  // Skip empty responses
  if (!data) {
    return data;
  }

  // Try to parse as JSON
  try {
    const result = JSON.parse(data) as ResponseDataWithRaw;
    // Store raw data as Symbol property (won't conflict with response data)
    result[RAW_RESPONSE_DATA] = data;
    return result;
  } catch {
    // If parsing fails, return data as-is (might be plain text or other format)
    return data;
  }
};
