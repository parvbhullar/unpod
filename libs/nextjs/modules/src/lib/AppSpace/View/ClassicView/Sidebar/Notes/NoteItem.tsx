import {Badge, Space, Tooltip, Typography} from 'antd';
import {changeDateStringFormat, getTimeFromNow,} from '@unpod/helpers/DateHelper';
import {getPostIcon} from '@unpod/helpers/PermissionHelper';
import {getStringFromHtml} from '@unpod/helpers/GlobalHelper';
import {
  StyledContent,
  StyledConversationHeader,
  StyledConversationItem,
  StyledConversationTime,
  StyledItem,
  StyledTitle,
} from './index.styled';
import UserAvatar from '@unpod/components/common/UserAvatar';
import AppLink from '@unpod/components/next/AppLink';

const {Paragraph, Text} = Typography;

const NoteItem = ({
                    thread,
                    onThreadClick,
                    activeNote,
                  }: {
  thread: any;
  onThreadClick: (thread: any) => void;
  activeNote?: any;
}) => {
  const onTitleClick = (event: any) => {
    event.preventDefault();

    onThreadClick(thread);
  };

  const postTitle =
    thread.title === 'No Title' ||
    thread.title === 'Write Title' ||
    thread.title === 'Upload Title'
      ? getStringFromHtml(thread.content || thread.block?.data?.content)
      : thread.title;

  return (
    <StyledConversationItem
      onClick={onTitleClick}
      className={activeNote?.slug === thread?.slug ? 'active' : ''}
    >
      <StyledItem>
        <UserAvatar user={thread.user} size={32}/>
      </StyledItem>

      <StyledContent>
        <StyledConversationHeader>
          <AppLink href={`/thread/${thread.slug}/`}>
            <StyledTitle
              className={'font-weight-medium'}
              ellipsis={{
                rows: 1,
                tooltip: postTitle,
              }}
            >
              {postTitle}
            </StyledTitle>
          </AppLink>
          {thread.created && (
            <Tooltip
              title={changeDateStringFormat(
                thread.created,
                'YYYY-MM-DD HH:mm:ss',
                'hh:mm A . DD MMM, YYYY',
              )}
            >
              <StyledConversationTime>
                {getTimeFromNow(thread.created)}
              </StyledConversationTime>
            </Tooltip>
          )}
        </StyledConversationHeader>

        <Paragraph
          type="secondary"
          ellipsis={{rows: 1}}
          style={{
            fontSize: 13,
            marginBottom: 3,
          }}
        >
          {getStringFromHtml(thread.content || thread.block?.data?.content)}
        </Paragraph>

        <Space align="center" size={6} wrap={true} style={{fontSize: 13}}>
          <Text
            className="text-capitalize"
            type="secondary"
            style={{fontSize: 13}}
          >
            {thread?.user?.full_name}
          </Text>
          <Tooltip title={thread?.privacy_type}>
            <span style={{display: 'inline-flex', alignItems: 'center'}}>
              {getPostIcon(thread?.privacy_type)}
            </span>
          </Tooltip>
          {thread.seen ? null : <Badge color="#796cff"/>}
        </Space>
      </StyledContent>
    </StyledConversationItem>
  );
};

export default NoteItem;
