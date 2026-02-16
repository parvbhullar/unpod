import { Popover } from 'antd';
import styled from 'styled-components';

export const StyledAppConfirmPopover = styled(Popover)`
  & .ant-popover-title {
    padding: 12px 16px 6px;
  }
`;

export const StyledConfirmDeleteActions = styled.div`
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;

  & .ant-btn {
    font-size: 12px;
    padding: 2px 10px;
    height: 25px;
  }
`;

export const StyledMessageBody = styled.p`
  max-width: 260px;
`;
