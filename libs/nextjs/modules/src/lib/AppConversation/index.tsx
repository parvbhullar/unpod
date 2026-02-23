'use client';
import type {Dispatch, RefObject, SetStateAction} from 'react';
import {Spin} from 'antd';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import {
  ConversationContainer,
  ConversationHeader,
  ConversationInput,
  ConversationMessages,
  ConversationMessagesInner,
  DateSeparator,
  LoadMoreButton,
} from './index.styled';
import dayjs from 'dayjs';
import AgentView from '../AppPost/AgentView';
import {VoiceOverlay} from '../AppPost/index.styled';
import {useIntl} from 'react-intl';
import {useConversation} from './useConversation';
import UnpodLogoAnimation from '@unpod/components/common/UnpodLogoAnimation';

type CurrentPost = {
  post_id: string | number;
  title?: string;
};

type FileAttachmentItem = {
  media_id?: string | number;
  name?: string;
  media_type?: string;
  media_url?: string;
  url?: string;
  size?: number;
};

type ConversationMessageItem = {
  block_id?: string | number;
  created?: string;
  data?: {
    content?: string;
    files?: FileAttachmentItem[];
    cards?: { type?: string };
    block_type?: string;
    [key: string]: unknown;
  };
  block_type?: string;
  [key: string]: unknown;
};

type AppConversationProps = {
  currentPost: CurrentPost;
  lastMessage?: unknown;
  thinking: boolean;
  setThinking: Dispatch<SetStateAction<boolean>>;
  setStreaming: Dispatch<SetStateAction<boolean>>;
  setDataLoading: Dispatch<SetStateAction<boolean>>;
  sendJsonMessage?: (payload: unknown) => void;
  onStartVoice?: (callback: () => void) => void | Promise<void>;
  voiceAssistant?: unknown;
  onLocationResponse?: (requestId: string | number, accepted: boolean) => void;
  isGeneratingToken?: boolean;
};

const AppConversation = ({
                           currentPost,
                           lastMessage,
                           thinking,
                           setThinking,
                           setStreaming,
                           setDataLoading,
                           sendJsonMessage,
                           onStartVoice,
                           voiceAssistant,
                           onLocationResponse,
                           isGeneratingToken,
                         }: AppConversationProps) => {
  const {formatMessage} = useIntl();

  // Use custom hook for all business logic
  const {
    items,
    streamItems,
    loading,
    loadingMore,
    hasMoreRecords,
    allMessages,
    roomToken,
    connectionMode,
    messagesEndRef,
    messagesContainerRef,
    loadOlderMessages,
    handleSendMessage,
    handleVoiceClick,
    isUserMessage,
  } = useConversation({
    currentPost,
    lastMessage,
    setThinking,
    setStreaming,
    setDataLoading,
    sendJsonMessage,
    onStartVoice,
    voiceAssistant,
  }) as unknown as {
    items: ConversationMessageItem[];
    streamItems: ConversationMessageItem[];
    loading: boolean;
    loadingMore: boolean;
    hasMoreRecords: boolean;
    allMessages: ConversationMessageItem[];
    roomToken?: string;
    connectionMode?: string;
    messagesEndRef: RefObject<HTMLDivElement>;
    messagesContainerRef: RefObject<HTMLDivElement>;
    loadOlderMessages: (
      formatMessage: (descriptor: { id: string }) => string,
    ) => void;
    handleSendMessage: (payload: { content: string; files?: unknown }) => void;
    handleVoiceClick: () => void;
    isUserMessage: (message: ConversationMessageItem) => boolean;
  };

  // Helper function to format date labels
  const getDateLabel = (dateString?: string) => {
    const messageDate = dayjs(dateString);
    const today = dayjs().startOf('day');
    const yesterday = today.subtract(1, 'day');

    if (messageDate.isSame(today, 'day')) {
      return formatMessage({id: 'day.today'});
    } else if (messageDate.isSame(yesterday, 'day')) {
      return formatMessage({id: 'day.yesterday'});
    } else if (messageDate.isAfter(today.subtract(7, 'days'))) {
      // Within last week - show day name
      return messageDate.format('dddd');
    } else {
      // Older than a week - show full date
      return messageDate.format('MMMM D, YYYY');
    }
  };

  // Helper function to check if two dates are on different days
  const isDifferentDay = (date1?: string, date2?: string) => {
    if (!date1 || !date2) return true;
    return !dayjs(date1).isSame(dayjs(date2), 'day');
  };

  console.log('Rendering AppConversation with messages:', {
    roomToken,
    connectionMode,
  });
  return (
    <ConversationContainer>
      {/* Header */}
      <ConversationHeader>
        <h3 style={{margin: 0, fontSize: '16px', fontWeight: 600}}>
          {currentPost.title ||
            formatMessage({id: 'conversation.conversation'})}
        </h3>
      </ConversationHeader>

      {/* Messages */}
      <ConversationMessages
        ref={messagesContainerRef}
        style={{
          // Instant scrolling (no smooth animation)
          scrollBehavior: 'auto',
        }}
      >
        {/* Inject CSS for shimmer animation */}
        <style>{`
          @keyframes shimmer {
            0% {
              background-position: -1000px 0;
            }
            100% {
              background-position: 1000px 0;
            }
          }
        `}</style>
        <ConversationMessagesInner>
          {/* Load More Button with Shimmer State */}
          {hasMoreRecords && (
            <LoadMoreButton
              onClick={() => loadOlderMessages(formatMessage)}
              disabled={loadingMore}
              style={{
                position: 'relative',
                overflow: 'hidden',
                ...(loadingMore && {
                  color: 'transparent',
                  pointerEvents: 'none',
                }),
              }}
            >
              {loadingMore && (
                <div
                  style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background:
                      'linear-gradient(90deg, rgba(0,0,0,0.05) 25%, rgba(0,0,0,0.1) 50%, rgba(0,0,0,0.05) 75%)',
                    backgroundSize: '1000px 100%',
                    animation: 'shimmer 2s infinite linear',
                  }}
                />
              )}
              <span style={{visibility: loadingMore ? 'hidden' : 'visible'}}>
                {formatMessage({id: 'common.loadOlderMessages'})}
              </span>
            </LoadMoreButton>
          )}

          {/* Loading Spinner */}
          {loading && items.length === 0 && (
            <div style={{textAlign: 'center', padding: '40px'}}>
              <Spin/>
            </div>
          )}

          {/* Message List */}
          {allMessages.map((message, index) => {
            const isUser = isUserMessage(message);
            const prevMessage = index > 0 ? allMessages[index - 1] : null;
            const nextMessage =
              index < allMessages.length - 1 ? allMessages[index + 1] : null;

            const isFirstInGroup =
              !prevMessage || isUserMessage(prevMessage) !== isUser;
            const isLastInGroup =
              !nextMessage || isUserMessage(nextMessage) !== isUser;

            // Check if we need to show a date separator
            const showDateSeparator =
              !prevMessage ||
              isDifferentDay(prevMessage.created, message.created);

            return (
              <div key={message.block_id ?? index}>
                {/* Date Separator */}
                {showDateSeparator && (
                  <DateSeparator>
                    <span>{getDateLabel(message.created)}</span>
                  </DateSeparator>
                )}

                {/* Message with data-message-id for scroll anchor */}
                <div data-message-id={message.block_id}>
                  <MessageBubble
                    message={message}
                    isUser={isUser}
                    isFirstInGroup={isFirstInGroup}
                    isLastInGroup={isLastInGroup}
                    onLocationResponse={onLocationResponse}
                  />
                </div>
              </div>
            );
          })}
          {/* Thinking Indicator */}
          {(thinking || isGeneratingToken) && streamItems.length === 0 && (
            <UnpodLogoAnimation size={80} showOrbits={false} showGlow={true}/>
          )}

          <div ref={messagesEndRef}/>
        </ConversationMessagesInner>
      </ConversationMessages>

      {/* Input */}
      <ConversationInput>
        <ChatInput
          onSend={handleSendMessage}
          // disabled={thinking || !sendJsonMessage || isGeneratingToken}
          thinking={thinking || isGeneratingToken}
          onStartVoice={handleVoiceClick}
          isGeneratingToken={isGeneratingToken}
        >
          {roomToken && connectionMode === 'voice' && (
            <VoiceOverlay show={!!roomToken}>
              <AgentView spaceView={true}/>
            </VoiceOverlay>
          )}
        </ChatInput>
      </ConversationInput>
    </ConversationContainer>
  );
};
export default AppConversation;
