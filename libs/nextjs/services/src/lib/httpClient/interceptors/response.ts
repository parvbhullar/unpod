/**
 * Response interceptor for validating checksum on incoming HTTP responses
 */

import {AxiosResponse} from 'axios';
import {generateChecksum, isTimestampValid, validateChecksum} from '@unpod/helpers';
import {getChecksumSecret, getRelativeUrl, isChecksumEnabled, shouldSkipChecksum} from '../utils/checksum';
import {AxiosResponseWithRaw, serializeResponseData} from '../utils/serialization';

/**
 * Log detailed debug information when checksum validation fails
 * @param clientName - Client name for logging
 * @param response - Axios response object
 * @param serializedData - Serialized response data
 * @param receivedTimestamp - Timestamp from response headers
 * @param receivedChecksum - Checksum from response headers
 */
const logChecksumDebugInfo = (
  clientName: string,
  response: AxiosResponse,
  serializedData: string,
  receivedTimestamp: string,
  receivedChecksum: string,
): void => {
  if (process.env.NODE_ENV === 'production') return;

  const method = response.config.method?.toUpperCase();
  const url = response.config.url;
  const relativeUrl = getRelativeUrl(url);

  const expectedChecksum = generateChecksum(
    response.config.method || 'get',
    relativeUrl,
    serializedData,
    receivedTimestamp,
    getChecksumSecret(),
  );

  console.error(
    `[${clientName}] ==================== RESPONSE CHECKSUM VALIDATION FAILED ====================`,
  );
  console.error(`[${clientName}] Method:`, method);
  console.error(`[${clientName}] Original URL:`, url);
  console.error(`[${clientName}] Relative URL (used):`, relativeUrl);
  console.error(
    `[${clientName}] Serialized Data:`,
    serializedData.length > 500
      ? serializedData.substring(0, 500) + '... (truncated)'
      : serializedData,
  );
  console.error(`[${clientName}] Timestamp:`, receivedTimestamp);
  console.error(
    `[${clientName}] Checksum Formula: ${method} + "${relativeUrl}" + DATA + "${receivedTimestamp}" + SECRET`,
  );
  console.error(`[${clientName}] Received Checksum:`, receivedChecksum);
  console.error(`[${clientName}] Expected Checksum:`, expectedChecksum);
  console.error(
    `[${clientName}] Match:`,
    receivedChecksum === expectedChecksum ? '✅ MATCH' : '❌ NO MATCH',
  );
  console.error(
    `[${clientName}] ==============================================================================`,
  );
};

/**
 * Create a response interceptor that validates checksums
 * @param clientName - Name for logging (e.g., 'httpClient', 'httpLocalClient')
 * @returns Response interceptor function
 */
export const createResponseInterceptor =
  (clientName: string) =>
    (response: AxiosResponseWithRaw): AxiosResponseWithRaw | Promise<never> => {
      try {
        // Skip checksum validation for specific endpoints
        if (shouldSkipChecksum(response.config.url)) {
          if (process.env.NODE_ENV !== 'production') {
            console.log(
              `[${clientName}] Skipping checksum validation for response:`,
              response.config.url,
            );
          }
          return response;
        }

        // Only validate checksum if feature is enabled
        if (isChecksumEnabled()) {
          const receivedChecksum = response.headers['up-checksum'] as
            | string
            | undefined;
          const receivedTimestamp = response.headers['up-timestamp'] as
            | string
            | undefined;

          // If backend sends checksum, validate it
          if (receivedChecksum && receivedTimestamp) {
            // Validate timestamp freshness (prevent replay attacks)
            if (!isTimestampValid(receivedTimestamp, 5 * 60 * 1000)) {
              console.error(
                `[${clientName}] Response timestamp is invalid or expired`,
              );
              return Promise.reject(
                new Error(
                  'Response timestamp validation failed - possible replay attack',
                ),
              );
            }

            // Serialize response data for validation
            const serializedData = serializeResponseData(response);

            // Normalize URL to relative format (strip API prefix) to match backend
            const relativeUrl = getRelativeUrl(response.config.url);

            // Validate checksum
            const isValid = validateChecksum(
              response.config.method || 'get',
              relativeUrl,
              serializedData,
              receivedTimestamp,
              receivedChecksum,
              getChecksumSecret(),
            );

            if (!isValid) {
              console.error(
                `[${clientName}] Response checksum validation failed`,
              );

              // Log debug information (only in development)
              logChecksumDebugInfo(
                clientName,
                response,
                serializedData,
                receivedTimestamp,
                receivedChecksum,
              );

              // In production, reject the response
              if (process.env.NODE_ENV === 'production') {
                return Promise.reject(
                  new Error(
                    'Checksum validation failed - data integrity compromised',
                  ),
                );
              }
              // In development, warn but allow the response through
            }

            if (process.env.NODE_ENV !== 'production') {
              console.log(
                `[${clientName}] Response checksum validated successfully:`,
                {
                  url: response.config.url,
                  relativeUrl,
                  checksum: receivedChecksum.substring(0, 16) + '...',
                  timestamp: receivedTimestamp,
                },
              );
            }
          } else if (process.env.NODE_ENV !== 'production') {
            // Backend doesn't support checksum yet - warn in dev mode
            console.warn(
              `[${clientName}] Response missing checksum headers - backend not ready yet`,
            );
          }
        }
      } catch (error) {
        console.error(
          `[${clientName}] Error validating response checksum:`,
          error,
        );
        // In production, reject the response if validation fails
        if (process.env.NODE_ENV === 'production') {
          return Promise.reject(error);
        }
        // In development, log error but allow response (for testing)
      }

      return response;
    };

/**
 * Response interceptor error handler
 * @param error
 * @returns Promise
 */
export const responseInterceptorError = (error: unknown): Promise<never> => {
  return Promise.reject(error);
};
