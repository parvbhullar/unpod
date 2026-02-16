import type { ReactNode } from 'react';
import { Divider, Space } from 'antd';
import AppClapBtn from '../AppClapBtn';
import AppCommentBtn from '../AppCommentBtn';

import { useAuthContext } from '@unpod/providers';
import AppCopyToClipboard from '../../third-party/AppCopyToClipboard';
import type { PostShare } from './AppShare';
import AppShare from './AppShare';

type AppPostFooterProps = {
  post?: PostShare;
  comment?: string | ReactNode;
  clapCount?: number;
  commentCount?: number;
  activeComment?: boolean;
  onClapClick?: (count: number) => void;
  onCommentClick?: () => void;
  hideComment?: boolean;
  hideClap?: boolean;
  isSharable?: boolean;
  children?: ReactNode;
  copyContent?: string;};

const AppPostFooter = ({
  post,
  comment,
  clapCount,
  commentCount,
  activeComment,
  onClapClick,
  onCommentClick,
  hideComment = false,
  hideClap = false,
  isSharable = false,
  children,
  copyContent,
}: AppPostFooterProps) => {
  const { isAuthenticated } = useAuthContext();

  return (
    <Space
      onClick={(e) => {
        e.stopPropagation();
      }}
      split={<Divider type="vertical" />}
      className="app-post-footer"
    >
      {copyContent && <AppCopyToClipboard text={copyContent} />}

      {isAuthenticated && !hideClap && (
        <AppClapBtn clapCount={clapCount} onClapClick={onClapClick} />
      )}

      {!hideComment && (
        <AppCommentBtn
          comment={comment}
          activeComment={activeComment}
          commentCount={commentCount}
          onCommentClick={onCommentClick}
        />
      )}
      {isSharable && <AppShare post={post} />}
      {children}
    </Space>
  );
};

export default AppPostFooter;
