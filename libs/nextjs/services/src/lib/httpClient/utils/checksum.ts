/**
 * Checksum utilities for HTTP requests/responses
 * Provides URL pattern matching for endpoints that should skip checksum validation
 */

// API prefixes to strip from URL to match backend's relative URLs
const API_PREFIXES: string[] = [
  '/api/v2/platform/',
  '/api/v2/platform',
  '/api/v1/',
  '/api/v1',
];

// Endpoints to skip checksum validation (regex patterns)
const CHECKSUM_SKIP_PATTERNS: RegExp[] = [
  /\/?core\/voice\/.*\/generate_room_token/, // Voice room token generation
  /\/?token\/livekit/, // LiveKit token generation
];

/**
 * Convert URL to relative format matching backend's get_relative_url()
 * Strips API prefix, query string, and leading slash to match backend's URL format
 *
 * Examples:
 *   /api/v1/auth/login/ -> auth/login/
 *   /api/v1/agents -> agents
 *   /api/v2/platform/spaces/ -> spaces/
 *   spaces/ -> spaces/ (already relative)
 *   spaces/?model_type=LLM -> spaces/ (query string stripped)
 *   /api/v1/agents?page=1&limit=10 -> agents (query string stripped)
 *
 * Note: Query parameters are serialized separately in the DATA part of the checksum,
 * so they must be stripped from the URL to avoid double-counting.
 *
 * @param url - The URL to normalize
 * @returns Relative URL without API prefix and query string
 */
export const getRelativeUrl = (url: string | undefined): string => {
  if (!url) return '';

  let relativeUrl = url;

  // Strip query string first (params are serialized separately)
  const queryIndex = relativeUrl.indexOf('?');
  if (queryIndex !== -1) {
    relativeUrl = relativeUrl.substring(0, queryIndex);
  }

  // Strip API prefix if present
  for (const prefix of API_PREFIXES) {
    if (relativeUrl.startsWith(prefix)) {
      relativeUrl = relativeUrl.substring(prefix.length);
      break;
    }
  }

  // Remove leading slash (frontend doesn't have it in config.url when using baseURL)
  if (relativeUrl.startsWith('/')) {
    relativeUrl = relativeUrl.substring(1);
  }

  return relativeUrl;
};

/**
 * Check if a URL should skip checksum validation
 * @param url - The URL to check
 * @returns True if checksum should be skipped
 */
export const shouldSkipChecksum = (url: string | undefined): boolean => {
  if (!url) return false;

  // Remove query parameters for pattern matching
  const urlWithoutQuery = url.split('?')[0];

  // Log in development for debugging
  if (process.env.NODE_ENV !== 'production') {
    const shouldSkip = CHECKSUM_SKIP_PATTERNS.some((pattern) =>
      pattern.test(urlWithoutQuery),
    );
    if (shouldSkip) {
      console.log('[Checksum] Skipping URL:', urlWithoutQuery);
    }
  }

  return CHECKSUM_SKIP_PATTERNS.some((pattern) =>
    pattern.test(urlWithoutQuery),
  );
};

/**
 * Check if checksum feature is enabled
 * @returns boolean
 */
export const isChecksumEnabled = (): boolean => {
  return (
    process.env.ENABLE_CHECKSUM === 'true' && !!process.env.CHECKSUM_SECRET
  );
};

/**
 * Get the checksum secret
 * @returns string
 */
export const getChecksumSecret = (): string => {
  return process.env.CHECKSUM_SECRET || '';
};
