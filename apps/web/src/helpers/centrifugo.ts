/**
 * Centrifugo Real-time Client
 * Provides real-time notification functionality via Centrifugo server
 * with automatic fallback to SSE when Centrifugo is not available.
 */

import { httpClient } from '@unpod/services';

type CentrifugeConfig = {
  enabled: boolean;
  url: string;
  user_channel: string;
};

type CentrifugeTokenResponse = {
  token: string;
  expires_in?: number;
};

type CentrifugeClient = {
  on: (event: string, cb: (ctx: any) => void) => void;
  newSubscription: (
    channel: string,
    opts?: { getToken?: () => Promise<string> },
  ) => CentrifugeSubscription;
  connect: () => void;
  disconnect: () => void;
};

type CentrifugeSubscription = {
  on: (event: string, cb: (ctx: any) => void) => void;
  subscribe: () => void;
  unsubscribe: () => void;
};

// Centrifugo client instance
let centrifugeInstance: CentrifugeClient | null = null;
let subscriptionInstance: CentrifugeSubscription | null = null;
let connectionState = 'disconnected';
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_DELAY = 3000;

/**
 * Get Centrifugo configuration from backend
 * @returns {Promise<{enabled: boolean, url: string, user_channel: string}>}
 */
export const getCentrifugoConfig = async (): Promise<CentrifugeConfig> => {
  try {
    const response = await httpClient.get('notifications/centrifugo/config/');
    return response.data.data as CentrifugeConfig;
  } catch (error) {
    console.error('[Centrifugo] Failed to get config:', error);
    return { enabled: false, url: '', user_channel: '' };
  }
};

/**
 * Get connection token from backend
 * @returns {Promise<{token: string, expires_in: number}>}
 */
export const getCentrifugoToken =
  async (): Promise<CentrifugeTokenResponse> => {
    try {
      const response = await httpClient.get('notifications/centrifugo/token/');
      console.log('[Centrifugo] Token response:', response.data);
      return response.data.data as CentrifugeTokenResponse;
    } catch (error) {
      console.error('[Centrifugo] Failed to get token:', error);
      throw error;
    }
  };

/**
 * Get subscription token for a channel
 * @param {string} channel - The channel to subscribe to
 * @returns {Promise<{token: string, channel: string, expires_in: number}>}
 */
export const getSubscriptionToken = async (
  channel: string,
): Promise<CentrifugeTokenResponse & { channel?: string }> => {
  try {
    const response = await httpClient.post(
      'notifications/centrifugo/subscription-token/',
      { channel },
    );
    console.log('[Centrifugo] Subscription token response:', response.data);
    return response.data.data as CentrifugeTokenResponse & { channel?: string };
  } catch (error) {
    console.error('[Centrifugo] Failed to get subscription token:', error);
    throw error;
  }
};

/**
 * Initialize Centrifugo client and connect
 * @param {Object} options - Connection options
 * @param {Function} options.onNotification - Callback for new notifications
 * @param {Function} options.onConnect - Callback when connected
 * @param {Function} options.onDisconnect - Callback when disconnected
 * @param {Function} options.onError - Callback for errors
 * @returns {Promise<{connected: boolean, useCentrifugo: boolean}>}
 */
type InitOptions = {
  onNotification?: (data: unknown) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: unknown) => void;
};

export const initCentrifugo = async ({
  onNotification,
  onConnect,
  onDisconnect,
  onError,
}: InitOptions): Promise<{ connected: boolean; useCentrifugo: boolean }> => {
  try {
    // Check if Centrifugo is enabled
    const config = await getCentrifugoConfig();

    if (!config.enabled || !config.url) {
      console.log('[Centrifugo] Not enabled, falling back to SSE', config);
      return { connected: false, useCentrifugo: false };
    }

    // Dynamically import centrifuge-js
    const { Centrifuge } = await import('centrifuge');

    // Get connection token
    const { token } = await getCentrifugoToken();

    // Create Centrifuge client
    centrifugeInstance = new Centrifuge(config.url, {
      token,
      // Token refresh function for long-lived connections
      getToken: async () => {
        const { token: newToken } = await getCentrifugoToken();
        return newToken;
      },
    }) as unknown as CentrifugeClient;

    // Connection state handlers
    centrifugeInstance.on('connecting', (ctx) => {
      console.log('[Centrifugo] Connecting...', ctx);
      connectionState = 'connecting';
    });

    centrifugeInstance.on('connected', (ctx) => {
      console.log('[Centrifugo] Connected:', ctx);
      connectionState = 'connected';
      reconnectAttempts = 0;
      onConnect?.();
    });

    centrifugeInstance.on('disconnected', (ctx) => {
      console.log('[Centrifugo] Disconnected:', ctx);
      connectionState = 'disconnected';
      onDisconnect?.();

      // Auto-reconnect logic
      if (ctx.code !== 3000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++;
        console.log(
          `[Centrifugo] Reconnecting (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})...`,
        );
        setTimeout(() => {
          centrifugeInstance?.connect();
        }, RECONNECT_DELAY);
      }
    });

    centrifugeInstance.on('error', (ctx) => {
      console.error('[Centrifugo] Error:', ctx);
      onError?.(ctx.error);
    });

    // Subscribe to user channel
    subscriptionInstance = centrifugeInstance.newSubscription(
      config.user_channel,
      {
        // Get subscription token for private channels if needed
        getToken: async () => {
          try {
            const { token: subToken } = await getSubscriptionToken(
              config.user_channel,
            );
            return subToken;
          } catch {
            // Channel might be public, no token needed
            return '';
          }
        },
      },
    );

    // Handle incoming publications
    subscriptionInstance.on('publication', (ctx) => {
      console.log('[Centrifugo] Publication received:', ctx.data);

      const { event, data } = ctx.data;

      if (event === 'notification' && data) {
        onNotification?.(data);
      }
    });

    subscriptionInstance.on('subscribing', (ctx) => {
      console.log('[Centrifugo] Subscribing to channel...', ctx);
    });

    subscriptionInstance.on('subscribed', (ctx) => {
      console.log('[Centrifugo] Subscribed to channel:', ctx);
    });

    subscriptionInstance.on('unsubscribed', (ctx) => {
      console.log('[Centrifugo] Unsubscribed from channel:', ctx);
    });

    subscriptionInstance.on('error', (ctx) => {
      console.error('[Centrifugo] Subscription error:', ctx);
      onError?.(ctx.error);
    });

    // Start subscription and connection
    subscriptionInstance.subscribe();
    centrifugeInstance.connect();

    return { connected: true, useCentrifugo: true };
  } catch (error) {
    console.error('[Centrifugo] Initialization failed:', error);
    onError?.(error);
    return { connected: false, useCentrifugo: false };
  }
};

/**
 * Disconnect from Centrifugo
 */
export const disconnectCentrifugo = () => {
  try {
    if (subscriptionInstance) {
      subscriptionInstance.unsubscribe();
      subscriptionInstance = null;
    }
    if (centrifugeInstance) {
      centrifugeInstance.disconnect();
      centrifugeInstance = null;
    }
    connectionState = 'disconnected';
    reconnectAttempts = 0;
    console.log('[Centrifugo] Disconnected');
  } catch (error) {
    console.error('[Centrifugo] Disconnect error:', error);
  }
};

/**
 * Get current connection state
 * @returns {'disconnected' | 'connecting' | 'connected'}
 */
export const getConnectionState = () => connectionState;

/**
 * Check if connected to Centrifugo
 * @returns {boolean}
 */
export const isConnected = () => connectionState === 'connected';

export default {
  getCentrifugoConfig,
  getCentrifugoToken,
  getSubscriptionToken,
  initCentrifugo,
  disconnectCentrifugo,
  getConnectionState,
  isConnected,
};
