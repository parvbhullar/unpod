'use client';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import {MessageBubbleContainer, MessageContent, MessageMeta, MessageWrapper,} from './index.styled';
import {getMarkdownComponents} from './MarkdownComponents';
import {getFormattedDate} from '@unpod/helpers/DateHelper';
import ProviderCards from './ProviderCards';
import WebCards from './WebCards';
import BookingCards from './BookingCards';
import CallCards from './CallCards';
import EventCards from './EventCards';
import PersonCards from './PersonCards';
import FileAttachment from './FileAttachment';
import LocationRequestCard from './LocationRequestCard';

type FileAttachmentItem = {
  media_id?: string | number;
  name?: string;
  media_type?: string;
  media_url?: string;
  url?: string;
  size?: number;
};

type ConversationMessage = {
  block_id?: string | number;
  created?: string;
  block_type?: string;
  data?: {
    content?: string;
    files?: FileAttachmentItem[];
    cards?: { type?: string };
    block_type?: string;
    [key: string]: unknown;
  };
  [key: string]: unknown;
};

type MessageBubbleProps = {
  message: ConversationMessage;
  isUser: boolean;
  isFirstInGroup: boolean;
  isLastInGroup: boolean;
  onLocationResponse?: (requestId: string | number, accepted: boolean) => void;
};

const MessageBubble = ({
                         message,
                         isUser,
                         isFirstInGroup,
                         isLastInGroup,
                         onLocationResponse,
                       }: MessageBubbleProps) => {
  const {data, created} = message;
  const content = data?.content || '';
  const files = data?.files || [];
  const blockType = data?.block_type || message.block_type;
  const markdownComponents = getMarkdownComponents(isUser);

  // Render content based on type
  const renderContent = () => {
    // Check for location request first
    if (
      blockType === 'location_request' ||
      blockType === 'location_success' ||
      blockType === 'location_declined'
    ) {
      return (
        <LocationRequestCard
          data={(data ?? {}) as any}
          onLocationResponse={onLocationResponse}
          status={blockType}
        />
      );
    }

    switch (data?.cards?.type) {
      case 'provider':
        return <ProviderCards data={data?.cards as any}/>;
      case 'web':
        return <WebCards data={data?.cards as any}/>;
      case 'booking':
        return <BookingCards data={data?.cards as any}/>;
      case 'call':
        return <CallCards data={data?.cards as any}/>;
      case 'event':
        return <EventCards data={data?.cards as any}/>;
      case 'person':
        return <PersonCards data={data?.cards as any}/>;
      default: {
        const hasFiles = files.length > 0;
        const hasContent = content.trim().length > 0;

        return (
          <MessageWrapper $isUser={isUser}>
            {hasFiles && (
              <FileAttachment
                files={files}
                isUser={isUser}
                hasContent={hasContent}
              />
            )}
            {hasContent && (
              <MessageContent>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw]}
                  components={markdownComponents}
                >
                  {content}
                </ReactMarkdown>
              </MessageContent>
            )}
          </MessageWrapper>
        );
      }
    }
  };

  // Cards and location requests are always from agents, so force left alignment
  const hasCards = !!data?.cards?.type;
  const isLocationRequest =
    blockType === 'location_request' ||
    blockType === 'location_success' ||
    blockType === 'location_declined';
  const effectiveIsUser = hasCards || isLocationRequest ? false : isUser;

  return (
    <MessageBubbleContainer
      $isUser={effectiveIsUser}
      $isFirstInGroup={isFirstInGroup}
      $isLastInGroup={isLastInGroup}
    >
      {/* Spacer for non-first messages to align with messages that have avatar */}
      {/* {isUser && !isFirstInGroup && (
        <div style={{ width: '36px', flexShrink: 0 }} />
      )} */}

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          maxWidth: effectiveIsUser ? '700px' : '100%',
          minWidth: 0,
          width: effectiveIsUser ? 'auto' : '100%',
          alignItems: effectiveIsUser ? 'flex-end' : 'flex-start',
        }}
      >
        {renderContent()}
        {isLastInGroup && !hasCards && !isLocationRequest && (
          <MessageMeta $isUser={isUser}>
            {getFormattedDate(created, 'hh:mm:ss A')}
          </MessageMeta>
        )}
      </div>

      {/* Show avatar on FIRST message of user group */}
      {/* {isUser && isFirstInGroup && (
        <UserAvatar $color={user?.profile_color}>
          {user?.name?.charAt(0)?.toUpperCase() || 'U'}
        </UserAvatar>
      )} */}
    </MessageBubbleContainer>
  );
};

export default MessageBubble;
