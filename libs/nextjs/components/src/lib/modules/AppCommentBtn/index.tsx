import type { ReactNode } from 'react';
import { Space, Typography } from 'antd';

import styled from 'styled-components';
import { BsChatRightText } from 'react-icons/bs';
import { GlobalTheme } from '@unpod/constants';

export const StyledItemWrapper = styled(Space)`
  cursor: pointer;
  user-select: none;

  &:hover .ant-typography {
    color: ${({ theme }: { theme: GlobalTheme }) => theme.palette.primary};
  }
`;
export const StyledSpaceWrapper = styled(Space)<{ $activeComment?: boolean }>`
  cursor: pointer;
  user-select: none;
  color: ${({
    theme,
    $activeComment,
  }: {
    theme: GlobalTheme;
    $activeComment?: boolean;
  }) =>
    $activeComment ? theme.palette.primary : theme.palette.text.secondary};

  &:hover .ant-typography {
    color: ${({ theme }: { theme: GlobalTheme }) => theme.palette.primary};
  }
`;

type AppCommentBtnProps = {
  onCommentClick?: () => void;
  activeComment?: boolean;
  commentCount?: number;
  comment?: string | ReactNode;};

const AppCommentBtn = ({
  onCommentClick,
  activeComment,
  commentCount,
  comment,
}: AppCommentBtnProps) => {
  return (
    <StyledItemWrapper>
      {comment ? (
        <Typography.Text
          type="secondary"
          onClick={(e) => {
            e.stopPropagation();
            if (onCommentClick) onCommentClick();
          }}
        >
          {comment}
        </Typography.Text>
      ) : (
        <StyledSpaceWrapper
          $activeComment={activeComment}
          orientation="horizontal"
          onClick={(e) => {
            e.stopPropagation();
            if (onCommentClick) onCommentClick();
          }}
        >
          <BsChatRightText fontSize={20} />
          <Typography.Text>{commentCount}</Typography.Text>
        </StyledSpaceWrapper>
      )}
    </StyledItemWrapper>
  );
};

export default AppCommentBtn;

