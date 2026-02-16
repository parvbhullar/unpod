import { Tooltip, Typography } from 'antd';
import { getStringFromHtml } from '@unpod/helpers/GlobalHelper';
import UserAvatar from '@unpod/components/common/UserAvatar';
import {
  changeDateStringFormat,
  getTimeFromNow,
} from '@unpod/helpers/DateHelper';
import {
  StyledContent,
  StyledConversationItem,
  StyledItem,
  StyledListHeader,
  StyledTitle,
} from './index.styled';
import type { MouseEvent } from 'react';

const { Paragraph, Text } = Typography;

type ConversationThread = {
  slug?: string;
  title?: string;
  created?: string;
  content?: string;
  user?: Record<string, unknown>;
  block?: { data?: { content?: string } };
  [key: string]: unknown;
};

type ConversationItemProps = {
  thread: ConversationThread;
  activeConversation?: ConversationThread | null;
  onThreadClick: (thread: ConversationThread) => void;
};

const ConversationItem = ({
  thread,
  onThreadClick,
  activeConversation,
}: ConversationItemProps) => {
  const onTitleClick = (event: MouseEvent<HTMLDivElement>) => {
    event.preventDefault();
    onThreadClick(thread);
  };

  return (
    <StyledConversationItem
      onClick={onTitleClick}
      className={activeConversation?.slug === thread?.slug ? 'active' : ''}
    >
      <StyledItem>
        <UserAvatar user={thread.user} size={32} />
      </StyledItem>
      <StyledContent>
        <StyledListHeader>
          <StyledTitle
            className="text-capitalize title-text"
            level={5}
            ellipsis
          >
            {thread?.title}
          </StyledTitle>

          {thread.created ? (
            <Tooltip
              title={changeDateStringFormat(
                thread.created,
                'YYYY-MM-DD HH:mm:ss',
                'hh:mm A . DD MMM, YYYY',
              )}
            >
              <Text type="secondary" style={{ fontSize: 11 }}>
                {getTimeFromNow(thread.created)}
              </Text>
            </Tooltip>
          ) : null}
        </StyledListHeader>
        <Paragraph
          className="mb-0"
          type="secondary"
          style={{ maxWidth: '95%', fontSize: 13 }}
          ellipsis
        >
          {getStringFromHtml(thread.content || thread.block?.data?.content)}
        </Paragraph>
      </StyledContent>
    </StyledConversationItem>
  );
};

export default ConversationItem;
