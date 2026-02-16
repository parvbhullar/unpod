import {
  AssistantBubble,
  AssistantChatRow,
  AvatarContainer,
  MessageMeta,
  MessageWrapper,
  UserBubble,
  UserChatRow,
} from './index.styled';
import { useAppSpaceContext } from '@unpod/providers';
import AppList from '@unpod/components/common/AppList';
import { UserOutlined } from '@ant-design/icons';
import { getFormattedDate } from '@unpod/helpers/DateHelper';
import UserAvatar from '@unpod/components/common/UserAvatar';
import { useMediaQuery } from 'react-responsive';
import { DesktopWidthQuery } from '@unpod/constants';

const Conversations = () => {
  const { activeCall } = useAppSpaceContext();
  const mobileScreen = useMediaQuery(DesktopWidthQuery);

  const transcript = activeCall?.output?.transcript as any;

  // Transform transcript into structured conversation array
  const data = (() => {
    if (!transcript) return [];

    // If already an array with proper structure, return as-is
    if (Array.isArray(transcript) && transcript.length > 0) {
      return transcript;
    }

    // If transcript is a string
    if (typeof transcript === 'string') {
      // First, try to parse as JSON
      try {
        const parsed = JSON.parse(transcript);
        if (Array.isArray(parsed)) {
          return parsed;
        }
      } catch {
        // Not JSON, continue to text parsing
      }

      // Parse "User:" and "AI:" format
      const messages: any[] = [];
      const lines = transcript.split('\n').filter((line) => line.trim());

      lines.forEach((line) => {
        const trimmedLine = line.trim();
        if (trimmedLine.startsWith('User:')) {
          messages.push({
            role: 'user',
            content: trimmedLine.substring(5).trim(),
            user_id: 'unknown',
            timestamp: '',
          });
        } else if (trimmedLine.startsWith('AI:')) {
          messages.push({
            role: 'assistant',
            content: trimmedLine.substring(3).trim(),
            user_id: null,
            timestamp: '',
          });
        }
      });

      return messages;
    }

    // If transcript is an object with messages property
    if (transcript?.messages && Array.isArray(transcript.messages)) {
      return transcript.messages;
    }

    // Default: return empty array for unexpected formats
    return [];
  })();

  const renderUserMessage = (item: any, index: number) => (
    <UserChatRow key={index}>
      <MessageWrapper $isUser>
        <UserBubble>{item?.content}</UserBubble>
        {item?.timestamp && (
          <MessageMeta>
            {getFormattedDate(item.timestamp, 'hh:mm A', true)}
          </MessageMeta>
        )}
      </MessageWrapper>
      <AvatarContainer $isUser>
        <UserOutlined />
      </AvatarContainer>
    </UserChatRow>
  );

  const renderAssistantMessage = (item: any, index: number) => (
    <AssistantChatRow key={index}>
      <UserAvatar
        shape="square"
        src="/images/unpod/logo-icon.svg"
        bgColor="transparent"
        size={mobileScreen ? 25 : undefined}
      />
      <MessageWrapper>
        <AssistantBubble>{item?.content}</AssistantBubble>
        {item?.timestamp && (
          <MessageMeta>
            {getFormattedDate(item.timestamp, 'hh:mm A', true)}
          </MessageMeta>
        )}
      </MessageWrapper>
    </AssistantChatRow>
  );

  return (
    <AppList
      data={data}
      itemSpacing={0}
      style={{
        height: 'calc(100vh - 135px)',
      }}
      renderItem={(item: any, index: number) =>
        item.role === 'user'
          ? renderUserMessage(item, index)
          : renderAssistantMessage(item, index)
      }
    />
  );
};

export default Conversations;
