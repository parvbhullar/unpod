/**
 * WebSocket Message Handler Helper
 * Handles parsing and processing of WebSocket messages for conversation/chat
 * Also includes LiveKit data channel and text stream message handling
 */

import { getLocalLocalTimeFromUTC } from './DateHelper';

export type WebSocketParticipant = {
  identity?: string;
  metadata?: string;
  permissions?: {
    agent?: boolean;
  };};

export type WebSocketMessage = {
  data?: string;
  timestamp?: number | string;
  participant?: WebSocketParticipant;};

export type MessageUser = {
  role?: string;
  user_id?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  profile_color?: string;
  user_token?: string;
  is_active?: number;};

export type MessageData = {
  block_id?: string;
  id?: string;
  thread_id?: string;
  user_id?: string;
  user?: MessageUser;
  block?: string;
  block_type?: string;
  data?: MessageDataContent;
  media?: Record<string, unknown>;
  seq_number?: number;
  reaction_count?: number;
  parent_id?: string | null;
  parent?: Record<string, unknown>;
  created?: string;
  event?: string;
  timestamp?: number | string;};

export type MessageDataContent = {
  content?: string;
  final?: boolean;
  cards?: {
    type?: string;
    items?: Array<{ id?: string; status?: string }>;
  };
  block_type?: string;
  [key: string]: unknown;};

export type CurrentPost = {
  post_id?: string;};

export type StreamInfo = {
  topic?: string;
  timestamp?: number;
  id?: string;
  size?: number;};

/**
 * Parse JSON data safely with error handling
 */
const parseJsonSafely = (
  data: string,
  context = 'Unknown',
): Record<string, unknown> | null => {
  try {
    return JSON.parse(data);
  } catch (error) {
    console.warn(`⚠️ [${context}] Failed to parse JSON:`, error);
    return null;
  }
};

/**
 * Validate if message contains required data
 */
const validateMessageData = (
  parsedData: Record<string, unknown> | null,
  validatorFn?: (data: Record<string, unknown>) => boolean,
): boolean => {
  if (!parsedData) return false;
  if (validatorFn) return validatorFn(parsedData);
  return true;
};

/**
 * Create LiveKit message in WebSocket-compatible format
 */
type CreateLiveKitMessageOptions = {
  data: string;
  source: string;
  topic?: string | null;
  streamInfo?: StreamInfo | null;
  kind?: string | null;};

const createLiveKitMessage = ({
  data,
  source,
  topic = null,
  streamInfo = null,
  kind = null,
}: CreateLiveKitMessageOptions): WebSocketMessage & {
  topic?: string;
  streamInfo?: StreamInfo;
  kind?: string;
  source: string;
} => {
  return {
    data,
    timestamp:
      getLocalLocalTimeFromUTC(Date.now())?.format?.('YYYY-MM-DD HH:mm:ss') ||
      new Date().toISOString(),
    source,
    ...(topic && { topic }),
    ...(streamInfo && { streamInfo }),
    ...(kind && { kind }),
  };
};

/**
 * Parse participant metadata from WebSocket message
 */
const parseParticipantMetadata = (
  participant: WebSocketParticipant | null | undefined,
): Record<string, unknown> => {
  try {
    return participant?.metadata ? JSON.parse(participant.metadata) : {};
  } catch (error) {
    console.error('Error parsing participant metadata:', error);
    return {};
  }
};

/**
 * Determine if participant is an agent
 */
const isAgentParticipant = (
  participant: WebSocketParticipant | null | undefined,
  participantMetadata: Record<string, unknown>,
): boolean => {
  return (
    participant?.permissions?.agent ||
    participantMetadata?.agent_type === 'pipecat'
  );
};

/**
 * Determine message role and whether it's an assistant message
 */
const getMessageRole = (
  data: MessageData,
  isAgent: boolean,
): { msgRole: string; isAssistantMsg: boolean } => {
  const msgRole = data.user?.role || (isAgent ? 'assistant' : 'user');
  const isAssistantMsg =
    msgRole === 'assistant' || msgRole === 'agent' || msgRole === 'system';
  return { msgRole, isAssistantMsg };
};

/**
 * Transform WebSocket data to message format
 */
const transformToMessageData = (
  data: MessageData,
  lastMessage: WebSocketMessage,
  participant: WebSocketParticipant | null | undefined,
  participantMetadata: Record<string, unknown>,
  msgRole: string,
  color: string,
  currentPost: CurrentPost | null | undefined,
): MessageData => {
  const blockId = data.block_id || data.id;
  const agentName = (participantMetadata?.agent_name as string) || 'Agent';

  return {
    block_id: blockId,
    thread_id: data.thread_id || currentPost?.post_id,
    user_id: data.user_id || participant?.identity,
    user: data.user || {
      role: msgRole,
      user_id: participant?.identity,
      first_name: agentName.split(' ')[0],
      last_name: agentName.split(' ').slice(1).join(' '),
      full_name: agentName,
      profile_color: color,
      user_token: participant?.identity,
      is_active: 1,
    },
    block: data.block || 'html',
    block_type: data.block_type || 'pilot_response',
    data: data.data,
    media: data.media || {},
    seq_number: data.seq_number || 1,
    reaction_count: data.reaction_count || 0,
    parent_id: data.parent_id || null,
    parent: data.parent || {},
    created:
      data.created ||
      getLocalLocalTimeFromUTC(
        data.timestamp || lastMessage.timestamp,
      )?.format?.('YYYY-MM-DD HH:mm:ss') ||
      new Date().toISOString(),
  };
};

export type WebSocketUpdateResult = {
  type: string;
  itemsUpdate?: (prevItems: MessageData[]) => MessageData[];
  streamItemsUpdate?:
    | ((prevState: MessageData[]) => MessageData[])
    | ((prevState: MessageData[]) => {
        newStreamItems: MessageData[];
        finalizedMessage: MessageData;
      });
  thinking?: boolean;
  streaming?: boolean;
  shouldScroll?: boolean;
  finalizeStreamItems?: boolean;
  dataLoading?: boolean;};

/**
 * Handle block event - process streaming message
 */
const handleBlockEvent = (
  data: MessageData,
  lastMessage: WebSocketMessage,
  currentPost: CurrentPost | null | undefined,
  items: MessageData[],
  streamItems: MessageData[],
  agentColor: string,
  userColor: string,
): WebSocketUpdateResult => {
  const participant = lastMessage?.participant;
  const participantMetadata = parseParticipantMetadata(participant);
  const isAgent = isAgentParticipant(participant, participantMetadata);

  const { msgRole, isAssistantMsg } = getMessageRole(data, isAgent);
  const color = isAssistantMsg ? agentColor : userColor;

  // Check if this is a call type with ended status
  const isCallType = data?.data?.cards?.type === 'call';
  const hasEndedCall =
    isCallType &&
    data?.data?.cards?.items?.some((item) => item.status === 'ended');

  // Append '-ended' suffix to block_id if call has ended
  let blockId = data.block_id || data.id;
  if (hasEndedCall && blockId && !blockId.endsWith('-ended')) {
    blockId = `${blockId}-ended`;
  }

  // Clone and modify data to append '-ended' to call IDs
  let modifiedData = data;
  if (hasEndedCall && data?.data?.cards?.items) {
    modifiedData = {
      ...data,
      block_id: blockId,
      data: {
        ...data.data,
        cards: {
          ...data.data.cards,
          items: data.data.cards.items.map((item) =>
            item.status === 'ended' && item.id && !item.id.endsWith('-ended')
              ? { ...item, id: `${item.id}-ended` }
              : item,
          ),
        },
      },
    };
  }

  const messageData = transformToMessageData(
    modifiedData,
    lastMessage,
    participant,
    participantMetadata,
    msgRole,
    color,
    currentPost,
  );

  // Check if message exists in items or streamItems
  const existsInItems = items.some((item) => item.block_id === blockId);
  const existingStreamIndex = streamItems.findIndex(
    (item) => item.block_id === blockId,
  );

  // Check for recent messages from the same user (within 2 seconds) that might be updates
  const twoSecondsAgo = Date.now() - 2000;
  const recentMessageIndex = items.findIndex((item) => {
    const itemTimestamp = new Date(item.created || '').getTime();
    const isSameRole = item.user?.role === msgRole;
    const isRecent = itemTimestamp > twoSecondsAgo;
    const hasNoCards = !item.data?.cards;
    return isSameRole && isRecent && hasNoCards;
  });

  const isFinal = data.data?.final;

  // Check if this message has cards
  const hasCards = data.data?.cards;

  // If we have cards and there's a recent message without cards, replace it
  if (hasCards && recentMessageIndex !== -1) {
    console.log(
      `🔄 Replacing recent message at index ${recentMessageIndex} with cards version`,
    );
    return {
      type: 'REPLACE_RECENT_MESSAGE',
      itemsUpdate: (prevItems: MessageData[]) => {
        const newItems = [...prevItems];
        newItems[recentMessageIndex] = messageData;
        return newItems;
      },
      thinking: false,
      streaming: false,
      shouldScroll: true,
    };
  }

  // Message already in items - update if final
  if (existsInItems) {
    if (isFinal) {
      return {
        type: 'UPDATE_EXISTING_ITEM',
        itemsUpdate: (prevItems: MessageData[]) =>
          prevItems.map((item) =>
            item.block_id === blockId
              ? {
                  ...item,
                  data: {
                    ...item.data,
                    content: data.data?.content,
                    final: data.data?.final,
                  },
                }
              : item,
          ),
        thinking: false,
        streaming: false,
        shouldScroll: true,
      };
    }
    return { type: 'NO_UPDATE' };
  }

  // Message exists in streamItems
  if (existingStreamIndex !== -1) {
    if (isFinal) {
      // Finalize message - move from streamItems to items
      return {
        type: 'FINALIZE_STREAM_ITEM',
        streamItemsUpdate: (prevState: MessageData[]) => {
          const finalizedMessage = {
            ...prevState[existingStreamIndex],
            data: {
              ...prevState[existingStreamIndex].data,
              content: data.data?.content,
              final: data.data?.final,
            },
          };
          return {
            newStreamItems: prevState.filter(
              (_, index) => index !== existingStreamIndex,
            ),
            finalizedMessage,
          };
        },
        thinking: false,
        streaming: false,
        shouldScroll: true,
      };
    } else {
      // Update streaming content
      return {
        type: 'UPDATE_STREAM_ITEM',
        streamItemsUpdate: (prevState: MessageData[]) =>
          prevState.map((item) =>
            item.block_id === blockId
              ? {
                  ...item,
                  data: {
                    ...item.data,
                    content: data.data?.content,
                    final: data.data?.final,
                  },
                }
              : item,
          ),
        thinking: false,
        streaming: true,
        shouldScroll: true,
      };
    }
  }

  // New message
  const isMessageFinal =
    data.data?.final === undefined || data.data?.final === true;

  if (isMessageFinal) {
    // Complete message - add directly to items
    return {
      type: 'ADD_NEW_ITEM',
      itemsUpdate: (prevItems: MessageData[]) => [...prevItems, messageData],
      thinking: false,
      streaming: false,
      shouldScroll: true,
    };
  } else {
    // Streaming message - add to streamItems
    return {
      type: 'ADD_NEW_STREAM_ITEM',
      streamItemsUpdate: (prevState: MessageData[]) => [
        ...prevState,
        messageData,
      ],
      thinking: false,
      streaming: true,
      shouldScroll: true,
    };
  }
};

/**
 * Process WebSocket message and return state updates
 */
export const processWebSocketMessage = (
  lastMessage: WebSocketMessage | null | undefined,
  currentPost: CurrentPost | null | undefined,
  items: MessageData[],
  streamItems: MessageData[],
  agentColor: string,
  userColor: string,
): WebSocketUpdateResult | null => {
  if (!lastMessage?.data) {
    return null;
  }

  console.log('🔔 WebSocket message received:', lastMessage.data);

  let data: MessageData;
  try {
    data = JSON.parse(lastMessage.data);
  } catch (error) {
    console.error('Error parsing WebSocket message:', error);
    return null;
  }

  console.log('AppConversation lastMessage changed:', {
    content: data?.data?.content,
    cards: data?.data?.cards,
    data: data,
  });

  // Handle block_response event (can have cards or just content)
  if (data?.event === 'block_response') {
    return handleBlockEvent(
      data,
      lastMessage,
      currentPost,
      items,
      streamItems,
      agentColor,
      userColor,
    );
  }
  // Handle block event (streaming messages)
  if (data?.event === 'block') {
    return handleBlockEvent(
      data,
      lastMessage,
      currentPost,
      items,
      streamItems,
      agentColor,
      userColor,
    );
  }

  // Handle location request
  if (data?.event === 'location_request') {
    const participant = lastMessage?.participant;
    const participantMetadata = parseParticipantMetadata(participant);
    const isAgent = isAgentParticipant(participant, participantMetadata);

    const { msgRole } = getMessageRole(data, isAgent);
    const color = agentColor; // Location requests are always from agent

    const messageData = transformToMessageData(
      data,
      lastMessage,
      participant,
      participantMetadata,
      msgRole,
      color,
      currentPost,
    );

    return {
      type: 'ADD_NEW_ITEM',
      itemsUpdate: (prevItems: MessageData[]) => [...prevItems, messageData],
      thinking: false,
      streaming: false,
      shouldScroll: true,
    };
  }

  // Handle location success - update existing location request
  if (data?.event === 'location_success') {
    const blockId = data.block_id || data.id;

    return {
      type: 'UPDATE_LOCATION_STATUS',
      itemsUpdate: (prevItems: MessageData[]) =>
        prevItems.map((item) =>
          item.block_id === blockId
            ? {
                ...item,
                block_type: 'location_success',
                data: {
                  ...item.data,
                  ...data.data,
                  block_type: 'location_success',
                },
              }
            : item,
        ),
      thinking: false,
      streaming: false,
      shouldScroll: true,
    };
  }

  // Handle location declined - update existing location request
  if (data?.event === 'location_declined') {
    const blockId = data.block_id || data.id;

    return {
      type: 'UPDATE_LOCATION_STATUS',
      itemsUpdate: (prevItems: MessageData[]) =>
        prevItems.map((item) =>
          item.block_id === blockId
            ? {
                ...item,
                block_type: 'location_declined',
                data: {
                  ...item.data,
                  block_type: 'location_declined',
                },
              }
            : item,
        ),
      thinking: false,
      streaming: false,
      shouldScroll: true,
    };
  }

  // Handle typing indicator
  if (data?.event === 'typing') {
    return {
      type: 'TYPING',
      thinking: true,
      shouldScroll: true,
    };
  }

  // Handle task end
  if (data?.event === 'task_end') {
    return {
      type: 'TASK_END',
      finalizeStreamItems: true,
      thinking: false,
      streaming: false,
      dataLoading: false,
    };
  }

  return null;
};

export type StateSetters = {
  setItems: React.Dispatch<React.SetStateAction<MessageData[]>>;
  setStreamItems: React.Dispatch<React.SetStateAction<MessageData[]>>;
  setThinking: React.Dispatch<React.SetStateAction<boolean>>;
  setStreaming: React.Dispatch<React.SetStateAction<boolean>>;
  setDataLoading?: React.Dispatch<React.SetStateAction<boolean>>;};

/**
 * Apply WebSocket message updates to component state
 */
export const applyWebSocketUpdates = (
  updates: WebSocketUpdateResult | null,
  setters: StateSetters,
  scrollToBottom?: () => void,
): void => {
  if (!updates) return;

  const {
    setItems,
    setStreamItems,
    setThinking,
    setStreaming,
    setDataLoading,
  } = setters;

  // Apply thinking state
  if (updates.thinking !== undefined) {
    setThinking(updates.thinking);
  }

  // Apply streaming state
  if (updates.streaming !== undefined) {
    setStreaming(updates.streaming);
  }

  // Apply data loading state
  if (updates.dataLoading !== undefined && setDataLoading) {
    setDataLoading(updates.dataLoading);
  }

  // Handle different update types
  switch (updates.type) {
    case 'REPLACE_RECENT_MESSAGE':
    case 'UPDATE_EXISTING_ITEM':
    case 'UPDATE_LOCATION_STATUS':
      if (updates.itemsUpdate) {
        setItems(updates.itemsUpdate);
      }
      break;

    case 'FINALIZE_STREAM_ITEM':
      if (updates.streamItemsUpdate) {
        setStreamItems((prevState) => {
          const result = (
            updates.streamItemsUpdate as (prevState: MessageData[]) => {
              newStreamItems: MessageData[];
              finalizedMessage: MessageData;
            }
          )(prevState);
          // Add finalized message to items
          setItems((prevItems) => [...prevItems, result.finalizedMessage]);
          return result.newStreamItems;
        });
      }
      break;

    case 'UPDATE_STREAM_ITEM':
      if (updates.streamItemsUpdate) {
        setStreamItems(
          updates.streamItemsUpdate as (
            prevState: MessageData[],
          ) => MessageData[],
        );
      }
      break;

    case 'ADD_NEW_ITEM':
      if (updates.itemsUpdate) {
        setItems(updates.itemsUpdate);
      }
      break;

    case 'ADD_NEW_STREAM_ITEM':
      if (updates.streamItemsUpdate) {
        setStreamItems(
          updates.streamItemsUpdate as (
            prevState: MessageData[],
          ) => MessageData[],
        );
      }
      break;

    case 'TASK_END':
      if (updates.finalizeStreamItems) {
        setStreamItems((prevState) => {
          setItems((prevItems) => [...prevItems, ...prevState]);
          return [];
        });
      }
      break;

    case 'TYPING':
      // Already handled thinking state above
      break;

    case 'NO_UPDATE':
      // No action needed
      break;

    default:
      console.warn('Unknown update type:', updates.type);
  }

  // Auto-scroll if needed
  if (updates.shouldScroll && scrollToBottom) {
    scrollToBottom();
  }
};

export type ProcessLiveKitOptions = {
  validator?: (data: Record<string, unknown>) => boolean;};

export type ParticipantInfo = {
  identity?: string;};

/**
 * Process LiveKit DataPacket and create message
 */
export const processLiveKitDataPacket = (
  payload: Uint8Array,
  participant: ParticipantInfo,
  kind: number,
  options: ProcessLiveKitOptions = {},
): (WebSocketMessage & { source: string; kind?: string }) | null => {
  const { validator } = options;

  try {
    // Decode binary payload to text
    const decoder = new TextDecoder();
    const strData = decoder.decode(payload);

    console.log(`📩 [DataPacket] Content:`, strData, validator);

    // Parse JSON data
    const parsedData = parseJsonSafely(strData, 'DataPacket');

    // Validate message data - only process if it contains required fields
    if (!validateMessageData(parsedData, validator)) {
      // Log detailed rejection reason
      const hasCards = (parsedData as MessageData)?.data?.cards;
      console.log(
        `🚫 [DataPacket] Message rejected - ${hasCards ? 'validation failed' : 'no cards found'}`,
        { hasCards, data: parsedData?.data, strData, parsedData },
      );
      return null;
    }

    console.log(`✅ [DataPacket] Message validated - cards found`);

    // Create formatted message
    const message = createLiveKitMessage({
      data: strData,
      source: 'livekit-datapacket',
      kind: kind === 1 ? 'reliable' : 'lossy', // DataPacket_Kind.RELIABLE = 1
    });

    console.log(`🔔 [DataPacket] Message created:`, message);
    return message;
  } catch (error) {
    console.error(`❌ [DataPacket] Processing failed:`, error);
    return null;
  }
};

/**
 * Process LiveKit TextStream and create message
 */
export const processLiveKitTextStream = (
  text: string,
  participantInfo: ParticipantInfo,
  streamInfo: StreamInfo,
  topic: string,
  options: ProcessLiveKitOptions = {},
):
  | (WebSocketMessage & {
      source: string;
      topic?: string;
      streamInfo?: StreamInfo;
    })
  | null => {
  const { validator } = options;

  try {
    console.log(
      `📨 [${topic}] Received text stream from ${participantInfo.identity}`,
    );
    console.log(
      `  Topic: ${streamInfo.topic}\n` +
        `  Timestamp: ${streamInfo.timestamp}\n` +
        `  ID: ${streamInfo.id}` +
        (streamInfo.size ? `\n  Size: ${streamInfo.size} bytes` : ''),
    );

    console.log(`📩 [${topic}] Content:`, text);

    // Parse and validate JSON
    const parsedData = parseJsonSafely(text, topic);
    if (parsedData) {
      console.log(`✅ [${topic}] Parsed data:`, parsedData);
    }

    // Validate message data
    if (!validateMessageData(parsedData, validator)) {
      console.log(`🚫 [${topic}] Message validation failed - ignoring`);
      return null;
    }

    // Create formatted message
    const message = createLiveKitMessage({
      data: text,
      source: 'livekit',
      topic,
      streamInfo,
    });

    console.log(`🔔 [${topic}] Message created:`, message);
    return message;
  } catch (error) {
    console.error(`❌ [${topic}] Processing failed:`, error);
    return null;
  }
};

/**
 * Create a validator function that checks for specific fields in message data
 */
export const createMessageValidator = (
  requiredFields: string | string[],
): ((parsedData: Record<string, unknown>) => boolean) => {
  const fields = Array.isArray(requiredFields)
    ? requiredFields
    : [requiredFields];

  return (parsedData: Record<string, unknown>): boolean => {
    // Check if at least one of the required fields exists
    const result = fields.some((fieldPath) => {
      const pathParts = fieldPath.split('.');
      let current: unknown = parsedData;

      for (const part of pathParts) {
        if (current == null || typeof current !== 'object') {
          return false;
        }
        current = (current as Record<string, unknown>)[part];
      }

      const exists = current !== undefined && current !== null;
      return exists;
    });

    return result;
  };
};
