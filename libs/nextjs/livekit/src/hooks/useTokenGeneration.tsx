import { useCallback, useEffect, useRef, useState } from 'react';
import { getDataApi, postDataApi, useInfoViewActionsContext } from '@unpod/providers';

/**
 * Unified hook for LiveKit token generation
 * Provides consistent Promise-based API for all token generation scenarios
 *
 * @param {Object} options - Configuration options
 * @param {string} options.endpoint - API endpoint for token generation
 * @param {string} [options.method='GET'] - HTTP method ('GET' or 'POST')
 * @param {boolean} [options.cacheToken=true] - Whether to cache and reuse tokens
 * @param {Function} [options.onSuccess] - Callback on successful token generation
 * @param {Function} [options.onError] - Callback on error
 * @returns {Object} Token generation state and functions
 */
type TokenGenerationOptions = {
  endpoint?: string;
  method?: 'GET' | 'POST';
  cacheToken?: boolean;
  onSuccess?: (token: string, response: any) => void;
  onError?: (error: any) => void;};

type TokenPayload = {
  token?: string;
  accessToken?: string;
  [key: string]: unknown;
};

export const useTokenGeneration = (options: TokenGenerationOptions = {}) => {
  const {
    endpoint,
    method = 'GET',
    cacheToken = true,
    onSuccess,
    onError,
  } = options;

  const [token, setToken] = useState<string | null>(null);
  const [responseData, setResponseData] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<any>(null);
  const infoViewActionsContext = useInfoViewActionsContext();
  const abortControllerRef = useRef<AbortController | null>(null);

  // Use refs for callbacks to avoid recreating generateToken
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onSuccessRef.current = onSuccess;
  }, [onSuccess]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  /**
   * Generate token with consistent Promise-based API
   * @param {Object} payload - Request payload
   * @returns {Promise<string>} Resolves with token
   */
  const generateToken = useCallback(
    async (payload: Record<string, unknown> = {}) => {
      // Return cached token if available and caching is enabled
      if (cacheToken && token) {
        console.log('🔄 Reusing cached token');
        return Promise.resolve(token);
      }

      // Cancel any pending request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setIsGenerating(true);
      setError(null);

      try {
        if (!endpoint) {
          throw new Error('Token generation endpoint is required');
        }

        console.log(`🔑 Generating token via ${method} ${endpoint}...`);
        const startTime = performance.now();

        const response =
          method === 'POST'
            ? await postDataApi(endpoint, infoViewActionsContext, payload)
            : await getDataApi(endpoint, infoViewActionsContext, payload);

        const typedResponse = response as {
          data?: TokenPayload;
          accessToken?: string;
          [key: string]: unknown;
        };

        // Extract token from various response formats
        const generatedToken =
          typedResponse.data?.token ||
          typedResponse.data?.accessToken ||
          typedResponse.accessToken;

        if (!generatedToken) {
          throw new Error('Token not found in response');
        }

        const duration = (performance.now() - startTime).toFixed(2);
        console.log(`✅ Token generated successfully in ${duration}ms`);

        const fullResponseData = typedResponse.data || typedResponse;
        setToken(generatedToken);
        setResponseData(fullResponseData);
        setIsGenerating(false);

        if (onSuccessRef.current) {
          onSuccessRef.current(generatedToken, fullResponseData);
        }

        return generatedToken;
      } catch (err: any) {
        if (err?.name === 'AbortError') {
          console.log('⏹️ Token generation cancelled');
          return Promise.reject(new Error('Token generation cancelled'));
        }

        console.error('❌ Token generation failed:', err);
        setError(err);
        setIsGenerating(false);

        if (onErrorRef.current) {
          onErrorRef.current(err);
        } else {
          infoViewActionsContext.showError(
            err?.message || 'Failed to generate token',
          );
        }

        return Promise.reject(err);
      }
    },
    [endpoint, method, token, cacheToken, infoViewActionsContext],
  );

  /**
   * Clear cached token
   */
  const clearToken = useCallback(() => {
    setToken(null);
    setError(null);
  }, []);

  /**
   * Cancel ongoing token generation
   */
  const cancelGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    token,
    responseData,
    isGenerating,
    error,
    generateToken,
    clearToken,
    cancelGeneration,
  };
};
