import type { ReactNode } from 'react';
import { useMemo } from 'react';

import { Spin, Tooltip } from 'antd';
import { useRouter } from 'next/navigation';
import { downloadFile } from '@unpod/helpers/FileHelper';
import {
  getDataApi,
  useAuthContext,
  useInfoViewActionsContext,
} from '@unpod/providers';
import UserAvatar from '../../../common/UserAvatar';
import clsx from 'clsx';
import {
  StyledAvatar,
  StyledContent,
  StyledContentWrapper,
  StyledReplyContainer,
} from '../index.styled';
import UserMessage from './UserMessage';
import SystemMessage from './SystemMessage';

const items = [
  {
    label: 'Delete',
    key: 'delete',
    danger: true,
  },
];

const ReplyItem = ({
  reply,
  onReplyClick,
  onClapClick,
  replyParent,
  children,
  actionsStyle,
  onMenuClick,
  noteTitle,
  onSaveNote,
  hideReply = false,
  hideDelete = false,
}: {
  reply: any;
  onReplyClick?: (reply: any) => void;
  onClapClick?: (
    reply: any,
    reactionCount: number,
    isSubReply?: boolean,
    parentReply?: any,
  ) => void;
  replyParent?: any;
  children?: ReactNode;
  actionsStyle?: any;
  onMenuClick?: (key: any, block: any) => void;
  noteTitle?: string | null;
  onSaveNote?: (data: any) => void;
  hideReply?: boolean;
  hideDelete?: boolean;
}) => {
  const infoViewActionsContext = useInfoViewActionsContext();
  const { isAuthenticated } = useAuthContext();
  const router = useRouter();

  const onDownloadClick = (item: any) => {
    getDataApi('media/pre-signed-url/', infoViewActionsContext, {
      url: item.url,
    })
      .then((res: any) => {
        downloadFile(res.data.url);
      })
      .catch((response: any) => {
        infoViewActionsContext.showError(response.message);
      });
  };

  const { attachmentImages, attachmentFiles } = useMemo(() => {
    const filteredFiles = reply?.data?.files?.filter(
      (item: any) => item.file_type === 'image',
    );

    const mappedFiles = filteredFiles?.map((item: any) => ({
      ...item,
      media_url: item.url,
    }));

    const attachmentFiles = reply?.data?.files?.filter(
      (item: any) => item.file_type !== 'image',
    );

    return { attachmentImages: mappedFiles || [], attachmentFiles };
  }, [reply?.data?.files]);

  const onClickName = () => {
    if (isAuthenticated && !reply.user.user_token && reply.user.user_id) {
      router.push(
        `/ai-agents/${reply.user.user_id}/?source=thread&title=${reply.user.full_name}`,
      );
    }
  };

  return reply.user.role === 'system' ? (
    <StyledReplyContainer
      className={clsx({ 'user-question': reply.block === 'html' })}
    >
      <StyledAvatar>
        <Tooltip title={reply.user.full_name}>
          <UserAvatar user={reply.user} />
        </Tooltip>
      </StyledAvatar>

      <StyledContent>
        <StyledContentWrapper className="system-message">
          <Spin size="small" /> {reply.data.content}
        </StyledContentWrapper>
      </StyledContent>
    </StyledReplyContainer>
  ) : reply.user.role !== 'assistant' ? (
    <UserMessage
      reply={reply}
      replyParent={replyParent}
      onClapClick={onClapClick}
      onReplyClick={onReplyClick}
      onMenuClick={onMenuClick}
      items={items}
      isAuthenticated={isAuthenticated}
      user={reply.user}
      attachmentImages={attachmentImages}
      attachmentFiles={attachmentFiles}
      onDownloadClick={onDownloadClick}
      onSaveNote={onSaveNote}
      noteTitle={noteTitle}
      actionsStyle={actionsStyle}
      children={children}
      onClickName={onClickName}
      hideReply={hideReply}
      hideDelete={hideDelete}
    />
  ) : (
    <SystemMessage
      reply={reply}
      replyParent={replyParent}
      onClapClick={onClapClick}
      onReplyClick={onReplyClick}
      onMenuClick={onMenuClick}
      items={items}
      isAuthenticated={isAuthenticated}
      user={reply.user}
      attachmentImages={attachmentImages}
      attachmentFiles={attachmentFiles}
      onDownloadClick={onDownloadClick}
      onSaveNote={onSaveNote}
      noteTitle={noteTitle}
      actionsStyle={actionsStyle}
      children={children}
      onClickName={onClickName}
      hideReply={hideReply}
      hideDelete={hideDelete}
    />
  );
};

export default ReplyItem;
