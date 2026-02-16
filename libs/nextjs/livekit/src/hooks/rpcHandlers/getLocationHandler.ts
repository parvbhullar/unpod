import type { MutableRefObject } from 'react';

type AnyMessage = {
  data: string;
  timestamp: number;
  source: string;
};

type LocationRequestResolver = {
  resolve: (value: { accepted: boolean }) => void;
  reject: (error: Error) => void;
  timeout?: ReturnType<typeof setTimeout>;};

type RegisterGetLocationHandlerOptions = {
  localParticipant: any;
  setLastMessage: (message: AnyMessage) => void;
  locationRequestResolvers: MutableRefObject<
    Map<string, LocationRequestResolver>
  >;
  room: any;
  isConnected: boolean;
  topic?: string | string[];};

/**
 * RPC handler for getLocation method
 *
 * This handler allows LiveKit agents to request the user's geolocation with permission.
 * It creates a UI flow for user consent, retrieves location, and sends it back to the agent.
 *
 * @param {Object} options - Handler configuration
 * @param {Object} options.localParticipant - LiveKit local participant
 * @param {Function} options.setLastMessage - Function to update UI with messages
 * @param {React.MutableRefObject} options.locationRequestResolvers - Map of pending location requests
 * @param {Object} options.room - LiveKit room instance
 * @param {boolean} options.isConnected - Connection status
 * @param {string|string[]} options.topic - Message topic(s) for routing
 * @returns {Function} Unregister function to cleanup the RPC handler
 */
export const registerGetLocationHandler = ({
  localParticipant,
  setLastMessage,
  locationRequestResolvers,
  room,
  isConnected,
  topic,
}: RegisterGetLocationHandlerOptions) => {
  console.log('🔧 Registering RPC handler: getLocation');

  const unregisterGetLocation = localParticipant.registerRpcMethod(
    'getLocation',
    async (data: any) => {
      console.log('📍 getLocation RPC called with data:', data);

      try {
        // Parse the payload to get request details
        const requestPayload = JSON.parse(data.payload || '{}');
        const requestId = data.requestId;

        console.log('📍 Parsed location request:', {
          requestId,
          action: requestPayload.action,
          reason: requestPayload.reason,
        });

        // Send location request message to UI directly via lastMessage
        // (can't use sendText because local messages don't trigger handlers)
        const requestMessage = {
          data: JSON.stringify({
            event: 'location_request',
            id: requestId,
            block_id: requestId,
            pilot: 'multi-ai',
            execution_type: 'contact',
            block: 'html',
            block_type: 'location_request',
            user: {
              role: 'assistant',
              user_id: 0,
              first_name: 'Agent',
            },
            data: {
              request_id: requestId,
              reason:
                requestPayload.reason ||
                'The agent is requesting your location',
              accept_text: requestPayload.accept_text || 'Share Location',
              cancel_text: requestPayload.cancel_text || 'Not Now',
              block_type: 'location_request',
              timeout: data.responseTimeout || 90000, // 90 seconds (1.5 minutes) for user to respond
            },
            timestamp: Date.now(),
          }),
          timestamp: Date.now(),
          source: 'location_request',
        };

        console.log(
          '📤 Setting location request message to UI:',
          requestMessage,
        );

        setLastMessage(requestMessage);

        // Wait for user response (will be resolved by onLocationResponse)
        const userResponse = await new Promise<{ accepted: boolean }>(
          (resolve, reject) => {
            locationRequestResolvers.current.set(requestId, {
              resolve,
              reject,
            });

            // Set timeout (90 seconds / 1.5 minutes for user to respond)
            const timeout = setTimeout(() => {
              locationRequestResolvers.current.delete(requestId);
              reject(new Error('Location request timed out'));
            }, data.responseTimeout || 90000);

            // Store timeout to clear it if resolved early
            const resolver = locationRequestResolvers.current.get(requestId);
            if (resolver) {
              resolver.timeout = timeout;
            }
          },
        );

        console.log('✅ User response received:', userResponse);

        // If user accepted, get location
        if (userResponse.accepted) {
          const position = await new Promise<GeolocationPosition>(
            (resolve, reject) => {
              navigator.geolocation.getCurrentPosition(resolve, reject, {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0,
              });
            },
          );

          const response = {
            status: 'success',
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            altitude: position.coords.altitude,
            altitudeAccuracy: position.coords.altitudeAccuracy,
            heading: position.coords.heading,
            speed: position.coords.speed,
            timestamp: position.timestamp,
          };

          console.log('✅ Location retrieved successfully:', response);

          // Send location success status to UI
          const successMessage = {
            data: JSON.stringify({
              event: 'location_success',
              id: requestId,
              block_id: requestId,
              pilot: 'multi-ai',
              execution_type: 'contact',
              block: 'html',
              block_type: 'location_success',
              user: {
                role: 'assistant',
                user_id: 0,
                first_name: 'Agent',
              },
              data: {
                request_id: requestId,
                latitude: response.latitude,
                longitude: response.longitude,
                accuracy: response.accuracy,
                block_type: 'location_success',
              },
              timestamp: Date.now(),
            }),
            timestamp: Date.now(),
            source: 'location_success',
          };

          console.log(
            '📤 Setting location success message to UI:',
            successMessage,
          );
          setLastMessage(successMessage);

          // Send location data as a message event via text stream
          if (room && isConnected) {
            const messagePayload = {
              event: 'location',
              data: {
                content: `Location: ${response.latitude}, ${response.longitude}`,
                location: response,
                block_type: 'location',
              },
            };

            console.log('📤 Sending location message:', messagePayload);

            const streamTopic = Array.isArray(topic)
              ? topic[0]
              : topic || 'lk.chat';

            await room.localParticipant.sendText(
              JSON.stringify(messagePayload),
              {
                topic: streamTopic,
              },
            );
          }

          return JSON.stringify(response);
        } else {
          // User declined - update UI to show declined status
          const declinedMessage = {
            data: JSON.stringify({
              event: 'location_declined',
              id: requestId,
              block_id: requestId,
              pilot: 'multi-ai',
              execution_type: 'contact',
              block: 'html',
              block_type: 'location_declined',
              user: {
                role: 'assistant',
                user_id: 0,
                first_name: 'Agent',
              },
              data: {
                request_id: requestId,
                block_type: 'location_declined',
              },
              timestamp: Date.now(),
            }),
            timestamp: Date.now(),
            source: 'location_declined',
          };

          console.log(
            '📤 Setting location declined message to UI:',
            declinedMessage,
          );
          setLastMessage(declinedMessage);

          const errorResponse = {
            status: 'error',
            error: 'User declined to share location',
            code: 'PERMISSION_DENIED',
          };

          return JSON.stringify(errorResponse);
        }
      } catch (error) {
        const err = error as Error & { code?: string };
        console.error('❌ Failed to get location:', err);

        const errorResponse = {
          status: 'error',
          error: err.message,
          code: err.code || 'UNKNOWN_ERROR',
        };

        return JSON.stringify(errorResponse);
      }
    },
  );

  console.log('✅ Registered RPC handler: getLocation');

  return unregisterGetLocation;
};
