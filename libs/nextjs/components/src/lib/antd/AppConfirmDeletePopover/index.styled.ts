import { Popover } from 'antd';
import styled from 'styled-components';

export const StyledAppDeletePopoverWrapper = styled(Popover)`
  & .ant-popover-title {
    padding: 12px 16px 6px;
  }

  & .message-body {
    max-width: 260px;
  }
`;

export const StyledConfirmDeleteActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;

  & .ant-btn:last-child {
    margin-left: 10px;
  }
`;

export const StyledMessageBody = styled.p`
  max-width: 260px;
`;
