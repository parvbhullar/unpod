import styled from 'styled-components';
import { Typography } from 'antd';

export const StyledRowItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;

  &.borderless {
    border-bottom: none;
  }
`;

export const StyledContent = styled.div`
  flex: 1;
`;

export const StyledTitle = styled(Typography.Title)`
  font-size: 14px !important;
  font-weight: 500;
  margin-bottom: 0 !important;
`;

export const StyledDesc = styled.div`
  font-size: 13px;
  color: #888;
`;
export const StyledPhoneInput = styled.div`
  margin-top: 8px;

  .react-tel-input .form-control {
    width: 62%;
  }
`;
