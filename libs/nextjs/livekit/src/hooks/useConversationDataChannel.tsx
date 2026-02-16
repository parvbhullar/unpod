import { useCallback, useEffect, useRef, useState } from 'react';
import {
  useLocalParticipant,
  useRoomContext,
  useTrackTranscription,
  useVoiceAssistant
} from '@livekit/components-react';
import { createMessageValidator, processLiveKitDataPacket } from '@unpod/helpers';

import { RoomEvent, Track } from 'livekit-client';
import { registerGetLocationHandler } from './rpcHandlers/getLocationHandler';
import { registerTopicHandlers, unregisterTopicHandlers } from './textStreamHandlers/registerTopicHandlers';

/**
 * Message source types for tracking and deduplication
 */
const MESSAGE_SOURCES = {
  TRANSCRIPTION_AGENT: 'transcription_agent',
  TRANSCRIPTION_LOCAL: 'transcription_local',
  TEXT_STREAM: 'text_stream',
  DATA_PACKET: 'data_packet',
};

/**
 * Priority levels for message source deduplication
 * Higher values take precedence when same message ID appears from multiple sources
 */
const SOURCE_PRIORITIES = {
  [MESSAGE_SOURCES.TRANSCRIPTION_AGENT]: 3,
  [MESSAGE_SOURCES.TRANSCRIPTION_LOCAL]: 3,
  [MESSAGE_SOURCES.TEXT_STREAM]: 2,
  [MESSAGE_SOURCES.DATA_PACKET]: 1,
};

/**
 * Custom hook to manage conversation messaging using LiveKit Text Streams
 *
 * Uses LiveKit's official Text Streams API for sending and receiving messages.
 * Supports both voice/video mode and text-only mode (data-only connection).
 *
 * Agent transcriptions are received via:
 * 1. Audio track transcription (agentTranscription)
 * 2. Text stream topics (lk.chat, superkik.cards, lk.block_response)
 * 3. Data packets (legacy API)
 *
 * Local participant transcriptions are tracked from microphone audio.
 *
 * RPC Handlers:
 * - getLocation: Returns user's geolocation and sends it as a message event
 *
 * @param {Object} options - Configuration options
 * @param {string} options.conversationId - The conversation ID (optional, for metadata)
 * @param {Object} options.params - Additional parameters to include in messages
 * @param {boolean} options.enabled - Enable/disable messaging (default: true)
 * @param {string|string[]} options.topic - Message topic(s) for routing (default: ['lk.chat', 'superkik.cards', 'lk.block_response']). Can be a single topic or array of topics
 * @returns {Object} - { sendJsonMessage, lastMessage, isConnected, agentTranscription, localTranscription, voiceAssistant, testReceive }
 */
type AnyMessage = Record<string, any>;

type MessageMetadata = {
  source: string;
  timestamp: number;
  topic?: string;
  [key: string]: unknown;
};

type TranscriptSegment = {
  id: string;
  text: string;
  final?: boolean;
};

type ParticipantLike = {
  identity?: string;
  name?: string;
  metadata?: string;
};

type UseConversationDataChannelOptions = {
  conversationId?: string;
  params?: Record<string, unknown>;
  enabled?: boolean;
  topic?: string | string[];
};

export const useConversationDataChannel = ({
  conversationId,
  params,
  enabled = true,
  topic, // Default topic: 'chat'
}: UseConversationDataChannelOptions) => {
  const [lastMessage, setLastMessage] = useState<AnyMessage | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const didUnmount = useRef(false);
  const registeredTopics = useRef<Set<string>>(new Set());
  const room = useRoomContext();

  // Store all transcripts in a Map (keyed by segment ID)
  const [transcripts, setTranscripts] = useState<Map<string, AnyMessage>>(
    new Map(),
  );

  // Track message metadata for deduplication (Map<block_id, {source, timestamp, topic?}>)
  const [messageMetadata, setMessageMetadata] = useState<
    Map<string, MessageMetadata>
  >(new Map());

  // Get voice assistant and local participant
  const voiceAssistant = useVoiceAssistant();
  const participant = useLocalParticipant();
  const { localParticipant } = participant;
  // Get transcriptions for both agent and local participant
  const agentTranscription = useTrackTranscription(voiceAssistant.audioTrack);
  const localTranscription = useTrackTranscription({
    publication: participant.microphoneTrack,
    source: Track.Source.Microphone,
    participant: localParticipant,
  });

  // Helper function to convert segment to chat message
  const segmentToChatMessage = useCallback(
    (
      segment: TranscriptSegment,
      existingMessage: AnyMessage | null,
      participant: ParticipantLike | null | undefined,
    ) => {
      const isAgent =
        participant?.identity ===
        voiceAssistant.audioTrack?.participant?.identity;
      const isSelf = participant?.identity === localParticipant?.identity;

      let name = participant?.name || participant?.identity;
      if (!name) {
        if (isAgent) {
          name = 'Agent';
        } else if (isSelf) {
          name = 'You';
        } else {
          name = 'Unknown';
        }
      }

      // Extract user information from participant metadata
      const participantMetadata = participant?.metadata
        ? JSON.parse(participant.metadata)
        : {};
      const userId =
        participantMetadata?.user_id ||
        participantMetadata?.userId ||
        participant?.identity;

      // Parse name into first and last name
      const nameParts = name.split(' ');
      const firstName = nameParts[0] || name;
      const lastName = nameParts.slice(1).join(' ') || '';

      // Format timestamp to local time using DateHelper
      const timestamp = existingMessage?.timestamp || Date.now();
      // Ensure created is in ISO string format for consistent date comparisons
      const createdDate =
        existingMessage?.created || new Date(timestamp).toISOString();

      // Determine block type based on whether it's a question or answer
      const blockType = isAgent ? 'answer' : 'question';

      return {
        thread_id: conversationId || null,
        block_id: segment.id,
        user_id: userId?.toString(),
        event: 'block',
        user: {
          role: isAgent ? 'assistant' : 'user',
          user_id: parseInt(userId) || 0,
          first_name: firstName,
          last_name: lastName,
          user_token: participantMetadata?.user_token || participant?.identity,
          is_active: 1,
          full_name: name,
        },
        block: 'html',
        block_type: blockType,
        data: {
          block: 'text',
          content: segment.text,
          knowledge_bases: participantMetadata?.knowledge_bases || [],
          conversation_type: segment.final ? 'response' : 'partial',
          final: segment.final,
        },
        media: {},
        seq_number: existingMessage?.seq_number || 1,
        reaction_count: 0,
        parent_id: null,
        parent: {},
        created: createdDate,
        // Keep legacy fields for backward compatibility
      };
    },
    [voiceAssistant.audioTrack?.participant, localParticipant, conversationId],
  );

  /**
   * Track message source for deduplication
   */
  const trackMessageSource = useCallback(
    (
      blockId: string,
      source: string,
      additionalMeta: Record<string, unknown> = {},
    ) => {
      setMessageMetadata((prev) => {
        const newMetadata = new Map(prev);
        newMetadata.set(blockId, {
          source,
          timestamp: Date.now(),
          ...additionalMeta,
        });
        return newMetadata;
      });
    },
    [],
  );

  /**
   * Decide if new message should replace existing based on priority
   * Returns true if new message should be accepted, false otherwise
   */
  const shouldAcceptMessage = useCallback(
    (
      prevMetadata: MessageMetadata | undefined,
      newSource: string,
      isSameId = false,
    ) => {
      if (!prevMetadata) return true; // No previous metadata, accept new

      const prevPriority = SOURCE_PRIORITIES[prevMetadata.source] || 0;
      const newPriority = SOURCE_PRIORITIES[newSource] || 0;

      // Same ID updates (streaming transcriptions) should ALWAYS be accepted
      if (isSameId && prevMetadata.source === newSource) {
        console.log(`✅ Accepting ${newSource} update for same ID (streaming)`);
        return true;
      }

      // Higher priority wins
      if (newPriority > prevPriority) {
        console.log(
          `✅ Accepting ${newSource} (priority ${newPriority}) over ${prevMetadata.source} (priority ${prevPriority})`,
        );
        return true;
      }

      // Lower priority loses
      if (newPriority < prevPriority) {
        console.log(
          `⏭️ Skipping ${newSource} (priority ${newPriority}), keeping ${prevMetadata.source} (priority ${prevPriority})`,
        );
        return false;
      }

      // Same priority, different sources: newer timestamp wins
      const timeDiff = Date.now() - prevMetadata.timestamp;
      if (timeDiff > 100) {
        // Only accept if more than 100ms newer
        console.log(
          `✅ Accepting newer ${newSource} message (${timeDiff}ms later)`,
        );
        return true;
      }

      console.log(
        `⏭️ Skipping ${newSource}, recent message from ${prevMetadata.source} still valid`,
      );
      return false;
    },
    [],
  );

  // Track LiveKit room connection state
  useEffect(() => {
    if (!enabled) {
      console.log('useConversationDataChannel: disabled');
      setIsConnected(false);
      return;
    }

    if (!room) {
      console.log('useConversationDataChannel: no room context');
      setIsConnected(false);
      return;
    }

    const currentState = room.state === 'connected';
    console.log(
      'useConversationDataChannel: room state =',
      room.state,
      'connected =',
      currentState,
    );
    setIsConnected(currentState);

    const handleConnectionChange = (state: string) => {
      const isConnected = state === 'connected';
      console.log(
        'useConversationDataChannel: connection state changed to',
        state,
        'connected =',
        isConnected,
      );
      setIsConnected(isConnected);
    };

    room.on('connectionStateChanged', handleConnectionChange);

    return () => {
      room.off('connectionStateChanged', handleConnectionChange);
    };
  }, [room, enabled]);

  // Log current connection mode
  useEffect(() => {
    if (!enabled) return;

    if (isConnected) {
      console.log('🎙️ LiveKit connected - text streams ready');
    } else {
      console.log('❌ LiveKit disconnected');
    }
  }, [isConnected, enabled]);

  // Store and process transcription segments (following LiveKit reference pattern)
  useEffect(() => {
    if (!enabled || didUnmount.current) {
      return;
    }

    console.log('📝 Processing transcriptions:', {
      agentSegments: agentTranscription.segments?.length || 0,
      localSegments: localTranscription.segments?.length || 0,
    });

    // Update transcripts Map with all segments from both agent and local
    setTranscripts((prevTranscripts) => {
      const newTranscripts = new Map(prevTranscripts);

      // Process agent transcription segments
      agentTranscription.segments?.forEach((segment) => {
        const existingMessage = newTranscripts.get(segment.id) ?? null;
        const message = segmentToChatMessage(
          segment as TranscriptSegment,
          existingMessage,
          voiceAssistant.audioTrack?.participant,
        );
        newTranscripts.set(segment.id, message);

        // Track message source for deduplication
        trackMessageSource(segment.id, MESSAGE_SOURCES.TRANSCRIPTION_AGENT, {
          segmentId: segment.id,
          final: segment.final,
        });
      });

      // Process local transcription segments
      localTranscription.segments?.forEach((segment) => {
        const existingMessage = newTranscripts.get(segment.id) ?? null;
        const message = segmentToChatMessage(
          segment as TranscriptSegment,
          existingMessage,
          localParticipant,
        );
        newTranscripts.set(segment.id, message);

        // Track message source for deduplication
        trackMessageSource(segment.id, MESSAGE_SOURCES.TRANSCRIPTION_LOCAL, {
          segmentId: segment.id,
          final: segment.final,
        });
      });

      console.log('📊 Total transcripts in map:', newTranscripts.size);
      return newTranscripts;
    });
  }, [
    enabled,
    agentTranscription.segments,
    localTranscription.segments,
    voiceAssistant.audioTrack?.participant,
    localParticipant,
    segmentToChatMessage,
    trackMessageSource,
  ]);

  // Update lastMessage whenever transcripts change (from LiveKit transcription)
  useEffect(() => {
    const allMessages = Array.from(transcripts.values());
    if (allMessages.length > 0) {
      // Sort by created timestamp and get the latest
      allMessages.sort((a, b) => {
        const timeA = new Date(a.created).getTime();
        const timeB = new Date(b.created).getTime();
        return timeA - timeB;
      });
      const latestTranscript = allMessages[allMessages.length - 1];

      // Create message in the format expected by components
      const message = {
        data: JSON.stringify({
          event: latestTranscript.event || 'block',
          id: latestTranscript.block_id,
          pilot: 'multi-ai',
          execution_type: 'contact',
          block: latestTranscript.block,
          block_type: latestTranscript.block_type,
          user: {
            role: latestTranscript.user.role || 'assistant',
            user_id: latestTranscript.user.user_id,
            first_name: latestTranscript.user.first_name,
          },
          data: {
            content: latestTranscript.data.content,
            focus: latestTranscript.data.focus || 'my_space',
            final: latestTranscript.data.final,
          },
          timestamp: latestTranscript.created,
        }),
        timestamp: latestTranscript.created,
        // participant: latestTranscript._legacy.participant,
        source: 'transcription',
      };

      console.log('useConversationDataChannel lastMessage:', message);

      // Update lastMessage with deduplication logic
      setLastMessage((prevMessage) => {
        if (!prevMessage) {
          return message;
        }

        try {
          const prevData = JSON.parse(prevMessage.data);
          const newData = JSON.parse(message.data);

          // Same block ID - check if we should update based on priority
          if (prevData.id === newData.id) {
            const prevMetadata = messageMetadata.get(prevData.id);
            const newSource = MESSAGE_SOURCES.TRANSCRIPTION_AGENT; // From transcription

            // Pass isSameId=true to allow streaming updates
            if (shouldAcceptMessage(prevMetadata, newSource, true)) {
              console.log(
                `🔄 Updating message ${newData.id} from ${prevMetadata?.source || 'unknown'} to ${newSource}`,
              );
              return message;
            } else {
              console.log(
                `⏭️ Skipping duplicate transcription for ${newData.id}`,
              );
              return prevMessage; // Keep existing
            }
          } else {
            // Different ID = new transcript message
            console.log('✨ New transcript message:', newData.id, message);
            return message;
          }
        } catch (err) {
          console.warn('Failed to parse message for deduplication:', err);
          return message;
        }
      });
    }
  }, [transcripts, messageMetadata, shouldAcceptMessage]);

  // Register LiveKit text stream handler for receiving messages
  // Agent transcriptions and all messages come through these topics
  useEffect(() => {
    if (!room || !enabled || !isConnected || didUnmount.current) {
      console.log('⚠️ Cannot register handlers:', {
        hasRoom: !!room,
        enabled,
        isConnected,
        didUnmount: didUnmount.current,
      });
      return;
    }

    // Support both single topic and array of topics
    const topics = Array.isArray(topic)
      ? topic
      : topic
        ? [topic]
        : ['lk.chat', 'lk.block_response']; // Default: listen to both chat and cards topics

    console.log(
      '🔧 Registering LiveKit text stream handlers for topics:',
      topics,
    );

    // Create validator for cards - ONLY accept messages that contain cards
    // Messages without cards will be automatically rejected and logged
    const cardsValidator = createMessageValidator('data.cards');

    // Register DataReceived event handler (for legacy data packets)
    const handleDataReceived = (
      payload: Uint8Array,
      participant: any,
      kind: any,
    ) => {
      if (didUnmount.current) return;

      // Process data packet using helper with cards validation
      // Returns null if message doesn't contain cards
      const message = processLiveKitDataPacket(payload, participant, kind, {
        validator: cardsValidator, // Only allow messages with data.cards
      });

      // Set message only if it passed validation (has cards)
      if (message) {
        try {
          const data = JSON.parse(message.data);
          const blockId = data.id;

          // Track message source
          trackMessageSource(blockId, MESSAGE_SOURCES.DATA_PACKET);

          console.log('✅ DataPacket accepted and set as lastMessage');
          setLastMessage(message);
        } catch (err) {
          console.error('Failed to process DataPacket:', err);
          setLastMessage(message); // Still set message on error
        }
      }
    };

    room.on(RoomEvent.DataReceived, handleDataReceived);
    console.log('✅ Registered DataReceived event handler');

    // Register text stream handlers for topics using extracted function
    const unregisterFunctions = registerTopicHandlers({
      room,
      topics,
      registeredTopics,
      didUnmount,
      setLastMessage,
      trackMessageSource,
      shouldAcceptMessage,
      messageMetadata,
      MESSAGE_SOURCE: MESSAGE_SOURCES.TEXT_STREAM,
    });

    // Cleanup: unregister all handlers on unmount or when connection drops
    return () => {
      console.log('🧹 Cleaning up text stream handlers');

      // Remove DataReceived event handler
      if (room && handleDataReceived) {
        room.off(RoomEvent.DataReceived, handleDataReceived);
        console.log('🗑️ Unregistered DataReceived event handler');
      }

      // Remove text stream handlers using extracted function
      if (unregisterFunctions && unregisterFunctions.length > 0) {
        unregisterTopicHandlers({
          unregisterFunctions,
          topics,
          registeredTopics,
        });
      }
    };
  }, [room, enabled, topic, isConnected]);

  // Store pending location requests with their resolvers
  const locationRequestResolvers = useRef<
    Map<
      string,
      {
        resolve: (value: { accepted: boolean }) => void;
        reject: (error: Error) => void;
        timeout?: ReturnType<typeof setTimeout>;
      }
    >
  >(new Map());

  // Register RPC handler for getLocation (independent of agent/voice mode)
  useEffect(() => {
    if (!localParticipant || !isConnected || !enabled || didUnmount.current) {
      console.log('⚠️ Cannot register RPC handler:', {
        hasLocalParticipant: !!localParticipant,
        isConnected,
        enabled,
        didUnmount: didUnmount.current,
      });
      return;
    }

    // Register getLocation RPC handler using extracted function
    const unregisterGetLocation = registerGetLocationHandler({
      localParticipant,
      setLastMessage,
      locationRequestResolvers,
      room,
      isConnected,
      topic,
    });

    // Cleanup function
    return () => {
      if (unregisterGetLocation) {
        unregisterGetLocation();
        console.log('🗑️ Unregistered RPC handler: getLocation');
      }

      // Clear all pending requests
      locationRequestResolvers.current.forEach(({ timeout, reject }) => {
        if (timeout) {
          clearTimeout(timeout);
        }
        reject(new Error('Component unmounted'));
      });
      locationRequestResolvers.current.clear();
    };
  }, [localParticipant, isConnected, enabled, room, topic]);

  // Function to handle location request response from UI
  const onLocationResponse = useCallback(
    (requestId: string, accepted: boolean) => {
      console.log(
        `📍 Location request ${requestId} ${accepted ? 'accepted' : 'declined'} by user`,
      );

      const resolver = locationRequestResolvers.current.get(requestId);
      if (resolver) {
        clearTimeout(resolver.timeout);
        resolver.resolve({ accepted });
        locationRequestResolvers.current.delete(requestId);
      } else {
        console.warn(`⚠️ No resolver found for request ${requestId}`);
      }
    },
    [],
  );

  // Send JSON message using LiveKit text streams
  const sendJsonMessage = useCallback(
    async (data: Record<string, unknown>) => {
      if (!enabled) {
        console.warn('Cannot send message: Messaging disabled');
        return;
      }

      if (!room || !isConnected) {
        console.warn('Cannot send message: LiveKit room not connected');
        return;
      }

      try {
        // Prepare message payload
        const payload = {
          ...data,
          ...params,
        };

        const text = JSON.stringify(payload);

        // Determine which topic to send to
        // If topic is array, use first one; if string, use that; if undefined, default to 'lk.chat'
        const streamTopic = Array.isArray(topic)
          ? topic[0]
          : topic || 'lk.chat';

        console.log('📤 Sending message via LiveKit text stream:', {
          topic: streamTopic,
          payload,
        });

        // Use LiveKit's sendText API (supports automatic chunking for large messages)
        await room.localParticipant.sendText(text, {
          topic: streamTopic,
        });

        console.log('✓ Message sent via LiveKit');
      } catch (error) {
        console.error('Failed to send message via LiveKit:', error);
      }
    },
    [room, isConnected, params, enabled, topic],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      didUnmount.current = true;
      setLastMessage(null);
    };
  }, []);

  // Debug function to test if receiving is working
  const testReceive = useCallback(() => {
    if (!room || !isConnected) {
      console.error('❌ Cannot test: Room not connected');
      return;
    }

    console.log('🧪 Testing text stream reception...');
    console.log('📋 Current room state:', {
      roomState: room.state,
      isConnected,
      hasLocalParticipant: !!room.localParticipant,
      numParticipants: room.remoteParticipants.size,
    });

    // Send a test message to ourselves on lk.block_response
    room.localParticipant
      .sendText(
        JSON.stringify({
          type: 'test',
          message: 'Self-test message',
          timestamp: Date.now(),
        }),
        { topic: 'lk.block_response' },
      )
      .then(() => {
        console.log(
          '✅ Test message sent to lk.block_response - if handler is working, you should see it above',
        );
      })
      .catch((err) => {
        console.error('❌ Failed to send test message:', err);
      });
  }, [room, isConnected]);

  // Master cleanup effect on unmount
  useEffect(() => {
    return () => {
      didUnmount.current = true;
      setLastMessage(null);
    };
  }, []);

  return {
    sendJsonMessage,
    lastMessage,
    isConnected,
    // Expose transcription data for both agent and local participant
    agentTranscription,
    localTranscription,
    voiceAssistant,
    testReceive, // Debug function
    onLocationResponse, // Function to respond to location requests
  };
};
