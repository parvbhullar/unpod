import { processLiveKitTextStream } from '@unpod/helpers';
import type { MutableRefObject } from 'react';

type AnyMessage = {
  data: string;
  [key: string]: unknown;
};

type RegisterTopicHandlersOptions = {
  room: any;
  topics: string[];
  registeredTopics: MutableRefObject<Set<string>>;
  didUnmount: MutableRefObject<boolean>;
  setLastMessage: (message: AnyMessage) => void;
  trackMessageSource?: (
    blockId: string,
    source: string,
    meta?: Record<string, unknown>,
  ) => void;
  shouldAcceptMessage?: (...args: any[]) => boolean;
  messageMetadata?: Map<string, any>;
  MESSAGE_SOURCE?: string;
};

type UnregisterTopicHandlersOptions = {
  unregisterFunctions: Array<(() => void) | null>;
  topics: string[];
  registeredTopics: MutableRefObject<Set<string>>;
};

/**
 * Registers text stream handlers for specified LiveKit topics
 *
 * This function registers handlers for LiveKit text streams on specified topics.
 * Each handler processes incoming text streams and converts them to message format.
 *
 * @param {Object} options - Handler configuration
 * @param {Object} options.room - LiveKit room instance
 * @param {string[]} options.topics - Array of topic strings to register handlers for
 * @param {React.MutableRefObject<Set>} options.registeredTopics - Ref containing Set of already registered topics
 * @param {React.MutableRefObject<boolean>} options.didUnmount - Ref to check if component is unmounted
 * @param {Function} options.setLastMessage - Function to update the lastMessage state
 * @param {Function} options.trackMessageSource - Function to track message source for deduplication
 * @param {Function} options.shouldAcceptMessage - Function to check if message should be accepted based on priority
 * @param {Map} options.messageMetadata - Map of message metadata for deduplication
 * @param {string} options.MESSAGE_SOURCE - Source type constant (e.g., 'text_stream')
 * @returns {Function[]} Array of unregister functions for cleanup
 */
export const registerTopicHandlers = ({
  room,
  topics,
  registeredTopics,
  didUnmount,
  setLastMessage,
  trackMessageSource,
  MESSAGE_SOURCE,
}: RegisterTopicHandlersOptions) => {
  console.log(
    '🔧 Registering LiveKit text stream handlers for topics:',
    topics,
  );

  // Register handler for each topic (following LiveKit official pattern)
  const unregisterFunctions = topics.map((streamTopic: string) => {
    // Check if already registered
    if (registeredTopics.current.has(streamTopic)) {
      console.log(
        `⏭️ Handler for topic "${streamTopic}" already registered, skipping`,
      );
      return null;
    }

    try {
      const unregister = room?.registerTextStreamHandler(
        streamTopic,
        async (reader: any, participantInfo: any) => {
          if (didUnmount.current) return;

          try {
            // Read the complete text after the stream completes
            const text = await reader.readAll();

            // Process text stream using helper
            const message = processLiveKitTextStream(
              text,
              participantInfo,
              reader.info,
              streamTopic,
            );

            // Set message if valid
            if (message) {
              // Track message source if available
              if (trackMessageSource && MESSAGE_SOURCE) {
                try {
                  const data = JSON.parse(message.data);
                  const blockId = data.id;
                  trackMessageSource(blockId, MESSAGE_SOURCE, {
                    topic: streamTopic,
                  });
                } catch (err) {
                  console.warn(`Failed to track message source:`, err);
                }
              }

              // Set the message (deduplication is handled in useConversationDataChannel)
              setLastMessage(message);
            }
          } catch (error) {
            console.error(
              `❌ [${streamTopic}] Failed to process text stream:`,
              error,
            );
          }
        },
      );

      // Mark as registered
      registeredTopics.current.add(streamTopic);
      console.log(`✅ Registered handler for topic: ${streamTopic}`);
      return unregister;
    } catch (error) {
      console.error(
        `❌ Failed to register handler for topic "${streamTopic}":`,
        error,
      );
      return null;
    }
  });

  return unregisterFunctions;
};

/**
 * Unregisters all topic handlers
 *
 * @param {Object} options - Cleanup configuration
 * @param {Function[]} options.unregisterFunctions - Array of unregister functions
 * @param {string[]} options.topics - Array of topic strings that were registered
 * @param {React.MutableRefObject<Set>} options.registeredTopics - Ref containing Set of registered topics
 */
export const unregisterTopicHandlers = ({
  unregisterFunctions,
  topics,
  registeredTopics,
}: UnregisterTopicHandlersOptions) => {
  console.log('🧹 Cleaning up topic handlers');

  // Remove text stream handlers
  unregisterFunctions.forEach((unregister, index) => {
    if (unregister) {
      const topicToUnregister = topics[index];
      console.log(`🗑️ Unregistering handler for topic: ${topicToUnregister}`);
      unregister();
      // Remove from registered topics set
      registeredTopics.current.delete(topicToUnregister);
    }
  });
};
