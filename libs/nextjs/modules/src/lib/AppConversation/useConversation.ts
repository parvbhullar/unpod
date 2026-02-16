import type { Dispatch, SetStateAction } from 'react';
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from 'react';
import {
  getDataApi,
  useAuthContext,
  useGetDataApi,
  useInfoViewActionsContext,
} from '@unpod/providers';
import { tablePageSize } from '@unpod/constants';
import { applyWebSocketUpdates, processWebSocketMessage } from '@unpod/helpers';
import { useAgentConnection } from '@unpod/livekit/hooks/useAgentConnection';

type MessageData = {
  block_id?: string | number;
  block_type?: string;
  created?: string;
  user?: { role?: string; user_token?: boolean; profile_color?: string };
  data?: { content?: string; block_type?: string; [key: string]: any };
  [key: string]: any;
};

type ScrollRestoreInfo = {
  previousScrollHeight: number;
  previousScrollTop: number;
};

type UseConversationParams = {
  currentPost: { post_id: string | number };
  lastMessage?: any;
  setThinking: Dispatch<SetStateAction<boolean>>;
  setStreaming: Dispatch<SetStateAction<boolean>>;
  setDataLoading: Dispatch<SetStateAction<boolean>>;
  sendJsonMessage?: (payload: any) => void;
  onStartVoice?: (callback: () => void) => void | Promise<void>;
  voiceAssistant?: any;
};

export const useConversation = ({
  currentPost,
  lastMessage,
  setThinking,
  setStreaming,
  setDataLoading,
  sendJsonMessage,
  onStartVoice,
  voiceAssistant,
}: UseConversationParams) => {
  const { isLoading, visitorId, isAuthenticated } = useAuthContext();
  const {
    roomToken,
    connectionMode,
    setConnectionMode,
    connect,
    shouldConnect,
  } = useAgentConnection();
  const infoViewActionsContext = useInfoViewActionsContext() as any;
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);

  // State
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<MessageData[]>([]);
  const [streamItems, setStreamItems] = useState<MessageData[]>([]);
  const [hasMoreRecords, setHasMoreRecords] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [isRoomInitialized, setIsRoomInitialized] = useState(false);
  const [isAgentJoined] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<string | null>(null);
  const [agentColor] = useState('#666');
  const [userColor] = useState('#3f51b5');
  const [scrollRestoreInfo, setScrollRestoreInfo] =
    useState<ScrollRestoreInfo | null>(null);
  const [isLoadingOlderMessages, setIsLoadingOlderMessages] = useState(false);
  const [hasInitialLoad, setHasInitialLoad] = useState(false);

  // Fetch initial messages
  const [{ apiData, loading }, { setData, updateInitialUrl, setQueryParams }] =
    useGetDataApi(
      `conversation/${currentPost.post_id}/messages/`,
      { data: [] },
      { page: 1, page_size: tablePageSize },
      false,
    ) as any;

  // Initialize conversation
  useEffect(() => {
    if (!isLoading && visitorId) {
      updateInitialUrl(`conversation/${currentPost.post_id}/messages/`, false);
      setPage(1);

      if (isAuthenticated) {
        setQueryParams({ page: 1, page_size: tablePageSize });
      } else {
        setQueryParams({
          page: 1,
          page_size: tablePageSize,
          session_user: visitorId,
        });
      }
    }

    return () => {
      setItems([]);
      setData({ data: [] });
      setHasInitialLoad(false);
    };
  }, [currentPost.post_id, isLoading, isAuthenticated, visitorId]);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(
    (forceInstant = false) => {
      if (isLoadingOlderMessages || scrollRestoreInfo) {
        console.log('🚫 Blocked auto-scroll (restoration in progress)');
        return;
      }

      // Use requestAnimationFrame to ensure DOM has updated
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({
          behavior: forceInstant ? 'instant' : 'smooth',
          block: 'end',
        });
      });
    },
    [isLoadingOlderMessages, scrollRestoreInfo],
  );

  // Process fetched messages (initial load ONLY - run once)
  useEffect(() => {
    if (apiData?.data?.length > 0 && !hasInitialLoad) {
      setDataLoading(false);
      setHasMoreRecords(apiData.data.length === tablePageSize);

      const processedMessages = apiData.data
        .filter((item: any) => item.block_type !== 'sys_msg')
        .map((item: any) => {
          const msgRole = item.user?.role;
          const isAssistantMsg =
            msgRole === 'assistant' ||
            msgRole === 'agent' ||
            msgRole === 'system';
          const color = isAssistantMsg ? agentColor : userColor;

          return {
            ...item,
            user: {
              ...item.user,
              profile_color: item.user.profile_color || color,
            },
          };
        });

      setItems(processedMessages);
      setHasInitialLoad(true);
      setTimeout(() => scrollToBottom(), 100);
    }
  }, [apiData?.data, hasInitialLoad, agentColor, userColor, scrollToBottom]);

  // Restore scroll position after loading older messages
  useLayoutEffect(() => {
    if (scrollRestoreInfo && !loadingMore) {
      const { previousScrollHeight, previousScrollTop } = scrollRestoreInfo;
      const messagesContainer = messagesContainerRef.current;

      if (messagesContainer) {
        const currentScrollHeight = messagesContainer.scrollHeight;
        const heightDifference = currentScrollHeight - previousScrollHeight;

        if (heightDifference > 0) {
          messagesContainer.scrollTop = previousScrollTop + heightDifference;
        }

        setScrollRestoreInfo(null);
        setIsLoadingOlderMessages(false);
      }
    }
  }, [items, scrollRestoreInfo, loadingMore]);

  // Handle WebSocket messages
  useEffect(() => {
    const updates = processWebSocketMessage(
      lastMessage,
      currentPost as any,
      items as any,
      streamItems as any,
      agentColor,
      userColor,
    );

    if (updates) {
      applyWebSocketUpdates(
        updates as any,
        {
          setItems: setItems as any,
          setStreamItems: setStreamItems as any,
          setThinking: setThinking as any,
          setStreaming: setStreaming as any,
          setDataLoading: setDataLoading as any,
        },
        scrollToBottom,
      );
    }
  }, [lastMessage, scrollToBottom, currentPost.post_id]);

  // Track when agent joins the room
  /*  useEffect(() => {
    const agentParticipant = voiceAssistant?.audioTrack?.participant;

    if (agentParticipant) {
      console.log('🤖 Agent joined the room:', {
        identity: agentParticipant.identity,
        name: agentParticipant.name,
      });
      setIsAgentJoined(true);
    } else {
      setIsAgentJoined(false);
    }
  }, [voiceAssistant?.audioTrack?.participant]);*/

  // Send pending message when agent joins
  useEffect(() => {
    if (isAgentJoined && pendingMessage && sendJsonMessage) {
      console.log('📤 Agent joined - sending pending message:', pendingMessage);

      sendJsonMessage({
        event: 'message',
        data: {
          content: pendingMessage,
          block_type: 'text',
        },
      });

      setPendingMessage(null);
      scrollToBottom();
    }
  }, [isAgentJoined, pendingMessage, sendJsonMessage, scrollToBottom]);

  // Handle voice icon click
  const handleVoiceClick = useCallback(async () => {
    console.log('🎤 Voice icon clicked', {
      currentMode: connectionMode,
      hasRoomToken: !!roomToken,
    });

    if (connectionMode !== 'voice') {
      console.log('🎙️ Setting conversation mode to: voice');
      setConnectionMode('voice');
    }

    if (!roomToken && onStartVoice) {
      try {
        console.log('🔌 Generating new room token for voice mode...');
        await onStartVoice(() => {
          console.log('✅ Voice room token generated');
          setIsRoomInitialized(true);
        });
      } catch (error) {
        console.error('❌ Failed to generate room token:', error);
      }
    } else if (roomToken) {
      console.log('✅ Room token already exists, reusing for voice mode');
    } else {
      console.warn('⚠️ onStartVoice function not available');
    }
  }, [connectionMode, roomToken, onStartVoice, setConnectionMode]);

  // Auto-connect when mode is set to 'voice' and token exists
  useEffect(() => {
    if (connectionMode === 'voice' && roomToken && !shouldConnect && connect) {
      console.log('🔌 Connecting to LiveKit in voice mode...');
      connect();
    }
  }, [connectionMode, roomToken, shouldConnect, connect]);

  // Load older messages
  const loadOlderMessages = async (
    formatMessage: (descriptor: { id: string }) => string,
  ) => {
    if (loadingMore) return;

    setLoadingMore(true);
    setIsLoadingOlderMessages(true);

    try {
      const messagesContainer = messagesContainerRef.current;

      const previousScrollHeight = messagesContainer?.scrollHeight || 0;
      const previousScrollTop = messagesContainer?.scrollTop || 0;

      console.log('📍 Storing scroll position:', {
        previousScrollHeight,
        previousScrollTop,
      });

      const queryParams: {
        page: number;
        page_size: number;
        session_user?: string;
      } = {
        page: page + 1,
        page_size: tablePageSize,
      };

      if (!isAuthenticated && visitorId) {
        queryParams.session_user = visitorId;
      }

      console.log('📥 Loading older messages:', {
        currentPage: page,
        nextPage: page + 1,
        isAuthenticated,
        previousScrollHeight,
        previousScrollTop,
      });

      const data: any = await getDataApi(
        `conversation/${currentPost.post_id}/messages/`,
        infoViewActionsContext,
        queryParams,
      );

      if (data?.data?.length > 0) {
        const processedMessages = data.data
          .filter((item: any) => item.block_type !== 'sys_msg')
          .map((item: any) => {
            const msgRole = item.user?.role;
            const isAssistantMsg =
              msgRole === 'assistant' ||
              msgRole === 'agent' ||
              msgRole === 'system';
            const color = isAssistantMsg ? agentColor : userColor;

            return {
              ...item,
              user: {
                ...item.user,
                profile_color: item.user.profile_color || color,
              },
            };
          });

        console.log('✅ Loaded older messages:', {
          count: processedMessages.length,
          hasMore: data.data.length === tablePageSize,
        });

        setHasMoreRecords(data.data.length === tablePageSize);
        setPage(page + 1);

        setItems((prevState) => {
          const existingIds = new Set(
            prevState.map((msg: MessageData) => msg.block_id),
          );
          const newMessages = processedMessages.filter(
            (msg: MessageData) => !existingIds.has(msg.block_id),
          );

          if (newMessages.length < processedMessages.length) {
            console.warn(
              '⚠️ Filtered out duplicate messages:',
              processedMessages.length - newMessages.length,
            );
          }

          const updatedItems = [...newMessages, ...prevState];

          console.log('📝 Items updated:', {
            previousCount: prevState.length,
            newMessagesCount: newMessages.length,
            totalCount: updatedItems.length,
            newMessageIds: newMessages.map((m: MessageData) => m.block_id),
          });

          return updatedItems;
        });

        console.log('💾 Storing scroll restore info:', {
          previousScrollHeight,
          previousScrollTop,
        });
        setScrollRestoreInfo({
          previousScrollHeight,
          previousScrollTop,
        });
      } else {
        console.log('📭 No more older messages to load');
        setHasMoreRecords(false);
      }
    } catch (error) {
      console.error('❌ Error loading older messages:', error);

      if (infoViewActionsContext?.fetchError) {
        infoViewActionsContext.fetchError(
          formatMessage({ id: 'error.loadingMessages' }) ||
            'Failed to load older messages',
        );
      }

      setIsLoadingOlderMessages(false);
    } finally {
      setLoadingMore(false);
    }
  };

  // Send message
  const handleSendMessage = useCallback(
    async (messageData: string | { content: string; files?: unknown }) => {
      const message =
        typeof messageData === 'string' ? messageData : messageData.content;
      const files = typeof messageData === 'object' ? messageData.files : null;

      if ((message.trim() || !!files) && sendJsonMessage) {
        setThinking(true);

        if (!connectionMode) {
          console.log('💬 Setting conversation mode to: chat');
          setConnectionMode('chat');
        }

        const userMessage = {
          block_id: `temp-${Date.now()}`,
          user: {
            user_token: true,
            name: 'You',
            profile_color: userColor,
            role: 'user',
          },
          data: {
            content: message,
            final: true,
            ...(files ? { files } : {}),
          },
          created: new Date().toISOString(),
          block_type: 'text',
        };

        setItems((prev) => [...prev, userMessage]);

        // Scroll to show the new user message
        setTimeout(() => scrollToBottom(), 0);

        if (!isRoomInitialized && onStartVoice) {
          try {
            console.log('🔌 Connecting to LiveKit room...');
            await onStartVoice(() => {
              console.log('✅ LiveKit room token received');
              setIsRoomInitialized(true);
            });
          } catch (error) {
            console.error('❌ Failed to initialize room:', error);
          }
        }

        const messagePayload = {
          event: 'message',
          data: {
            content: message,
            block_type: 'text',
            ...(files ? { files } : {}),
          },
        };

        // if (isAgentJoined) {
        console.log(
          '📤 Agent already in room - sending message immediately',
          messagePayload,
        );
        sendJsonMessage(messagePayload);
        scrollToBottom();
        // } else {
        console.log('⏳ Waiting for agent to join - message pending');
        setPendingMessage(message);
        // }
      }
    },
    [
      sendJsonMessage,
      onStartVoice,
      isRoomInitialized,
      isAgentJoined,
      setPendingMessage,
      scrollToBottom,
      connectionMode,
      setConnectionMode,
    ],
  );

  // Helper to determine if message is from user
  const isUserMessage = (message: MessageData) => {
    const role = message.user?.role;
    const userToken = message.user?.user_token;
    const isAssistant =
      role === 'assistant' || role === 'agent' || role === 'system';
    return !isAssistant && (userToken === true || role === 'user');
  };

  // All messages to display
  const allMessages = [...items, ...streamItems].sort((a, b) => {
    const timeA = new Date(a.created ?? 0).getTime();
    const timeB = new Date(b.created ?? 0).getTime();
    return timeA - timeB;
  });

  return {
    // State
    items,
    streamItems,
    loading,
    loadingMore,
    hasMoreRecords,
    allMessages,
    roomToken,
    connectionMode,

    // Refs
    messagesEndRef,
    messagesContainerRef,

    // Functions
    loadOlderMessages,
    handleSendMessage,
    handleVoiceClick,
    isUserMessage,
  };
};
