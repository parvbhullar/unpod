import CryptoJS from 'crypto-js';

/**
 * Generate HMAC-SHA256 checksum for data integrity validation
 * @param {string} method - HTTP method (GET, POST, PUT, PATCH, DELETE)
 * @param {string} url - Request URL/endpoint
 * @param {unknown} data - The data to hash (will be JSON stringified)
 * @param {string} timestamp - ISO timestamp string
 * @param {string} secret - Shared secret key
 * @returns {string} Hex string of the HMAC-SHA256 hash
 */
export const generateChecksum = (
  method: string,
  url: string,
  data: unknown,
  timestamp: string,
  secret: string,
): string => {
  try {
    // Normalize method to uppercase
    const normalizedMethod = (method || '').toUpperCase();

    // Handle null/undefined data
    let processedData = data;
    if (processedData === null || processedData === undefined) {
      processedData = '';
    }

    // Serialize data for consistent hashing
    const serializedData =
      typeof processedData === 'string'
        ? processedData
        : JSON.stringify(processedData);

    // Concatenate method + url + data + timestamp + secret
    const message =
      normalizedMethod + url + serializedData + timestamp + secret;

    // Generate HMAC-SHA256 hash
    const hash = CryptoJS.HmacSHA256(message, secret);

    // Return as hex string
    return hash.toString(CryptoJS.enc.Hex);
  } catch (error) {
    console.error('[CryptoHelper] Error generating checksum:', error);
    throw error;
  }
};

/**
 * Validate HMAC-SHA256 checksum
 * @param {string} method - HTTP method (GET, POST, PUT, PATCH, DELETE)
 * @param {string} url - Request URL/endpoint
 * @param {unknown} data - The data to validate
 * @param {string} timestamp - ISO timestamp string
 * @param {string} receivedChecksum - The checksum to validate against
 * @param {string} secret - Shared secret key
 * @returns {boolean} True if checksum is valid
 */
export const validateChecksum = (
  method: string,
  url: string,
  data: unknown,
  timestamp: string,
  receivedChecksum: string,
  secret: string,
): boolean => {
  try {
    // Generate expected checksum
    const expectedChecksum = generateChecksum(
      method,
      url,
      data,
      timestamp,
      secret,
    );

    // Compare checksums (constant-time comparison would be better for production)
    return expectedChecksum === receivedChecksum;
  } catch (error) {
    console.error('[CryptoHelper] Error validating checksum:', error);
    return false;
  }
};

/**
 * Get current timestamp in ISO format
 * @returns {string} ISO timestamp string
 */
export const getCurrentTimestamp = (): string => {
  return new Date().toISOString();
};

/**
 * Validate if timestamp is within acceptable age (prevents replay attacks)
 * @param {string} timestamp - ISO timestamp string to validate
 * @param {number} maxAgeMs - Maximum age in milliseconds (default: 5 minutes)
 * @returns {boolean} True if timestamp is valid and fresh
 */
export const isTimestampValid = (
  timestamp: string,
  maxAgeMs = 5 * 60 * 1000,
): boolean => {
  try {
    const timestampDate = new Date(timestamp);
    const now = new Date();

    // Check if timestamp is valid date
    if (isNaN(timestampDate.getTime())) {
      return false;
    }

    // Check if timestamp is in the future (allow 1 minute clock skew)
    if (timestampDate.getTime() > now.getTime() + 60000) {
      return false;
    }

    // Check if timestamp is too old
    const age = now.getTime() - timestampDate.getTime();
    return age <= maxAgeMs;
  } catch (error) {
    console.error('[CryptoHelper] Error validating timestamp:', error);
    return false;
  }
};
