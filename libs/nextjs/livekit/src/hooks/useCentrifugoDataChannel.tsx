import { useCallback, useEffect, useRef, useState } from 'react';

/**
 * Message source types for tracking
 */
const MESSAGE_SOURCES = {
  CENTRIFUGO: 'centrifugo',
  LOCAL: 'local',
};

type AnyMessage = Record<string, any>;

type CentrifugoConfig = {
  url?: string;
  token?: string;
  channel_name?: string;
  agent_name?: string;
  space_token?: string;
  metadata?: Record<string, unknown>;};

type LocationRequestResolver = {
  resolve: (value: { accepted: boolean }) => void;
  reject: (error: Error) => void;
  timeout?: ReturnType<typeof setTimeout>;};

/**
 * Custom hook to manage conversation messaging using Centrifugo
 *
 * Uses Centrifugo's WebSocket connection for real-time messaging.
 * Provides similar interface to useConversationDataChannel for easy switching.
 *
 * @param {Object} options - Configuration options
 * @param {string} options.conversationId - The conversation ID (optional, for metadata)
 * @param {Object} options.params - Additional parameters to include in messages
 * @param {boolean} options.enabled - Enable/disable messaging (default: true)
 * @param {Object} options.centrifugoConfig - Centrifugo connection configuration
 * @param {string} options.centrifugoConfig.url - Centrifugo WebSocket URL (required)
 * @param {string} options.centrifugoConfig.token - JWT token for Centrifugo authentication
 * @param {string} options.centrifugoConfig.channel_name - Channel to subscribe to
 * @param {string} options.centrifugoConfig.agent_name - Agent name for the session
 * @param {string} options.centrifugoConfig.space_token - Space token identifier
 * @param {Object} options.centrifugoConfig.metadata - Additional metadata for the session
 * @returns {Object} - { sendJsonMessage, lastMessage, isConnected, voiceAssistant, testReceive, onLocationResponse }
 */
export const useCentrifugoDataChannel = ({
  conversationId: _conversationId, // Reserved for future use (metadata)
  params,
  enabled = true,
  centrifugoConfig = {},
}: {
  conversationId?: string;
  params?: Record<string, unknown>;
  enabled?: boolean;
  centrifugoConfig?: CentrifugoConfig;
} = {}) => {
  const [lastMessage, setLastMessage] = useState<AnyMessage | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState<Record<string, any>>({});
  const didUnmount = useRef(false);
  const centrifugeRef = useRef<any>(null);
  const subscriptionRef = useRef<any>(null);
  const reconnectAttemptsRef = useRef(0);
  // Store streaming messages by ID for concatenation
  const streamingMessagesRef = useRef<Map<string, AnyMessage>>(new Map());
  const {
    url: centrifugoUrl,
    token,
    channel_name,
    agent_name,
    space_token,
    metadata,
  } = centrifugoConfig || {};

  // Store pending location requests with their resolvers (for compatibility)
  const locationRequestResolvers = useRef<Map<string, LocationRequestResolver>>(
    new Map(),
  );

  // Get Centrifugo WebSocket URL from config, environment, or use default
  const getCentrifugoUrl = useCallback(() => {
    // First, try to use URL from config
    if (centrifugoUrl) {
      return centrifugoUrl;
    }
    // Then try environment variables
    const envUrl =
      process.env.centrifugoUrl || process.env.NEXT_PUBLIC_CENTRIFUGO_URL;
    if (envUrl) {
      return envUrl;
    }
    // Default to QA server
    return 'wss://qa1-block-service.unpod.tv/connection/websocket';
  }, [centrifugoUrl]);

  // Build user info for agent messages
  const getAgentUserInfo = useCallback(
    (data: AnyMessage) => {
      // If data already has user info, use it
      if (data.user) {
        return {
          role: data.user.role || 'assistant',
          user_id: data.user.user_id || 0,
          first_name: data.user.first_name || agent_name || 'Agent',
          last_name: data.user.last_name || '',
          user_token: data.user.user_token || space_token || '',
          is_active: data.user.is_active ?? 1,
          full_name:
            data.user.full_name ||
            `${data.user.first_name || agent_name || 'Agent'} ${data.user.last_name || ''}`.trim(),
        };
      }

      // Default agent user info
      return {
        role: 'assistant',
        user_id: 0,
        first_name: agent_name || 'Agent',
        last_name: '',
        user_token: space_token || '',
        is_active: 1,
        full_name: agent_name || 'Agent',
      };
    },
    [agent_name, space_token],
  );

  // Convert Centrifugo message to expected format
  const formatMessage = useCallback(
    (data: AnyMessage, source = MESSAGE_SOURCES.CENTRIFUGO) => {
      const userInfo = getAgentUserInfo(data);

      // If data already has the expected structure, enhance it with proper user info
      if (data.event && data.data) {
        const enhancedData = {
          ...data,
          user: userInfo,
        };
        return {
          data: JSON.stringify(enhancedData),
          timestamp: data.timestamp || new Date().toISOString(),
          source,
        };
      }

      // Otherwise, wrap it in the expected format
      return {
        data: JSON.stringify({
          event: data.event || 'block',
          id: data.id || data.block_id,
          pilot: data.pilot || 'multi-ai',
          execution_type: data.execution_type || 'contact',
          block: data.block || 'html',
          block_type: data.block_type || 'answer',
          user: userInfo,
          data: {
            content: data.content || data.data?.content || '',
            focus: data.focus || 'my_space',
            final: data.final !== undefined ? data.final : true,
            ...data.data,
          },
          timestamp: data.timestamp || new Date().toISOString(),
        }),
        timestamp: data.timestamp || new Date().toISOString(),
        source,
      };
    },
    [getAgentUserInfo],
  );

  // Initialize Centrifugo connection
  useEffect(() => {
    console.log('[Centrifugo DataChannel] Config received:', {
      url: centrifugoUrl,
      token: token ? `${token.substring(0, 20)}...` : null,
      channel_name,
      agent_name,
      space_token,
      metadata,
    });

    if (!enabled || !token || !channel_name || didUnmount.current) {
      console.log('[Centrifugo DataChannel] Not connecting:', {
        enabled,
        hasToken: !!token,
        hasChannel: !!channel_name,
        didUnmount: didUnmount.current,
      });
      return;
    }

    const initConnection = async () => {
      try {
        console.log('[Centrifugo DataChannel] Initializing connection...');

        // Dynamically import centrifuge-js
        const { Centrifuge } = await import('centrifuge');

        const wsUrl = getCentrifugoUrl();
        console.log('[Centrifugo DataChannel] Connecting to:', wsUrl);

        // Create Centrifuge client with token
        const centrifuge = new Centrifuge(wsUrl, {
          token,
          // Token refresh function for long-lived connections
          getToken: async () => {
            // For now, return the same token
            // In production, this should fetch a new token from the backend
            console.log('[Centrifugo DataChannel] Token refresh requested');
            return token;
          },
        });
        centrifugeRef.current = centrifuge;

        // Connection state handlers
        centrifuge.on('connecting', (ctx: any) => {
          console.log('[Centrifugo DataChannel] Connecting...', ctx);
        });

        centrifuge.on('connected', (ctx: any) => {
          console.log('[Centrifugo DataChannel] Connected:', ctx);
          setIsConnected(true);
          reconnectAttemptsRef.current = 0;
        });

        centrifuge.on('disconnected', (ctx: any) => {
          console.log('[Centrifugo DataChannel] Disconnected:', ctx);
          setIsConnected(false);

          // Auto-reconnect logic (unless intentionally closed)
          if (
            ctx.code !== 3000 &&
            reconnectAttemptsRef.current < 5 &&
            !didUnmount.current
          ) {
            reconnectAttemptsRef.current++;
            console.log(
              `[Centrifugo DataChannel] Reconnecting (${reconnectAttemptsRef.current}/5)...`,
            );
            setTimeout(() => {
              if (!didUnmount.current && centrifugeRef.current) {
                centrifugeRef.current.connect();
              }
            }, 3000);
          }
        });

        centrifuge.on('error', (ctx: any) => {
          console.error('[Centrifugo DataChannel] Error:', ctx);
        });

        // Create subscription to the channel
        // Note: If Centrifugo is configured with proxy subscription,
        // no getToken is needed - the server handles authorization
        const subscription = centrifuge.newSubscription(channel_name);
        subscriptionRef.current = subscription;

        // Handle incoming publications (messages)
        subscription.on('publication', (ctx: any) => {
          console.log(
            '[Centrifugo DataChannel] Publication received:',
            ctx.data,
          );

          if (didUnmount.current) return;

          const data = ctx.data as AnyMessage;
          const eventType = data.event;
          const messageId = data.id || data.block_id;

          // Handle streaming events - concatenate content based on ID
          if (eventType === 'stream') {
            const content = data.data?.content || data.content || '';
            const existingMessage = streamingMessagesRef.current.get(messageId);

            if (existingMessage) {
              // Concatenate new content to existing message
              const updatedContent =
                (existingMessage.data?.content || '') + content;
              const updatedData = {
                ...existingMessage,
                // Use 'block' event type so consumer renders it
                event: 'block',
                data: {
                  ...existingMessage.data,
                  content: updatedContent,
                  final: false, // Mark as not final (still streaming)
                },
                isStreaming: true,
              };
              streamingMessagesRef.current.set(messageId, updatedData);

              console.log(
                '[Centrifugo DataChannel] Stream concatenated:',
                updatedContent.length,
                'chars',
              );
              const message = formatMessage(updatedData);
              setLastMessage(message);
            } else {
              // First stream chunk - store it with block event type
              const initialData = {
                ...data,
                event: 'block',
                data: {
                  ...data.data,
                  final: false,
                },
                isStreaming: true,
              };
              streamingMessagesRef.current.set(messageId, initialData);
              console.log(
                '[Centrifugo DataChannel] Stream started for id:',
                messageId,
              );
              const message = formatMessage(initialData);
              setLastMessage(message);
            }
            return;
          }

          // Handle block_response - final message, replace streaming message
          if (eventType === 'block_response') {
            // Clean up streaming message from cache
            streamingMessagesRef.current.delete(messageId);

            // Mark as final and not streaming
            const finalData = {
              ...data,
              data: {
                ...data.data,
                final: true,
              },
              isStreaming: false,
            };

            console.log(
              '[Centrifugo DataChannel] Stream completed for id:',
              messageId,
            );
            const message = formatMessage(finalData);
            setLastMessage(message);
            return;
          }

          // Handle other events normally
          const message = formatMessage(data);
          setLastMessage(message);
        });

        subscription.on('subscribing', (ctx: any) => {
          console.log(
            '[Centrifugo DataChannel] Subscribing to channel...',
            ctx,
          );
        });

        subscription.on('subscribed', (ctx: any) => {
          console.log('[Centrifugo DataChannel] Subscribed to channel:', ctx);
        });

        subscription.on('unsubscribed', (ctx: any) => {
          console.log(
            '[Centrifugo DataChannel] Unsubscribed from channel:',
            ctx,
          );
        });

        subscription.on('error', (ctx: any) => {
          console.error('[Centrifugo DataChannel] Subscription error:', ctx);
        });

        // Presence event handlers (requires presence enabled on server)
        subscription.on('join', (ctx: any) => {
          console.log('[Centrifugo DataChannel] Participant joined:', ctx.info);
          if (didUnmount.current) return;
          setParticipants((prev) => ({
            ...prev,
            [ctx.info.client]: ctx.info,
          }));
        });

        subscription.on('leave', (ctx: any) => {
          console.log('[Centrifugo DataChannel] Participant left:', ctx.info);
          if (didUnmount.current) return;
          setParticipants((prev) => {
            const updated = { ...prev };
            delete updated[ctx.info.client];
            return updated;
          });
        });

        // Start subscription and connection
        subscription.subscribe();
        centrifuge.connect();
      } catch (error) {
        console.error('[Centrifugo DataChannel] Initialization failed:', error);
        setIsConnected(false);
      }
    };

    initConnection();

    // Cleanup on unmount
    return () => {
      console.log('[Centrifugo DataChannel] Cleaning up...');
      if (subscriptionRef.current) {
        subscriptionRef.current.unsubscribe();
        subscriptionRef.current = null;
      }
      if (centrifugeRef.current) {
        centrifugeRef.current.disconnect();
        centrifugeRef.current = null;
      }
    };
  }, [
    enabled,
    token,
    channel_name,
    centrifugoUrl,
    agent_name,
    space_token,
    metadata,
    getCentrifugoUrl,
    formatMessage,
  ]);

  // Send JSON message via Centrifugo
  const sendJsonMessage = useCallback(
    async (data: Record<string, unknown>) => {
      console.log(
        '[Centrifugo DataChannel] sendJsonMessage called with data:',
        data,
      );
      if (!enabled) {
        console.warn(
          '[Centrifugo DataChannel] Cannot send message: Messaging disabled',
        );
        return;
      }

      if (!centrifugeRef.current || !isConnected) {
        console.warn(
          '[Centrifugo DataChannel] Cannot send message: Not connected',
        );
        return;
      }

      if (!subscriptionRef.current) {
        console.warn(
          '[Centrifugo DataChannel] Cannot send message: No subscription',
        );
        return;
      }

      try {
        // Prepare message payload
        const payload = {
          ...data,
          ...params,
          agent_name,
          space_token,
          metadata,
        };

        console.log('[Centrifugo DataChannel] Sending message:', payload);

        // Publish message to the channel
        await subscriptionRef.current.publish(payload);

        console.log('[Centrifugo DataChannel] Message sent successfully');
      } catch (error) {
        console.error(
          '[Centrifugo DataChannel] Failed to send message:',
          error,
        );
      }
    },
    [enabled, isConnected, params, agent_name, space_token, metadata],
  );

  // Function to handle location request response from UI (for compatibility)
  const onLocationResponse = useCallback(
    (requestId: string, accepted: boolean) => {
      console.log(
        `[Centrifugo DataChannel] Location request ${requestId} ${accepted ? 'accepted' : 'declined'} by user`,
      );

      const resolver = locationRequestResolvers.current.get(requestId);
      if (resolver) {
        if (resolver.timeout) {
          clearTimeout(resolver.timeout);
        }
        resolver.resolve({ accepted });
        locationRequestResolvers.current.delete(requestId);
      } else {
        console.warn(
          `[Centrifugo DataChannel] No resolver found for request ${requestId}`,
        );
      }
    },
    [],
  );

  // Get current presence (all active participants in the channel)
  const getPresence = useCallback(async () => {
    if (!subscriptionRef.current) {
      console.warn(
        '[Centrifugo DataChannel] Cannot get presence: No subscription',
      );
      return null;
    }

    try {
      const result = await subscriptionRef.current.presence();
      console.log('[Centrifugo DataChannel] Current presence:', result);
      // Update participants state with current presence
      if (result.clients) {
        setParticipants(result.clients);
      }
      return result;
    } catch (error) {
      console.error('[Centrifugo DataChannel] Failed to get presence:', error);
      return null;
    }
  }, []);

  // Debug function to test if receiving is working
  const testReceive = useCallback(() => {
    if (!centrifugeRef.current || !isConnected) {
      console.error('[Centrifugo DataChannel] Cannot test: Not connected');
      return;
    }

    console.log('[Centrifugo DataChannel] Testing connection...');
    console.log('[Centrifugo DataChannel] Current state:', {
      isConnected,
      hasSubscription: !!subscriptionRef.current,
      channel: channel_name,
    });

    // Send a test message
    if (subscriptionRef.current) {
      subscriptionRef.current
        .publish({
          type: 'test',
          message: 'Self-test message',
          timestamp: Date.now(),
        })
        .then(() => {
          console.log('[Centrifugo DataChannel] Test message sent');
        })
        .catch((err: any) => {
          console.error(
            '[Centrifugo DataChannel] Failed to send test message:',
            err,
          );
        });
    }
  }, [isConnected, channel_name]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      didUnmount.current = true;
      setLastMessage(null);

      // Clear streaming messages cache
      streamingMessagesRef.current.clear();

      // Clear all pending location requests
      locationRequestResolvers.current.forEach(({ timeout, reject }) => {
        if (timeout) {
          clearTimeout(timeout);
        }
        reject(new Error('Component unmounted'));
      });
      locationRequestResolvers.current.clear();
    };
  }, []);

  return {
    sendJsonMessage,
    lastMessage,
    isConnected,
    // Presence features
    participants,
    getPresence,
    // Voice assistant is not available in Centrifugo (text-only)
    voiceAssistant: null,
    // Transcription data is not available in Centrifugo
    agentTranscription: null,
    localTranscription: null,
    testReceive,
    onLocationResponse,
  };
};

export default useCentrifugoDataChannel;
